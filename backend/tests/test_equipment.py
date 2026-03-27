import json

from handlers.equipment import handler


def _event(method="GET", resource="/api/equipment", body=None, headers=None, path_params=None):
    return {
        "httpMethod": method,
        "headers": headers or {},
        "body": json.dumps(body) if body else None,
        "resource": resource,
        "pathParameters": path_params,
    }


def test_list_equipment_empty(auth_header):
    resp = handler(_event(headers=auth_header), None)
    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])
    assert body["equipment"] == []


def test_create_equipment(auth_header):
    resp = handler(
        _event(
            method="POST",
            headers=auth_header,
            body={"name": "Olympic Barbell", "equipment_type": "bar", "weight_kg": 20},
        ),
        None,
    )
    assert resp["statusCode"] == 201
    body = json.loads(resp["body"])
    eq = body["equipment"]
    assert eq["name"] == "Olympic Barbell"
    assert eq["equipment_type"] == "bar"
    assert eq["weight_kg"] == 20
    assert eq["is_archived"] is False
    assert "equipment_id" in eq


def test_create_equipment_invalid_type(auth_header):
    resp = handler(
        _event(method="POST", headers=auth_header, body={"name": "Foo", "equipment_type": "invalid"}),
        None,
    )
    assert resp["statusCode"] == 400


def test_create_equipment_missing_name(auth_header):
    resp = handler(
        _event(method="POST", headers=auth_header, body={"equipment_type": "bar"}),
        None,
    )
    assert resp["statusCode"] == 400


def test_list_equipment_after_create(auth_header):
    handler(
        _event(method="POST", headers=auth_header, body={"name": "Bar", "equipment_type": "bar", "weight_kg": 20}),
        None,
    )
    resp = handler(_event(headers=auth_header), None)
    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])
    assert len(body["equipment"]) == 1
    assert body["equipment"][0]["name"] == "Bar"


def test_update_equipment(auth_header):
    # Create
    create_resp = handler(
        _event(method="POST", headers=auth_header, body={"name": "Bar", "equipment_type": "bar", "weight_kg": 20}),
        None,
    )
    eq_id = json.loads(create_resp["body"])["equipment"]["equipment_id"]

    # Update
    resp = handler(
        _event(
            method="PUT",
            resource="/api/equipment/{id}",
            headers=auth_header,
            body={"name": "Olympic Barbell 20kg"},
            path_params={"id": eq_id},
        ),
        None,
    )
    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])
    assert body["equipment"]["name"] == "Olympic Barbell 20kg"


def test_update_equipment_not_found(auth_header):
    resp = handler(
        _event(
            method="PUT",
            resource="/api/equipment/{id}",
            headers=auth_header,
            body={"name": "X"},
            path_params={"id": "nonexistent"},
        ),
        None,
    )
    assert resp["statusCode"] == 404


def test_delete_equipment(auth_header):
    # Create
    create_resp = handler(
        _event(method="POST", headers=auth_header, body={"name": "Bar", "equipment_type": "bar", "weight_kg": 20}),
        None,
    )
    eq_id = json.loads(create_resp["body"])["equipment"]["equipment_id"]

    # Delete (archive)
    resp = handler(
        _event(
            method="DELETE",
            resource="/api/equipment/{id}",
            headers=auth_header,
            path_params={"id": eq_id},
        ),
        None,
    )
    assert resp["statusCode"] == 200

    # List should be empty (archived items filtered out)
    list_resp = handler(_event(headers=auth_header), None)
    body = json.loads(list_resp["body"])
    assert len(body["equipment"]) == 0


def test_delete_equipment_not_found(auth_header):
    resp = handler(
        _event(
            method="DELETE",
            resource="/api/equipment/{id}",
            headers=auth_header,
            path_params={"id": "nonexistent"},
        ),
        None,
    )
    assert resp["statusCode"] == 404


def test_equipment_requires_auth():
    resp = handler(_event(headers={}), None)
    assert resp["statusCode"] == 401


def test_equipment_expired_jwt(expired_auth_header):
    resp = handler(_event(headers=expired_auth_header), None)
    assert resp["statusCode"] == 401
