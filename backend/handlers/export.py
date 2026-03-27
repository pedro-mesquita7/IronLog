import re
from datetime import datetime, timedelta, timezone

from shared.athena import AthenaQueryError, run_athena_query
from shared.auth_middleware import require_auth
from shared.constants import ATHENA_GOLD_DATABASE
from shared.response import api_response, options_response

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_MAX_RANGE_DAYS = 365


@require_auth
def handler(event, context):
    if event.get("httpMethod") == "OPTIONS":
        return options_response()

    method = event["httpMethod"]
    resource = event.get("resource", "")

    if resource == "/api/export" and method == "GET":
        return _export(event)

    return api_response(405, {"error": "Method not allowed"})


def _export(event):
    params = event.get("queryStringParameters") or {}
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    default_from = (datetime.now(timezone.utc) - timedelta(days=90)).strftime("%Y-%m-%d")

    date_from = params.get("from", default_from)
    date_to = params.get("to", today)

    if not _DATE_RE.match(date_from):
        return api_response(400, {"error": "from must be YYYY-MM-DD"})
    if not _DATE_RE.match(date_to):
        return api_response(400, {"error": "to must be YYYY-MM-DD"})

    # Validate range
    from_dt = datetime.strptime(date_from, "%Y-%m-%d")
    to_dt = datetime.strptime(date_to, "%Y-%m-%d")
    if (to_dt - from_dt).days > _MAX_RANGE_DAYS:
        return api_response(400, {"error": f"Date range cannot exceed {_MAX_RANGE_DAYS} days"})
    if to_dt < from_dt:
        return api_response(400, {"error": "to must be after from"})

    # Export sessions
    sessions_sql = (
        f"SELECT session_id, plan_id, plan_day_number, date, status, "
        f"total_sets, exercise_count, session_total_load, weight_prs, e1rm_prs, "
        f"duration_minutes "
        f"FROM {ATHENA_GOLD_DATABASE}.fact_sessions "
        f"WHERE date >= '{date_from}' AND date <= '{date_to}' "
        f"ORDER BY date ASC"
    )

    # Export sets with exercise names
    sets_sql = (
        f"SELECT fs.set_id, fs.session_id, fs.exercise_id, de.name AS exercise_name, "
        f"fs.weight_kg, fs.reps, fs.rir, fs.set_type, "
        f"fs.is_weight_pr, fs.is_e1rm_pr, fs.estimated_1rm, fs.total_load, "
        f"fs.timestamp "
        f"FROM {ATHENA_GOLD_DATABASE}.fact_sets fs "
        f"JOIN {ATHENA_GOLD_DATABASE}.dim_exercises de ON fs.exercise_id = de.exercise_id "
        f"JOIN {ATHENA_GOLD_DATABASE}.fact_sessions sess ON fs.session_id = sess.session_id "
        f"WHERE sess.date >= '{date_from}' AND sess.date <= '{date_to}' "
        f"ORDER BY fs.timestamp ASC"
    )

    try:
        sessions = run_athena_query(sessions_sql)
        sets = run_athena_query(sets_sql)
    except AthenaQueryError as e:
        return api_response(500, {"error": f"Export failed: {e}"})

    return api_response(200, {
        "export": {
            "from": date_from,
            "to": date_to,
            "sessions": sessions,
            "sets": sets,
        }
    })
