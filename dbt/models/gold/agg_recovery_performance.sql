{{
    config(
        materialized='table',
        partitioned_by=['year', 'month']
    )
}}

select
    fs.date,
    fr.recovery_score,
    fr.hrv_rmssd,
    fr.resting_heart_rate,
    fs.session_total_load,
    fs.total_sets,
    fs.weight_prs,
    fs.duration_minutes,
    cast(year(cast(fs.date as date)) as varchar) as year,
    lpad(cast(month(cast(fs.date as date)) as varchar), 2, '0') as month
from {{ ref('fact_sessions') }} fs
inner join {{ ref('fact_recovery') }} fr
    on fs.date = fr.date
