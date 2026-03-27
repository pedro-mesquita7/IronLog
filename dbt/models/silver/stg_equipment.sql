with ranked as (
    select
        *,
        row_number() over (
            partition by regexp_extract(pk, 'EQ#(.+)', 1)
            order by _cdc_timestamp desc, _cdc_sequence_number desc
        ) as _row_num
    from {{ source('bronze', 'bronze_equipment') }}
    where _cdc_event_name != 'REMOVE'
)

select
    regexp_extract(pk, 'EQ#(.+)', 1) as equipment_id,
    name,
    equipment_type,
    cast(weight_kg as double) as weight_kg,
    cast(quantity as integer) as quantity,
    settings_schema,
    cast(is_archived as boolean) as is_archived,
    created_at,
    updated_at
from ranked
where _row_num = 1
