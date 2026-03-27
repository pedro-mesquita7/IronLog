select
    equipment_id,
    name,
    equipment_type,
    weight_kg,
    quantity,
    is_archived,
    created_at,
    updated_at
from {{ ref('stg_equipment') }}
where is_archived = false
