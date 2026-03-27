import json
import uuid
from datetime import datetime, timezone

import boto3
from boto3.dynamodb.conditions import Key

from shared.auth_middleware import require_auth
from shared.constants import GSI1_INDEX, TABLE_NAME
from shared.dynamo import get_table
from shared.response import api_response, options_response

_dynamo_client = None


def _get_client():
    global _dynamo_client
    if _dynamo_client is None:
        _dynamo_client = boto3.client("dynamodb")
    return _dynamo_client


def reset_client():
    global _dynamo_client
    _dynamo_client = None


@require_auth
def handler(event, context):
    if event.get("httpMethod") == "OPTIONS":
        return options_response()

    method = event["httpMethod"]
    resource = event.get("resource", "")

    if resource == "/api/plans/{id}/activate" and method == "PUT":
        return _activate_plan(event)
    if resource == "/api/plans" and method == "GET":
        return _list_plans()
    if resource == "/api/plans" and method == "POST":
        return _create_plan(event)
    if resource == "/api/plans/{id}" and method == "GET":
        return _get_plan(event)
    if resource == "/api/plans/{id}" and method == "PUT":
        return _update_plan(event)
    if resource == "/api/plans/{id}" and method == "DELETE":
        return _delete_plan(event)

    return api_response(405, {"error": "Method not allowed"})


def _list_plans():
    table = get_table()
    # Active plan has GSI1PK=ACTIVE_PLAN, inactive have GSI1PK=PLANS
    inactive = table.query(
        IndexName=GSI1_INDEX,
        KeyConditionExpression=Key("GSI1PK").eq("PLANS"),
    )
    active = table.query(
        IndexName=GSI1_INDEX,
        KeyConditionExpression=Key("GSI1PK").eq("ACTIVE_PLAN"),
    )
    plans = inactive["Items"] + active["Items"]
    return api_response(200, {"plans": plans})


def _get_plan(event):
    plan_id = event["pathParameters"]["id"]
    table = get_table()
    resp = table.query(KeyConditionExpression=Key("PK").eq(f"PLAN#{plan_id}"))
    items = resp["Items"]

    meta = None
    days = []
    for item in items:
        if item["SK"] == "META":
            meta = item
        elif item["SK"].startswith("DAY#"):
            days.append(item)

    if meta is None:
        return api_response(404, {"error": "Plan not found"})

    days.sort(key=lambda d: d["SK"])
    plan = {**meta, "days": days}
    return api_response(200, {"plan": plan})


def _create_plan(event):
    body = json.loads(event.get("body") or "{}")

    name = body.get("name")
    if not name:
        return api_response(400, {"error": "name is required"})

    days = body.get("days")
    if not days or not isinstance(days, list):
        return api_response(400, {"error": "days is required and must be a non-empty list"})

    plan_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    meta_item = {
        "PK": f"PLAN#{plan_id}",
        "SK": "META",
        "GSI1PK": "PLANS",
        "GSI1SK": f"PLAN#{plan_id}",
        "plan_id": plan_id,
        "name": name,
        "split_type": body.get("split_type"),
        "is_active": False,
        "created_at": now,
        "updated_at": now,
    }

    day_items = []
    for i, day in enumerate(days, start=1):
        day_item = {
            "PK": f"PLAN#{plan_id}",
            "SK": f"DAY#{i:02d}",
            "day_number": i,
            "day_name": day.get("day_name", f"Day {i}"),
            "exercises": day.get("exercises", []),
        }
        day_items.append(day_item)

    table = get_table()
    with table.batch_writer() as batch:
        batch.put_item(Item=meta_item)
        for day_item in day_items:
            batch.put_item(Item=day_item)

    return api_response(201, {"plan": {**meta_item, "days": day_items}})


