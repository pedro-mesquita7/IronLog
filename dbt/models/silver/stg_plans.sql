with ranked as (
    select
        *,
        row_number() over (
            partition by regexp_extract(pk, 'PLAN#(.+)', 1)
            order by _cdc_timestamp desc, _cdc_sequence_number desc
        ) as _row_num
    from {{ source('bronze', 'bronze_plans') }}
    where _cdc_event_name != 'REMOVE'
)

select
    regexp_extract(pk, 'PLAN#(.+)', 1) as plan_id,
    name,
    split_type,
    cast(is_active as boolean) as is_active,
    created_at,
    updated_at
from ranked
where _row_num = 1
