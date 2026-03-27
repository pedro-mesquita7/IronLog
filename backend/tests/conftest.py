import sys
from pathlib import Path

import boto3
import jwt as pyjwt
import moto
import pytest
from datetime import datetime, timedelta, timezone

# Ensure backend/ is on the path so "shared" and "handlers" are importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture(autouse=True)
def aws_env(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "eu-west-3")
    monkeypatch.setenv("TABLE_NAME", "ironlog")
    monkeypatch.setenv("SSM_AUTH_TOKEN", "/ironlog/auth-token")
    monkeypatch.setenv("SSM_JWT_SECRET", "/ironlog/jwt-secret")
    monkeypatch.setenv("CORS_ORIGIN", "https://pedro-mesquita7.github.io")
    monkeypatch.setenv("DATA_LAKE_BUCKET", "ironlog-data-lake-test")
    monkeypatch.setenv("SSM_WHOOP_CLIENT_ID", "/ironlog/whoop-client-id")
    monkeypatch.setenv("SSM_WHOOP_CLIENT_SECRET", "/ironlog/whoop-client-secret")
    monkeypatch.setenv("SSM_WHOOP_ACCESS_TOKEN", "/ironlog/whoop-access-token")
    monkeypatch.setenv("SSM_WHOOP_REFRESH_TOKEN", "/ironlog/whoop-refresh-token")
    monkeypatch.setenv("SSM_WHOOP_REFRESH_TOKEN_EXPIRY", "/ironlog/whoop-refresh-token-expiry")
    monkeypatch.setenv("SNS_TOPIC_ARN", "arn:aws:sns:eu-west-3:123456789012:ironlog-alerts")
    monkeypatch.setenv("ATHENA_WORKGROUP", "ironlog")
    monkeypatch.setenv("ATHENA_DATABASE", "ironlog")
    monkeypatch.setenv("ATHENA_OUTPUT_BUCKET", "ironlog-data-lake-test")
    monkeypatch.setenv("ATHENA_GOLD_DATABASE", "gold")


AUTH_TOKEN = "a" * 64
JWT_SECRET = "b" * 32


@pytest.fixture(autouse=True)
def mock_aws(aws_env):
    with moto.mock_aws():
        # DynamoDB table matching infra/dynamodb.tf
        client = boto3.client("dynamodb", region_name="eu-west-3")
        client.create_table(
            TableName="ironlog",
            KeySchema=[
                {"AttributeName": "PK", "KeyType": "HASH"},
                {"AttributeName": "SK", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "PK", "AttributeType": "S"},
                {"AttributeName": "SK", "AttributeType": "S"},
                {"AttributeName": "GSI1PK", "AttributeType": "S"},
                {"AttributeName": "GSI1SK", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "GSI1",
                    "KeySchema": [
                        {"AttributeName": "GSI1PK", "KeyType": "HASH"},
                        {"AttributeName": "GSI1SK", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                }
            ],
            BillingMode="PAY_PER_REQUEST",
        )

        # SSM parameters
        ssm = boto3.client("ssm", region_name="eu-west-3")
        ssm.put_parameter(
            Name="/ironlog/auth-token", Value=AUTH_TOKEN, Type="SecureString"
        )
        ssm.put_parameter(
            Name="/ironlog/jwt-secret", Value=JWT_SECRET, Type="SecureString"
        )

        # S3 bucket for CDC tests
        s3 = boto3.client("s3", region_name="eu-west-3")
        s3.create_bucket(
            Bucket="ironlog-data-lake-test",
            CreateBucketConfiguration={"LocationConstraint": "eu-west-3"},
        )

        # WHOOP SSM parameters
        ssm.put_parameter(
            Name="/ironlog/whoop-client-id", Value="test-client-id", Type="SecureString"
        )
        ssm.put_parameter(
            Name="/ironlog/whoop-client-secret", Value="test-client-secret", Type="SecureString"
        )
        ssm.put_parameter(
            Name="/ironlog/whoop-access-token", Value="test-access-token", Type="SecureString"
        )
        ssm.put_parameter(
            Name="/ironlog/whoop-refresh-token", Value="test-refresh-token", Type="SecureString"
        )
        ssm.put_parameter(
            Name="/ironlog/whoop-refresh-token-expiry", Value="2099-01-01T00:00:00+00:00", Type="String"
        )

        # SNS topic for alerts
        sns = boto3.client("sns", region_name="eu-west-3")
        sns.create_topic(Name="ironlog-alerts")

        # Clear module-level caches
        from shared.auth_middleware import _clear_cache
        from shared.dynamo import reset_table
        from shared.s3_writer import reset_client as reset_s3_client
        from shared.athena import reset_client as reset_athena_client
        from handlers.plans import reset_client as reset_plans_client
        from handlers.whoop_sync import reset_clients as reset_whoop_clients

        _clear_cache()
        reset_table()
        reset_s3_client()
        reset_athena_client()
        reset_plans_client()
        reset_whoop_clients()

        yield

        _clear_cache()
        reset_table()
        reset_s3_client()
        reset_athena_client()
        reset_plans_client()
        reset_whoop_clients()


@pytest.fixture
def auth_header():
    now = datetime.now(timezone.utc)
    token = pyjwt.encode(
        {"exp": now + timedelta(hours=24), "iat": now},
        JWT_SECRET,
        algorithm="HS256",
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def expired_auth_header():
    past = datetime.now(timezone.utc) - timedelta(hours=25)
    token = pyjwt.encode(
        {"exp": past + timedelta(hours=24), "iat": past},
        JWT_SECRET,
        algorithm="HS256",
    )
    return {"Authorization": f"Bearer {token}"}
