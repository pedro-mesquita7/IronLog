import uuid
from datetime import datetime, timezone
from decimal import Decimal

from boto3.dynamodb.conditions import Key

from shared.auth_middleware import require_auth
from shared.constants import GSI1_INDEX
from shared.dynamo import get_table
from shared.response import api_response, options_response

# --- Seed data constants ---

EQUIPMENT = [
    {"name": "Olympic Barbell (BB)", "equipment_type": "bar", "weight_kg": Decimal("20")},
    {"name": "Olympic Bar 15kg", "equipment_type": "bar", "weight_kg": Decimal("15")},
    {"name": "EZ Curl Bar", "equipment_type": "bar", "weight_kg": Decimal("10")},
    {"name": "Plate 2.5kg", "equipment_type": "plate", "weight_kg": Decimal("2.5"), "quantity": 10},
    {"name": "Plate 5kg", "equipment_type": "plate", "weight_kg": Decimal("5"), "quantity": 10},
    {"name": "Plate 10kg", "equipment_type": "plate", "weight_kg": Decimal("10"), "quantity": 10},
    {"name": "Plate 15kg", "equipment_type": "plate", "weight_kg": Decimal("15"), "quantity": 10},
    {"name": "Plate 20kg", "equipment_type": "plate", "weight_kg": Decimal("20"), "quantity": 10},
]

# Exercise definitions: name, muscle_group, bar_name (or None), has_plate_calculator,
# is_unilateral, weak_side, rest_timer_seconds, replacement_names (list)
EXERCISES = [
    ("DB Incline Chest Press", "chest", None, False, True, None, 180, []),
    ("Weighted Pull Up", "back", None, False, False, None, 180, []),
    ("Weighted Dips", "chest", None, False, False, None, 180, []),
    ("T-Bar Row", "back", None, False, False, None, 180, []),
    ("Lateral Raise Pulley", "shoulders", None, False, True, None, 120, ["Lateral Raise DB"]),
    ("Tricep Pushdown Pulley Uni", "arms", None, False, True, None, 120, ["Tricep Bar Pushdown Pulley"]),
    ("Deadlift", "back", "Olympic Barbell (BB)", True, False, None, 180, []),
    ("Zercher Squat", "legs", "Olympic Barbell (BB)", True, False, None, 180, []),
    ("Leg Press 45", "legs", None, False, False, None, 180, []),
    ("Laying Leg Curl", "legs", None, False, False, None, 120, ["Seated Leg Curl"]),
    ("Adductor Machine", "legs", None, False, False, None, 120, []),
    ("Barbell OHP", "shoulders", "Olympic Barbell (BB)", True, False, None, 180, []),
    ("Strict Row BB", "back", "Olympic Barbell (BB)", True, False, None, 180, []),
    ("DB Chest Press", "chest", None, False, True, None, 180, []),
    ("Lat Pulldown", "back", None, False, False, None, 120, []),
    ("Rear Delt Fly Machine", "shoulders", None, False, False, None, 120, ["Rear Delt Pulley Uni"]),
    ("Bicep Curl EZ Bar", "arms", "EZ Curl Bar", True, False, None, 120, []),
    ("Hack Squat", "legs", None, False, False, None, 180, []),
    ("Hip Thrust Machine", "legs", None, False, False, None, 180, []),
    ("Walking Lunges DB", "legs", None, False, True, None, 120, []),
    ("Leg Extension Uni Machine", "legs", None, False, True, None, 120, []),
    ("Seated Leg Curl", "legs", None, False, False, None, 120, ["Laying Leg Curl"]),
    ("Lateral Raise DB", "shoulders", None, False, True, None, 120, ["Lateral Raise Pulley"]),
    ("Tricep Bar Pushdown Pulley", "arms", None, False, False, None, 120, ["Tricep Pushdown Pulley Uni"]),
    ("Rear Delt Pulley Uni", "shoulders", None, False, True, None, 120, ["Rear Delt Fly Machine"]),
]

# Plan: Upper Lower 4x
# Each tuple: (day_number, day_name, [(exercise_name, target_sets, target_reps, set_type), ...])
PLAN_DAYS = [
    (1, "Upper A", [
        ("DB Incline Chest Press", 2, "4-6", "working"),
        ("Weighted Pull Up", 2, "3-5", "working"),
        ("Weighted Dips", 2, "4-6", "working"),
        ("T-Bar Row", 2, "5-8", "working"),
        ("Lateral Raise Pulley", 2, "10-12", "working"),
        ("Tricep Pushdown Pulley Uni", 2, "8-12", "working"),
    ]),
    (2, "Lower A", [
        ("Deadlift", 2, "3-5", "working"),
        ("Zercher Squat", 2, "3-5", "working"),
        ("Leg Press 45", 2, "6-8", "working"),
        ("Laying Leg Curl", 2, "8-12", "working"),
        ("Adductor Machine", 2, "8-12", "working"),
    ]),
    (3, "Upper B", [
        ("Barbell OHP", 2, "4-8", "working"),
        ("Strict Row BB", 2, "4-8", "working"),
        ("DB Chest Press", 2, "4-8", "working"),
        ("Lat Pulldown", 2, "6-10", "working"),
        ("Rear Delt Fly Machine", 2, "8-12", "working"),
        ("Bicep Curl EZ Bar", 2, "4-8", "working"),
    ]),
    (4, "Lower B", [
        ("Hack Squat", 2, "4-6", "working"),
        ("Hip Thrust Machine", 2, "5-8", "working"),
        ("Walking Lunges DB", 2, "8-12", "working"),
        ("Leg Extension Uni Machine", 2, "5-8", "working"),
        ("Seated Leg Curl", 2, "5-8", "working"),
    ]),
]


