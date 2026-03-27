-- Verify all sets have non-negative total load
select set_id
from {{ ref('fact_sets') }}
where total_load < 0
