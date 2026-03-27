with ranked as (
    select
        *,
        row_number() over (
            partition by regexp_extract(sk, 'CORR#(.+)', 1)
            order by _cdc_timestamp desc, _cdc_sequence_number desc
        ) as _row_num
    from {{ source('bronze', 'bronze_corrections') }}
    where _cdc_event_name != 'REMOVE'
)

select
    regexp_extract(sk, 'CORR#(.+)', 1) as correction_id,
    regexp_extract(pk, 'CORR#(.+)', 1) as set_id,
    session_id,
    field,
    old_value,
    new_value,
    reason,
    created_at
from ranked
where _row_num = 1
