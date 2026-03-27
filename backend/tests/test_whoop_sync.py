"""Tests for WHOOP sync Lambda handler."""

import gzip
import io
import json
import urllib.error
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import boto3
import pytest

from handlers.whoop_sync import (
    _check_token_expiry,
    _fetch_paginated,
    _refresh_access_token,
    _whoop_api_call,
    _whoop_request,
    handler,
)


# --- Helpers ---


def _mock_http_response(body, status=200):
    """Create a mock urllib response."""
    data = json.dumps(body).encode("utf-8")
    mock = MagicMock()
    mock.read.return_value = data
    mock.status = status
    mock.__enter__ = MagicMock(return_value=mock)
    mock.__exit__ = MagicMock(return_value=False)
    return mock


def _mock_http_error(code, body=None):
    """Create an HTTPError."""
    body_bytes = json.dumps(body or {}).encode("utf-8")
    return urllib.error.HTTPError(
        url="https://api.prod.whoop.com/test",
        code=code,
        msg=f"HTTP {code}",
        hdrs={},
        fp=io.BytesIO(body_bytes),
    )


SAMPLE_RECOVERY = {
    "cycle_id": "12345",
    "recovery_score": 85.0,
    "resting_heart_rate": 52.0,
    "hrv_rmssd": 65.3,
    "spo2_percentage": 97.0,
    "skin_temp_celsius": 33.5,
    "created_at": "2026-03-23T06:00:00Z",
    "updated_at": "2026-03-23T06:00:00Z",
}

SAMPLE_SLEEP = {
    "sleep_id": "67890",
    "start": "2026-03-22T23:00:00Z",
    "end": "2026-03-23T07:00:00Z",
    "score_total_sleep_duration": 28800000,
    "score_rem_sleep_duration": 7200000,
    "score_deep_sleep_duration": 5400000,
    "score_light_sleep_duration": 14400000,
    "score_awake_duration": 1800000,
    "score_sleep_efficiency": 0.94,
    "score_respiratory_rate": 15.2,
    "created_at": "2026-03-23T07:00:00Z",
    "updated_at": "2026-03-23T07:00:00Z",
}


# --- Token Refresh Tests ---


class TestTokenRefresh:
    @patch("handlers.whoop_sync.urllib.request.urlopen")
    def test_refresh_success(self, mock_urlopen):
        mock_urlopen.return_value = _mock_http_response({
            "access_token": "new-access-123",
            "refresh_token": "new-refresh-456",
            "expires_in": 86400,
        })

        result = _refresh_access_token()

        assert result == "new-access-123"

        # Verify tokens written back to SSM
        ssm = boto3.client("ssm", region_name="eu-west-3")
        access = ssm.get_parameter(
            Name="/ironlog/whoop-access-token", WithDecryption=True
        )["Parameter"]["Value"]
        assert access == "new-access-123"

        refresh = ssm.get_parameter(
            Name="/ironlog/whoop-refresh-token", WithDecryption=True
        )["Parameter"]["Value"]
        assert refresh == "new-refresh-456"

    @patch("handlers.whoop_sync.urllib.request.urlopen")
    def test_refresh_failure_raises(self, mock_urlopen):
        mock_urlopen.side_effect = _mock_http_error(401, {"error": "invalid_grant"})

        with pytest.raises(urllib.error.HTTPError):
            _refresh_access_token()

    @patch("handlers.whoop_sync.urllib.request.urlopen")
    def test_refresh_preserves_refresh_token_if_not_returned(self, mock_urlopen):
        mock_urlopen.return_value = _mock_http_response({
            "access_token": "new-access-789",
        })

        _refresh_access_token()

        ssm = boto3.client("ssm", region_name="eu-west-3")
        refresh = ssm.get_parameter(
            Name="/ironlog/whoop-refresh-token", WithDecryption=True
        )["Parameter"]["Value"]
        assert refresh == "test-refresh-token"  # unchanged from conftest


# --- Token Expiry Alert Tests ---


