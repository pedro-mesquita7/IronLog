import json
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from boto3.dynamodb.conditions import Attr, Key

from shared.auth_middleware import require_auth
from shared.constants import GSI1_INDEX
from shared.dynamo import get_table
from shared.response import api_response, options_response


def _epley_e1rm(weight, reps):
    """Epley formula: weight × (1 + reps/30). Returns Decimal for DynamoDB."""
    if reps <= 0 or weight <= 0:
        return Decimal("0")
    result = Decimal(str(weight)) * (1 + Decimal(str(reps)) / 30)
    return result.quantize(Decimal("0.01"))


def _detect_prs(table, exercise_id, weight_kg, reps, set_type):
    """Detect weight PR and e1RM PR for working/backoff sets.
    Returns (is_weight_pr, is_e1rm_pr, estimated_1rm).
    """
    estimated_1rm = _epley_e1rm(weight_kg, reps)

    # Warmup sets never get PRs
    if set_type not in ("working", "backoff"):
        return False, False, estimated_1rm

    # Query exercise history
    resp = table.query(
        IndexName=GSI1_INDEX,
        KeyConditionExpression=Key("GSI1PK").eq(f"SETS#EX#{exercise_id}"),
        ScanIndexForward=False,
    )
    history = resp.get("Items", [])

    max_weight = Decimal("0")
    max_e1rm = Decimal("0")

    for s in history:
        if s.get("set_type") not in ("working", "backoff"):
            continue
        w = s.get("weight_kg", Decimal("0"))
        if isinstance(w, (int, float)):
            w = Decimal(str(w))
        if w > max_weight:
            max_weight = w

        e = s.get("estimated_1rm", Decimal("0"))
        if isinstance(e, (int, float)):
            e = Decimal(str(e))
        if e > max_e1rm:
            max_e1rm = e

    weight_decimal = Decimal(str(weight_kg))
    e1rm_decimal = Decimal(str(estimated_1rm))

    is_weight_pr = weight_decimal > max_weight
    is_e1rm_pr = e1rm_decimal > max_e1rm

    return is_weight_pr, is_e1rm_pr, estimated_1rm


@require_auth
def handler(event, context):
    if event.get("httpMethod") == "OPTIONS":
        return options_response()

    method = event["httpMethod"]
    resource = event.get("resource", "")

    if resource == "/api/sessions/{id}/sets" and method == "POST":
        return _create_set(event)
    if resource == "/api/sessions/{id}/sets/{sid}" and method == "PUT":
        return _update_set(event)
    if resource == "/api/sessions/{id}/sets/{sid}" and method == "DELETE":
        return _delete_set(event)

    return api_response(405, {"error": "Method not allowed"})


def _create_set(event):
    session_id = event["pathParameters"]["id"]
    body = json.loads(event.get("body") or "{}")
    table = get_table()

    # Verify session is in_progress
    meta = table.get_item(Key={"PK": f"SESSION#{session_id}", "SK": "META"}).get("Item")
    if not meta:
        return api_response(404, {"error": "Session not found"})
    if meta["status"] != "in_progress":
        return api_response(409, {"error": "Cannot modify completed session"})

    exercise_id = body.get("exercise_id")
    set_type = body.get("set_type")
    set_order = body.get("set_order")
    weight_kg = body.get("weight_kg")
    reps = body.get("reps")
    rir = body.get("rir")

    if not all([exercise_id, set_type is not None, set_order is not None, weight_kg is not None, reps is not None]):
        return api_response(400, {"error": "exercise_id, set_type, set_order, weight_kg, and reps are required"})

    valid_set_types = {"warmup_50", "warmup_75", "working", "backoff"}
    if set_type not in valid_set_types:
        return api_response(400, {"error": f"set_type must be one of: {', '.join(sorted(valid_set_types))}"})

    set_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    order_padded = f"{int(set_order):03d}"

    # Dual PR detection
    is_weight_pr, is_e1rm_pr, estimated_1rm = _detect_prs(
        table, exercise_id, weight_kg, reps, set_type
    )

    item = {
        "PK": f"SESSION#{session_id}",
        "SK": f"SET#{order_padded}#{set_id}",
        "GSI1PK": f"SETS#EX#{exercise_id}",
        "GSI1SK": f"{now}#{set_id}",
        "set_id": set_id,
        "session_id": session_id,
        "exercise_id": exercise_id,
        "original_exercise_id": body.get("original_exercise_id"),
        "set_type": set_type,
        "set_order": set_order,
        "weight_kg": weight_kg,
        "reps": reps,
        "rir": rir,
        "is_weight_pr": is_weight_pr,
        "is_e1rm_pr": is_e1rm_pr,
        "estimated_1rm": estimated_1rm,
        "timestamp": now,
    }

    table.put_item(Item=item)
    return api_response(201, {
        "set_id": set_id,
        "is_weight_pr": is_weight_pr,
        "is_e1rm_pr": is_e1rm_pr,
        "estimated_1rm": estimated_1rm,
        **item,
    })


