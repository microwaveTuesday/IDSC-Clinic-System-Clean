# ADR 0005: Maintain a Canonical OpenAPI Contract, Health Route, and Swagger Route

## Status

Accepted

## Context

The midterm requires an OpenAPI contract and running Swagger UI.

Earlier repository states contained route/documentation inconsistencies, including health-route shape and Swagger location differences.

The integration baseline requires:

- canonical health endpoint `/api/v1/health`;
- exact health response `{ "status": "ok" }`;
- Swagger UI at `/docs`;
- OpenAPI metadata that matches runtime authentication semantics;
- validation with drf-spectacular and Redocly.

The runtime retains selected backward-compatible aliases, but the generated OpenAPI contract must have one canonical operation for each API action.

## Decision

The Clinic backend will maintain the following canonical contract:

- Business API namespace: `/api/v1/`
- Health endpoint: `GET /api/v1/health`
- Health response: exactly `{ "status": "ok" }`
- Dynamic schema endpoint: `/api/schema/`
- Canonical Swagger UI: `/docs`
- Root static contract: `openapi.yaml`
- OpenAPI version: 3.1
- Public operations explicitly use `security: []`
- Protected operations require the session-cookie security scheme

A trailing-slash health runtime alias may remain for compatibility, but it must be excluded from schema generation so the OpenAPI operation inventory is not duplicated.

The older Swagger route may remain as a backward-compatible alias, but `/docs` is the canonical documented UI route.

## Rationale

A single canonical contract prevents frontend/backend ambiguity and makes automated validation possible.

Explicit public/protected security metadata avoids misleading generated documentation.

Keeping aliases out of the canonical operation inventory preserves compatibility without weakening contract clarity.

## Consequences

### Positive

- Swagger and generated schema match the expected rubric.
- Static and dynamic contracts can be compared automatically.
- Public operations are explicit.
- Protected operations remain visible as authenticated.
- Backward-compatible runtime aliases can exist without duplicating canonical API operations.

### Trade-offs

- Schema postprocessing must remain synchronized with routes and operation metadata.
- New endpoints require explicit summaries/security consistency.
- Static `openapi.yaml` must be regenerated or synchronized when API operations change.

## Implementation Evidence

Relevant source:

- `backend/config/urls.py`
- `backend/clinic/urls.py`
- `backend/clinic/views.py`
- `backend/config/schema.py`
- `backend/config/settings.py`
- `openapi.yaml`
- `redocly.yaml`

Verified behavior includes:

- `/docs` and `/docs/` Swagger routes;
- `/api/schema/` dynamic schema route;
- canonical `/api/v1/health`;
- exact health response;
- canonical public-operation normalization;
- 45 static and 45 dynamic operations with parity;
- 3 public and 42 protected operations;
- static and dynamic Redocly validation passing.

## Invariants

1. `/api/v1/health` must keep the exact required response.
2. `/docs` remains the canonical Swagger route.
3. Public operations must be explicit in OpenAPI.
4. Protected operations must not become anonymously documented.
5. Static and dynamic operation inventories must remain synchronized.
6. Redocly validation must pass before final merge.

## Related Documentation

- `openapi.yaml`
- `redocly.yaml`
- `docs/TEST-EVIDENCE.md`
- `docs/architecture.md`
