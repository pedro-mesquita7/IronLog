import json
from unittest.mock import patch, call

from handlers.export import handler


def _event(method="GET", headers=None, query=None):
    return {
        "httpMethod": method,
        "headers": headers or {},
        "body": None,
        "resource": "/api/export",
        "pathParameters": None,
        "queryStringParameters": query,
    }


MOCK_SESSIONS = [
    {
        "session_id": "sess-1",
        "plan_id": "plan-1",
        "plan_day_number": "1",
        "date": "2025-01-06",
        "status": "completed",
        "total_sets": "10",
        "exercise_count": "5",
        "session_total_load": "5000.0",
        "weight_prs": "2",
        "e1rm_prs": "1",
        "duration_minutes": "55",
    }
]

MOCK_SETS = [
    {
        "set_id": "set-1",
        "session_id": "sess-1",
        "exercise_id": "ex-1",
        "exercise_name": "Deadlift",
        "weight_kg": "140.0",
        "reps": "5",
        "rir": "1",
        "set_type": "working",
        "is_weight_pr": "true",
        "is_e1rm_pr": "true",
        "estimated_1rm": "163.33",
        "total_load": "700.0",
        "timestamp": "2025-01-06T10:30:00Z",
    }
]


def test_requires_auth():
    resp = handler(_event(headers={}), None)
    assert resp["statusCode"] == 401


def test_options(auth_header):
    resp = handler(_event(method="OPTIONS", headers=auth_header), None)
    assert resp["statusCode"] == 200


def test_method_not_allowed(auth_header):
    resp = handler(_event(method="POST", headers=auth_header), None)
    assert resp["statusCode"] == 405


@patch("handlers.export.run_athena_query", side_effect=[MOCK_SESSIONS, MOCK_SETS])
def test_export_success(mock_query, auth_header):
    resp = handler(
        _event(headers=auth_header, query={"from": "2025-01-01", "to": "2025-03-31"}),
        None,
    )
    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])
    export = body["export"]
    assert export["from"] == "2025-01-01"
    assert export["to"] == "2025-03-31"
    assert len(export["sessions"]) == 1
    assert len(export["sets"]) == 1
    assert mock_query.call_count == 2


@patch("handlers.export.run_athena_query", side_effect=[[], []])
def test_export_defaults(mock_query, auth_header):
    """Without from/to params, defaults to last 90 days."""
    resp = handler(_event(headers=auth_header), None)
    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])
    assert "from" in body["export"]
    assert "to" in body["export"]


def test_export_invalid_from_date(auth_header):
    resp = handler(
        _event(headers=auth_header, query={"from": "bad-date"}),
        None,
    )
    assert resp["statusCode"] == 400


def test_export_invalid_to_date(auth_header):
    resp = handler(
        _event(headers=auth_header, query={"from": "2025-01-01", "to": "bad"}),
        None,
    )
    assert resp["statusCode"] == 400


def test_export_range_too_large(auth_header):
    resp = handler(
        _event(headers=auth_header, query={"from": "2023-01-01", "to": "2025-12-31"}),
        None,
    )
    assert resp["statusCode"] == 400
    assert "365" in json.loads(resp["body"])["error"]


def test_export_to_before_from(auth_header):
    resp = handler(
        _event(headers=auth_header, query={"from": "2025-06-01", "to": "2025-01-01"}),
        None,
    )
    assert resp["statusCode"] == 400
    assert "after" in json.loads(resp["body"])["error"].lower()


@patch("handlers.export.run_athena_query")
def test_export_athena_error(mock_query, auth_header):
    from shared.athena import AthenaQueryError

    mock_query.side_effect = AthenaQueryError("query failed")
    resp = handler(
        _event(headers=auth_header, query={"from": "2025-01-01", "to": "2025-03-31"}),
        None,
    )
    assert resp["statusCode"] == 500
    assert "failed" in json.loads(resp["body"])["error"].lower()