@require_auth
def handler(event, context):
    if event.get("httpMethod") == "OPTIONS":
        return options_response()

    method = event["httpMethod"]
    resource = event.get("resource", "")

    if resource == "/api/seed" and method == "POST":
        return _seed()

    return api_response(405, {"error": "Method not allowed"})


def _seed():
    table = get_table()

    # Idempotency check: if equipment already exists, skip
    existing = table.query(
        IndexName=GSI1_INDEX,
        KeyConditionExpression=Key("GSI1PK").eq("EQUIPMENT"),
        Limit=1,
    )
    if existing["Items"]:
        return api_response(200, {"seeded": False, "message": "Data already exists"})

    now = datetime.now(timezone.utc).isoformat()

    # --- Equipment ---
    equipment_items = []
    equipment_name_to_id = {}
    for eq in EQUIPMENT:
        eq_id = str(uuid.uuid4())
        equipment_name_to_id[eq["name"]] = eq_id
        item = {
            "PK": f"EQ#{eq_id}",
            "SK": f"EQ#{eq_id}",
            "GSI1PK": "EQUIPMENT",
            "GSI1SK": f"EQ#{eq_id}",
            "equipment_id": eq_id,
            "name": eq["name"],
            "equipment_type": eq["equipment_type"],
            "weight_kg": eq["weight_kg"],
            "is_archived": False,
            "created_at": now,
            "updated_at": now,
        }
        if "quantity" in eq:
            item["quantity"] = eq["quantity"]
        equipment_items.append(item)

    # --- Exercises (first pass: create all, resolve bar IDs) ---
    exercise_items = []
    exercise_name_to_id = {}
    exercise_name_to_replacements = {}

    for (name, muscle_group, bar_name, has_plate_calc,
         is_uni, weak_side, rest_timer, replacement_names) in EXERCISES:
        ex_id = str(uuid.uuid4())
        exercise_name_to_id[name] = ex_id
        exercise_name_to_replacements[name] = replacement_names

        item = {
            "PK": f"EX#{ex_id}",
            "SK": f"EX#{ex_id}",
            "GSI1PK": "EXERCISES",
            "GSI1SK": f"EX#{ex_id}",
            "exercise_id": ex_id,
            "name": name,
            "muscle_group": muscle_group,
            "has_plate_calculator": has_plate_calc,
            "is_unilateral": is_uni,
            "weak_side": weak_side,
            "rest_timer_seconds": rest_timer,
            "replacement_exercise_ids": [],
            "is_archived": False,
            "created_at": now,
            "updated_at": now,
        }
        if bar_name:
            item["default_bar_id"] = equipment_name_to_id[bar_name]
        exercise_items.append(item)

    # Resolve replacement exercise IDs
    for item in exercise_items:
        name = item["name"]
        replacement_names = exercise_name_to_replacements[name]
        if replacement_names:
            item["replacement_exercise_ids"] = [
                exercise_name_to_id[rn] for rn in replacement_names
            ]

    # --- Plan ---
    plan_id = str(uuid.uuid4())
    plan_meta = {
        "PK": f"PLAN#{plan_id}",
        "SK": "META",
        "GSI1PK": "ACTIVE_PLAN",
        "GSI1SK": f"PLAN#{plan_id}",
        "plan_id": plan_id,
        "name": "Upper Lower 4x",
        "split_type": "Upper/Lower",
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }

    plan_day_items = []
    for day_num, day_name, exercises in PLAN_DAYS:
        day_exercises = []
        for order, (ex_name, target_sets, target_reps, set_type) in enumerate(exercises, start=1):
            day_exercises.append({
                "exercise_id": exercise_name_to_id[ex_name],
                "order": order,
                "target_sets": target_sets,
                "target_reps": target_reps,
                "set_type": set_type,
            })
        plan_day_items.append({
            "PK": f"PLAN#{plan_id}",
            "SK": f"DAY#{day_num:02d}",
            "day_number": day_num,
            "day_name": day_name,
            "exercises": day_exercises,
        })

    # --- Batch write everything ---
    with table.batch_writer() as batch:
        for item in equipment_items:
            batch.put_item(Item=item)
        for item in exercise_items:
            batch.put_item(Item=item)
        batch.put_item(Item=plan_meta)
        for item in plan_day_items:
            batch.put_item(Item=item)

    return api_response(201, {
        "seeded": True,
        "equipment_count": len(equipment_items),
        "exercise_count": len(exercise_items),
        "plan_id": plan_id,
        "message": "Seed data created successfully",
    })
