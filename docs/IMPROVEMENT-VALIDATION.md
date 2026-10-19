# Improvement validation —20 October2026

Imported baseline:9514469fe0eddac3d185e806d94d46a093d95586, exact source submission tree/history. Baseline273 Django tests passed with normal hashing in135.900s. Baseline frontend npm ci/lint/build passed. Audit was recorded before implementation in IMPROVEMENT-AUDIT.md.

## Executed checks

| Check | Final recorded result |
| --- | --- |
| PostgreSQL full Django suite, normal hashing |294 passed,0 failed,0 skipped;148.849s |
| SQLite full Django suite, test-only faster hasher |294 discovered;292 passed,0 failed,2 PostgreSQL-only concurrency checks skipped; final run4.906s |
| PostgreSQL final full suite after refactor/formatting, test-only faster hasher |294 passed,0 failed/skipped;8.908s |
| Focused PostgreSQL repository/reliability/concurrency |16 passed before the final added API/delete/deployment regressions |
| PostgreSQL restart |All four Clinic resource kinds and unchanged Inventory transaction reference survived PostgreSQL17 server restart and a new application process |
| SQLite restart |All four Clinic kinds read in separate application process |
| Clinical browser on PostgreSQL repository |1 passed: login, health/consultation/status CRUD, reload, dispensing/rollback, reports/logout |
| Existing functional browser stories |9 passed across final suite and targeted rerun;8 passed in combined run, mock-catalog passed after pending-state fix |
| First-Owner and modal-focus browser stories |2 passed |
| Accessibility/responsive browser |1 passed:seven main pages in both themes, reduced-motion environment, axe WCAG2A/AA scan, mobile390x844 navigation/focus/Escape and no horizontal overflow |
| Newman collections |6 collections;173 requests;190 assertions;0 failures |
| Frontend ESLint/build |Passed |
| Django checks/migration drift |Passed |
| Static/dynamic OpenAPI generation/Redocly |Passed;45 paths/72 operations,5 public/67 protected |
| Production config tests |Missing secret/wildcard hosts fail; explicit valid deployment settings pass check --deploy |
| npm audit |0 known vulnerabilities; verified with system CA |
| pip-audit resolved requirements-finals dependencies |18 resolved packages,0 known vulnerabilities; verified with Windows system CA bundle |

PostgreSQL concurrency tests cover simultaneous first-Owner claims (201/409, one Owner) and simultaneous replay-key requests (one receipt/record). Reliability tests cover replay/different-body conflict, rollback once, role-scoped replay, invalid versions, protected audit metadata, known compensation incidents, weak Staff passwords, throttle and empty204 replay. Persistent API regression verifies stale ETag409 and real ORM CRUD. Production hashing was not weakened in application settings.

Newman breakdown:

| Collection | Requests | Assertions | Failures |
| --- | ---: | ---: | ---: |
| IDSC-Clinic-System |45|46|0|
| Password-change |11|13|0|
| Account-management |19|21|0|
| Account-lifecycle |22|24|0|
| Role-hierarchy |42|46|0|
| External-workflows |34|40|0|

## Failed intermediate checks and fixes

- Initial persistent API test exposed timestamp precision mismatch in ETag hashing; normalize datetimes identically before hashing.
- Initial full run exposed test-only Inventory state leakage after an intentionally failed compensation; restore isolated fixture state in teardown.
- Initial idempotent DELETE browser flow exposed a non-null receipt response rejecting204; migration0008 allows the empty response and a regression verifies replay.
- Mock catalog edit could race an earlier save/refresh and lose the newly opened form; disable competing controls while pending. Targeted story then passed.
- Initial axe scan found low-contrast light secondary text; darken only the secondary text token. Scans use the actual theme toggle and reduced-motion preference to avoid measuring mid-transition colors.
- An initial wrong-directory test invocation discovered0 tests and was rejected as evidence; the full suite was rerun from backend.
- Advisory queries initially failed certificate trust; use the operating-system trust store, never disable TLS verification.

## Scope limits

Real provider contracts/services, hosted TLS/proxy deployment, load/soak and operational backup recovery were not executed. External mocks reset; PostgreSQL proof applies to Clinic-owned records. Independent security review had partial repository coverage and three validated baseline findings; no exhaustive security certification is claimed. No new live provider endpoints/credentials were invented.

See DATABASE.md for reproducible restart script, frontend/README.md for browser fixtures, DEPLOYMENT.md and KNOWN-LIMITATIONS.md for operational requirements. Original repository was read-only; all changes belong to the clean improvement branch.
