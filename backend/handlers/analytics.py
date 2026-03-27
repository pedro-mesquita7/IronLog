import re

from shared.athena import AthenaQueryError, run_athena_query
from shared.auth_middleware import require_auth
from shared.constants import ATHENA_GOLD_DATABASE
from shared.response import api_response, options_response

_UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@require_auth
def handler(event, context):
    if event.get("httpMethod") == "OPTIONS":
        return options_response()

    method = event["httpMethod"]
    resource = event.get("resource", "")

    if method != "GET":
        return api_response(405, {"error": "Method not allowed"})

    if resource == "/api/analytics/progression":
        return _get_progression(event)
    if resource == "/api/analytics/recovery-correlation":
        return _get_recovery_correlation(event)
    if resource == "/api/analytics/prs":
        return _get_prs(event)

    return api_response(404, {"error": "Not found"})


def _get_progression(event):
    params = event.get("queryStringParameters") or {}
    exercise_id = params.get("exercise_id")

    if not exercise_id:
        return api_response(400, {"error": "exercise_id query parameter is required"})

    if not _UUID_RE.match(exercise_id):
        return api_response(400, {"error": "exercise_id must be a valid UUID"})

    sql = (
        f"SELECT week_start, max_weight_kg, avg_weight_kg, weekly_total_load, "
        f"max_estimated_1rm, total_sets, weight_prs, e1rm_prs "
        f"FROM {ATHENA_GOLD_DATABASE}.agg_exercise_progression "
        f"WHERE exercise_id = '{exercise_id}' "
        f"ORDER BY week_start ASC"
    )

    try:
        rows = run_athena_query(sql)
    except AthenaQueryError as e:
        return api_response(500, {"error": f"Query failed: {e}"})

    return api_response(200, {"progression": rows})


def _get_recovery_correlation(event):
    params = event.get("queryStringParameters") or {}
    date_from = params.get("from")
    date_to = params.get("to")

    where_clauses = []
    if date_from:
        if not _DATE_RE.match(date_from):
            return api_response(400, {"error": "from must be YYYY-MM-DD"})
        where_clauses.append(f"date >= '{date_from}'")
    if date_to:
        if not _DATE_RE.match(date_to):
            return api_response(400, {"error": "to must be YYYY-MM-DD"})
        where_clauses.append(f"date <= '{date_to}'")

    where = f" WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    sql = (
        f"SELECT date, recovery_score, hrv_rmssd, resting_heart_rate, "
        f"session_total_load, total_sets, weight_prs, duration_minutes "
        f"FROM {ATHENA_GOLD_DATABASE}.agg_recovery_performance"
        f"{where} "
        f"ORDER BY date ASC"
    )

    try:
        rows = run_athena_query(sql)
    except AthenaQueryError as e:
        return api_response(500, {"error": f"Query failed: {e}"})

    return api_response(200, {"correlation": rows})


def _get_prs(event):
    params = event.get("queryStringParameters") or {}
    exercise_id = params.get("exercise_id")

    where_parts = ["(fs.is_weight_pr = true OR fs.is_e1rm_pr = true)"]
    if exercise_id:
        if not _UUID_RE.match(exercise_id):
            return api_response(400, {"error": "exercise_id must be a valid UUID"})
        where_parts.append(f"fs.exercise_id = '{exercise_id}'")

    where = " AND ".join(where_parts)

    sql = (
        f"SELECT fs.timestamp, fs.exercise_id, de.name AS exercise_name, "
        f"fs.weight_kg, fs.estimated_1rm, fs.reps, "
        f"fs.is_weight_pr, fs.is_e1rm_pr "
        f"FROM {ATHENA_GOLD_DATABASE}.fact_sets fs "
        f"JOIN {ATHENA_GOLD_DATABASE}.dim_exercises de ON fs.exercise_id = de.exercise_id "
        f"WHERE {where} "
        f"ORDER BY fs.timestamp ASC"
    )

    try:
        rows = run_athena_query(sql)
    except AthenaQueryError as e:
        return api_response(500, {"error": f"Query failed: {e}"})

    return api_response(200, {"prs": rows})
