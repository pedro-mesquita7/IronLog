{{
    config(
        materialized='table',
        partitioned_by=['year', 'month']
    )
}}

select
    fs.exercise_id,
    de.name as exercise_name,
    de.muscle_group,
    date_trunc('week', cast(sess.date as date)) as week_start,
    count(fs.set_id) as total_sets,
    max(fs.weight_kg) as max_weight_kg,
    avg(fs.weight_kg) as avg_weight_kg,
    sum(fs.total_load) as weekly_total_load,
    max(fs.estimated_1rm) as max_estimated_1rm,
    sum(case when fs.is_weight_pr then 1 else 0 end) as weight_prs,
    sum(case when fs.is_e1rm_pr then 1 else 0 end) as e1rm_prs,
    cast(year(date_trunc('week', cast(sess.date as date))) as varchar) as year,
    lpad(cast(month(date_trunc('week', cast(sess.date as date))) as varchar), 2, '0') as month
from {{ ref('fact_sets') }} fs
join {{ ref('stg_sessions') }} sess
    on fs.session_id = sess.session_id
join {{ ref('dim_exercises') }} de
    on fs.exercise_id = de.exercise_id
where fs.set_type in ('working', 'backoff')
group by
    fs.exercise_id, de.name, de.muscle_group,
    date_trunc('week', cast(sess.date as date))
