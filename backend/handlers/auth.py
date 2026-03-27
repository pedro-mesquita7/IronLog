import json

from shared.auth_middleware import (
    _get_ssm_param,
    generate_jwt,
    validate_login_token,
)
from shared.constants import SSM_JWT_SECRET
from shared.response import api_response, init_cors, options_response


def handler(event, context):
    init_cors(event)
    if event.get("httpMethod") == "OPTIONS":
        return options_response()

    if event.get("httpMethod") != "POST":
        return api_response(405, {"error": "Method not allowed"})

    body = json.loads(event.get("body") or "{}")
    token = body.get("token", "")

    if not token or not validate_login_token(token):
        return api_response(401, {"error": "Invalid token"})

    secret = _get_ssm_param(SSM_JWT_SECRET)
    jwt_token, expires_at = generate_jwt(secret)
    return api_response(200, {"jwt": jwt_token, "expires_at": expires_at})
