# Final verification evidence — 20 October 2026

Initial revision: `3737588c01b6d5bb957d8ad7ca412389c3ca6b81` (latest starting
improvement branch, independently fetched). Development branch:
`improvement/clinic-final-verification` in microwaveTuesday/IDSC-Clinic-System-Clean.
No original repository writes, main changes, force pushes, legacy branch changes,
or PR #2 changes were performed. The starting improvement branch remains3737588.

## Independently executed CI

Verified runtime revision: `1f61646c1c3da789c3ab321dbe5e251f57c4c1e6`.
[Actions run39347858545](https://github.com/microwaveTuesday/IDSC-Clinic-System-Clean/actions/runs/39347858545)
completed **success**, all **11 jobs**. Execution window:2026-10-20
00:28:36–00:31:10 UTC. Subsequent release documentation does not change runtime.
See the [workflow runs](https://github.com/microwaveTuesday/IDSC-Clinic-System-Clean/actions/workflows/quality.yml)
for later final-branch/PR reruns. Results here are executed evidence, not a
prediction that a newly edited workflow will pass.

Environment: GitHub-hosted Ubuntu, Python3.13, Node24, PostgreSQL16 service;
deployment smoke uses PostgreSQL17, Gunicorn26.2.0 and Caddy HTTPS containers.
Normal configured password hashing was used. Synthetic accounts and isolated
databases only. No real medical data or production credentials were used.

| Check | Executed result |
| --- | --- |
| Full PostgreSQL Django suite | **308 passed,0 failed,0 skipped**,79.890s |
| Full SQLite Django suite | **306 passed,0 failed,2 skipped**,308 discovered,49.557s |
| Explicit authorization/security regressions |37 passed on each database; repeated subset, not added to full-suite count |
| Explicit persistence/concurrency/reliability |PostgreSQL18 passed; SQLite16 passed/2 PostgreSQL-only skips; repeated subset |
| Django system checks |Pass,0 issues |
| Migration drift and application |Pass; no missing migrations |
| PostgreSQL physical dump/restore |Pass, all four clinical resource types, application reads, Inventory reference/stock, rollback and constraint |
| SQLite physical backup/restore |Pass with same checks |
| PostgreSQL actual service restart |Pass: docker restart service, fresh application process reads all four records and unchanged Inventory transaction/stock |
| Simulated Inventory hard process exit/restart |Pass in automated provider regression; committed stock survives and pending fence remains |
| Static/runtime OpenAPI equality |Pass,45 paths/72 operations |
| Runtime schema validation and Redocly static/dynamic |Pass |
| Frontend ESLint and production build |Pass |
| pip-audit, including deployment requirements |0 known vulnerabilities |
| npm audit |0 vulnerabilities |
| Newman collections |**173 requests,190 assertions,0 failures** |
| Browser workflows fixture |8 passed,49.3s |
| Browser account-limit fixture |1 passed,12.2s |
| Browser first-Owner fixture |1 passed,5.4s |
| Browser accessibility/focus/expired-session fixture |3 passed,24.9s |
| Total distinct Playwright stories |**13 passed,0 failed,0 skipped** across four isolated jobs |
| Private HTTPS production-image smoke |Pass: trusted TLS, session/CSRF, Owner setup, dashboard, clinical/dispensing writes, backend restart, retained records/stock/reference, rollback |

SQLite skips are explicitly the two real PostgreSQL row-lock concurrency tests.
Expected constraint violations in PostgreSQL service logs are intentional negative
tests, not ignored failures. CI uploads only count/status/revision summaries;
raw backups, credential-bearing Postman state and medical responses are not
uploaded as artifacts.

Newman breakdown (each request/assertion group passed with0 failures):

| Collection | Requests | Assertions |
| --- | ---: | ---: |
| IDSC-Clinic-System |45|46|
| Password-change |11|13|
| Account-management |19|21|
| Account-lifecycle |22|24|
| Role-hierarchy |42|46|
| External-workflows |34|40|

## Commands and fixture isolation

The exact reproducible commands/steps are committed in
[quality.yml](../.github/workflows/quality.yml). Core commands:

```text
python -m pip install -r backend/requirements-finals.txt
python backend/manage.py check
python backend/manage.py makemigrations --check --dry-run
python backend/manage.py migrate --noinput
cd backend
python manage.py test --noinput --verbosity 2
python manage.py test clinic.tests.test_verification_security clinic.tests.test_permissions authentication.tests.test_role_hierarchy --noinput
python manage.py test clinic.tests.test_persistent_repository clinic.tests.test_concurrency clinic.tests.test_reliability --noinput
cd ..
python scripts/verify_restore.py
python scripts/verify_persistence.py write
# Restart disposable PostgreSQL service, then:
python scripts/verify_persistence.py read
python scripts/check_contract.py
npx --yes @redocly/cli@2.7.0 lint openapi.yaml
python -m pip_audit -r backend/requirements-deployment.txt
npm ci --prefix frontend
npm audit --prefix frontend --audit-level=moderate
npm --prefix frontend run lint
npm --prefix frontend run build
```

Backup script requires `CLINIC_DISPOSABLE=1`. Database environment and separate
Inventory modes are explicit in the workflow. Each browser job starts its own
fresh migrated database. First-owner has no precreated Owner; limits has exactly
eleven seeded Staff and no Admin; normal workflows/accessibility have separate
synthetic Owners. The six Newman collections run against another isolated API.
Playwright executes all existing stories plus session-expiry; no baseline story
was removed. PostgreSQL/SQLite full suites include all294 inherited tests plus
14 new tests. See frontend/README.md for locally reproducing fixtures.

## Local evidence and intermediate failures

- Starting SQLite baseline rerun:294 discovered,292 passed/2 PostgreSQL-only
  skips,0 failures,130.565s with normal hashing on Windows/Python3.13.
- Final local SQLite rerun:308 discovered,306 passed/2 PostgreSQL-only skips,0 failures,139.952s with normal hashing.
- Intermediate expanded PostgreSQL run:306 passed,0 failures/skips,141.082s
  against isolated PostgreSQL17; two more regressions were then added and all308
  passed in final CI.
- Physical restore drills passed locally on SQLite and PostgreSQL17, using
  disposable databases and temporary physical backups.
- New ledger tests initially exposed SQLite connections left open on Windows;
  explicit closing fixed cleanup/handle leakage. A subprocess test initially
  depended on the caller's directory; it now sets its backend cwd explicitly.
- One local invocation used the wrong working directory and ran no tests; it is
  not counted as evidence. Correctly scoped reruns and final CI passed.
- A local evidence-print command encountered Windows output encoding; CI logs
  were retrieved as UTF-8. No test failure was concealed by that tooling issue.
- All reported final checks passed. Historical273/294-test reports remain
  labelled historical and do not substitute for the new308-test run.

## Findings, changes and remaining scope

The baseline lacked CI/restore proof and lost Inventory state on restart. Changes
add isolated automation, a durable simulated provider, conservative crash fences,
paired restore drills, a verified HTTPS container stack, bounded replay response
retention, credential validation, private exception logs, session-expiry UI and
14 meaningful backend regressions. Full details and ownership diagrams:
[INVENTORY-RECOVERY.md](INVENTORY-RECOVERY.md),
[BACKUP-RESTORE.md](BACKUP-RESTORE.md),
[VERIFICATION-SECURITY.md](VERIFICATION-SECURITY.md).

No critical/high exploitable issue was established by the reviewed source
boundaries and executed tests. This is not an independent penetration test or a
guarantee of no undiscovered vulnerabilities. Real providers, public hosted
deployment, load/soak, distributed throttling, off-host backup operations and
institutional medical-data retention approval remain unavailable/unverified.
Ambiguous outcomes intentionally require manual reconciliation; Registrar edits
remain process-local. Automated axe/keyboard checks are not WCAG certification.

Engineering assessment: **9.8/10 for a school final project**, subject to the
actual course rubric. Reliability evidence is substantially stronger, but manual
uncertain-outcome repair, process-local Registrar and unverified institutional
operations prevent an unconditional10/10 or production-readiness claim.

Run/demo: [SETUP.md](../SETUP.md), [FINAL-DEMO.md](FINAL-DEMO.md),
[DEPLOYMENT.md](DEPLOYMENT.md). Remaining limitations:
[KNOWN-LIMITATIONS.md](KNOWN-LIMITATIONS.md).
