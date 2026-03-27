import json
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from boto3.dynamodb.conditions import Key

from shared.auth_middleware import require_auth
from shared.constants import GSI1_INDEX
from shared.dynamo import get_table
from shared.response import api_response, options_response


@require_auth
def handler(event, context):
    if event.get("httpMethod") == "OPTIONS":
        return options_response()

    method = event["httpMethod"]
    resource = event.get("resource", "")

    if resource == "/api/sessions/{id}/complete" and method == "PUT":
        return _complete_session(event)
    if resource == "/api/sessions/{id}/notes" and method == "POST":
        return _create_session_exercise_note(event)
    if resource == "/api/sessions/{id}/notes" and method == "GET":
        return _list_session_exercise_notes(event)
    if resource == "/api/sessions" and method == "POST":
        return _start_session(event)
    if resource == "/api/sessions" and method == "GET":
        return _list_sessions(event)
    if resource == "/api/sessions/{id}" and method == "GET":
        return _get_session(event)
    if resource == "/api/sessions/{id}" and method == "PUT":
        return _update_session(event)
    if resource == "/api/sessions/{id}" and method == "DELETE":
        return _delete_session(event)

    return api_response(405, {"error": "Method not allowed"})


def _start_session(event):
    body = json.loads(event.get("body") or "{}")
    plan_id = body.get("plan_id")
    plan_day_number = body.get("plan_day_number")

    if not plan_id or plan_day_number is None:
        return api_response(400, {"error": "plan_id and plan_day_number are required"})

    table = get_table()

    # Check for existing in_progress session
    recent = table.query(
        IndexName=GSI1_INDEX,
        KeyConditionExpression=Key("GSI1PK").eq("SESSIONS"),
        ScanIndexForward=False,
        Limit=10,
    )
    for s in recent.get("Items", []):
        if s.get("status") == "in_progress":
            return api_response(409, {
                "error": "You already have a session in progress. Complete or delete it first.",
                "existing_session_id": s["session_id"],
            })

    # Get plan day
    day_sk = f"DAY#{int(plan_day_number):02d}"
    day_resp = table.get_item(Key={"PK": f"PLAN#{plan_id}", "SK": day_sk}).get("Item")
    if not day_resp:
        return api_response(404, {"error": "Plan day not found"})

    session_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y-%m-%d")

    session_item = {
        "PK": f"SESSION#{session_id}",
        "SK": "META",
        "GSI1PK": "SESSIONS",
        "GSI1SK": f"{date_str}#{session_id}",
        "session_id": session_id,
        "plan_id": plan_id,
        "plan_day_number": plan_day_number,
        "date": date_str,
        "status": "in_progress",
        "started_at": now.isoformat(),
        "completed_at": None,
        "notes": None,
        "created_at": now.isoformat(),
    }
    table.put_item(Item=session_item)

    # Build exercise list with warmup calculations
    exercises = []
    for plan_ex in day_resp.get("exercises", []):
        exercise_id = plan_ex["exercise_id"]

        # Get exercise details
        ex_item = table.get_item(
            Key={"PK": f"EX#{exercise_id}", "SK": f"EX#{exercise_id}"}
        ).get("Item", {})

        # Get last working set from exercise history (GSI1)
        last_set = _get_last_working_set(table, exercise_id)
        last_weight = last_set.get("weight_kg") if last_set else None

        warmup = None
        if last_weight is not None and last_weight > 0:
            warmup = {
                "warmup_50": {
                    "weight_kg": _snap_weight(float(last_weight) * 0.5),
                    "reps": "5-7",
                },
                "warmup_75": {
                    "weight_kg": _snap_weight(float(last_weight) * 0.75),
                    "reps": "3-5",
                },
            }

        # Smart suggestions based on last set performance
        suggested_weight_kg = None
        suggested_reps = None
        if last_set and last_weight is not None:
            last_reps = last_set.get("reps", 0)
            target_reps_str = plan_ex.get("target_reps", "")
            # Parse max target reps (e.g., "8-10" → 10, "8" → 8)
            max_target = _parse_max_reps(target_reps_str)
            if last_reps and max_target and int(last_reps) >= max_target:
                # Hit target reps → suggest progression (+2.5kg)
                suggested_weight_kg = float(_snap_weight(float(last_weight) + 2.5))
            else:
                suggested_weight_kg = float(last_weight)
            suggested_reps = str(last_reps) if last_reps else None

        exercises.append({
            "exercise_id": exercise_id,
            "name": ex_item.get("name", ""),
            "order": plan_ex.get("order", 0),
            "target_sets": plan_ex.get("target_sets", 0),
            "target_reps": plan_ex.get("target_reps", ""),
            "set_type": plan_ex.get("set_type", "working"),
            "is_unilateral": ex_item.get("is_unilateral", False),
            "weak_side": ex_item.get("weak_side"),
            "has_plate_calculator": ex_item.get("has_plate_calculator", False),
            "rest_timer_seconds": ex_item.get("rest_timer_seconds", 120),
            "notes": ex_item.get("notes"),
            "warmup": warmup,
            "last_working_weight_kg": float(last_weight) if last_weight is not None else None,
            "suggested_weight_kg": suggested_weight_kg,
            "suggested_reps": suggested_reps,
            "machine_settings": ex_item.get("machine_settings"),
            "replacement_exercise_ids": ex_item.get("replacement_exercise_ids", []),
        })

    return api_response(201, {"session_id": session_id, "status": "in_progress", "exercises": exercises})


