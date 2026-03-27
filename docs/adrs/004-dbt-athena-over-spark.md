# ADR 004: dbt + Athena Over Spark

## Status
Accepted

## Context
Bronze-to-Silver-to-Gold transformations need an ELT engine. Options: AWS Glue (Spark), dbt-core + dbt-athena-community, or custom Lambda ETL.

## Decision
Use dbt-core with dbt-athena-community adapter. Models are materialized as external Hive tables (Parquet on S3) via Athena CREATE TABLE AS SELECT. Silver deduplicates CDC events; Gold builds fact/dim/aggregate tables partitioned by year/month.

## Consequences
- **Positive**: SQL-only transforms, version-controlled models, built-in testing and documentation
- **Positive**: Athena serverless pricing (~$5/TB scanned), no cluster management
- **Positive**: Strong portfolio signal for modern data stack (dbt is industry standard)
- **Negative**: Athena materializations are full table refreshes (no incremental merge), acceptable at low volume
- **Negative**: dbt-athena-community is a third-party adapter with occasional version lag
