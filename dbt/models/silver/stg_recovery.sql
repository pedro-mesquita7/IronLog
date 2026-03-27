with ranked as (
    select
        *,
        row_number() over (
            partition by cycle_id
            order by _sync_timestamp desc
        ) as _row_num
    from {{ source('bronze', 'bronze_recovery') }}
    where score_state = 'SCORED'
)

select
    cast(cycle_id as varchar) as recovery_id,
    cast(substr(created_at, 1, 10) as varchar) as date,
    score.recovery_score as recovery_score,
    score.hrv_rmssd_milli as hrv_rmssd,
    score.resting_heart_rate as resting_heart_rate,
    score.spo2_percentage as spo2,
    score.skin_temp_celsius as skin_temp_celsius,
    created_at
from ranked
where _row_num = 1
