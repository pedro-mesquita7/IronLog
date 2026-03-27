# ADR 002: Pure Data Lake Over Lakehouse

## Status
Accepted

## Context
Data from DynamoDB (via CDC) and WHOOP API needs to be stored for analytics. Options: lakehouse (Delta Lake/Iceberg on S3) vs pure data lake (raw files on S3 with Glue Catalog + Athena).

## Decision
Use a pure S3 data lake with Bronze/Silver/Gold medallion layers. Bronze holds raw CDC JSON Lines, Silver and Gold hold dbt-materialized Parquet. Athena provides SQL access via Glue Catalog metadata.

## Consequences
- **Positive**: No Spark infrastructure, no EMR/Glue ETL costs, serverless-only
- **Positive**: dbt-athena handles the Silver/Gold transforms at near-zero cost
- **Negative**: No ACID transactions on the lake (acceptable for single-user, append-mostly workload)
- **Negative**: No time-travel or schema evolution features (not needed at this scale)