class TestTokenExpiryAlert:
    def test_no_alert_when_expiry_far(self):
        ssm = boto3.client("ssm", region_name="eu-west-3")
        future = (datetime.now(timezone.utc) + timedelta(days=60)).isoformat()
        ssm.put_parameter(
            Name="/ironlog/whoop-refresh-token-expiry",
            Value=future,
            Type="String",
            Overwrite=True,
        )

        # Should not raise or publish
        _check_token_expiry()

    def test_alert_when_expiry_within_30_days(self, monkeypatch):
        ssm = boto3.client("ssm", region_name="eu-west-3")
        near = (datetime.now(timezone.utc) + timedelta(days=15)).isoformat()
        ssm.put_parameter(
            Name="/ironlog/whoop-refresh-token-expiry",
            Value=near,
            Type="String",
            Overwrite=True,
        )

        sns = boto3.client("sns", region_name="eu-west-3")
        topics = sns.list_topics()["Topics"]
        topic_arn = topics[0]["TopicArn"]
        monkeypatch.setenv("SNS_TOPIC_ARN", topic_arn)

        _check_token_expiry()

    def test_alert_when_expiry_past(self, monkeypatch):
        ssm = boto3.client("ssm", region_name="eu-west-3")
        past = (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()
        ssm.put_parameter(
            Name="/ironlog/whoop-refresh-token-expiry",
            Value=past,
            Type="String",
            Overwrite=True,
        )

        sns = boto3.client("sns", region_name="eu-west-3")
        topics = sns.list_topics()["Topics"]
        topic_arn = topics[0]["TopicArn"]
        monkeypatch.setenv("SNS_TOPIC_ARN", topic_arn)

        _check_token_expiry()


# --- API Call Tests ---


class TestWhoopApiCall:
    @patch("handlers.whoop_sync.urllib.request.urlopen")
    def test_successful_get(self, mock_urlopen):
        expected = {"records": [SAMPLE_RECOVERY]}
        mock_urlopen.return_value = _mock_http_response(expected)

        result = _whoop_api_call(
            "https://api.prod.whoop.com/developer/v1/recovery",
            "test-token",
        )
        assert result == expected

    @patch("handlers.whoop_sync.urllib.request.urlopen")
    @patch("handlers.whoop_sync.time.sleep")
    def test_429_retry_success(self, mock_sleep, mock_urlopen):
        expected = {"records": [SAMPLE_RECOVERY]}
        mock_urlopen.side_effect = [
            _mock_http_error(429),
            _mock_http_response(expected),
        ]

        result = _whoop_api_call(
            "https://api.prod.whoop.com/developer/v1/recovery",
            "test-token",
        )
        assert result == expected
        mock_sleep.assert_called_once_with(1)

    @patch("handlers.whoop_sync.urllib.request.urlopen")
    @patch("handlers.whoop_sync.time.sleep")
    def test_429_exhausted_retries(self, mock_sleep, mock_urlopen):
        mock_urlopen.side_effect = [
            _mock_http_error(429),
            _mock_http_error(429),
            _mock_http_error(429),
        ]

        with pytest.raises(urllib.error.HTTPError) as exc_info:
            _whoop_api_call(
                "https://api.prod.whoop.com/developer/v1/recovery",
                "test-token",
            )
        assert exc_info.value.code == 429

    @patch("handlers.whoop_sync.urllib.request.urlopen")
    def test_non_retryable_error_raises(self, mock_urlopen):
        mock_urlopen.side_effect = _mock_http_error(500)

        with pytest.raises(urllib.error.HTTPError) as exc_info:
            _whoop_api_call(
                "https://api.prod.whoop.com/developer/v1/recovery",
                "test-token",
            )
        assert exc_info.value.code == 500


class TestWhoopRequest:
    @patch("handlers.whoop_sync.urllib.request.urlopen")
    def test_401_triggers_refresh_then_retries(self, mock_urlopen):
        expected = {"records": [SAMPLE_RECOVERY]}
        # First call: 401 from API, then refresh succeeds, then retry succeeds
        mock_urlopen.side_effect = [
            _mock_http_error(401),
            # Refresh token call
            _mock_http_response({
                "access_token": "refreshed-token",
                "refresh_token": "new-refresh",
            }),
            # Retry API call
            _mock_http_response(expected),
        ]

        result = _whoop_request("/recovery", "expired-token")
        assert result == expected


# --- Pagination Tests ---


class TestPagination:
    @patch("handlers.whoop_sync.urllib.request.urlopen")
    def test_single_page(self, mock_urlopen):
        mock_urlopen.return_value = _mock_http_response({
            "records": [SAMPLE_RECOVERY],
        })

        result = _fetch_paginated("/recovery", "token", {"start": "2026-01-01"})
        assert len(result) == 1
        assert result[0]["cycle_id"] == "12345"

    @patch("handlers.whoop_sync.urllib.request.urlopen")
    def test_multi_page(self, mock_urlopen):
        page1 = {"records": [SAMPLE_RECOVERY], "next_token": "page2"}
        page2 = {"records": [dict(SAMPLE_RECOVERY, cycle_id="99999")]}
        mock_urlopen.side_effect = [
            _mock_http_response(page1),
            _mock_http_response(page2),
        ]

        result = _fetch_paginated("/recovery", "token", {"start": "2026-01-01"})
        assert len(result) == 2
        assert result[0]["cycle_id"] == "12345"
        assert result[1]["cycle_id"] == "99999"

    @patch("handlers.whoop_sync.urllib.request.urlopen")
    def test_empty_response(self, mock_urlopen):
        mock_urlopen.return_value = _mock_http_response({"records": []})

        result = _fetch_paginated("/recovery", "token", {"start": "2026-01-01"})
        assert result == []


# --- Full Handler Tests ---


class TestHandler:
    @patch("handlers.whoop_sync.urllib.request.urlopen")
    def test_full_sync_writes_two_sources(self, mock_urlopen):
        # Setup: refresh → recovery page → sleep page
        mock_urlopen.side_effect = [
            # Token refresh
            _mock_http_response({
                "access_token": "fresh-token",
                "refresh_token": "fresh-refresh",
                "expires_in": 86400,
            }),
            # Recovery
            _mock_http_response({"records": [SAMPLE_RECOVERY]}),
            # Sleep
            _mock_http_response({"records": [SAMPLE_SLEEP]}),
        ]

        result = handler({}, None)

        assert result["status"] == "success"
        assert result["recovery_count"] == 1
        assert result["sleep_count"] == 1
        assert len(result["keys_written"]) == 2

        # Verify S3 files
        s3 = boto3.client("s3", region_name="eu-west-3")
        for key in result["keys_written"]:
            obj = s3.get_object(Bucket="ironlog-data-lake-test", Key=key)
            body = gzip.decompress(obj["Body"].read()).decode("utf-8")
            records = [json.loads(line) for line in body.strip().split("\n")]
            assert len(records) == 1
            assert "_sync_timestamp" in records[0]

    @patch("handlers.whoop_sync.urllib.request.urlopen")
    def test_s3_keys_have_hive_partitions(self, mock_urlopen):
        mock_urlopen.side_effect = [
            _mock_http_response({
                "access_token": "fresh",
                "refresh_token": "fresh-r",
            }),
            _mock_http_response({"records": [SAMPLE_RECOVERY]}),
            _mock_http_response({"records": [SAMPLE_SLEEP]}),
        ]

        result = handler({}, None)

        for key in result["keys_written"]:
            assert "/year=" in key
            assert "/month=" in key
            assert "/day=" in key

    @patch("handlers.whoop_sync.urllib.request.urlopen")
    def test_empty_recovery_still_writes_sleep(self, mock_urlopen):
        mock_urlopen.side_effect = [
            _mock_http_response({
                "access_token": "fresh",
                "refresh_token": "fresh-r",
            }),
            _mock_http_response({"records": []}),
            _mock_http_response({"records": [SAMPLE_SLEEP]}),
        ]

        result = handler({}, None)

        assert result["recovery_count"] == 0
        assert result["sleep_count"] == 1
        assert len(result["keys_written"]) == 1
        assert "sleep" in result["keys_written"][0]

    @patch("handlers.whoop_sync.urllib.request.urlopen")
    def test_both_empty_writes_nothing(self, mock_urlopen):
        mock_urlopen.side_effect = [
            _mock_http_response({
                "access_token": "fresh",
                "refresh_token": "fresh-r",
            }),
            _mock_http_response({"records": []}),
            _mock_http_response({"records": []}),
        ]

        result = handler({}, None)

        assert result["recovery_count"] == 0
        assert result["sleep_count"] == 0
        assert result["keys_written"] == []

    @patch("handlers.whoop_sync.urllib.request.urlopen")
    def test_recovery_record_content(self, mock_urlopen):
        mock_urlopen.side_effect = [
            _mock_http_response({
                "access_token": "fresh",
                "refresh_token": "fresh-r",
            }),
            _mock_http_response({"records": [SAMPLE_RECOVERY]}),
            _mock_http_response({"records": []}),
        ]

        result = handler({}, None)

        s3 = boto3.client("s3", region_name="eu-west-3")
        key = result["keys_written"][0]
        obj = s3.get_object(Bucket="ironlog-data-lake-test", Key=key)
        body = gzip.decompress(obj["Body"].read()).decode("utf-8")
        record = json.loads(body.strip())

        assert record["cycle_id"] == "12345"
        assert record["recovery_score"] == 85.0
        assert record["hrv_rmssd"] == 65.3
        assert "_sync_timestamp" in record
