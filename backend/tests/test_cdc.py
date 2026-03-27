"""Tests for the CDC Lambda handler."""

import gzip
import json

import boto3
import pytest

from handlers.cdc import _classify_record, handler

BUCKET = "ironlog-data-lake-test"


# --- _classify_record tests ---


class TestClassifyRecord:
    def test_equipment(self):
        assert _classify_record("EQ#abc", "EQ#abc") == "equipment"

    def test_exercises(self):
        assert _classify_record("EX#abc", "EX#abc") == "exercises"

    def test_plans(self):
        assert _classify_record("PLAN#abc", "META") == "plans"

    def test_plan_days(self):
        assert _classify_record("PLAN#abc", "DAY#1") == "plan_days"

    def test_sessions(self):
        assert _classify_record("SESSION#abc", "META") == "sessions"

    def test_sets(self):
        assert _classify_record("SESSION#abc", "SET#001#xyz") == "sets"

    def test_session_exercise_notes(self):
        assert (
            _classify_record("SESSION#abc", "EXNOTE#ex1")
            == "session_exercise_notes"
        )

    def test_corrections(self):
        assert _classify_record("CORR#abc", "CORR#xyz") == "corrections"

    def test_unknown_returns_none(self):
        assert _classify_record("UNKNOWN#abc", "UNKNOWN#abc") is None

    def test_plan_pk_with_non_matching_sk(self):
        # PLAN# PK but SK doesn't match META or DAY#
        assert _classify_record("PLAN#abc", "SOMETHING") is None

    def test_session_pk_with_non_matching_sk(self):
        assert _classify_record("SESSION#abc", "SOMETHING") is None


# --- Helper to build DynamoDB Streams records ---


def _stream_record(pk, sk, event_name="INSERT", attrs=None, epoch=1700000000):
    """Build a minimal DynamoDB Streams record."""
    image = {
        "PK": {"S": pk},
        "SK": {"S": sk},
    }
    if attrs:
        for k, v in attrs.items():
            if isinstance(v, str):
                image[k] = {"S": v}
            elif isinstance(v, (int, float)):
                image[k] = {"N": str(v)}
            elif isinstance(v, bool):
                image[k] = {"BOOL": v}

    image_key = "OldImage" if event_name == "REMOVE" else "NewImage"

    return {
        "eventName": event_name,
        "dynamodb": {
            "Keys": {"PK": {"S": pk}, "SK": {"S": sk}},
            image_key: image,
            "ApproximateCreationDateTime": epoch,
            "SequenceNumber": "111000000000000001",
        },
    }


def _read_s3_jsonl(key):
    """Read and decompress a .jsonl.gz file from S3."""
    s3 = boto3.client("s3", region_name="eu-west-3")
    obj = s3.get_object(Bucket=BUCKET, Key=key)
    raw = gzip.decompress(obj["Body"].read())
    lines = raw.decode("utf-8").strip().split("\n")
    return [json.loads(line) for line in lines]


def _list_s3_keys(prefix="bronze/"):
    """List all S3 keys under a prefix."""
    s3 = boto3.client("s3", region_name="eu-west-3")
    resp = s3.list_objects_v2(Bucket=BUCKET, Prefix=prefix)
    return [obj["Key"] for obj in resp.get("Contents", [])]


# --- Handler tests ---


