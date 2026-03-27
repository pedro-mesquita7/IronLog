import json

from handlers.plans import handler


def _event(method="GET", resource="/api/plans", body=None, headers=None, path_params=None):
    return {
        "httpMethod": method,
        "headers": headers or {},
        "body": json.dumps(body) if body else None,
        "resource": resource,
        "pathParameters": path_params,
    }


SAMPLE_DAYS = [
    {
        "day_name": "Upper A",
        "exercises": [
            {"exercise_id": "ex-1", "order": 1, "target_sets": 3, "target_reps": "4-6", "set_type": "working"},
        ],
    },
    {
        "day_name": "Lower A",
        "exercises": [
            {"exercise_id": "ex-2", "order": 1, "target_sets": 2, "target_reps": "6-8", "set_type": "working"},
        ],
    },
]


def _create_plan(auth_header, name="Test Plan", days=None):
    resp = handler(
        _event(method="POST", headers=auth_header, body={"name": name, "split_type": "upper_lower", "days": days or SAMPLE_DAYS}),
        None,
    )
    return json.loads(resp["body"])["plan"]


def test_list_plans_empty(auth_header):
    resp = handler(_event(headers=auth_header), None)
    assert resp["statusCode"] == 200
    assert json.loads(resp["body"])["plans"] == []


def test_create_plan(auth_header):
    resp = handler(
        _event(method="POST", headers=auth_header, body={"name": "UL 4x", "split_type": "upper_lower", "days": SAMPLE_DAYS}),
        None,
    )
    assert resp["statusCode"] == 201
    plan = json.loads(resp["body"])["plan"]
    assert plan["name"] == "UL 4x"
    assert plan["is_active"] is False
    assert len(plan["days"]) == 2
    assert plan["days"][0]["day_name"] == "Upper A"
    assert "plan_id" in plan


def test_create_plan_missing_name(auth_header):
    resp = handler(_event(method="POST", headers=auth_header, body={"days": SAMPLE_DAYS}), None)
    assert resp["statusCode"] == 400


def test_create_plan_missing_days(auth_header):
    resp = handler(_event(method="POST", headers=auth_header, body={"name": "X"}), None)
    assert resp["statusCode"] == 400


def test_get_plan_with_days(auth_header):
    plan = _create_plan(auth_header)
    plan_id = plan["plan_id"]

    resp = handler(
        _event(method="GET", resource="/api/plans/{id}", headers=auth_header, path_params={"id": plan_id}),
        None,
    )
    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])["plan"]
    assert body["name"] == "Test Plan"
    assert len(body["days"]) == 2
    assert body["days"][0]["day_name"] == "Upper A"
    assert body["days"][1]["day_name"] == "Lower A"


def test_get_plan_not_found(auth_header):
    resp = handler(
        _event(method="GET", resource="/api/plans/{id}", headers=auth_header, path_params={"id": "nope"}),
        None,
    )
    assert resp["statusCode"] == 404


def test_list_plans_after_create(auth_header):
    _create_plan(auth_header)
    resp = handler(_event(headers=auth_header), None)
    plans = json.loads(resp["body"])["plans"]
    assert len(plans) == 1
    assert "days" not in plans[0]  # List returns metadata only


def test_update_plan_metadata(auth_header):
    plan = _create_plan(auth_header)
    plan_id = plan["plan_id"]

    resp = handler(
        _event(method="PUT", resource="/api/plans/{id}", headers=auth_header, body={"name": "Updated"}, path_params={"id": plan_id}),
        None,
    )
    assert resp["statusCode"] == 200
    assert json.loads(resp["body"])["plan"]["name"] == "Updated"


def test_update_plan_days(auth_header):
    plan = _create_plan(auth_header)
    plan_id = plan["plan_id"]

    new_days = [{"day_name": "Full Body", "exercises": []}]
    resp = handler(
        _event(method="PUT", resource="/api/plans/{id}", headers=auth_header, body={"days": new_days}, path_params={"id": plan_id}),
        None,
    )
    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])["plan"]
    assert len(body["days"]) == 1
    assert body["days"][0]["day_name"] == "Full Body"


