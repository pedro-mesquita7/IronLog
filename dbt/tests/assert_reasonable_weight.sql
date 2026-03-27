-- Verify all set weights are within reasonable bounds (0-500kg)
select set_id
from {{ ref('fact_sets') }}
where weight_kg < 0 or weight_kg > 500
