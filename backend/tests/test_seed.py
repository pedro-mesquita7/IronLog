import json

from handlers.seed import handler


def _event(method="POST", resource="/api/seed", headers=None):
    return {
        "httpMethod": method,
        "headers": headers or {},
        "body": None,
        "resource": resource,
        "pathParameters": None,
    }


def test_seed_creates_data(auth_header):
    resp = handler(_event(headers=auth_header), None)
    assert resp["statusCode"] == 201
    body = json.loads(resp["body"])
    assert body["seeded"] is True
    assert body["equipment_count"] == 8
    assert body["exercise_count"] == 25
    assert body["plan_id"]
    assert body["message"] == "Seed data created successfully"


def test_seed_idempotent(auth_header):
    # First call seeds
    resp1 = handler(_event(headers=auth_header), None)
    assert resp1["statusCode"] == 201

    # Second call skips
    resp2 = handler(_event(headers=auth_header), None)
    assert resp2["statusCode"] == 200
    body = json.loads(resp2["body"])
    assert body["seeded"] is False


def test_seed_creates_equipment(auth_header):
    from boto3.dynamodb.conditions import Key
    from shared.dynamo import get_table

    handler(_event(headers=auth_header), None)

    table = get_table()
    resp = table.query(
        IndexName="GSI1",
        KeyConditionExpression=Key("GSI1PK").eq("EQUIPMENT"),
    )
    items = resp["Items"]
    assert len(items) == 8

    names = {i["name"] for i in items}
    assert "Olympic Barbell (BB)" in names
    assert "Plate 20kg" in names


def test_seed_creates_exercises_with_replacements(auth_header):
    from boto3.dynamodb.conditions import Key
    from shared.dynamo import get_table

    handler(_event(headers=auth_header), None)

    table = get_table()
    resp = table.query(
        IndexName="GSI1",
        KeyConditionExpression=Key("GSI1PK").eq("EXERCISES"),
    )
    items = resp["Items"]
    assert len(items) == 25

    # Check replacement links are populated
    by_name = {i["name"]: i for i in items}
    lateral_pulley = by_name["Lateral Raise Pulley"]
    lateral_db = by_name["Lateral Raise DB"]
    assert lateral_db["exercise_id"] in lateral_pulley["replacement_exercise_ids"]
    assert lateral_pulley["exercise_id"] in lateral_db["replacement_exercise_ids"]


def test_seed_creates_exercises_with_bar_ids(auth_header):
    from boto3.dynamodb.conditions import Key
    from shared.dynamo import get_table

    handler(_event(headers=auth_header), None)

    table = get_table()
    eq_resp = table.query(
        IndexName="GSI1",
        KeyConditionExpression=Key("GSI1PK").eq("EQUIPMENT"),
    )
    eq_by_name = {i["name"]: i for i in eq_resp["Items"]}

    ex_resp = table.query(
        IndexName="GSI1",
        KeyConditionExpression=Key("GSI1PK").eq("EXERCISES"),
    )
    ex_by_name = {i["name"]: i for i in ex_resp["Items"]}

    deadlift = ex_by_name["Deadlift"]
    assert deadlift["default_bar_id"] == eq_by_name["Olympic Barbell (BB)"]["equipment_id"]

    bicep_curl = ex_by_name["Bicep Curl EZ Bar"]
    assert bicep_curl["default_bar_id"] == eq_by_name["EZ Curl Bar"]["equipment_id"]


def test_seed_creates_plan(auth_header):
    from boto3.dynamodb.conditions import Key
    from shared.dynamo import get_table

    resp = handler(_event(headers=auth_header), None)
    body = json.loads(resp["body"])
    plan_id = body["plan_id"]

    table = get_table()
    plan_resp = table.query(
        KeyConditionExpression=Key("PK").eq(f"PLAN#{plan_id}"),
    )
    items = plan_resp["Items"]

    meta = next(i for i in items if i["SK"] == "META")
    assert meta["name"] == "Upper Lower 4x"
    assert meta["is_active"] is True
    assert meta["GSI1PK"] == "ACTIVE_PLAN"

    days = [i for i in items if i["SK"].startswith("DAY#")]
    assert len(days) == 4

    day1 = next(d for d in days if d["SK"] == "DAY#01")
    assert day1["day_name"] == "Upper A"
    assert len(day1["exercises"]) == 6


def test_seed_requires_auth():
    resp = handler(_event(), None)
    assert resp["statusCode"] == 401


def test_seed_options(auth_header):
    resp = handler(_event(method="OPTIONS", headers=auth_header), None)
    assert resp["statusCode"] == 200
