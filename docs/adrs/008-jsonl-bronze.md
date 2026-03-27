# ADR 008: JSON Lines for Bronze Layer Instead of Parquet

## Status
Accepted

## Context
The original spec called for Parquet files in the S3 Bronze layer, written by the CDC Lambda. However, pyarrow (the standard Python Parquet library) is approximately 200MB unpacked, which exceeds practical Lambda layer limits (250MB total including runtime). Options considered:

1. **JSON Lines** — zero extra dependencies, stdlib `json` module + `gzip`
2. **awswrangler Lambda layer** — AWS-managed layer with pyarrow, but ~260MB and adds cold start latency
3. **Custom slim pyarrow build** — fragile across Python versions, maintenance burden

## Decision
Use gzip-compressed JSON Lines (`.jsonl.gz`) for Bronze layer files. Athena reads JSON natively via `org.openx.data.jsonserde.JsonSerDe`. The Silver and Gold layers are materialized as Parquet via `dbt-athena-community`, so the analytics layer remains columnar and performant.

## Consequences
- **Positive**: Zero additional Lambda dependencies, faster cold starts, simpler deployment
- **Positive**: Athena reads JSON with no conversion step needed
- **Negative**: Slightly larger storage footprint in Bronze vs Parquet (mitigated by gzip compression)
- **Negative**: Slightly slower Athena scans on Bronze (acceptable — Bronze is only read by dbt, not ad-hoc queries)
- **Neutral**: The portfolio signal for columnar/efficient storage comes from Silver/Gold Parquet layers
