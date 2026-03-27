import json
import uuid
from datetime import datetime, timezone

from boto3.dynamodb.conditions import Attr, Key

from shared.auth_middleware import require_auth
from shared.constants import GSI1_INDEX
from shared.dynamo import get_table
from shared.response import api_response, options_response

VALID_TYPES = {"bar", "plate", "machine"}


@require_auth
def handler(event, context):
    if event.get("httpMethod") == "OPTIONS":
        return options_response()

    method = event["httpMethod"]
    resource = event.get("resource", "")

    if resource == "/api/equipment" and method == "GET":
        return _list_equipment()
    if resource == "/api/equipment" and method == "POST":
        return _create_equipment(event)
    if resource == "/api/equipment/{id}" and method == "PUT":
        return _update_equipment(event)
    if resource == "/api/equipment/{id}" and method == "DELETE":
        return _delete_equipment(event)

    return api_response(405, {"error": "Method not allowed"})


def _list_equipment():
    table = get_table()
    resp = table.query(
        IndexName=GSI1_INDEX,
        KeyConditionExpression=Key("GSI1PK").eq("EQUIPMENT"),
        FilterExpression=Attr("is_archived").ne(True),
    )
    return api_response(200, {"equipment": resp["Items"]})


def _create_equipment(event):
    body = json.loads(event.get("body") or "{}")

    name = body.get("name")
    if not name:
        return api_response(400, {"error": "name is required"})

    equipment_type = body.get("equipment_type")
    if equipment_type not in VALID_TYPES:
        return api_response(400, {"error": f"equipment_type must be one of: {', '.join(sorted(VALID_TYPES))}"})

    equipment_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    item = {
        "PK": f"EQ#{equipment_id}",
        "SK": f"EQ#{equipment_id}",
        "GSI1PK": "EQUIPMENT",
        "GSI1SK": f"EQ#{equipment_id}",
        "equipment_id": equipment_id,
        "equipment_type": equipment_type,
        "name": name,
        "is_archived": False,
        "created_at": now,
        "updated_at": now,
    }

    if "weight_kg" in body:
        item["weight_kg"] = body["weight_kg"]
    if "quantity" in body:
        item["quantity"] = body["quantity"]
    if "settings_schema" in body:
        item["settings_schema"] = body["settings_schema"]

    get_table().put_item(Item=item)
    return api_response(201, {"equipment": item})


def _update_equipment(event):
    equipment_id = event["pathParameters"]["id"]
    body = json.loads(event.get("body") or "{}")

    updatable = ["name", "equipment_type", "weight_kg", "quantity", "settings_schema"]
    expr_parts = []
    attr_names = {}
    attr_values = {":updated_at": datetime.now(timezone.utc).isoformat()}
    expr_parts.append("#updated_at = :updated_at")
    attr_names["#updated_at"] = "updated_at"

    for field in updatable:
        if field in body:
            if field == "equipment_type" and body[field] not in VALID_TYPES:
                return api_response(400, {"error": f"equipment_type must be one of: {', '.join(sorted(VALID_TYPES))}"})
            placeholder = f":{field}"
            attr_names[f"#{field}"] = field
            attr_values[placeholder] = body[field]
            expr_parts.append(f"#{field} = {placeholder}")

    if len(expr_parts) == 1:
        return api_response(400, {"error": "No fields to update"})

    try:
        resp = get_table().update_item(
            Key={"PK": f"EQ#{equipment_id}", "SK": f"EQ#{equipment_id}"},
            UpdateExpression="SET " + ", ".join(expr_parts),
            ExpressionAttributeNames=attr_names,
            ExpressionAttributeValues=attr_values,
            ConditionExpression=Attr("PK").exists(),
            ReturnValues="ALL_NEW",
        )
        return api_response(200, {"equipment": resp["Attributes"]})
    except get_table().meta.client.exceptions.ConditionalCheckFailedException:
        return api_response(404, {"error": "Equipment not found"})


def _delete_equipment(event):
    equipment_id = event["pathParameters"]["id"]
    now = datetime.now(timezone.utc).isoformat()

    try:
        get_table().update_item(
            Key={"PK": f"EQ#{equipment_id}", "SK": f"EQ#{equipment_id}"},
            UpdateExpression="SET #archived = :val, #updated_at = :now",
            ExpressionAttributeNames={"#archived": "is_archived", "#updated_at": "updated_at"},
            ExpressionAttributeValues={":val": True, ":now": now},
            ConditionExpression=Attr("PK").exists(),
        )
        return api_response(200, {"message": "Equipment archived"})
    except get_table().meta.client.exceptions.ConditionalCheckFailedException:
        return api_response(404, {"error": "Equipment not found"})