def test_update_plan_not_found(auth_header):
    resp = handler(
        _event(method="PUT", resource="/api/plans/{id}", headers=auth_header, body={"name": "X"}, path_params={"id": "nope"}),
        None,
    )
    assert resp["statusCode"] == 404


def test_delete_plan(auth_header):
    plan = _create_plan(auth_header)
    plan_id = plan["plan_id"]

    resp = handler(
        _event(method="DELETE", resource="/api/plans/{id}", headers=auth_header, path_params={"id": plan_id}),
        None,
    )
    assert resp["statusCode"] == 200

    # Verify gone
    get_resp = handler(
        _event(method="GET", resource="/api/plans/{id}", headers=auth_header, path_params={"id": plan_id}),
        None,
    )
    assert get_resp["statusCode"] == 404


def test_delete_plan_not_found(auth_header):
    resp = handler(
        _event(method="DELETE", resource="/api/plans/{id}", headers=auth_header, path_params={"id": "nope"}),
        None,
    )
    assert resp["statusCode"] == 404


def test_activate_plan(auth_header):
    plan = _create_plan(auth_header)
    plan_id = plan["plan_id"]

    resp = handler(
        _event(method="PUT", resource="/api/plans/{id}/activate", headers=auth_header, path_params={"id": plan_id}),
        None,
    )
    assert resp["statusCode"] == 200
    assert json.loads(resp["body"])["plan_id"] == plan_id

    # Verify is_active
    get_resp = handler(
        _event(method="GET", resource="/api/plans/{id}", headers=auth_header, path_params={"id": plan_id}),
        None,
    )
    assert json.loads(get_resp["body"])["plan"]["is_active"] is True


def test_activate_plan_swaps_active(auth_header):
    plan1 = _create_plan(auth_header, name="Plan 1")
    plan2 = _create_plan(auth_header, name="Plan 2")

    # Activate plan 1
    handler(
        _event(method="PUT", resource="/api/plans/{id}/activate", headers=auth_header, path_params={"id": plan1["plan_id"]}),
        None,
    )

    # Activate plan 2
    handler(
        _event(method="PUT", resource="/api/plans/{id}/activate", headers=auth_header, path_params={"id": plan2["plan_id"]}),
        None,
    )

    # Plan 1 should be inactive
    resp1 = handler(
        _event(method="GET", resource="/api/plans/{id}", headers=auth_header, path_params={"id": plan1["plan_id"]}),
        None,
    )
    assert json.loads(resp1["body"])["plan"]["is_active"] is False

    # Plan 2 should be active
    resp2 = handler(
        _event(method="GET", resource="/api/plans/{id}", headers=auth_header, path_params={"id": plan2["plan_id"]}),
        None,
    )
    assert json.loads(resp2["body"])["plan"]["is_active"] is True


def test_activate_plan_idempotent(auth_header):
    plan = _create_plan(auth_header)
    plan_id = plan["plan_id"]

    handler(
        _event(method="PUT", resource="/api/plans/{id}/activate", headers=auth_header, path_params={"id": plan_id}),
        None,
    )
    resp = handler(
        _event(method="PUT", resource="/api/plans/{id}/activate", headers=auth_header, path_params={"id": plan_id}),
        None,
    )
    assert resp["statusCode"] == 200


def test_activate_plan_not_found(auth_header):
    resp = handler(
        _event(method="PUT", resource="/api/plans/{id}/activate", headers=auth_header, path_params={"id": "nope"}),
        None,
    )
    assert resp["statusCode"] == 404


def test_list_plans_includes_active(auth_header):
    plan1 = _create_plan(auth_header, name="Plan 1")
    _create_plan(auth_header, name="Plan 2")

    # Activate plan 1
    handler(
        _event(method="PUT", resource="/api/plans/{id}/activate", headers=auth_header, path_params={"id": plan1["plan_id"]}),
        None,
    )

    resp = handler(_event(headers=auth_header), None)
    plans = json.loads(resp["body"])["plans"]
    assert len(plans) == 2  # Both active and inactive appear


def test_plans_requires_auth():
    resp = handler(_event(headers={}), None)
    assert resp["statusCode"] == 401


def test_plans_expired_jwt(expired_auth_header):
    resp = handler(_event(headers=expired_auth_header), None)
    assert resp["statusCode"] == 401
