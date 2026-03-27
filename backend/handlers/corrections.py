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

    if resource == "/api/corrections" and method == "POST":
        return _create_correction(event)
    if resource == "/api/corrections" and method == "GET":
        return _list_corrections(event)

    return api_response(405, {"error": "Method not allowed"})


def _create_correction(event):
    body = json.loads(event.get("body") or "{}")
    table = get_table()

    set_id = body.get("set_id")
    session_id = body.get("session_id")
    field = body.get("field")
    old_value = body.get("old_value")
    new_value = body.get("new_value")

    if not all([set_id, session_id, field is not None, old_value is not None, new_value is not None]):
        return api_response(400, {"error": "set_id, session_id, field, old_value, and new_value are required"})

    valid_fields = {"weight_kg", "reps", "rir"}
    if field not in valid_fields:
        return api_response(400, {"error": f"field must be one of: {', '.join(sorted(valid_fields))}"})

    # Find the set in the session
    resp = table.query(
        KeyConditionExpression=Key("PK").eq(f"SESSION#{session_id}")
        & Key("SK").begins_with("SET#"),
    )
    target_set = None
    for item in resp["Items"]:
        if item.get("set_id") == set_id:
            target_set = item
            break

    if not target_set:
        return api_response(404, {"error": "Set not found"})

    # Apply correction to the set
    table.update_item(
        Key={"PK": target_set["PK"], "SK": target_set["SK"]},
        UpdateExpression=f"SET #{field} = :val",
        ExpressionAttributeNames={f"#{field}": field},
        ExpressionAttributeValues={":val": new_value},
    )

    # If weight or reps changed, recalculate e1RM
    if field in ("weight_kg", "reps"):
        w = Decimal(str(new_value)) if field == "weight_kg" else Decimal(str(target_set.get("weight_kg", 0)))
        r = Decimal(str(new_value)) if field == "reps" else Decimal(str(target_set.get("reps", 0)))
        e1rm = (w * (1 + r / 30)).quantize(Decimal("0.01")) if r > 0 and w > 0 else Decimal("0")
        table.update_item(
            Key={"PK": target_set["PK"], "SK": target_set["SK"]},
            UpdateExpression="SET estimated_1rm = :e",
            ExpressionAttributeValues={":e": e1rm},
        )

    # Record correction
    correction_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    correction_item = {
        "PK": f"CORR#{set_id}",
        "SK": f"CORR#{correction_id}",
        "GSI1PK": f"CORR#SESSION#{session_id}",
        "GSI1SK": f"{now}#{correction_id}",
        "correction_id": correction_id,
        "set_id": set_id,
        "session_id": session_id,
        "field": field,
        "old_value": old_value,
        "new_value": new_value,
        "reason": body.get("reason"),
        "created_at": now,
    }
    table.put_item(Item=correction_item)

    return api_response(201, {"correction": correction_item})


def _list_corrections(event):
    table = get_table()
    params = event.get("queryStringParameters") or {}
    session_id = params.get("session_id")

    if not session_id:
        return api_response(400, {"error": "session_id query parameter is required"})

    resp = table.query(
        IndexName=GSI1_INDEX,
        KeyConditionExpression=Key("GSI1PK").eq(f"CORR#SESSION#{session_id}"),
    )
    return api_response(200, {"corrections": resp["Items"]})
