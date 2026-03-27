"""WHOOP daily sync Lambda handler.

Fetches recovery and sleep data from WHOOP API v1, writes to S3 Bronze.
Triggered by EventBridge cron(0 6 * * ? *).
"""

import json
import logging
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

import os

from shared.constants import (
    SSM_WHOOP_ACCESS_TOKEN,
    SSM_WHOOP_CLIENT_ID,
    SSM_WHOOP_CLIENT_SECRET,
    SSM_WHOOP_REFRESH_TOKEN,
    SSM_WHOOP_REFRESH_TOKEN_EXPIRY,
    WHOOP_API_BASE,
    WHOOP_TOKEN_URL,
)
from shared.s3_writer import write_jsonl

import boto3

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

_ssm_client = None
_sns_client = None

BACKOFF_DELAYS = [1, 2, 4]
EXPIRY_WARNING_DAYS = 30
_USER_AGENT = "IronLog/1.0 (Lambda; WHOOP-Sync)"


def _get_ssm_client():
    global _ssm_client
    if _ssm_client is None:
        _ssm_client = boto3.client("ssm")
    return _ssm_client


def _get_sns_client():
    global _sns_client
    if _sns_client is None:
        _sns_client = boto3.client("sns")
    return _sns_client


def reset_clients():
    """Reset cached clients. Used in tests."""
    global _ssm_client, _sns_client
    _ssm_client = None
    _sns_client = None


def _get_ssm_param(name):
    resp = _get_ssm_client().get_parameter(Name=name, WithDecryption=True)
    return resp["Parameter"]["Value"]


def _put_ssm_param(name, value, secure=True):
    _get_ssm_client().put_parameter(
        Name=name,
        Value=value,
        Type="SecureString" if secure else "String",
        Overwrite=True,
    )


def _refresh_access_token():
    """Refresh WHOOP OAuth tokens. Returns new access token."""
    client_id = _get_ssm_param(SSM_WHOOP_CLIENT_ID)
    client_secret = _get_ssm_param(SSM_WHOOP_CLIENT_SECRET)
    refresh_token = _get_ssm_param(SSM_WHOOP_REFRESH_TOKEN)

    body = urllib.parse.urlencode({
        "grant_type": "refresh_token",
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
    }).encode("utf-8")

    req = urllib.request.Request(
        WHOOP_TOKEN_URL,
        data=body,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": _USER_AGENT,
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        logger.error("Token refresh failed: %d %s", e.code, e.read().decode())
        raise

    new_access = data["access_token"]
    new_refresh = data.get("refresh_token", refresh_token)

    _put_ssm_param(SSM_WHOOP_ACCESS_TOKEN, new_access)
    _put_ssm_param(SSM_WHOOP_REFRESH_TOKEN, new_refresh)

    # Compute and store expiry if expires_in is present
    if "expires_in" in data:
        expiry = datetime.now(timezone.utc) + timedelta(seconds=data["expires_in"])
        _put_ssm_param(
            SSM_WHOOP_REFRESH_TOKEN_EXPIRY,
            expiry.isoformat(),
            secure=False,
        )

    logger.info("WHOOP tokens refreshed successfully")
    return new_access


def _check_token_expiry():
    """Publish SNS alert if refresh token expires within 30 days."""
    expiry_str = _get_ssm_param(SSM_WHOOP_REFRESH_TOKEN_EXPIRY)
    try:
        expiry = datetime.fromisoformat(expiry_str)
    except ValueError:
        logger.warning("Could not parse refresh token expiry: %s", expiry_str)
        return

    days_remaining = (expiry - datetime.now(timezone.utc)).days
    if days_remaining < EXPIRY_WARNING_DAYS:
        topic_arn = os.environ.get("SNS_TOPIC_ARN", "")
        if not topic_arn:
            logger.warning("SNS_TOPIC_ARN not set, skipping expiry alert")
            return
        msg = (
            f"WHOOP refresh token expires in {days_remaining} days "
            f"({expiry.isoformat()}). Re-authorize at WHOOP developer portal "
            f"and update SSM parameters."
        )
        _get_sns_client().publish(
            TopicArn=topic_arn,
            Subject="IronLog: WHOOP Token Expiry Warning",
            Message=msg,
        )
        logger.warning("Token expiry alert sent: %d days remaining", days_remaining)


def _whoop_api_call(url, access_token):
    """Make a single WHOOP API call with backoff for 429."""
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {access_token}",
            "User-Agent": _USER_AGENT,
        },
        method="GET",
    )

    for attempt, delay in enumerate(BACKOFF_DELAYS):
        try:
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < len(BACKOFF_DELAYS) - 1:
                logger.warning("WHOOP 429, backing off %ds", delay)
                time.sleep(delay)
                continue
            raise

    # Should not reach here, but just in case
    raise RuntimeError("Exhausted retries")  # pragma: no cover


def _whoop_request(path, access_token, params=None):
    """GET from WHOOP API with 429 backoff and 401 auto-refresh."""
    url = f"{WHOOP_API_BASE}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)

    try:
        return _whoop_api_call(url, access_token)
    except urllib.error.HTTPError as e:
        if e.code == 401:
            logger.info("Access token expired, refreshing")
            new_token = _refresh_access_token()
            return _whoop_api_call(url, new_token)
        raise


def _fetch_paginated(path, access_token, params=None):
    """Fetch all pages from a WHOOP API endpoint."""
    params = dict(params or {})
    all_records = []

    while True:
        data = _whoop_request(path, access_token, params)
        records = data.get("records", [])
        all_records.extend(records)

        next_token = data.get("next_token")
        if not next_token:
            break
        params["nextToken"] = next_token

    return all_records


def _get_bucket():
    return os.environ.get("DATA_LAKE_BUCKET", "ironlog-data-lake")


def handler(event, context):
    """Daily WHOOP sync entry point."""
    now = datetime.now(timezone.utc)
    start = (now - timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    end = now.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    sync_ts = now.isoformat()

    # Step 1: Refresh tokens proactively
    access_token = _refresh_access_token()

    # Step 2: Check refresh token expiry
    _check_token_expiry()

    # Step 3: Fetch recovery and sleep data
    params = {"start": start, "end": end}

    recovery_records = _fetch_paginated("/recovery", access_token, params)
    sleep_records = _fetch_paginated("/activity/sleep", access_token, params)

    # Step 4: Add sync metadata
    for r in recovery_records:
        r["_sync_timestamp"] = sync_ts
    for r in sleep_records:
        r["_sync_timestamp"] = sync_ts

    # Step 5: Write to S3 Bronze
    bucket = _get_bucket()
    keys_written = []

    if recovery_records:
        key = write_jsonl(recovery_records, "recovery", bucket)
        keys_written.append(key)
        logger.info("Wrote %d recovery records to %s", len(recovery_records), key)

    if sleep_records:
        key = write_jsonl(sleep_records, "sleep", bucket)
        keys_written.append(key)
        logger.info("Wrote %d sleep records to %s", len(sleep_records), key)

    summary = {
        "status": "success",
        "recovery_count": len(recovery_records),
        "sleep_count": len(sleep_records),
        "keys_written": keys_written,
    }
    logger.info("WHOOP sync complete: %s", json.dumps(summary))
    return summary
