# ADR 0001: Use Mock In-Memory Clinic Domain Data for the Midterm

## Status

Accepted

## Context

The Clinic System midterm requires the business API to operate with mock data rather than a production database.

The repository also needs Django's normal database infrastructure for authentication, groups, permissions, sessions, and administration.

Earlier versions of the project mixed these concerns and created a mismatch between the midterm requirement and the presence of Django models and migrations.

The current backend configuration separates Clinic business-domain storage from Django framework infrastructure.

`CLINIC_DATA_BACKEND` defaults to `mock`.

Clinic-owned business resources are handled through `MockClinicRepository`.

The default SQLite database is used for Django framework concerns rather than Clinic business-resource persistence.

PostgreSQL configuration remains available as an opt-in path for finals work.

## Decision

For the midterm:

- Clinic-owned `HealthRecord`, `Consultation`, `HealthStatus`, and `MedicineDispensation` API operations use in-memory mock domain storage.
- Clinic business views do not persist those resources through Django ORM.
- Django authentication, permissions, groups, sessions, and administration may continue using the framework database.
- The default framework database is SQLite.
- Finals may introduce a database-backed Clinic repository without changing the public API routes.
- PostgreSQL remains an opt-in finals configuration rather than a midterm runtime requirement.

## Rationale

This satisfies the midterm mock-data requirement while preserving Django framework features that legitimately require database infrastructure.

It also prevents the presence of Django models or migrations from being mistaken for the active midterm business-data persistence path.

Separating the domain storage policy from framework infrastructure makes the migration to finals persistence more controlled.

## Consequences

### Positive

- Midterm behavior matches the project requirement.
- Tests can reset deterministic in-memory Clinic domain data.
- Business routes are insulated from the persistence implementation.
- Authentication and session features continue to work normally.
- Finals can introduce a database repository behind the same service boundary.

### Trade-offs

- Mock data is process-local and non-persistent.
- Restarting the application resets mock state.
- Django domain models and migrations remain present for later work but are not the active midterm storage mechanism.
- Developers must avoid accidentally bypassing the repository abstraction and writing Clinic domain data directly through ORM models.

## Implementation Evidence

Relevant source:

- `backend/config/settings.py`
- `backend/clinic/data/clinic.py`
- `backend/clinic/services/clinic.py`

Verified configuration facts:

- `CLINIC_DATA_BACKEND` defaults to `mock`.
- SQLite is described as framework infrastructure for the midterm.
- PostgreSQL remains configurable for finals.
- `ClinicService` defaults to `MockClinicRepository`.

## Invariants

1. Midterm Clinic domain operations must not silently switch to ORM persistence.
2. Django framework database use must not be described as Clinic business-data persistence.
3. Finals persistence changes should preserve public API routes and service contracts.
4. Mock-domain tests must remain deterministic and resettable.

## Related Documentation

- `docs/architecture.md`
- `docs/data-model.md`
- `docs/integration.md`
- `docs/TEST-EVIDENCE.md`
