with ranked as (
    select
        *,
        row_number() over (
            partition by id
            order by _sync_timestamp desc
        ) as _row_num
    from {{ source('bronze', 'bronze_sleep') }}
    where score_state = 'SCORED'
      and nap = false
)

select
    id as sleep_id,
    cast(substr("start", 1, 10) as varchar) as date,
    cast(score.stage_summary.total_in_bed_time_milli / 60000 as integer)
        - cast(score.stage_summary.total_awake_time_milli / 60000 as integer) as total_sleep_minutes,
    cast(score.stage_summary.total_rem_sleep_time_milli / 60000 as integer) as rem_sleep_minutes,
    cast(score.stage_summary.total_slow_wave_sleep_time_milli / 60000 as integer) as deep_sleep_minutes,
    cast(score.stage_summary.total_light_sleep_time_milli / 60000 as integer) as light_sleep_minutes,
    cast(score.stage_summary.total_awake_time_milli / 60000 as integer) as awake_minutes,
    score.sleep_efficiency_percentage / 100.0 as sleep_efficiency,
    score.respiratory_rate as respiratory_rate,
    created_at
from ranked
where _row_num = 1
