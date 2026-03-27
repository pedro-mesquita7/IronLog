import json
from decimal import Decimal

from shared.constants import CORS_ALLOWED_ORIGINS

_current_origin = next(iter(CORS_ALLOWED_ORIGINS))

_STATIC_HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Headers": "Content-Type,Authorization",
    "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
}


def init_cors(event):
    """Set the CORS origin for this request based on the incoming Origin header."""
    global _current_origin
    headers = event.get("headers") or {}
    origin = headers.get("Origin") or headers.get("origin") or ""
    if origin in CORS_ALLOWED_ORIGINS:
        _current_origin = origin
    else:
        _current_origin = next(iter(CORS_ALLOWED_ORIGINS))


def _cors_headers():
    return {**_STATIC_HEADERS, "Access-Control-Allow-Origin": _current_origin}


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return int(o) if o == int(o) else float(o)
        return super().default(o)


def api_response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": _cors_headers(),
        "body": json.dumps(body, cls=DecimalEncoder),
    }


def options_response():
    return {
        "statusCode": 200,
        "headers": _cors_headers(),
        "body": "",
    }
