# ADR 0002: Preserve Module Domain Ownership and External Identifiers

## Status

Accepted

## Context

The College Management System is composed of independent modules that communicate through APIs.

The Clinic module must not duplicate or take ownership of data that belongs to Registrar or Inventory.

The canonical ownership boundaries are:

- Registrar owns student identity and profile data.
- Clinic owns health records, consultations, health statuses, and medicine dispensations.
- Inventory owns medicine catalog, medicine stock, and inventory transactions.
- Faculty and Student Portal consume a restricted read-only Clinic health-status projection.

Clinic resources need stable references to externally owned records.

The important shared identifiers are:

- `student_id`
- `medicine_id`
- `inventory_transaction_id`
- `rollback_transaction_id` where compensation or rollback occurs

These values represent cross-module references, not shared-database foreign keys.

## Decision

Clinic will preserve module ownership boundaries and treat external identifiers as opaque API-level references.

Specifically:

- Clinic uses `student_id` to refer to Registrar-owned students.
- Clinic uses `medicine_id` to refer to Inventory-owned medicines.
- Clinic stores Inventory transaction identifiers required to trace medicine-dispensation stock operations.
- Clinic does not create, update, or delete Registrar student identity records.
- Clinic does not own or directly mutate the Inventory medicine catalog.
- Inventory stock changes occur only through the Inventory integration service boundary.
- Faculty and Student Portal receive read-only health-status projections rather than direct access to Clinic persistence.

## Rationale

Shared databases would blur ownership and tightly couple modules.

Opaque external identifiers allow each module to evolve its own persistence independently while keeping API contracts stable.

The approach also reflects the intended College Management System architecture: modules exchange data through APIs rather than direct table access.

## Consequences

### Positive

- Clear ownership boundaries.
- Reduced cross-module coupling.
- Independent persistence choices remain possible.
- External systems can be replaced without changing Clinic domain models into shared-database models.
- Integration errors can be translated explicitly at API boundaries.

### Trade-offs

- External references require runtime validation.
- Cross-module operations may fail if an owning module is unavailable.
- Referential integrity is enforced through integration logic rather than database foreign-key constraints.
- Distributed operations require compensation or rollback strategies.

## Implementation Evidence

Relevant source:

- `backend/clinic/services/registrar.py`
- `backend/clinic/services/inventory.py`
- `backend/clinic/services/clinic.py`
- `backend/clinic/views.py`
- `backend/clinic/urls.py`

Verified behavior:

- Registrar-backed student endpoints are read-only.
- Inventory-backed medicine endpoints are read-only projections.
- Clinic validates students through the Registrar boundary.
- Medicine dispensing coordinates Inventory stock operations with Clinic-owned dispensation records.
- Faculty and Student Portal health-status integration routes are read-only.

## Invariants

1. Registrar remains authoritative for student identity/profile.
2. Inventory remains authoritative for medicines and stock.
3. Clinic remains authoritative for its four medical-domain resources.
4. External identifiers must not be converted into shared database ownership.
5. Faculty and Student Portal must not receive write access to Clinic health status through integration projections.

## Related Documentation

- `docs/data-model.md`
- `docs/integration.md`
- `docs/architecture.md`
