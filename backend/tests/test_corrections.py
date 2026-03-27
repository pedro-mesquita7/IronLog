import json

import boto3

from handlers.corrections import handler as corr_handler
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


def _set_event(body=None, headers=None, path_params=None):
    return {
        "httpMethod": "POST",
        "headers": headers or {},
        "body": json.dumps(body) if body else None,
        "resource": "/api/sessions/{id}/sets",
        "pathParameters": path_params,
    }


def _corr_event(method="POST", resource="/api/corrections", body=None, headers=None, query=None):
    return {
        "httpMethod": method,
        "headers": headers or {},
        "body": json.dumps(body) if body else None,
        "resource": resource,
        "pathParameters": None,
        "queryStringParameters": query,
    }


def _setup_completed_session_with_set(auth_header):
    """Create exercise, plan, session, log a set, complete session."""
    table = boto3.resource("dynamodb").Table("ironlog")
    ex_id = "ex-row"
    table.put_item(Item={
        "PK": f"EX#{ex_id}", "SK": f"EX#{ex_id}",
        "GSI1PK": "EXERCISES", "GSI1SK": f"EX#{ex_id}",
        "exercise_id": ex_id, "name": "Row", "muscle_group": "back",
        "has_plate_calculator": False, "is_unilateral": False,
        "rest_timer_seconds": 120, "is_archived": False,
    })
    plan_id = "plan-corr"
    table.put_item(Item={
        "PK": f"PLAN#{plan_id}", "SK": "META",
        "GSI1PK": "PLANS", "GSI1SK": f"PLAN#{plan_id}",
        "plan_id": plan_id, "name": "Corr", "is_active": True,
    })
    table.put_item(Item={
        "PK": f"PLAN#{plan_id}", "SK": "DAY#01",
        "day_number": 1, "day_name": "Day 1",
        "exercises": [{"exercise_id": ex_id, "order": 1, "target_sets": 1, "target_reps": "5", "set_type": "working"}],
    })

    # Start session
    resp = session_handler(
        _session_event(headers=auth_header, body={"plan_id": plan_id, "plan_day_number": 1}),
        None,
    )
    session_id = json.loads(resp["body"])["session_id"]

    # Log set
    set_resp = set_handler(
        _set_event(headers=auth_header, body={
            "exercise_id": ex_id, "set_type": "working", "set_order": 1, "weight_kg": 80, "reps": 5, "rir": 1,
        }, path_params={"id": session_id}),
        None,
    )
    set_id = json.loads(set_resp["body"])["set_id"]

    # Complete session
    session_handler(
        _session_event(method="PUT", resource="/api/sessions/{id}/complete", headers=auth_header, path_params={"id": session_id}),
        None,
    )

    return session_id, set_id


def test_create_correction(auth_header):
    session_id, set_id = _setup_completed_session_with_set(auth_header)
    resp = corr_handler(
        _corr_event(headers=auth_header, body={
            "set_id": set_id, "session_id": session_id,
            "field": "reps", "old_value": 5, "new_value": 6, "reason": "Miscounted",
        }),
        None,
    )
    assert resp["statusCode"] == 201
    body = json.loads(resp["body"])["correction"]
    assert body["field"] == "reps"
    assert body["old_value"] == 5
    assert body["new_value"] == 6
    assert body["reason"] == "Miscounted"


def test_correction_updates_set_value(auth_header):
    session_id, set_id = _setup_completed_session_with_set(auth_header)
    corr_handler(
        _corr_event(headers=auth_header, body={
            "set_id": set_id, "session_id": session_id,
            "field": "weight_kg", "old_value": 80, "new_value": 85,
        }),
        None,
    )

    # Verify set was updated
    get_resp = session_handler(
        _session_event(method="GET", resource="/api/sessions/{id}", headers=auth_header, path_params={"id": session_id}),
        None,
    )
    session = json.loads(get_resp["body"])["session"]
    the_set = session["sets"][0]
    assert the_set["weight_kg"] == 85


def test_correction_invalid_field(auth_header):
    session_id, set_id = _setup_completed_session_with_set(auth_header)
    resp = corr_handler(
        _corr_event(headers=auth_header, body={
            "set_id": set_id, "session_id": session_id,
            "field": "name", "old_value": "x", "new_value": "y",
        }),
        None,
    )
    assert resp["statusCode"] == 400


def test_correction_set_not_found(auth_header):
    session_id, _ = _setup_completed_session_with_set(auth_header)
    resp = corr_handler(
        _corr_event(headers=auth_header, body={
            "set_id": "nope", "session_id": session_id,
            "field": "reps", "old_value": 5, "new_value": 6,
        }),
        None,
    )
    assert resp["statusCode"] == 404


def test_list_corrections(auth_header):
    session_id, set_id = _setup_completed_session_with_set(auth_header)
    corr_handler(
        _corr_event(headers=auth_header, body={
            "set_id": set_id, "session_id": session_id,
            "field": "reps", "old_value": 5, "new_value": 6,
        }),
        None,
    )

    resp = corr_handler(
        _corr_event(method="GET", headers=auth_header, query={"session_id": session_id}),
        None,
    )
    assert resp["statusCode"] == 200
    assert len(json.loads(resp["body"])["corrections"]) == 1


def test_corrections_requires_auth():
    resp = corr_handler(
        _corr_event(headers={}),
        None,
    )
    assert resp["statusCode"] == 401
