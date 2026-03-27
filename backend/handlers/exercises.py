import json
import uuid
from datetime import datetime, timezone

from boto3.dynamodb.conditions import Attr, Key

from shared.auth_middleware import require_auth
from shared.constants import GSI1_INDEX
from shared.dynamo import get_table
from shared.response import api_response, options_response

VALID_MUSCLE_GROUPS = {"chest", "back", "legs", "shoulders", "arms", "core", "full_body"}
VALID_REST_TIMERS = {60, 120, 180}
VALID_WEAK_SIDES = {"left", "right"}


@require_auth
def handler(event, context):
    if event.get("httpMethod") == "OPTIONS":
        return options_response()

    method = event["httpMethod"]
    resource = event.get("resource", "")

    if resource == "/api/exercises" and method == "GET":
        return _list_exercises()
    if resource == "/api/exercises" and method == "POST":
        return _create_exercise(event)
    if resource == "/api/exercises/{id}" and method == "PUT":
        return _update_exercise(event)
    if resource == "/api/exercises/{id}" and method == "DELETE":
        return _delete_exercise(event)

    return api_response(405, {"error": "Method not allowed"})


def _list_exercises():
    table = get_table()
    resp = table.query(
        IndexName=GSI1_INDEX,
        KeyConditionExpression=Key("GSI1PK").eq("EXERCISES"),
        FilterExpression=Attr("is_archived").ne(True),
    )
    return api_response(200, {"exercises": resp["Items"]})


def _create_exercise(event):
    body = json.loads(event.get("body") or "{}")

    name = body.get("name")
    if not name:
        return api_response(400, {"error": "name is required"})

    muscle_group = body.get("muscle_group")
    if muscle_group not in VALID_MUSCLE_GROUPS:
        return api_response(400, {"error": f"muscle_group must be one of: {', '.join(sorted(VALID_MUSCLE_GROUPS))}"})

    rest_timer = body.get("rest_timer_seconds", 60)
    if rest_timer not in VALID_REST_TIMERS:
        return api_response(400, {"error": f"rest_timer_seconds must be one of: {sorted(VALID_REST_TIMERS)}"})

    weak_side = body.get("weak_side")
    if weak_side is not None and weak_side not in VALID_WEAK_SIDES:
        return api_response(400, {"error": f"weak_side must be one of: {', '.join(sorted(VALID_WEAK_SIDES))}"})

    # Duplicate name check (including archived)
    table = get_table()
    existing = table.query(
        IndexName=GSI1_INDEX,
        KeyConditionExpression=Key("GSI1PK").eq("EXERCISES"),
    )
    for ex in existing["Items"]:
        if ex["name"].lower() == name.lower():
            if ex.get("is_archived"):
                return api_response(409, {"error": "Exercise exists but is archived", "exercise": ex})
            return api_response(409, {"error": "Exercise with this name already exists"})

    exercise_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    item = {
        "PK": f"EX#{exercise_id}",
        "SK": f"EX#{exercise_id}",
        "GSI1PK": "EXERCISES",
        "GSI1SK": f"EX#{exercise_id}",
        "exercise_id": exercise_id,
        "name": name,
        "muscle_group": muscle_group,
        "has_plate_calculator": body.get("has_plate_calculator", False),
        "is_unilateral": body.get("is_unilateral", False),
        "weak_side": weak_side,
        "rest_timer_seconds": rest_timer,
        "replacement_exercise_ids": body.get("replacement_exercise_ids", []),
        "is_archived": False,
        "created_at": now,
        "updated_at": now,
    }

    if "default_bar_id" in body:
        item["default_bar_id"] = body["default_bar_id"]
    if "machine_settings" in body:
        item["machine_settings"] = body["machine_settings"]
    if "notes" in body:
        item["notes"] = body["notes"]

    table.put_item(Item=item)
    return api_response(201, {"exercise": item})


def _update_exercise(event):
    exercise_id = event["pathParameters"]["id"]
    body = json.loads(event.get("body") or "{}")

    updatable = [
        "name", "muscle_group", "default_bar_id", "has_plate_calculator",
        "is_unilateral", "weak_side", "rest_timer_seconds", "machine_settings",
        "replacement_exercise_ids", "notes",
    ]

    expr_parts = ["#updated_at = :updated_at"]
    attr_names = {"#updated_at": "updated_at"}
    attr_values = {":updated_at": datetime.now(timezone.utc).isoformat()}

    for field in updatable:
        if field in body:
            if field == "muscle_group" and body[field] not in VALID_MUSCLE_GROUPS:
                return api_response(400, {"error": f"muscle_group must be one of: {', '.join(sorted(VALID_MUSCLE_GROUPS))}"})
            if field == "rest_timer_seconds" and body[field] not in VALID_REST_TIMERS:
                return api_response(400, {"error": f"rest_timer_seconds must be one of: {sorted(VALID_REST_TIMERS)}"})
            if field == "weak_side" and body[field] is not None and body[field] not in VALID_WEAK_SIDES:
                return api_response(400, {"error": f"weak_side must be one of: {', '.join(sorted(VALID_WEAK_SIDES))}"})
            attr_names[f"#{field}"] = field
            attr_values[f":{field}"] = body[field]
            expr_parts.append(f"#{field} = :{field}")

    if len(expr_parts) == 1:
        return api_response(400, {"error": "No fields to update"})

    try:
        resp = get_table().update_item(
            Key={"PK": f"EX#{exercise_id}", "SK": f"EX#{exercise_id}"},
            UpdateExpression="SET " + ", ".join(expr_parts),
            ExpressionAttributeNames=attr_names,
            ExpressionAttributeValues=attr_values,
            ConditionExpression=Attr("PK").exists(),
            ReturnValues="ALL_NEW",
        )
        return api_response(200, {"exercise": resp["Attributes"]})
    except get_table().meta.client.exceptions.ConditionalCheckFailedException:
        return api_response(404, {"error": "Exercise not found"})


def _delete_exercise(event):
    exercise_id = event["pathParameters"]["id"]
    now = datetime.now(timezone.utc).isoformat()

    try:
        get_table().update_item(
            Key={"PK": f"EX#{exercise_id}", "SK": f"EX#{exercise_id}"},
            UpdateExpression="SET #archived = :val, #updated_at = :now",
            ExpressionAttributeNames={"#archived": "is_archived", "#updated_at": "updated_at"},
            ExpressionAttributeValues={":val": True, ":now": now},
            ConditionExpression=Attr("PK").exists(),
        )
        return api_response(200, {"message": "Exercise archived"})
    except get_table().meta.client.exceptions.ConditionalCheckFailedException:
        return api_response(404, {"error": "Exercise not found"})
