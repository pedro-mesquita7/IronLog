with ranked as (
    select
        *,
        row_number() over (
            partition by regexp_extract(pk, 'SESSION#(.+)', 1)
            order by _cdc_timestamp desc, _cdc_sequence_number desc
        ) as _row_num
    from {{ source('bronze', 'bronze_sessions') }}
    where _cdc_event_name != 'REMOVE'
)

select
    regexp_extract(pk, 'SESSION#(.+)', 1) as session_id,
    plan_id,
    cast(plan_day_number as integer) as plan_day_number,
    date,
    status,
    started_at,
    completed_at,
    notes,
    created_at
from ranked
where _row_num = 1
