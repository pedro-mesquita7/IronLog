with ranked as (
    select
        *,
        row_number() over (
            partition by regexp_extract(pk, 'EX#(.+)', 1)
            order by _cdc_timestamp desc, _cdc_sequence_number desc
        ) as _row_num
    from {{ source('bronze', 'bronze_exercises') }}
    where _cdc_event_name != 'REMOVE'
)

select
    regexp_extract(pk, 'EX#(.+)', 1) as exercise_id,
    name,
    muscle_group,
    default_bar_id,
    cast(has_plate_calculator as boolean) as has_plate_calculator,
    cast(is_unilateral as boolean) as is_unilateral,
    weak_side,
    cast(rest_timer_seconds as integer) as rest_timer_seconds,
    machine_settings,
    replacement_exercise_ids,
    notes,
    cast(is_archived as boolean) as is_archived,
    created_at,
    updated_at
from ranked
where _row_num = 1
