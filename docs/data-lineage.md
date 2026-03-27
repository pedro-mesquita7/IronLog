# Data Lineage

## Overview

IronLog uses a **medallion architecture** (Bronze → Silver → Gold) with two data sources: DynamoDB (via CDC) and the WHOOP API.

```mermaid
graph LR
    subgraph "Sources"
        DDB[DynamoDB<br/>Streams]
        WHOOP[WHOOP API v2]
    end

    subgraph "Bronze (Raw)"
        B_EQ[bronze_equipment]
        B_EX[bronze_exercises]
        B_SESS[bronze_sessions]
        B_SETS[bronze_sets]
        B_PLANS[bronze_plans]
        B_DAYS[bronze_plan_days]
        B_CORR[bronze_corrections]
        B_NOTES[bronze_session_exercise_notes]
        B_REC[bronze_recovery]
        B_SLEEP[bronze_sleep]
    end

    subgraph "Silver (Staged)"
        S_EQ[stg_equipment]
        S_EX[stg_exercises]
        S_SESS[stg_sessions]
        S_SETS[stg_sets]
        S_PLANS[stg_plans]
        S_CORR[stg_corrections]
        S_REC[stg_recovery]
        S_SLEEP[stg_sleep]
    end

    subgraph "Gold (Analytics)"
        F_SETS[fact_sets]
        F_SESS[fact_sessions]
        F_REC[fact_recovery]
        D_EX[dim_exercises]
        D_EQ[dim_equipment]
        D_PL[dim_plans]
        A_PROG[agg_exercise_progression]
        A_RECPERF[agg_recovery_performance]
    end

    subgraph "Consumers"
        API[Analytics API]
        EXPORT[Export API]
    end

    DDB -->|CDC Lambda| B_EQ & B_EX & B_SESS & B_SETS & B_PLANS & B_DAYS & B_CORR & B_NOTES
    WHOOP -->|Sync Lambda| B_REC & B_SLEEP

    B_EQ -->|dbt| S_EQ
    B_EX -->|dbt| S_EX
    B_SESS -->|dbt| S_SESS
    B_SETS -->|dbt| S_SETS
    B_PLANS -->|dbt| S_PLANS
    B_CORR -->|dbt| S_CORR
    B_REC -->|dbt| S_REC
    B_SLEEP -->|dbt| S_SLEEP

    S_SETS & S_CORR -->|dbt| F_SETS
    S_SESS -->|dbt| F_SESS
    S_REC & S_SLEEP -->|dbt| F_REC
    S_EX -->|dbt| D_EX
    S_EQ -->|dbt| D_EQ
    S_PLANS -->|dbt| D_PL
    F_SETS & D_EX -->|dbt| A_PROG
    F_SESS & F_REC -->|dbt| A_RECPERF

    A_PROG & A_RECPERF & F_SETS & D_EX -->|Athena| API
    F_SETS & F_SESS & D_EX -->|Athena| EXPORT
```

## Layer Details

### Bronze (Raw Ingestion)

| Source | Target | Format | Trigger |
|---|---|---|---|
| DynamoDB Streams | `bronze/<entity>/year=YYYY/month=MM/day=DD/` | JSON Lines (.jsonl.gz) | CDC Lambda (real-time) |
| WHOOP API v2 | `bronze/recovery/`, `bronze/sleep/` | JSON Lines (.jsonl.gz) | EventBridge (daily 06:00 UTC) |

Each CDC record includes: `_cdc_event_name`, `_cdc_timestamp`, `_cdc_sequence_number`.

### Silver (Staged & Deduplicated)

dbt models with `ROW_NUMBER() OVER (PARTITION BY <id> ORDER BY cdc_timestamp DESC) = 1` deduplication. Materialized as Parquet external tables on S3.

### Gold (Analytics-Ready)

| Model | Description | Partitioning |
|---|---|---|
| `fact_sets` | Sets with corrections applied, total_load computed | year/month |
| `fact_sessions` | Sessions with aggregated metrics (sets, load, PRs, duration) | year/month |
| `fact_recovery` | WHOOP recovery enriched with sleep data | year/month |
| `dim_exercises` | Active exercise definitions | year/month |
| `dim_equipment` | Active equipment inventory | year/month |
| `dim_plans` | Training plan definitions | year/month |
| `agg_exercise_progression` | Weekly exercise metrics (weight, volume, PRs) | year/month |
| `agg_recovery_performance` | Recovery score vs training performance join | year/month |

## Data Quality

Silver layer: `not_null` (PKs, timestamps), `unique` (IDs), `accepted_values` (enums).
Gold layer: `not_null` (PKs), `unique` (facts), `relationships` (fact → dim), custom tests (e1RM > 0, volume >= 0).
