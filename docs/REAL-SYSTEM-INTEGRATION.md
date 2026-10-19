# Connecting real Registrar and Inventory systems

## Current state

The runtime uses MockRegistrarService and MockInventoryService in backend/clinic/services/. Owner workspaces in clinic/demo_integrations.py simulate external operators. There is no implemented real-service adapter or configuration that connects a provider simply by setting a URL. CLINIC_API_TARGET only points Vite at the Clinic backend.

Registrar owns student identity/profile/status. Inventory owns catalog, stock and transactions. Clinic owns clinical records and orchestrates dispensing/rollback. IDs cross API boundaries; modules do not share a database. Faculty/Student Portal routes expose authenticated read-only status projections.

## Transition plan: remaining work

1. Obtain verified provider contracts, stable IDs, status mappings, credentials, test environments, error formats and stock/delivery semantics.
2. Implement real adapters behind existing service interfaces while preserving Clinic routes/tests. Map external failures to domain exceptions. Add explicit mock/real adapter configuration and keep provider credentials server-side.
3. Replace direct in-memory accesses in demo_integrations.py for lookup/catalog/notifications/restocks with provider-backed services. Disable mock editing and simulated fulfillment in real mode.
4. Agree authenticated webhooks, polling or live reads for profile/catalog changes. The website's five-second refresh only re-reads Clinic projections; it is not yet real external synchronization. Define retry, conflict and last-success behavior.
5. Agree durable transaction IDs, idempotency, timeout reconciliation and compensating stock restore for dispensing/rollback/restock delivery. Retries must not deliver or deduct stock twice. Persist requests/events needed for recovery.
6. PersistentClinicRepository is now implemented for SQLite/PostgreSQL; select CLINIC_DATA_BACKEND=database. Real deployments still need backup/restore and retention policy.
7. Verify complete staging flows: active/ineligible students, external profile edits, stock shortage, requests/delivery, duplicate events, timeouts, rollback, notifications, permissions and restarts before switching.

## Keep mocks for demonstrations

Retain isolated mock mode for development/tests. Mock workspaces are independently enabled by MOCK_WORKSPACES_ENABLED, including in Clinic database mode. CLINIC_EMPTY_START=1 starts empty process-local stores; otherwise samples load. Neither setting is a real connector. Real and mock operations must use separate stock ledgers and credentials.

See [integration.md](integration.md) and [EXTERNAL-WORKFLOWS.md](EXTERNAL-WORKFLOWS.md). The transition plan is proposed work, not currently available functionality.
