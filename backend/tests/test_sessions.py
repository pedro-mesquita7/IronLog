import json

import boto3

from handlers.sessions import handler


def _event(method="GET", resource="/api/sessions", body=None, headers=None, path_params=None, query=None):
    return {
        "httpMethod": method,
        "headers": headers or {},
        "body": json.dumps(body) if body else None,
        "resource": resource,
        "pathParameters": path_params,
        "queryStringParameters": query,
    }


def _seed_plan_and_exercise(table):
    """Create a plan with one day and one exercise for session tests."""
    ex_id = "ex-deadlift"
    table.put_item(Item={
        "PK": f"EX#{ex_id}", "SK": f"EX#{ex_id}",
        "GSI1PK": "EXERCISES", "GSI1SK": f"EX#{ex_id}",
        "exercise_id": ex_id, "name": "Deadlift", "muscle_group": "back",
        "has_plate_calculator": True, "is_unilateral": False, "weak_side": None,
        "rest_timer_seconds": 180, "is_archived": False,
        "notes": "Brace core", "machine_settings": None,
    })

    plan_id = "plan-ul4x"
    table.put_item(Item={
        "PK": f"PLAN#{plan_id}", "SK": "META",
        "GSI1PK": "PLANS", "GSI1SK": f"PLAN#{plan_id}",
        "plan_id": plan_id, "name": "UL 4x", "is_active": True,
    })
    table.put_item(Item={
        "PK": f"PLAN#{plan_id}", "SK": "DAY#01",
        "day_number": 1, "day_name": "Upper A",
        "exercises": [
            {"exercise_id": ex_id, "order": 1, "target_sets": 2, "target_reps": "3-5", "set_type": "working"},
        ],
    })
    return plan_id, ex_id


def _start_session(auth_header):
    table = boto3.resource("dynamodb").Table("ironlog")
    plan_id, ex_id = _seed_plan_and_exercise(table)
    resp = handler(
        _event(method="POST", headers=auth_header, body={"plan_id": plan_id, "plan_day_number": 1}),
        None,
    )
    body = json.loads(resp["body"])
    return body["session_id"], plan_id, ex_id


def test_start_session(auth_header):
    session_id, _, _ = _start_session(auth_header)
    assert session_id is not None


def test_start_session_returns_exercises(auth_header):
    table = boto3.resource("dynamodb").Table("ironlog")
    plan_id, ex_id = _seed_plan_and_exercise(table)
    resp = handler(
        _event(method="POST", headers=auth_header, body={"plan_id": plan_id, "plan_day_number": 1}),
        None,
    )
    assert resp["statusCode"] == 201
    body = json.loads(resp["body"])
    assert len(body["exercises"]) == 1
    ex = body["exercises"][0]
    assert ex["name"] == "Deadlift"
    assert ex["rest_timer_seconds"] == 180
    assert ex["notes"] == "Brace core"


def test_start_session_warmup_no_history(auth_header):
    table = boto3.resource("dynamodb").Table("ironlog")
    plan_id, _ = _seed_plan_and_exercise(table)
    resp = handler(
        _event(method="POST", headers=auth_header, body={"plan_id": plan_id, "plan_day_number": 1}),
        None,
    )
    body = json.loads(resp["body"])
    assert body["exercises"][0]["warmup"] is None
    assert body["exercises"][0]["last_working_weight_kg"] is None


def test_start_session_missing_plan(auth_header):
    resp = handler(
        _event(method="POST", headers=auth_header, body={"plan_id": "nope", "plan_day_number": 1}),
        None,
    )
    assert resp["statusCode"] == 404


def test_get_session(auth_header):
    session_id, _, _ = _start_session(auth_header)
    resp = handler(
        _event(method="GET", resource="/api/sessions/{id}", headers=auth_header, path_params={"id": session_id}),
        None,
    )
    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])["session"]
    assert body["session_id"] == session_id
    assert body["status"] == "in_progress"
    assert "sets" in body


def test_get_session_not_found(auth_header):
    resp = handler(
        _event(method="GET", resource="/api/sessions/{id}", headers=auth_header, path_params={"id": "nope"}),
        None,
    )
    assert resp["statusCode"] == 404


def test_list_sessions(auth_header):
    _start_session(auth_header)
    resp = handler(_event(headers=auth_header), None)
    assert resp["statusCode"] == 200
    assert len(json.loads(resp["body"])["sessions"]) == 1


def test_list_sessions_date_range(auth_header):
    _start_session(auth_header)
    resp = handler(
        _event(headers=auth_header, query={"from": "2020-01-01", "to": "2020-12-31"}),
        None,
    )
    assert json.loads(resp["body"])["sessions"] == []


def test_update_session_notes(auth_header):
    session_id, _, _ = _start_session(auth_header)
    resp = handler(
        _event(method="PUT", resource="/api/sessions/{id}", headers=auth_header, body={"notes": "Felt great"}, path_params={"id": session_id}),
        None,
    )
    assert resp["statusCode"] == 200
    assert json.loads(resp["body"])["session"]["notes"] == "Felt great"