def _update_set(event):
    session_id = event["pathParameters"]["id"]
    set_id = event["pathParameters"]["sid"]
    body = json.loads(event.get("body") or "{}")
    table = get_table()

    # Verify session is in_progress
    meta = table.get_item(Key={"PK": f"SESSION#{session_id}", "SK": "META"}).get("Item")
    if not meta:
        return api_response(404, {"error": "Session not found"})
    if meta["status"] != "in_progress":
        return api_response(409, {"error": "Cannot modify completed session"})

    # Find the set by scanning session items (set SK includes order prefix)
    resp = table.query(
        KeyConditionExpression=Key("PK").eq(f"SESSION#{session_id}")
        & Key("SK").begins_with("SET#"),
    )
    target = None
    for item in resp["Items"]:
        if item.get("set_id") == set_id:
            target = item
            break

    if not target:
        return api_response(404, {"error": "Set not found"})

    updatable = ["weight_kg", "reps", "rir", "set_type"]
    expr_parts = []
    attr_names = {}
    attr_values = {}

    for field in updatable:
        if field in body:
            attr_names[f"#{field}"] = field
            attr_values[f":{field}"] = body[field]
            expr_parts.append(f"#{field} = :{field}")

    if not expr_parts:
        return api_response(400, {"error": "No fields to update"})

    # Recalculate PR flags if weight/reps changed
    new_weight = body.get("weight_kg", target.get("weight_kg"))
    new_reps = body.get("reps", target.get("reps"))
    new_set_type = body.get("set_type", target.get("set_type"))
    is_weight_pr, is_e1rm_pr, estimated_1rm = _detect_prs(
        table, target["exercise_id"], new_weight, new_reps, new_set_type
    )

    attr_names["#iwp"] = "is_weight_pr"
    attr_values[":iwp"] = is_weight_pr
    expr_parts.append("#iwp = :iwp")

    attr_names["#iep"] = "is_e1rm_pr"
    attr_values[":iep"] = is_e1rm_pr
    expr_parts.append("#iep = :iep")

    attr_names["#e1rm"] = "estimated_1rm"
    attr_values[":e1rm"] = estimated_1rm
    expr_parts.append("#e1rm = :e1rm")

    resp = table.update_item(
        Key={"PK": target["PK"], "SK": target["SK"]},
        UpdateExpression="SET " + ", ".join(expr_parts),
        ExpressionAttributeNames=attr_names,
        ExpressionAttributeValues=attr_values,
        ReturnValues="ALL_NEW",
    )
    return api_response(200, {"set": resp["Attributes"]})


def _delete_set(event):
    session_id = event["pathParameters"]["id"]
    set_id = event["pathParameters"]["sid"]
    table = get_table()

    # Verify session is in_progress
    meta = table.get_item(Key={"PK": f"SESSION#{session_id}", "SK": "META"}).get("Item")
    if not meta:
        return api_response(404, {"error": "Session not found"})
    if meta["status"] != "in_progress":
        return api_response(409, {"error": "Cannot modify completed session"})

    # Find the set
    resp = table.query(
        KeyConditionExpression=Key("PK").eq(f"SESSION#{session_id}")
        & Key("SK").begins_with("SET#"),
    )
    target = None
    for item in resp["Items"]:
        if item.get("set_id") == set_id:
            target = item
            break

    if not target:
        return api_response(404, {"error": "Set not found"})

    table.delete_item(Key={"PK": target["PK"], "SK": target["SK"]})
    return api_response(200, {"message": "Set deleted"})
