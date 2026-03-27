{{
    config(
        materialized='table',
        partitioned_by=['year', 'month']
    )
}}

select
    s.session_id,
    s.plan_id,
    s.plan_day_number,
    s.date,
    s.status,
    s.started_at,
    s.completed_at,
    s.notes,
    count(fs.set_id) as total_sets,
    count(distinct fs.exercise_id) as exercise_count,
    coalesce(sum(fs.total_load), 0) as session_total_load,
    coalesce(sum(case when fs.is_weight_pr then 1 else 0 end), 0) as weight_prs,
    coalesce(sum(case when fs.is_e1rm_pr then 1 else 0 end), 0) as e1rm_prs,
    date_diff(
        'minute',
        from_iso8601_timestamp(s.started_at),
        from_iso8601_timestamp(s.completed_at)
    ) as duration_minutes,
    cast(year(cast(s.date as date)) as varchar) as year,
    lpad(cast(month(cast(s.date as date)) as varchar), 2, '0') as month
from {{ ref('stg_sessions') }} s
left join {{ ref('fact_sets') }} fs
    on s.session_id = fs.session_id
where s.status = 'completed'
group by
    s.session_id, s.plan_id, s.plan_day_number, s.date,
    s.status, s.started_at, s.completed_at, s.notes
