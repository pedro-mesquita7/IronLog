import json

import boto3

from handlers.sessions import handler as session_handler
from handlers.sets import handler as set_handler


def _session_event(method="POST", resource="/api/sessions", body=None, headers=None, path_params=None):
    return {
        "httpMethod": method,
        "headers": headers or {},
        "body": json.dumps(body) if body else None,
        "resource": resource,
        "pathParameters": path_params,
        "queryStringParameters": None,
    }


def _set_event(method="POST", resource="/api/sessions/{id}/sets", body=None, headers=None, path_params=None):
    return {
        "httpMethod": method,
        "headers": headers or {},
        "body": json.dumps(body) if body else None,
        "resource": resource,
        "pathParameters": path_params,
    }


def _seed_and_start(auth_header):
    table = boto3.resource("dynamodb").Table("ironlog")
    ex_id = "ex-bench"
    table.put_item(Item={
        "PK": f"EX#{ex_id}", "SK": f"EX#{ex_id}",
        "GSI1PK": "EXERCISES", "GSI1SK": f"EX#{ex_id}",
        "exercise_id": ex_id, "name": "Bench Press", "muscle_group": "chest",
        "has_plate_calculator": True, "is_unilateral": False,
        "rest_timer_seconds": 180, "is_archived": False,
    })
    plan_id = "plan-test"
    table.put_item(Item={
        "PK": f"PLAN#{plan_id}", "SK": "META",
        "GSI1PK": "PLANS", "GSI1SK": f"PLAN#{plan_id}",
        "plan_id": plan_id, "name": "Test", "is_active": True,
    })
    table.put_item(Item={
        "PK": f"PLAN#{plan_id}", "SK": "DAY#01",
        "day_number": 1, "day_name": "Day 1",
        "exercises": [{"exercise_id": ex_id, "order": 1, "target_sets": 2, "target_reps": "5", "set_type": "working"}],
    })

    resp = session_handler(
        _session_event(headers=auth_header, body={"plan_id": plan_id, "plan_day_number": 1}),
        None,
    )
    session_id = json.loads(resp["body"])["session_id"]
    return session_id, ex_id


def test_create_set(auth_header):
    session_id, ex_id = _seed_and_start(auth_header)
    resp = set_handler(
        _set_event(headers=auth_header, body={
            "exercise_id": ex_id, "set_type": "working", "set_order": 1, "weight_kg": 60, "reps": 5, "rir": 2,
        }, path_params={"id": session_id}),
        None,
    )
    assert resp["statusCode"] == 201
    body = json.loads(resp["body"])
    assert body["set_id"] is not None
    assert body["weight_kg"] == 60
    assert body["reps"] == 5
    assert "estimated_1rm" in body


def test_create_set_invalid_type(auth_header):
    session_id, ex_id = _seed_and_start(auth_header)
    resp = set_handler(
        _set_event(headers=auth_header, body={
            "exercise_id": ex_id, "set_type": "invalid", "set_order": 1, "weight_kg": 60, "reps": 5,
        }, path_params={"id": session_id}),
        None,
    )
    assert resp["statusCode"] == 400


def test_create_set_session_not_found(auth_header):
    resp = set_handler(
        _set_event(headers=auth_header, body={
            "exercise_id": "ex", "set_type": "working", "set_order": 1, "weight_kg": 60, "reps": 5,
        }, path_params={"id": "nope"}),
        None,
    )
    assert resp["statusCode"] == 404


def test_cannot_add_set_to_completed_session(auth_header):
    session_id, ex_id = _seed_and_start(auth_header)
    session_handler(
        _session_event(method="PUT", resource="/api/sessions/{id}/complete", headers=auth_header, path_params={"id": session_id}),
        None,
    )
    resp = set_handler(
        _set_event(headers=auth_header, body={
            "exercise_id": ex_id, "set_type": "working", "set_order": 1, "weight_kg": 60, "reps": 5,
        }, path_params={"id": session_id}),
        None,
    )
    assert resp["statusCode"] == 409


def test_update_set(auth_header):
    session_id, ex_id = _seed_and_start(auth_header)
    create_resp = set_handler(
        _set_event(headers=auth_header, body={
            "exercise_id": ex_id, "set_type": "working", "set_order": 1, "weight_kg": 60, "reps": 5, "rir": 2,
        }, path_params={"id": session_id}),
        None,
    )
    set_id = json.loads(create_resp["body"])["set_id"]

    resp = set_handler(
        _set_event(method="PUT", resource="/api/sessions/{id}/sets/{sid}", headers=auth_header,
                   body={"weight_kg": 65, "reps": 4}, path_params={"id": session_id, "sid": set_id}),
        None,
    )
    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])["set"]
    assert body["weight_kg"] == 65
    assert body["reps"] == 4


def test_delete_set(auth_header):
    session_id, ex_id = _seed_and_start(auth_header)
    create_resp = set_handler(
        _set_event(headers=auth_header, body={
            "exercise_id": ex_id, "set_type": "working", "set_order": 1, "weight_kg": 60, "reps": 5,
        }, path_params={"id": session_id}),
        None,
    )
    set_id = json.loads(create_resp["body"])["set_id"]

    resp = set_handler(
        _set_event(method="DELETE", resource="/api/sessions/{id}/sets/{sid}", headers=auth_header,
                   path_params={"id": session_id, "sid": set_id}),
        None,
    )
    assert resp["statusCode"] == 200


def test_cannot_update_set_completed_session(auth_header):
    session_id, ex_id = _seed_and_start(auth_header)
    create_resp = set_handler(
        _set_event(headers=auth_header, body={
            "exercise_id": ex_id, "set_type": "working", "set_order": 1, "weight_kg": 60, "reps": 5,
        }, path_params={"id": session_id}),
        None,
    )
    set_id = json.loads(create_resp["body"])["set_id"]

    session_handler(
        _session_event(method="PUT", resource="/api/sessions/{id}/complete", headers=auth_header, path_params={"id": session_id}),
        None,
    )

    resp = set_handler(
        _set_event(method="PUT", resource="/api/sessions/{id}/sets/{sid}", headers=auth_header,
                   body={"weight_kg": 65}, path_params={"id": session_id, "sid": set_id}),
        None,
    )
    assert resp["statusCode"] == 409


def test_sets_requires_auth():
    resp = set_handler(
        _set_event(headers={}, path_params={"id": "x"}),
        None,
    )
    assert resp["statusCode"] == 401
