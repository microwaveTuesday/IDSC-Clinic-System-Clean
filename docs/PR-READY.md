# Draft PR: durable Clinic records and verified final-project reliability

Target: microwaveTuesday/IDSC-Clinic-System-Clean main. Head: improvement/clinic-final-10of10. Do not merge without review.

This branch imports the complete source submission9514469 and its ancestry without modifying corpeadmin or either main/fix branch. It adds an ORM Clinic repository for SQLite/PostgreSQL while retaining explicit mocks, constraints/transaction locks, scoped replay receipts, conditional updates, private audit/reconciliation metadata and first-Owner/role/lifecycle compatibility.

Security fixes enforce Staff password strength, deny roleless medical-status reads and fail closed for production secrets/hosts with secure cookies/HTTPS policy. Login throttling is production-only and documented as cache/peer scoped. Views and frontend controls/dialogs are split into focused modules. API client timeouts/retry keys, pending-state protection and secondary-text contrast improve reliability without redesigning the interface.

Verification: baseline273 normal-hasher tests; expanded PostgreSQL294 passed with normal hashing; final SQLite292 passed/2 PostgreSQL-only skips and PostgreSQL294 passed using a test-only faster hasher. PostgreSQL server restart and fresh application process retained all four Clinic resources/references. Six Newman collections:173 requests/190 assertions/0 failures. Twelve distinct browser stories passed across scoped runs plus a PostgreSQL clinical rerun. Schemas/lints/build/migrations/deploy and dependency checks pass. See IMPROVEMENT-VALIDATION.md for exact scope and failed intermediate checks/fixes.

Remaining limits: no genuine external contracts/adapters; external mock state remains process-local/single-worker; uncertain external crash windows require reconciliation; hosted TLS, operational recovery and exhaustive security/accessibility certification are not claimed. The school-project engineering assessment is9.5/10, not10/10. See KNOWN-LIMITATIONS.md and DATABASE.md.
