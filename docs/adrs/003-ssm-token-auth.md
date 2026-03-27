# ADR 003: SSM Parameter Store Token Auth

## Status
Accepted

## Context
IronLog is single-tenant (one user). Full auth systems (Cognito, Auth0) are overkill. A simple shared secret with JWT sessions is sufficient.

## Decision
Terraform generates a random 64-character token stored in SSM Parameter Store (SecureString). The user pastes this token to login; the Lambda validates it and issues a 24-hour JWT signed with a separate SSM-stored secret. All handlers validate the JWT via a shared `@require_auth` decorator.

## Consequences
- **Positive**: Minimal auth surface, no user management, no external auth provider costs
- **Positive**: JWT enables stateless validation with no SSM call per request (after initial param caching)
- **Negative**: Token rotation requires `terraform apply` and re-login
- **Negative**: Not suitable for multi-user — acceptable given single-tenant scope
