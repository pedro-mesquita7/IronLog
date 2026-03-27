# ADR 005: Raw Python Lambda Handlers

## Status
Accepted

## Context
API handlers need a runtime. Options: Python with a framework (Flask/FastAPI via Mangum), raw Python event handlers, or Node.js.

## Decision
Use raw Python Lambda handlers (no framework). Each Lambda receives the API Gateway proxy event directly and dispatches on `httpMethod` and `resource`. Shared utilities (auth, response, DynamoDB, S3) are in a `shared/` module deployed with every function.

## Consequences
- **Positive**: Minimal cold start, zero framework dependencies (only PyJWT as external dep)
- **Positive**: Single zip package for all handlers, simple deployment
- **Negative**: Manual routing dispatch (switch on resource/method) instead of decorator-based routing
- **Negative**: No built-in request validation or OpenAPI schema generation (acceptable for single-tenant)
