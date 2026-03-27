import gzip
import json
import uuid
from datetime import datetime, timezone
from decimal import Decimal

import boto3

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = boto3.client("s3")
    return _client


def reset_client():
    """Reset cached S3 client. Used in tests."""
    global _client
    _client = None


class _DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return int(o) if o == int(o) else float(o)
        return super().default(o)


def write_jsonl(records, source, bucket):
    """Write records as gzip-compressed JSON Lines to S3 bronze layer.

    Path: bronze/<source>/year=YYYY/month=MM/day=DD/<source>_<ts>_<batch>.jsonl.gz
    Returns the S3 key written.
    """
    now = datetime.now(timezone.utc)
    batch_id = uuid.uuid4().hex[:12]
    ts = now.strftime("%Y%m%dT%H%M%S")

    key = (
        f"bronze/{source}"
        f"/year={now.year}"
        f"/month={now.month:02d}"
        f"/day={now.day:02d}"
        f"/{source}_{ts}_{batch_id}.jsonl.gz"
    )

    lines = "\n".join(
        json.dumps(r, cls=_DecimalEncoder, default=str) for r in records
    )
    compressed = gzip.compress(lines.encode("utf-8"))

    _get_client().put_object(
        Bucket=bucket,
        Key=key,
        Body=compressed,
        ContentType="application/x-ndjson",
        ContentEncoding="gzip",
    )

    return key