def _get_last_working_weight(table, exercise_id):
    """Query GSI1 for the most recent working/backoff set for this exercise."""
    resp = table.query(
        IndexName=GSI1_INDEX,
        KeyConditionExpression=Key("GSI1PK").eq(f"SETS#EX#{exercise_id}"),
        ScanIndexForward=False,
        Limit=20,
    )
    for item in resp.get("Items", []):
        if item.get("set_type") in ("working", "backoff"):
            # Skip sets from deleted sessions
            session_id = item.get("session_id")
            if session_id:
                session_meta = table.get_item(
                    Key={"PK": f"SESSION#{session_id}", "SK": "META"}
                ).get("Item")
                if session_meta and session_meta.get("status") == "deleted":
                    continue
            return item.get("weight_kg")
    return None


def _get_last_working_set(table, exercise_id):
    """Query GSI1 for the most recent working/backoff set (weight + reps)."""
    resp = table.query(
        IndexName=GSI1_INDEX,
        KeyConditionExpression=Key("GSI1PK").eq(f"SETS#EX#{exercise_id}"),
        ScanIndexForward=False,
        Limit=20,
    )
    for item in resp.get("Items", []):
        if item.get("set_type") in ("working", "backoff"):
            session_id = item.get("session_id")
            if session_id:
                session_meta = table.get_item(
                    Key={"PK": f"SESSION#{session_id}", "SK": "META"}
                ).get("Item")
                if session_meta and session_meta.get("status") == "deleted":
                    continue
            return item
    return None


def _snap_weight(weight):
    """Snap to nearest 2.5kg increment. Returns Decimal for DynamoDB."""
    snapped = round(float(weight) / 2.5) * 2.5
    return Decimal(str(snapped))


def _parse_max_reps(target_reps_str):
    """Parse max reps from target string like '8-10' → 10, '8' → 8."""
    if not target_reps_str:
        return None
    parts = str(target_reps_str).split("-")
    try:
        return int(parts[-1])
    except (ValueError, IndexError):
        return None


def _get_session(event):
    session_id = event["pathParameters"]["id"]
    table = get_table()

    resp = table.query(KeyConditionExpression=Key("PK").eq(f"SESSION#{session_id}"))
    items = resp["Items"]

    meta = None
    sets = []
    notes = []
    for item in items:
        if item["SK"] == "META":
            meta = item
        elif item["SK"].startswith("SET#"):
            sets.append(item)
        elif item["SK"].startswith("EXNOTE#"):
            notes.append(item)

    if meta is None:
        return api_response(404, {"error": "Session not found"})

    sets.sort(key=lambda s: s["SK"])
    return api_response(200, {"session": {**meta, "sets": sets, "exercise_notes": notes}})


