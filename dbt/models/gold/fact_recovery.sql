{{
    config(
        materialized='table',
        partitioned_by=['year', 'month']
    )
}}

select
    r.recovery_id,
    r.date,
    r.recovery_score,
    r.hrv_rmssd,
    r.resting_heart_rate,
    r.spo2,
    r.skin_temp_celsius,
    sl.total_sleep_minutes,
    sl.sleep_efficiency,
    cast(year(cast(r.date as date)) as varchar) as year,
    lpad(cast(month(cast(r.date as date)) as varchar), 2, '0') as month
from {{ ref('stg_recovery') }} r
left join {{ ref('stg_sleep') }} sl
    on r.date = sl.date
