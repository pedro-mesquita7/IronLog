select
    exercise_id,
    name,
    muscle_group,
    has_plate_calculator,
    is_unilateral,
    weak_side,
    rest_timer_seconds,
    default_bar_id,
    is_archived,
    created_at,
    updated_at
from {{ ref('stg_exercises') }}
where is_archived = false
