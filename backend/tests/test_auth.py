import json

from handlers.auth import handler
from tests.conftest import AUTH_TOKEN


def _event(method="POST", body=None):
    return {
        "httpMethod": method,
        "headers": {},
        "body": json.dumps(body) if body else None,
        "resource": "/api/auth/login",
    }


def test_login_valid_token():
    resp = handler(_event(body={"token": AUTH_TOKEN}), None)
    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])
    assert "jwt" in body
    assert "expires_at" in body


def test_login_invalid_token():
    resp = handler(_event(body={"token": "wrong"}), None)
    assert resp["statusCode"] == 401


def test_login_missing_token():
    resp = handler(_event(body={}), None)
    assert resp["statusCode"] == 401


def test_login_empty_body():
    resp = handler(_event(), None)
    assert resp["statusCode"] == 401


def test_login_wrong_method():
    resp = handler(_event(method="GET"), None)
    assert resp["statusCode"] == 405


def test_login_options():
    resp = handler(_event(method="OPTIONS"), None)
    assert resp["statusCode"] == 200
    assert "Access-Control-Allow-Origin" in resp["headers"]
