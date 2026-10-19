# Improvement baseline audit — 20 October 2026

Recorded before implementation changes. Imported source9514469fe0eddac3d185e806d94d46a093d95586 exactly, including ancestry. Original main aab84b2f3865b105c7270ed941e541a1bdddd52c; clean main f37fd5cf74e426cf3c8129b994af27c890a203cb; clean fix/pre-main-integration195580e5336b7d8d5da683b7a35ab37da2d6101c. New branch improvement/clinic-final-10of10. Source push URL disabled locally; destination default origin. No inherited branch overwritten.

## Baseline observations

- 273 existing Django tests; full normal-hasher baseline completed:273 passed in135.900 seconds. Frontend npm ci, ESLint and production build pass.
- ClinicService always selects MockClinicRepository, ignoring storage configuration. Four Clinic ORM models/migrations already exist, but no persistent repository. All business history resets on restart.
- Read/modify/write operations lack optimistic concurrency checks. Mock inventory stock operations and clinical mock mutations lack one shared synchronization boundary. External transaction IDs restart their numeric sequence.
- Dispensing compensation catches and discards stock-restore failure. No durable idempotency or reconciliation receipt exists. Restock fulfillment does use a process lock and duplicate-state guard, but all mock state is process-local.
- Views exceed1600 lines; service/repository separation exists and must be preserved. Frontend App.jsx is oversized; dialogs handle pending state but general API client has no timeout, cancellation or duplicate request protection.
- Source includes development SECRET_KEY fallback, DEBUG defaults true, wildcard ALLOWED_HOSTS, no fail-closed production configuration. No private key or committed SQLite/.env/dependency trees found in current tracked tree; collection credential literals require classification as examples, not use against live systems.
- Staff creation validates only nonempty password instead of configured strength validators. Faculty/Student Portal status projections accept any authenticated account and arbitrary student_id, including free-text remarks. No genuine external trust contract exists; restrict these to Clinic roles rather than invent provider credentials.
- Existing Owner registration uses serialized permanent latch plus unique database index. Roles, account limits, CSRF and lifecycle tests already exist. Preserve their coverage; intentionally strengthen only verified weak controls.
- Registrar and Inventory are mocks, not production connectivity. No real provider contracts supplied. Do not invent adapters/endpoints.
- No durable security audit history. Medical data must not enter audit logs, idempotency keys or error traces unnecessarily.
- Documentation accurately acknowledges most limitations but must be updated for database mode, deployment, concurrency semantics and exact new evidence.

## Implementation priorities

1. Persistent repository using existing Clinic models, constraints, transactions and stale-write conflict checks; PostgreSQL plus SQLite; retain explicit mock mode.
2. Durable scoped idempotency receipts for dangerous writes, common lock boundary for mock Inventory operations and safe reconciliation behavior.
3. Harden production settings, staff password validation, status-projection authorization and audit metadata; add regression tests.
4. API client timeouts/idempotency and focused UI extraction preserving design; browser and responsive checks.
5. Execute actual PostgreSQL restart tests, backend/API/browser/tooling checks; record honest scope, limitations and rating.
