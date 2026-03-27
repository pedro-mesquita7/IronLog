"""Dedicated PR detection tests per spec:
- Weight PR only
- e1RM PR only
- Both PRs
- Neither PR
- Warmup excluded from PRs
"""
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


def _set_event(body=None, headers=None, path_params=None):
    return {
        "httpMethod": "POST",
        "headers": headers or {},
        "body": json.dumps(body) if body else None,
        "resource": "/api/sessions/{id}/sets",
        "pathParameters": path_params,
    }


def _setup(auth_header):
    """Create exercise, plan, session. Return (session_id, exercise_id)."""
    table = boto3.resource("dynamodb").Table("ironlog")
    ex_id = "ex-squat"
    table.put_item(Item={
        "PK": f"EX#{ex_id}", "SK": f"EX#{ex_id}",
        "GSI1PK": "EXERCISES", "GSI1SK": f"EX#{ex_id}",
        "exercise_id": ex_id, "name": "Squat", "muscle_group": "legs",
        "has_plate_calculator": True, "is_unilateral": False,
        "rest_timer_seconds": 180, "is_archived": False,
    })
    plan_id = "plan-pr"
    table.put_item(Item={
        "PK": f"PLAN#{plan_id}", "SK": "META",
        "GSI1PK": "PLANS", "GSI1SK": f"PLAN#{plan_id}",
        "plan_id": plan_id, "name": "PR Test", "is_active": True,
    })
    table.put_item(Item={
        "PK": f"PLAN#{plan_id}", "SK": "DAY#01",
        "day_number": 1, "day_name": "Day 1",
        "exercises": [{"exercise_id": ex_id, "order": 1, "target_sets": 3, "target_reps": "5", "set_type": "working"}],
    })
    resp = session_handler(
        _session_event(headers=auth_header, body={"plan_id": plan_id, "plan_day_number": 1}),
        None,
    )
    session_id = json.loads(resp["body"])["session_id"]
    return session_id, ex_id


def _log_set(auth_header, session_id, ex_id, weight, reps, set_type="working", order=1):
    resp = set_handler(
        _set_event(
            headers=auth_header,
            body={"exercise_id": ex_id, "set_type": set_type, "set_order": order, "weight_kg": weight, "reps": reps, "rir": 0},
            path_params={"id": session_id},
        ),
        None,
    )
    return json.loads(resp["body"])


def test_first_set_is_always_pr(auth_header):
    """First working set ever should be both weight PR and e1RM PR."""
    session_id, ex_id = _setup(auth_header)
    result = _log_set(auth_header, session_id, ex_id, 100, 5)
    assert result["is_weight_pr"] is True
    assert result["is_e1rm_pr"] is True
    # Epley: 100 * (1 + 5/30) = 116.67
    assert abs(float(result["estimated_1rm"]) - 116.67) < 0.01


def test_weight_pr_only(auth_header):
    """Higher weight but fewer reps → weight PR but not e1RM PR."""
    session_id, ex_id = _setup(auth_header)

    # First set: 100kg × 5 reps → e1RM = 116.67
    _log_set(auth_header, session_id, ex_id, 100, 5, order=1)

    # Second set: 105kg × 2 reps → e1RM = 112.0 (lower)
    result = _log_set(auth_header, session_id, ex_id, 105, 2, order=2)
    assert result["is_weight_pr"] is True
    assert result["is_e1rm_pr"] is False


def test_e1rm_pr_only(auth_header):
    """Same weight but more reps → e1RM PR but not weight PR."""
    session_id, ex_id = _setup(auth_header)

    # First set: 100kg × 5 reps → e1RM = 116.67
    _log_set(auth_header, session_id, ex_id, 100, 5, order=1)

    # Second set: 100kg × 8 reps → e1RM = 126.67 (higher e1RM, same weight)
    result = _log_set(auth_header, session_id, ex_id, 100, 8, order=2)
    assert result["is_weight_pr"] is False
    assert result["is_e1rm_pr"] is True


def test_both_prs(auth_header):
    """Higher weight AND more reps → both PRs."""
    session_id, ex_id = _setup(auth_header)

    # First set: 100kg × 5 reps
    _log_set(auth_header, session_id, ex_id, 100, 5, order=1)

    # Second set: 110kg × 6 reps → higher weight AND higher e1RM
    result = _log_set(auth_header, session_id, ex_id, 110, 6, order=2)
    assert result["is_weight_pr"] is True
    assert result["is_e1rm_pr"] is True


def test_neither_pr(auth_header):
    """Lower weight AND fewer reps → neither PR."""
    session_id, ex_id = _setup(auth_header)

    # First set: 100kg × 5 reps
    _log_set(auth_header, session_id, ex_id, 100, 5, order=1)

    # Second set: 90kg × 4 reps → neither PR
    result = _log_set(auth_header, session_id, ex_id, 90, 4, order=2)
    assert result["is_weight_pr"] is False
    assert result["is_e1rm_pr"] is False


def test_warmup_excluded_from_pr(auth_header):
    """Warmup sets should never trigger PRs, even if weight/reps exceed history."""
    session_id, ex_id = _setup(auth_header)

    # Working set: 100kg × 5
    _log_set(auth_header, session_id, ex_id, 100, 5, order=1)

    # Warmup with higher weight — should NOT be a PR
    result = _log_set(auth_header, session_id, ex_id, 200, 10, set_type="warmup_50", order=2)
    assert result["is_weight_pr"] is False
    assert result["is_e1rm_pr"] is False


def test_warmup_not_counted_in_history(auth_header):
    """A warmup set should not count toward PR history for future working sets."""
    session_id, ex_id = _setup(auth_header)

    # Log a heavy warmup first
    _log_set(auth_header, session_id, ex_id, 200, 10, set_type="warmup_75", order=1)

    # First working set should still be a PR (warmup excluded from comparison)
    result = _log_set(auth_header, session_id, ex_id, 100, 5, order=2)
    assert result["is_weight_pr"] is True
    assert result["is_e1rm_pr"] is True
