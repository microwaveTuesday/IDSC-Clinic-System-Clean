# ADR 0003: Enforce Routes to Services to Data Layering

## Status

Accepted

## Context

The Clinic backend needs a structure that keeps HTTP concerns, business orchestration, and persistence concerns separate.

Direct persistence logic inside views would make the midterm mock-data requirement harder to satisfy and would make a future database migration more invasive.

The repository currently uses the following layering:

`routes -> views/controllers -> ClinicService -> repository/data layer`

External Registrar and Inventory interactions are also isolated behind service boundaries.

## Decision

Clinic business operations must flow through the service layer rather than accessing persistence directly from views.

Responsibilities are divided as follows.

### Routes

Routes define public endpoint structure and connect URLs to controllers.

### Views/controllers

Views are responsible for:

- parsing path and query parameters;
- invoking serializers;
- validating HTTP payloads;
- translating domain/integration exceptions into API errors;
- delegating business operations to services;
- returning HTTP responses.

### Services

Services are responsible for:

- business rules;
- cross-resource orchestration;
- Registrar validation;
- Inventory coordination;
- compensation behavior;
- report/domain aggregation;
- choosing the configured repository boundary.

### Data layer

The data layer is responsible for:

- storing and retrieving Clinic-owned domain resources;
- deterministic in-memory mock behavior for the midterm;
- exposing repository operations used by `ClinicService`.

## Rationale

This structure supports both the midterm and finals without changing endpoint contracts.

It also makes ownership and external integration boundaries visible and testable.

The service layer provides the correct place for distributed business workflows such as medicine dispensing and rollback.

## Consequences

### Positive

- Views remain focused on HTTP responsibilities.
- Persistence can change behind the repository boundary.
- Business rules can be tested independently of route wiring.
- Integration orchestration is centralized.
- Future database repositories can be introduced with lower route-level impact.

### Trade-offs

- More files and abstractions than a minimal CRUD implementation.
- Developers must resist shortcuts that bypass services.
- Repository and service contracts must remain synchronized.

## Implementation Evidence

Relevant source:

- `backend/clinic/urls.py`
- `backend/clinic/views.py`
- `backend/clinic/services/clinic.py`
- `backend/clinic/data/clinic.py`
- `backend/clinic/services/registrar.py`
- `backend/clinic/services/inventory.py`

Verified implementation comments explicitly state that views must use the service instead of talking directly to Django ORM models.

`ClinicService` defaults to `MockClinicRepository` for the midterm.

Medicine-dispensation orchestration is implemented inside `ClinicService`, not in the route layer.

## Invariants

1. Views must not directly persist Clinic domain resources through Django ORM.
2. Business orchestration belongs in services.
3. Midterm Clinic persistence belongs behind the mock repository boundary.
4. Registrar and Inventory access must remain behind integration services.
5. Public routes should not need to change when the Clinic repository implementation changes.

## Related Documentation

- `docs/architecture.md`
- `docs/integration.md`
- `docs/data-model.md`
