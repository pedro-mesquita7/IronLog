# ADR 007: Intentional Over-Engineering for Portfolio

## Status
Accepted

## Context
IronLog could be built as a simple full-stack app with a single database. Instead, it is intentionally over-engineered to serve as a data engineering portfolio project.

## Decision
Adopt a production-grade architecture with: CDC pipeline (DynamoDB Streams → Lambda → S3), medallion data lake (Bronze/Silver/Gold), dbt transformations, Athena analytics, external API integration (WHOOP), Terraform IaC, CI/CD with GitHub Actions, and CloudWatch monitoring — all for a single-user gym tracker.

## Consequences
- **Positive**: Demonstrates cloud-native data engineering skills (AWS, IaC, ELT, medallion architecture)
- **Positive**: Each component represents a real-world pattern recruiters and hiring managers look for
- **Positive**: Running cost remains ~€0–2/month thanks to serverless and pay-per-use pricing
- **Negative**: Complexity far exceeds what the use case requires
- **Neutral**: This trade-off is the explicit goal — the project exists to demonstrate skills, not minimize code
