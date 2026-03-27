{{
    config(
        materialized='table',
        partitioned_by=['year', 'month']
    )
}}

with latest_weight_correction as (
    select
        set_id,
        cast(new_value as double) as corrected_weight_kg,
        row_number() over (partition by set_id order by created_at desc) as rn
    from {{ ref('stg_corrections') }}
    where field = 'weight_kg'
),

latest_reps_correction as (
    select
        set_id,
        cast(new_value as integer) as corrected_reps,
        row_number() over (partition by set_id order by created_at desc) as rn
    from {{ ref('stg_corrections') }}
    where field = 'reps'
),

latest_rir_correction as (
    select
        set_id,
        cast(new_value as integer) as corrected_rir,
        row_number() over (partition by set_id order by created_at desc) as rn
    from {{ ref('stg_corrections') }}
    where field = 'rir'
)

select
    s.set_id,
    s.session_id,
    s.exercise_id,
    s.original_exercise_id,
    s.set_type,
    s.set_order,
    coalesce(cw.corrected_weight_kg, s.weight_kg) as weight_kg,
    coalesce(cr.corrected_reps, s.reps) as reps,
    coalesce(ci.corrected_rir, s.rir) as rir,
    s.is_weight_pr,
    s.is_e1rm_pr,
    s.estimated_1rm,
    s.timestamp,
    coalesce(cw.corrected_weight_kg, s.weight_kg)
        * cast(coalesce(cr.corrected_reps, s.reps) as double) as total_load,
    cast(year(from_iso8601_timestamp(s.timestamp)) as varchar) as year,
    lpad(cast(month(from_iso8601_timestamp(s.timestamp)) as varchar), 2, '0') as month
from {{ ref('stg_sets') }} s
left join latest_weight_correction cw
    on s.set_id = cw.set_id and cw.rn = 1
left join latest_reps_correction cr
    on s.set_id = cr.set_id and cr.rn = 1
left join latest_rir_correction ci
    on s.set_id = ci.set_id and ci.rn = 1
