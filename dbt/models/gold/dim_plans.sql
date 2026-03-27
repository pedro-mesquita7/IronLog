select
    plan_id,
    name,
    split_type,
    is_active,
    created_at,
    updated_at
from {{ ref('stg_plans') }}