def test_complete_session(auth_header):
    session_id, _, _ = _start_session(auth_header)
    resp = handler(
        _event(method="PUT", resource="/api/sessions/{id}/complete", headers=auth_header, path_params={"id": session_id}),
        None,
    )
    assert resp["statusCode"] == 200
    assert json.loads(resp["body"])["session"]["status"] == "completed"


def test_cannot_update_completed_session(auth_header):
    session_id, _, _ = _start_session(auth_header)
    handler(
        _event(method="PUT", resource="/api/sessions/{id}/complete", headers=auth_header, path_params={"id": session_id}),
        None,
    )
    resp = handler(
        _event(method="PUT", resource="/api/sessions/{id}", headers=auth_header, body={"notes": "X"}, path_params={"id": session_id}),
        None,
    )
    assert resp["statusCode"] == 409


def test_session_exercise_notes(auth_header):
    session_id, _, ex_id = _start_session(auth_header)

    # Create note
    resp = handler(
        _event(method="POST", resource="/api/sessions/{id}/notes", headers=auth_header,
               body={"exercise_id": ex_id, "note_text": "Go heavier next time"}, path_params={"id": session_id}),
        None,
    )
    assert resp["statusCode"] == 201

    # List notes
    resp = handler(
        _event(method="GET", resource="/api/sessions/{id}/notes", headers=auth_header, path_params={"id": session_id}),
        None,
    )
    assert resp["statusCode"] == 200
    notes = json.loads(resp["body"])["notes"]
    assert len(notes) == 1
    assert notes[0]["note_text"] == "Go heavier next time"


def test_cannot_start_session_while_one_in_progress(auth_header):
    """Starting a new session should fail if one is already in_progress."""
    session_id, plan_id, _ = _start_session(auth_header)
    # Try starting another session — should get 409
    resp = handler(
        _event(method="POST", headers=auth_header, body={"plan_id": plan_id, "plan_day_number": 1}),
        None,
    )
    assert resp["statusCode"] == 409
    body = json.loads(resp["body"])
    assert "already have a session in progress" in body["error"]
    assert body["existing_session_id"] == session_id


def test_can_start_session_after_completing_previous(auth_header):
    """After completing a session, starting a new one should work."""
    session_id, plan_id, _ = _start_session(auth_header)
    # Complete it
    handler(
        _event(method="PUT", resource="/api/sessions/{id}/complete", headers=auth_header, path_params={"id": session_id}),
        None,
    )
    # Now start another — should succeed
    resp = handler(
        _event(method="POST", headers=auth_header, body={"plan_id": plan_id, "plan_day_number": 1}),
        None,
    )
    assert resp["statusCode"] == 201


def test_delete_session_soft_delete(auth_header):
    """Deleting a session should soft-delete it (status = 'deleted')."""
    session_id, _, _ = _start_session(auth_header)
    # Complete it first
    handler(
        _event(method="PUT", resource="/api/sessions/{id}/complete", headers=auth_header, path_params={"id": session_id}),
        None,
    )
    # Delete it
    resp = handler(
        _event(method="DELETE", resource="/api/sessions/{id}", headers=auth_header, path_params={"id": session_id}),
        None,
    )
    assert resp["statusCode"] == 200

    # Verify it's now deleted
    resp = handler(
        _event(method="GET", resource="/api/sessions/{id}", headers=auth_header, path_params={"id": session_id}),
        None,
    )
    body = json.loads(resp["body"])["session"]
    assert body["status"] == "deleted"


def test_deleted_session_excluded_from_list(auth_header):
    """Deleted sessions should not appear in the list."""
    session_id, plan_id, _ = _start_session(auth_header)
    # Complete it
    handler(
        _event(method="PUT", resource="/api/sessions/{id}/complete", headers=auth_header, path_params={"id": session_id}),
        None,
    )
    # Delete it
    handler(
        _event(method="DELETE", resource="/api/sessions/{id}", headers=auth_header, path_params={"id": session_id}),
        None,
    )
    # List should be empty
    resp = handler(_event(headers=auth_header), None)
    assert len(json.loads(resp["body"])["sessions"]) == 0


def test_can_start_session_after_deleting_in_progress(auth_header):
    """Deleting an in-progress session should allow starting a new one."""
    session_id, plan_id, _ = _start_session(auth_header)
    # Delete the in-progress session
    handler(
        _event(method="DELETE", resource="/api/sessions/{id}", headers=auth_header, path_params={"id": session_id}),
        None,
    )
    # Now start another — should succeed
    resp = handler(
        _event(method="POST", headers=auth_header, body={"plan_id": plan_id, "plan_day_number": 1}),
        None,
    )
    assert resp["statusCode"] == 201


def test_delete_nonexistent_session(auth_header):
    resp = handler(
        _event(method="DELETE", resource="/api/sessions/{id}", headers=auth_header, path_params={"id": "nope"}),
        None,
    )
    assert resp["statusCode"] == 404


def test_sessions_requires_auth():
    resp = handler(_event(headers={}), None)
    assert resp["statusCode"] == 401