def _update_plan(event):
    plan_id = event["pathParameters"]["id"]
    body = json.loads(event.get("body") or "{}")
    table = get_table()

    # Verify plan exists
    resp = table.query(KeyConditionExpression=Key("PK").eq(f"PLAN#{plan_id}"))
    items = resp["Items"]
    meta = next((i for i in items if i["SK"] == "META"), None)
    if meta is None:
        return api_response(404, {"error": "Plan not found"})

    now = datetime.now(timezone.utc).isoformat()

    # Update metadata fields
    meta_fields = ["name", "split_type"]
    expr_parts = ["#updated_at = :updated_at"]
    attr_names = {"#updated_at": "updated_at"}
    attr_values = {":updated_at": now}

    for field in meta_fields:
        if field in body:
            attr_names[f"#{field}"] = field
            attr_values[f":{field}"] = body[field]
            expr_parts.append(f"#{field} = :{field}")

    if len(expr_parts) > 1:
        table.update_item(
            Key={"PK": f"PLAN#{plan_id}", "SK": "META"},
            UpdateExpression="SET " + ", ".join(expr_parts),
            ExpressionAttributeNames=attr_names,
            ExpressionAttributeValues=attr_values,
        )

    # Replace days if provided
    if "days" in body:
        old_days = [i for i in items if i["SK"].startswith("DAY#")]
        with table.batch_writer() as batch:
            for old_day in old_days:
                batch.delete_item(Key={"PK": old_day["PK"], "SK": old_day["SK"]})

        new_days = body["days"]
        day_items = []
        for i, day in enumerate(new_days, start=1):
            day_item = {
                "PK": f"PLAN#{plan_id}",
                "SK": f"DAY#{i:02d}",
                "day_number": i,
                "day_name": day.get("day_name", f"Day {i}"),
                "exercises": day.get("exercises", []),
            }
            day_items.append(day_item)

        with table.batch_writer() as batch:
            for day_item in day_items:
                batch.put_item(Item=day_item)

    # Return updated plan
    return _get_plan(event)


def _delete_plan(event):
    plan_id = event["pathParameters"]["id"]
    table = get_table()

    resp = table.query(KeyConditionExpression=Key("PK").eq(f"PLAN#{plan_id}"))
    items = resp["Items"]
    if not items:
        return api_response(404, {"error": "Plan not found"})

    with table.batch_writer() as batch:
        for item in items:
            batch.delete_item(Key={"PK": item["PK"], "SK": item["SK"]})

    return api_response(200, {"message": "Plan deleted"})


def _activate_plan(event):
    plan_id = event["pathParameters"]["id"]
    table = get_table()
    now = datetime.now(timezone.utc).isoformat()

    # Check target plan exists
    target = table.get_item(Key={"PK": f"PLAN#{plan_id}", "SK": "META"}).get("Item")
    if not target:
        return api_response(404, {"error": "Plan not found"})

    # Already active — idempotent
    if target.get("is_active"):
        return api_response(200, {"message": "Plan activated", "plan_id": plan_id})

    # Find currently active plan
    active_resp = table.query(
        IndexName=GSI1_INDEX,
        KeyConditionExpression=Key("GSI1PK").eq("ACTIVE_PLAN"),
    )
    current_active = active_resp["Items"]

    # Build transaction
    transact_items = []

    if current_active:
        old = current_active[0]
        transact_items.append({
            "Update": {
                "TableName": TABLE_NAME,
                "Key": {"PK": {"S": old["PK"]}, "SK": {"S": "META"}},
                "UpdateExpression": "SET GSI1PK = :plans, is_active = :f, updated_at = :now",
                "ExpressionAttributeValues": {
                    ":plans": {"S": "PLANS"},
                    ":f": {"BOOL": False},
                    ":now": {"S": now},
                },
            }
        })

    transact_items.append({
        "Update": {
            "TableName": TABLE_NAME,
            "Key": {"PK": {"S": f"PLAN#{plan_id}"}, "SK": {"S": "META"}},
            "UpdateExpression": "SET GSI1PK = :active, is_active = :t, updated_at = :now",
            "ExpressionAttributeValues": {
                ":active": {"S": "ACTIVE_PLAN"},
                ":t": {"BOOL": True},
                ":now": {"S": now},
            },
            "ConditionExpression": "attribute_exists(PK)",
        }
    })

    _get_client().transact_write_items(TransactItems=transact_items)
    return api_response(200, {"message": "Plan activated", "plan_id": plan_id})
