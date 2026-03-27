with ranked as (
    select
        *,
        row_number() over (
            partition by regexp_extract(sk, 'SET#\d+#(.+)', 1)
            order by _cdc_timestamp desc, _cdc_sequence_number desc
        ) as _row_num
    from {{ source('bronze', 'bronze_sets') }}
    where _cdc_event_name != 'REMOVE'
)

select
    regexp_extract(sk, 'SET#\d+#(.+)', 1) as set_id,
    regexp_extract(pk, 'SESSION#(.+)', 1) as session_id,
    exercise_id,
    original_exercise_id,
    set_type,
    cast(set_order as integer) as set_order,
    cast(weight_kg as double) as weight_kg,
    cast(reps as integer) as reps,
    cast(rir as integer) as rir,
    cast(is_weight_pr as boolean) as is_weight_pr,
    cast(is_e1rm_pr as boolean) as is_e1rm_pr,
    cast(estimated_1rm as double) as estimated_1rm,
    timestamp
from ranked
where _row_num = 1
