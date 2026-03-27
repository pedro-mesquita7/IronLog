import json
from unittest.mock import patch

from handlers.analytics import handler


def _event(resource="/api/analytics/progression", method="GET", headers=None, query=None):
    return {
        "httpMethod": method,
        "headers": headers or {},
        "body": None,
        "resource": resource,
        "pathParameters": None,
        "queryStringParameters": query,
    }


MOCK_PROGRESSION = [
    {
        "week_start": "2025-01-06",
        "max_weight_kg": "100.0",
        "avg_weight_kg": "95.0",
        "weekly_total_load": "950.0",
        "max_estimated_1rm": "116.67",
        "total_sets": "4",
        "weight_prs": "1",
        "e1rm_prs": "1",
    }
]

MOCK_CORRELATION = [
    {
        "date": "2025-01-06",
        "recovery_score": "81",
        "hrv_rmssd": "69.0",
        "resting_heart_rate": "52",
        "session_total_load": "5000.0",
        "total_sets": "12",
        "weight_prs": "2",
        "duration_minutes": "65",
    }
]

MOCK_PRS = [
    {
        "timestamp": "2025-01-06T10:30:00Z",
        "exercise_id": "550e8400-e29b-41d4-a716-446655440000",
        "exercise_name": "Deadlift",
        "weight_kg": "140.0",
        "estimated_1rm": "163.33",
        "reps": "5",
        "is_weight_pr": "true",
        "is_e1rm_pr": "true",
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


def test_not_found(auth_header):
    resp = handler(_event(resource="/api/analytics/unknown", headers=auth_header), None)
    assert resp["statusCode"] == 404


# --- Progression ---


@patch("handlers.analytics.run_athena_query", return_value=MOCK_PROGRESSION)
def test_progression_success(mock_query, auth_header):
    resp = handler(
        _event(headers=auth_header, query={"exercise_id": "550e8400-e29b-41d4-a716-446655440000"}),
        None,
    )
    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])
    assert "progression" in body
    assert len(body["progression"]) == 1
    assert body["progression"][0]["week_start"] == "2025-01-06"
    mock_query.assert_called_once()


def test_progression_missing_exercise_id(auth_header):
    resp = handler(_event(headers=auth_header, query={}), None)
    assert resp["statusCode"] == 400
    assert "exercise_id" in json.loads(resp["body"])["error"]


def test_progression_no_query_params(auth_header):
    resp = handler(_event(headers=auth_header), None)
    assert resp["statusCode"] == 400


def test_progression_invalid_uuid(auth_header):
    resp = handler(
        _event(headers=auth_header, query={"exercise_id": "not-a-uuid"}),
        None,
    )
    assert resp["statusCode"] == 400
    assert "UUID" in json.loads(resp["body"])["error"]


@patch("handlers.analytics.run_athena_query", side_effect=Exception("Query FAILED: table not found"))
def test_progression_athena_error(mock_query, auth_header):
    from shared.athena import AthenaQueryError

    mock_query.side_effect = AthenaQueryError("table not found")
    resp = handler(
        _event(headers=auth_header, query={"exercise_id": "550e8400-e29b-41d4-a716-446655440000"}),
        None,
    )
    assert resp["statusCode"] == 500
    assert "failed" in json.loads(resp["body"])["error"].lower()


# --- Recovery Correlation ---


@patch("handlers.analytics.run_athena_query", return_value=MOCK_CORRELATION)
def test_recovery_correlation_success(mock_query, auth_header):
    resp = handler(
        _event(resource="/api/analytics/recovery-correlation", headers=auth_header),
        None,
    )
    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])
    assert "correlation" in body
    assert len(body["correlation"]) == 1
    mock_query.assert_called_once()


@patch("handlers.analytics.run_athena_query", return_value=MOCK_CORRELATION)
def test_recovery_correlation_with_dates(mock_query, auth_header):
    resp = handler(
        _event(
            resource="/api/analytics/recovery-correlation",
            headers=auth_header,
            query={"from": "2025-01-01", "to": "2025-03-31"},
        ),
        None,
    )
    assert resp["statusCode"] == 200
    sql = mock_query.call_args[0][0]
    assert "2025-01-01" in sql
    assert "2025-03-31" in sql


def test_recovery_correlation_invalid_date(auth_header):
    resp = handler(
        _event(
            resource="/api/analytics/recovery-correlation",
            headers=auth_header,
            query={"from": "not-a-date"},
        ),
        None,
    )
    assert resp["statusCode"] == 400


# --- PRs ---


@patch("handlers.analytics.run_athena_query", return_value=MOCK_PRS)
def test_prs_success(mock_query, auth_header):
    resp = handler(
        _event(resource="/api/analytics/prs", headers=auth_header),
        None,
    )
    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])
    assert "prs" in body
    assert len(body["prs"]) == 1
    assert body["prs"][0]["exercise_name"] == "Deadlift"
    mock_query.assert_called_once()


@patch("handlers.analytics.run_athena_query", return_value=MOCK_PRS)
def test_prs_with_exercise_filter(mock_query, auth_header):
    resp = handler(
        _event(
            resource="/api/analytics/prs",
            headers=auth_header,
            query={"exercise_id": "550e8400-e29b-41d4-a716-446655440000"},
        ),
        None,
    )
    assert resp["statusCode"] == 200
    sql = mock_query.call_args[0][0]
    assert "550e8400-e29b-41d4-a716-446655440000" in sql


def test_prs_invalid_exercise_id(auth_header):
    resp = handler(
        _event(
            resource="/api/analytics/prs",
            headers=auth_header,
            query={"exercise_id": "bad-id"},
        ),
        None,
    )
    assert resp["statusCode"] == 400
