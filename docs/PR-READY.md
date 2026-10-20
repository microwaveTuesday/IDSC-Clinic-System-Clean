# Verify final-project reliability, restoration and CI

Base: improvement/clinic-final-10of10. Head: improvement/clinic-final-verification.
Clean repository only; this draft does not merge or alter PR #2.

The previous branch lacked automated CI and a verified restore procedure, and
mock stock reset while clinical rows persisted. This pass adds fixture-isolated
Actions jobs, physical SQLite/PostgreSQL restore exercises, a separately owned
optional durable simulated Inventory ledger, and an ambiguity fence that refuses
unsafe retries after an interrupted external operation.

It preserves default mocks and all 294 inherited tests, adds 14 backend
regressions and an expired-session browser story, tightens login validation,
expires/purges replay bodies while retaining duplicate-operation tombstones,
minimizes error logs, and supplies a private HTTPS/Gunicorn/PostgreSQL deployment
profile with an executed restart smoke test. API routes remain 45 paths and 72
operations, with static/runtime schema equality checked in CI.

Validation and remaining limits: docs/VERIFICATION-RESULTS.md,
docs/VERIFICATION-SECURITY.md, docs/INVENTORY-RECOVERY.md,
docs/BACKUP-RESTORE.md and docs/KNOWN-LIMITATIONS.md. Real provider contracts,
public institutional hosting and compliance certification remain unavailable.
No real medical information or production credentials were used.
