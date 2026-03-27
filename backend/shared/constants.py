import os

TABLE_NAME = os.environ.get("TABLE_NAME", "ironlog")
GSI1_INDEX = "GSI1"
SSM_AUTH_TOKEN = os.environ.get("SSM_AUTH_TOKEN", "/ironlog/auth-token")
SSM_JWT_SECRET = os.environ.get("SSM_JWT_SECRET", "/ironlog/jwt-secret")
DATA_LAKE_BUCKET = os.environ.get("DATA_LAKE_BUCKET", "ironlog-data-lake")
_cors_raw = os.environ.get("CORS_ORIGIN", "https://pedro-mesquita7.github.io")
CORS_ALLOWED_ORIGINS = {o.strip() for o in _cors_raw.split(",") if o.strip()}

SSM_WHOOP_CLIENT_ID = os.environ.get("SSM_WHOOP_CLIENT_ID", "/ironlog/whoop-client-id")
SSM_WHOOP_CLIENT_SECRET = os.environ.get("SSM_WHOOP_CLIENT_SECRET", "/ironlog/whoop-client-secret")
SSM_WHOOP_ACCESS_TOKEN = os.environ.get("SSM_WHOOP_ACCESS_TOKEN", "/ironlog/whoop-access-token")
SSM_WHOOP_REFRESH_TOKEN = os.environ.get("SSM_WHOOP_REFRESH_TOKEN", "/ironlog/whoop-refresh-token")
SSM_WHOOP_REFRESH_TOKEN_EXPIRY = os.environ.get("SSM_WHOOP_REFRESH_TOKEN_EXPIRY", "/ironlog/whoop-refresh-token-expiry")
SNS_TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN", "")
WHOOP_API_BASE = "https://api.prod.whoop.com/developer/v2"
WHOOP_TOKEN_URL = "https://api.prod.whoop.com/oauth/oauth2/token"

ATHENA_WORKGROUP = os.environ.get("ATHENA_WORKGROUP", "ironlog")
ATHENA_DATABASE = os.environ.get("ATHENA_DATABASE", "ironlog")
ATHENA_GOLD_DATABASE = os.environ.get("ATHENA_GOLD_DATABASE", "gold")
ATHENA_OUTPUT_BUCKET = os.environ.get("ATHENA_OUTPUT_BUCKET", "ironlog-data-lake")
