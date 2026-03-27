import functools
import hmac
from datetime import datetime, timedelta, timezone

import boto3
import jwt

from shared.constants import SSM_AUTH_TOKEN, SSM_JWT_SECRET
from shared.response import api_response, init_cors

_cache = {}
_ssm_client = None


def _get_ssm_client():
    global _ssm_client
    if _ssm_client is None:
        _ssm_client = boto3.client("ssm")
    return _ssm_client


def _get_ssm_param(name):
    if name not in _cache:
        resp = _get_ssm_client().get_parameter(Name=name, WithDecryption=True)
        _cache[name] = resp["Parameter"]["Value"]
    return _cache[name]


def _clear_cache():
    global _ssm_client
    _cache.clear()
    _ssm_client = None


def validate_login_token(token):
    stored = _get_ssm_param(SSM_AUTH_TOKEN)
    return hmac.compare_digest(token, stored)


def generate_jwt(secret):
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(hours=24)
    payload = {"exp": expires_at, "iat": now}
    token = jwt.encode(payload, secret, algorithm="HS256")
    return token, expires_at.isoformat()


def require_auth(fn):
    @functools.wraps(fn)
    def wrapper(event, context):
        init_cors(event)
        headers = event.get("headers") or {}
        auth = headers.get("Authorization") or headers.get("authorization") or ""
        if not auth.startswith("Bearer "):
            return api_response(401, {"error": "Unauthorized"})

        token = auth[7:]
        secret = _get_ssm_param(SSM_JWT_SECRET)
        try:
            jwt.decode(token, secret, algorithms=["HS256"])
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return api_response(401, {"error": "Unauthorized"})

        return fn(event, context)

    return wrapper