class TestCdcHandler:
    def test_empty_records(self):
        result = handler({"Records": []}, None)
        assert result["files_written"] == 0
        assert result["keys"] == []

    def test_single_equipment_insert(self):
        event = {
            "Records": [
                _stream_record(
                    "EQ#eq1",
                    "EQ#eq1",
                    "INSERT",
                    {"name": "Olympic Barbell", "weight_kg": 20},
                )
            ]
        }
        result = handler(event, None)
        assert result["files_written"] == 1

        keys = _list_s3_keys("bronze/equipment/")
        assert len(keys) == 1
        assert keys[0].endswith(".jsonl.gz")

        records = _read_s3_jsonl(keys[0])
        assert len(records) == 1
        assert records[0]["name"] == "Olympic Barbell"
        assert records[0]["_cdc_event_name"] == "INSERT"
        assert records[0]["_cdc_timestamp"] is not None
        assert records[0]["_cdc_sequence_number"] == "111000000000000001"

    def test_remove_uses_old_image(self):
        event = {
            "Records": [
                _stream_record(
                    "EX#ex1",
                    "EX#ex1",
                    "REMOVE",
                    {"name": "Deadlift"},
                )
            ]
        }
        result = handler(event, None)
        assert result["files_written"] == 1

        keys = _list_s3_keys("bronze/exercises/")
        records = _read_s3_jsonl(keys[0])
        assert records[0]["name"] == "Deadlift"
        assert records[0]["_cdc_event_name"] == "REMOVE"

    def test_mixed_entity_types(self):
        event = {
            "Records": [
                _stream_record("EQ#eq1", "EQ#eq1", "INSERT", {"name": "Bar"}),
                _stream_record("EX#ex1", "EX#ex1", "INSERT", {"name": "Squat"}),
                _stream_record(
                    "SESSION#s1", "SET#001#set1", "INSERT", {"weight_kg": 100}
                ),
                _stream_record("SESSION#s1", "META", "INSERT", {"status": "in_progress"}),
                _stream_record("EQ#eq2", "EQ#eq2", "MODIFY", {"name": "EZ Bar"}),
            ]
        }
        result = handler(event, None)
        # equipment (2 records), exercises (1), sets (1), sessions (1) = 4 files
        assert result["files_written"] == 4

        eq_keys = _list_s3_keys("bronze/equipment/")
        assert len(eq_keys) == 1
        eq_records = _read_s3_jsonl(eq_keys[0])
        assert len(eq_records) == 2  # Both equipment records in one file

    def test_unknown_records_skipped(self):
        event = {
            "Records": [
                _stream_record("UNKNOWN#x", "UNKNOWN#x", "INSERT", {"foo": "bar"}),
            ]
        }
        result = handler(event, None)
        assert result["files_written"] == 0

    def test_modify_uses_new_image(self):
        event = {
            "Records": [
                _stream_record(
                    "PLAN#p1",
                    "META",
                    "MODIFY",
                    {"name": "Updated Plan"},
                )
            ]
        }
        result = handler(event, None)
        keys = _list_s3_keys("bronze/plans/")
        records = _read_s3_jsonl(keys[0])
        assert records[0]["name"] == "Updated Plan"
        assert records[0]["_cdc_event_name"] == "MODIFY"

    def test_s3_key_has_hive_partitions(self):
        event = {
            "Records": [
                _stream_record("CORR#c1", "CORR#c2", "INSERT", {"field": "reps"}),
            ]
        }
        handler(event, None)
        keys = _list_s3_keys("bronze/corrections/")
        key = keys[0]
        assert "/year=" in key
        assert "/month=" in key
        assert "/day=" in key

    def test_all_entity_types_routed(self):
        """Verify every entity type produces a file."""
        event = {
            "Records": [
                _stream_record("EQ#1", "EQ#1", "INSERT"),
                _stream_record("EX#1", "EX#1", "INSERT"),
                _stream_record("PLAN#1", "META", "INSERT"),
                _stream_record("PLAN#1", "DAY#1", "INSERT"),
                _stream_record("SESSION#1", "META", "INSERT"),
                _stream_record("SESSION#1", "SET#001#s1", "INSERT"),
                _stream_record("SESSION#1", "EXNOTE#ex1", "INSERT"),
                _stream_record("CORR#1", "CORR#2", "INSERT"),
            ]
        }
        result = handler(event, None)
        assert result["files_written"] == 8

    def test_epoch_converted_to_iso(self):
        event = {
            "Records": [
                _stream_record("EQ#1", "EQ#1", "INSERT", epoch=1700000000),
            ]
        }
        handler(event, None)
        keys = _list_s3_keys("bronze/equipment/")
        records = _read_s3_jsonl(keys[0])
        ts = records[0]["_cdc_timestamp"]
        assert "2023-11-14" in ts  # 1700000000 = 2023-11-14T22:13:20Z
