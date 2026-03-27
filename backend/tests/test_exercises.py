import json

from handlers.exercises import handler


def _event(method="GET", resource="/api/exercises", body=None, headers=None, path_params=None):
    return {
        "httpMethod": method,
        "headers": headers or {},
        "body": json.dumps(body) if body else None,
        "resource": resource,
        "pathParameters": path_params,
    }


VALID_EXERCISE = {
    "name": "Deadlift",
    "muscle_group": "back",
    "rest_timer_seconds": 180,
}


def test_list_exercises_empty(auth_header):
    resp = handler(_event(headers=auth_header), None)
    assert resp["statusCode"] == 200
    assert json.loads(resp["body"])["exercises"] == []


def test_create_exercise(auth_header):
    resp = handler(_event(method="POST", headers=auth_header, body=VALID_EXERCISE), None)
    assert resp["statusCode"] == 201
    ex = json.loads(resp["body"])["exercise"]
    assert ex["name"] == "Deadlift"
    assert ex["muscle_group"] == "back"
    assert ex["rest_timer_seconds"] == 180
    assert ex["is_archived"] is False
    assert ex["has_plate_calculator"] is False
    assert ex["is_unilateral"] is False
    assert "exercise_id" in ex


def test_create_exercise_defaults(auth_header):
    resp = handler(
        _event(method="POST", headers=auth_header, body={"name": "Curl", "muscle_group": "arms"}),
        None,
    )
    assert resp["statusCode"] == 201
    ex = json.loads(resp["body"])["exercise"]
    assert ex["rest_timer_seconds"] == 60
    assert ex["has_plate_calculator"] is False
    assert ex["is_unilateral"] is False
    assert ex["replacement_exercise_ids"] == []


def test_create_exercise_missing_name(auth_header):
    resp = handler(_event(method="POST", headers=auth_header, body={"muscle_group": "back"}), None)
    assert resp["statusCode"] == 400


def test_create_exercise_invalid_muscle_group(auth_header):
    resp = handler(
        _event(method="POST", headers=auth_header, body={"name": "X", "muscle_group": "invalid"}),
        None,
    )
    assert resp["statusCode"] == 400


def test_create_exercise_invalid_rest_timer(auth_header):
    resp = handler(
        _event(method="POST", headers=auth_header, body={"name": "X", "muscle_group": "back", "rest_timer_seconds": 90}),
        None,
    )
    assert resp["statusCode"] == 400


def test_create_exercise_duplicate_name(auth_header):
    handler(_event(method="POST", headers=auth_header, body=VALID_EXERCISE), None)
    resp = handler(_event(method="POST", headers=auth_header, body=VALID_EXERCISE), None)
    assert resp["statusCode"] == 409
    assert "already exists" in json.loads(resp["body"])["error"]


def test_create_exercise_duplicate_name_archived(auth_header):
    # Create and archive
    create_resp = handler(_event(method="POST", headers=auth_header, body=VALID_EXERCISE), None)
    ex_id = json.loads(create_resp["body"])["exercise"]["exercise_id"]
    handler(
        _event(method="DELETE", resource="/api/exercises/{id}", headers=auth_header, path_params={"id": ex_id}),
        None,
    )

    # Try creating with same name
    resp = handler(_event(method="POST", headers=auth_header, body=VALID_EXERCISE), None)
    assert resp["statusCode"] == 409
    body = json.loads(resp["body"])
    assert "archived" in body["error"]
    assert "exercise" in body


def test_list_exercises_after_create(auth_header):
    handler(_event(method="POST", headers=auth_header, body=VALID_EXERCISE), None)
    resp = handler(_event(headers=auth_header), None)
    assert len(json.loads(resp["body"])["exercises"]) == 1


def test_update_exercise(auth_header):
    create_resp = handler(_event(method="POST", headers=auth_header, body=VALID_EXERCISE), None)
    ex_id = json.loads(create_resp["body"])["exercise"]["exercise_id"]

    resp = handler(
        _event(
            method="PUT", resource="/api/exercises/{id}", headers=auth_header,
            body={"name": "Sumo Deadlift"}, path_params={"id": ex_id},
        ),
        None,
    )
    assert resp["statusCode"] == 200
    assert json.loads(resp["body"])["exercise"]["name"] == "Sumo Deadlift"


def test_update_exercise_invalid_muscle_group(auth_header):
    create_resp = handler(_event(method="POST", headers=auth_header, body=VALID_EXERCISE), None)
    ex_id = json.loads(create_resp["body"])["exercise"]["exercise_id"]

    resp = handler(
        _event(
            method="PUT", resource="/api/exercises/{id}", headers=auth_header,
            body={"muscle_group": "invalid"}, path_params={"id": ex_id},
        ),
        None,
    )
    assert resp["statusCode"] == 400


def test_update_exercise_not_found(auth_header):
    resp = handler(
        _event(method="PUT", resource="/api/exercises/{id}", headers=auth_header, body={"name": "X"}, path_params={"id": "nope"}),
        None,
    )
    assert resp["statusCode"] == 404


def test_delete_exercise(auth_header):
    create_resp = handler(_event(method="POST", headers=auth_header, body=VALID_EXERCISE), None)
    ex_id = json.loads(create_resp["body"])["exercise"]["exercise_id"]

    resp = handler(
        _event(method="DELETE", resource="/api/exercises/{id}", headers=auth_header, path_params={"id": ex_id}),
        None,
    )
    assert resp["statusCode"] == 200

    list_resp = handler(_event(headers=auth_header), None)
    assert json.loads(list_resp["body"])["exercises"] == []


def test_delete_exercise_not_found(auth_header):
    resp = handler(
        _event(method="DELETE", resource="/api/exercises/{id}", headers=auth_header, path_params={"id": "nope"}),
        None,
    )
    assert resp["statusCode"] == 404


def test_exercises_requires_auth():
    resp = handler(_event(headers={}), None)
    assert resp["statusCode"] == 401


def test_exercises_expired_jwt(expired_auth_header):
    resp = handler(_event(headers=expired_auth_header), None)
    assert resp["statusCode"] == 401