def _list_sessions(event):
    table = get_table()
    params = event.get("queryStringParameters") or {}
    date_from = params.get("from", "0000-00-00")
    date_to = params.get("to", "9999-99-99")

    resp = table.query(
        IndexName=GSI1_INDEX,
        KeyConditionExpression=Key("GSI1PK").eq("SESSIONS")
        & Key("GSI1SK").between(date_from, date_to + "~"),
    )
    # Filter out soft-deleted sessions
    sessions = [s for s in resp["Items"] if s.get("status") != "deleted"]
    return api_response(200, {"sessions": sessions})


def _update_session(event):
    session_id = event["pathParameters"]["id"]
    body = json.loads(event.get("body") or "{}")
    table = get_table()

    meta = table.get_item(Key={"PK": f"SESSION#{session_id}", "SK": "META"}).get("Item")
    if not meta:
        return api_response(404, {"error": "Session not found"})
    if meta["status"] != "in_progress":
        return api_response(409, {"error": "Cannot modify completed session"})

    notes = body.get("notes")
    if notes is None:
        return api_response(400, {"error": "notes field is required"})

    resp = table.update_item(
        Key={"PK": f"SESSION#{session_id}", "SK": "META"},
        UpdateExpression="SET notes = :n",
        ExpressionAttributeValues={":n": notes},
        ReturnValues="ALL_NEW",
    )
    return api_response(200, {"session": resp["Attributes"]})


def _complete_session(event):
    session_id = event["pathParameters"]["id"]
    table = get_table()

    meta = table.get_item(Key={"PK": f"SESSION#{session_id}", "SK": "META"}).get("Item")
    if not meta:
        return api_response(404, {"error": "Session not found"})
    if meta["status"] == "completed":
        return api_response(200, {"session": meta})

    now = datetime.now(timezone.utc).isoformat()
    resp = table.update_item(
        Key={"PK": f"SESSION#{session_id}", "SK": "META"},
        UpdateExpression="SET #status = :s, completed_at = :c",
        ExpressionAttributeNames={"#status": "status"},
        ExpressionAttributeValues={":s": "completed", ":c": now},
        ReturnValues="ALL_NEW",
    )
    return api_response(200, {"session": resp["Attributes"]})


def _create_session_exercise_note(event):
    session_id = event["pathParameters"]["id"]
    body = json.loads(event.get("body") or "{}")
    table = get_table()

    exercise_id = body.get("exercise_id")
    note_text = body.get("note_text")
    if not exercise_id or not note_text:
        return api_response(400, {"error": "exercise_id and note_text are required"})

    now = datetime.now(timezone.utc).isoformat()
    item = {
        "PK": f"SESSION#{session_id}",
        "SK": f"EXNOTE#{exercise_id}",
        "session_id": session_id,
        "exercise_id": exercise_id,
        "note_text": note_text,
        "created_at": now,
    }
    table.put_item(Item=item)
    return api_response(201, {"note": item})


def _list_session_exercise_notes(event):
    session_id = event["pathParameters"]["id"]
    table = get_table()

    resp = table.query(
        KeyConditionExpression=Key("PK").eq(f"SESSION#{session_id}")
        & Key("SK").begins_with("EXNOTE#"),
    )
    return api_response(200, {"notes": resp["Items"]})


def _delete_session(event):
    """Soft-delete a session by setting status to 'deleted'."""
    session_id = event["pathParameters"]["id"]
    table = get_table()

    meta = table.get_item(Key={"PK": f"SESSION#{session_id}", "SK": "META"}).get("Item")
    if not meta:
        return api_response(404, {"error": "Session not found"})
    if meta["status"] == "deleted":
        return api_response(200, {"message": "Session already deleted"})

    now = datetime.now(timezone.utc).isoformat()
    table.update_item(
        Key={"PK": f"SESSION#{session_id}", "SK": "META"},
        UpdateExpression="SET #status = :s, deleted_at = :d",
        ExpressionAttributeNames={"#status": "status"},
        ExpressionAttributeValues={":s": "deleted", ":d": now},
    )
    return api_response(200, {"message": "Session deleted"})
