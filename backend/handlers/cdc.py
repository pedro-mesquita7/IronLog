"""CDC handler — consumes DynamoDB Streams and writes JSON Lines to S3 Bronze."""

import logging
import os
from datetime import datetime, timezone

from boto3.dynamodb.types import TypeDeserializer

from shared.s3_writer import write_jsonl

logger = logging.getLogger()
logger.setLevel(logging.INFO)

_deserializer = TypeDeserializer()


def _get_bucket():
    return os.environ.get("DATA_LAKE_BUCKET", "ironlog-data-lake")


def _classify_record(pk, sk):
    """Return source entity name based on PK/SK prefixes, or None."""
    if pk.startswith("EQ#") and sk.startswith("EQ#"):
        return "equipment"
    if pk.startswith("EX#") and sk.startswith("EX#"):
        return "exercises"
    if pk.startswith("PLAN#") and sk == "META":
        return "plans"
    if pk.startswith("PLAN#") and sk.startswith("DAY#"):
        return "plan_days"
    if pk.startswith("SESSION#") and sk == "META":
        return "sessions"
    if pk.startswith("SESSION#") and sk.startswith("SET#"):
        return "sets"
    if pk.startswith("SESSION#") and sk.startswith("EXNOTE#"):
        return "session_exercise_notes"
    if pk.startswith("CORR#") and sk.startswith("CORR#"):
        return "corrections"
    return None


def _deserialize_image(raw_image):
    """Convert DynamoDB JSON format to Python dict."""
    return {k: _deserializer.deserialize(v) for k, v in raw_image.items()}


def _epoch_to_iso(epoch):
    """Convert epoch seconds (int/float) to ISO 8601 string."""
    if epoch is None:
        return None
    return datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat()


def handler(event, context):
    records_by_source = {}

    for record in event.get("Records", []):
        event_name = record["eventName"]
        keys = record["dynamodb"]["Keys"]
        pk = keys["PK"]["S"]
        sk = keys["SK"]["S"]

        source = _classify_record(pk, sk)
        if source is None:
            logger.warning("Unclassified record: PK=%s SK=%s", pk, sk)
            continue

        # Use NewImage for INSERT/MODIFY, OldImage for REMOVE
        image_key = "OldImage" if event_name == "REMOVE" else "NewImage"
        raw_image = record["dynamodb"].get(image_key, {})
        deserialized = _deserialize_image(raw_image)

        # Enrich with CDC metadata
        deserialized["_cdc_event_name"] = event_name
        deserialized["_cdc_timestamp"] = _epoch_to_iso(
            record["dynamodb"].get("ApproximateCreationDateTime")
        )
        deserialized["_cdc_sequence_number"] = record["dynamodb"].get(
            "SequenceNumber"
        )

        records_by_source.setdefault(source, []).append(deserialized)

    keys_written = []
    for source, records in records_by_source.items():
        key = write_jsonl(records, source, _get_bucket())
        keys_written.append(key)
        logger.info("Wrote %d records to %s", len(records), key)

    return {"files_written": len(keys_written), "keys": keys_written}
