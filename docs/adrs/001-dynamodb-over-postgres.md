# ADR 001: DynamoDB Over PostgreSQL

## Status
Accepted

## Context
IronLog needs an operational database for real-time CRUD. The choice was between PostgreSQL (RDS) and DynamoDB. Key factors: single-tenant app, simple access patterns, and AWS-native portfolio goals.

## Decision
Use DynamoDB with single-table design and one GSI. PAY_PER_REQUEST billing eliminates idle costs. DynamoDB Streams enables the CDC pipeline to S3 without additional infrastructure.

## Consequences
- **Positive**: Zero idle cost (pay-per-request), no connection management, built-in Streams for CDC
- **Positive**: Demonstrates NoSQL single-table design pattern for portfolio
- **Negative**: Complex access patterns require careful key design (mitigated by single GSI)
- **Negative**: No ad-hoc SQL queries on operational data (mitigated by Athena on Gold layer)
