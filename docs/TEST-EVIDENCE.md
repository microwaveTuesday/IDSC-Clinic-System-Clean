# Phase 7 — Tests & Contract Validation Evidence

> Historical stage-by-stage evidence. Counts and branch names below describe the stage when recorded, not the current submission. Latest scope/results: [CURRENT-VALIDATION.md](CURRENT-VALIDATION.md). Current setup: [SETUP.md](../SETUP.md).

## 1. Purpose

This document records the verified testing, contract-validation, regression, lifecycle, and repository-integrity evidence produced during Phase 7 of the IDSC Clinic System backend.

Phase 7 covers:

- automated backend regression testing
- API contract validation
- authentication and permission regression
- integration contract validation
- reports and data consistency
- CORS and browser contract validation
- Postman request coverage
- Newman execution
- database lifecycle verification
- repository and deliverable hygiene

The evidence in this document is based on the validation commands and terminal results produced during Phase 7.

---

## 2. Final Phase 7 Baseline

| Item | Verified Result |
|---|---:|
| Branch | `phase7/tests-contract-validation` |
| Permanent Django tests | 167 |
| Permanent Django tests passed | 167 |
| Permanent Django tests failed | 0 |
| OpenAPI version | 3.1.0 |
| OpenAPI paths | 29 |
| OpenAPI operations | 45 |
| Public operations | 3 |
| Protected operations | 42 |
| `BadGateway` response present | No |
| Postman requests | 45 |
| Postman requests with status assertions | 45 |
| Newman requests executed | 45 |
| Newman failed requests | 0 |
| Newman test scripts | 45 |
| Newman failed test scripts | 0 |
| Newman assertions | 46 |
| Newman failed assertions | 0 |
| Persistent domain database after regression | Clean |
| Temporary artifacts remaining after cleanup | 0 |
| Unstaged tracked changes at final consistency check | 0 |
| Untracked files at final consistency check | 0 |

---

## 3. Permanent Automated Tests

The permanent Django test suite was reorganized into dedicated test modules under:

```text
authentication/tests/
clinic/tests/
```

The permanent suite contains 167 test methods across eight test modules:

| Test module | Test methods |
|---|---:|
| `authentication/tests/test_auth.py` | 11 |
| `clinic/tests/test_consultations.py` | 25 |
| `clinic/tests/test_dispensations.py` | 26 |
| `clinic/tests/test_health_records.py` | 22 |
| `clinic/tests/test_health_statuses.py` | 25 |
| `clinic/tests/test_integrations.py` | 22 |
| `clinic/tests/test_permissions.py` | 17 |
| `clinic/tests/test_reports.py` | 19 |
| **Total** | **167** |

### Verified regression run

Command:

```powershell
python manage.py test --verbosity 1
```

Verified result:

```text
Found 167 test(s).
Ran 167 tests
OK
Destroying test database for alias 'default'...
```

The test suite completed with zero failures and the temporary Django test database was destroyed after execution.

---

## 4. OpenAPI Contract Validation

The canonical OpenAPI contract was validated against the expected Phase 7 structure.

| Contract property | Verified result |
|---|---:|
| OpenAPI version | 3.1.0 |
| Paths | 29 |
| Operations | 45 |
| Public operations | 3 |
| Protected operations | 42 |
| `BadGateway` response | Absent |

The canonical structure check returned:

```text
OPENAPI = 3.1.0
PATHS = 29
OPERATIONS = 45
PUBLIC = 3
PROTECTED = 42
BADGATEWAY PRESENT = False
OPENAPI CANONICAL = True
```

---

## 5. Postman Collection Validation

The final Postman collection contains 45 API requests.

| Validation | Result |
|---|---:|
| Requests | 45 |
| Requests with status assertions | 45 |
| JSON validity | PASS |
| Canonical request count | PASS |

The staged collection was independently read from Git's index and successfully parsed as JSON.

Verified collection metadata:

```text
COLLECTION NAME = IDSC Clinic System API
COLLECTION SCHEMA = https://schema.getpostman.com/json/collection/v2.1.0/collection.json
```

---

## 6. Newman Execution Evidence

The Phase 7 Postman collection was executed through Newman.

| Newman result | Verified result |
|---|---:|
| Requests executed | 45 |
| Failed requests | 0 |
| Test scripts | 45 |
| Failed test scripts | 0 |
| Assertions | 46 |
| Failed assertions | 0 |

The recorded Newman result therefore completed without request failures or failed test assertions.

---

## 7. Authentication and Permission Regression

Authentication and authorization behavior was included in the permanent regression suite.

The permanent authentication test module contains 11 tests, while the permission regression module contains 17 tests.

The Phase 7 suite verifies the documented authentication, permission, and protected-endpoint behavior through automated Django tests.

---

## 8. Integration Contract Validation

Integration behavior was included in the permanent regression suite.

The integration test module contains 22 tests.

The validated integration areas include the Clinic integration endpoints represented by the permanent test suite, including Student Portal, Faculty, Registrar, and Inventory-related contracts.

---

## 9. Reports and Data Consistency

Reports and data-consistency behavior was included in the permanent regression suite.

The reports test module contains 19 tests.

Phase 7 regression also verified that the persistent Clinic domain database remained clean after the final test run.

Verified persistent domain counts:

```text
HealthRecord = 0
Consultation = 0
HealthStatus = 0
MedicineDispensation = 0
DOMAIN DATABASE CLEAN = True
```

---

## 10. CORS and Browser Contract Validation

CORS and browser-contract validation was completed during Phase 7 and is recorded as a completed Phase 7 validation area.

The final Phase 7 evidence baseline therefore records CORS and browser contract validation as part of the completed regression work.

---

## 11. Database Lifecycle Verification

Permanent Django regression uses Django's test database lifecycle.

The final regression run verified:

1. A test database was created.
2. All 167 permanent tests executed successfully.
3. The test database was destroyed after execution.
4. A separate persistent-database check confirmed that Clinic domain tables remained empty.

---

## 12. Repository Integrity and Hygiene

Phase 7 included repository-integrity checks covering staged content, working-tree state, temporary artifacts, and diff integrity.

Final consistency verification recorded:

| Repository check | Result |
|---|---:|
| Current branch | `phase7/tests-contract-validation` |
| Staged files | 18 |
| Unstaged tracked files | 0 |
| Untracked files | 0 |
| Missing required Phase 7 files | 0 |
| Staged/unstaged overlap | 0 |
| Forbidden artifact patterns | 0 |
| Staged diff check | PASS |
| Working-tree diff check | PASS |

Temporary recovery artifacts were removed before the final staged-content audit.

---

## 13. Django and Migration Integrity

The final Phase 7 integrity checks verified the Django project and migration state.

Verified commands:

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
git diff --check
```

Verified results:

```text
System check identified no issues (0 silenced).
No changes detected
Diff-check exit = 0
```

---

## 14. Phase 7 Evidence Summary

Phase 7 produced the following verified evidence:

- 167 permanent Django tests passing.
- 45 canonical OpenAPI operations.
- 29 OpenAPI paths.
- 3 public operations.
- 42 protected operations.
- 45 Postman requests.
- 45 Postman requests with status assertions.
- 45 Newman requests executed.
- 0 Newman request failures.
- 46 Newman assertions.
- 0 Newman assertion failures.
- Clean persistent Clinic domain database after regression.
- No temporary recovery artifacts remaining.
- No unstaged tracked changes at final consistency verification.
- No untracked files at final consistency verification.

These results represent the recorded Phase 7 test and contract-validation evidence before the Phase 7 commit and push stage.

---

## 15. Evidence Status

**Phase 7 test and contract-validation evidence: COMPLETE.**

The evidence document itself must be included in the Phase 7 commit together with the already staged backend tests, OpenAPI contract, and Postman collection.

Phase 7 remains subject to the final commit and push procedure documented as Goal 7.12.

## Subsequent password-change extension

On 17 October 2026, the additive password-change implementation passed all 180 Django tests (167 preserved plus 13 new), three browser stories, both schema lints, the original Newman suite (45 requests / 46 assertions), and the separate password flow (11 requests / 13 assertions). All passed with zero failures. Current inventory is 30 paths / 46 operations; all original operation definitions are unchanged. See `PASSWORD-CHANGE.md` and `INTEGRATION-VALIDATION.md` for reproduction and scope.


## Username and administrator extension

The additive username/admin implementation passed all 198 Django tests. Current schema: 32 paths / 49 operations. Both Redocly lints passed, no migration drift, and all three Newman collections passed: 75 requests / 80 assertions with zero failures. The 18 new backend tests cover self-only username updates, validation, authentication, CSRF, administrator creation/role isolation, staff denial and new-admin capabilities. See `ACCOUNT-MANAGEMENT.md` and latest `INTEGRATION-VALIDATION.md` for browser results and reproduction.

Final browser verification after repairing the login navigation race: all four stories passed together. Frontend lint/build and desktop/mobile dialog checks passed.


## Account lifecycle extension

All 221 Django tests passed; schema inventory is 35 paths / 53 operations. Both schema lints, configuration/migration checks and frontend lint/build passed. All four Newman collections passed: 97 requests / 104 assertions, zero failures. The 23 lifecycle tests cover deletion, deactivation/reactivation, authorization/CSRF, actor-password verification, session revocation, self/last-admin protections, system/mixed-role boundaries and medical-record preservation. See latest browser evidence in `INTEGRATION-VALIDATION.md`.


### Final account lifecycle validation

- 221 Django tests passed, including 23 account lifecycle tests.
- All five browser stories passed: account lifecycle, administrator creation/username, clinical CRUD/dispensing/reports, staff permissions, and password changes. The clinical story passed in a targeted rerun after fixing test synchronization: wait for the pending confirmation and dispensing refresh before proceeding, and use unique consultation/status markers to avoid prior aborted-run fixtures. The full pass initially had four passes and one clinical synchronization failure; no backend baseline tests were changed.
- Four Newman collections passed: 97 requests and 104 assertions total.
- Frontend lint and production build passed; static/dynamic schemas match at 35 paths and 53 operations; schema lint and migration/configuration checks passed.
- Changes remain local on integration/clinic-final; main was not modified and nothing was pushed.


## Owner/Admin/Staff hierarchy validation

- Clean full Django run: **233 tests passed** (182 seconds). This includes twelve new hierarchy tests and revised extension tests for Owner-only Admin management. Original backend clinic/auth contract tests are unchanged.
- All **six browser workflows passed** across the full run and targeted hierarchy rerun. The five existing stories passed in the full run; the new hierarchy story passed after synchronizing sign-in with completed logout (21.9 seconds). It covers Owner editing Admin, Admin creating/editing/deactivating/activating/deleting Staff, Staff clinic access, and denied management access.
- Frontend lint and production build passed.
- No database migration changes detected. Static/dynamic inventories match: **35 paths, 56 operations**, with **3 public and 53 protected** under effective inherited security.
- Role mapping uses existing Django superusers as Owners without promoting regular Admin/Staff accounts. Owner credential changes retain the session; management endpoints protect Owner accounts and reject mixed-role bypasses.
- New API collection: `postman/Role-hierarchy.postman_collection.json` (42 requests). Final collection and schema results are recorded below.
- Changes remain local on `integration/clinic-final`; main and the original Postman collection are unchanged.

Both static and generated OpenAPI descriptions passed Redocly lint without warnings.


Final API collections: original baseline **45 requests / 46 assertions**; password change **11 / 13**; account management **19 / 21**; account lifecycle **22 / 24**; role hierarchy **42 / 46**. Total: **139 requests / 150 assertions**, zero failures. Lifecycle directory assertions were updated to verify that Owner is excluded from manageable Admins. All original baseline collection requests/tests remain unchanged. Validation used an isolated API database; temporary credentials/results were removed afterward. Website and API remain available on ports 5173 and 8000.


## Staff pagination and five-Admin limit validation

Full backend run: **242 tests passed** (246.8 seconds), including nine new pagination/capacity tests. All **seven browser workflows passed** across the full run and targeted reruns. The five unaffected stories passed in the full run. The new boundary story passed in 19.8 seconds on fresh disposable fixtures, and account management passed in 22.1 seconds after scoping its Settings role selector. The first boundary attempt was interrupted by a Vite configuration-format reload; no product defect was indicated by that interruption. The final boundary story verifies ten/one Staff rows across two pages, search reset, deletion of the last row returning to page one, sixth-Admin rejection, inactive Admins retaining their slots, deletion enabling creation and successful replacement.

Frontend lint/build, migration-drift check, schema generation/validation and both Redocly lints passed. Static/runtime schema inventories still match at 35 paths / 56 operations. The original backend clinic/auth contract tests and original Postman collection are unchanged. Admin capacity counts inactive Admins, excludes Owner and is checked transactionally in the backend. Existing over-limit accounts are preserved, with new creation blocked.

Validation ran on an isolated database and frontend (ports 8001/5174); normal user development services remain on 8000/5173. Temporary validation services and sensitive files were cleaned up afterward. Changes remain local on integration/clinic-final; main is untouched.

Original Postman baseline passed unchanged: **45 requests / 46 assertions**, zero failures. Normal website/API health checks both returned 200 after updating the running backend.


## Registrar/Inventory workflows and clinical deletion validation

- Full backend run: **257 tests passed**, including fifteen new external-workflow tests (263.4 seconds). Tests exercise current Registrar profiles and enrollment gating, direct role/CSRF/auth checks, catalog CRUD and notifications with per-user receipts, selected/all requests, no stock before delivery, atomic delivery validation, duplicate fulfillment, and stock-preserving dispensing-history deletion.
- **Nine browser workflows passed across regression runs**. Account lifecycle and capacity passed in the initial run. Adding Owner mock navigation exposed a short-window sidebar overflow; the sidebar was made scrollable and account management then passed. The final six-story run passed clinical CRUD/reporting, Staff management, the complete new external workflow (42.4 seconds), mock Registrar/catalog edit/delete (4.9 seconds), password changes and role hierarchy. Older quantity selectors were scoped to the dispensing form; native select controls use accessible combobox selectors. API-created clinical fixtures are reloaded before checking website labels.
- The new complete browser flow verifies health/consultation display labels restart at #1 after deletion while internal IDs continue increasing, a Registrar update reaches an open Staff page, graduated/dropped-out students cannot create, a new Inventory medicine generates Clinic notifications, selected and all requests reach Inventory and are fulfilled, and removing dispensing history leaves stock unchanged. The catalog story verifies Owner editing status/profile and editing/deleting an unused medicine in the mock workspaces.
- API collections passed: original baseline **45 requests / 46 assertions**; new External-workflows collection **34 requests / 40 assertions**. Total **79 requests / 86 assertions**, zero failures. The original Postman collection is unchanged.
- The earlier clinical deletion contract tests now explicitly authorize an Admin for deletion; the former dispensing-delete-405 test now expects Staff 403. These are intentional adjustments to the newly requested permissions, not removal of regression checks.
- Frontend lint/build, Django configuration/migration checks, static/runtime schema generation and both Redocly lints passed. Matching inventory: **43 paths / 70 operations**, 3 public / 67 protected. Main runtime schema returns 200 with 43 paths; website HTML returns 200.
- Desktop sidebar scrolling and the medicine/restock/notification screen were visually checked. Test screenshots are in the ignored frontend/test-results directory.
- Isolated validation services used 8001/5174 and disposable accounts. Those services, credentials, API response reports and database were removed afterward. User services remain on **8000/5173**. Main was not modified; changes remain local on integration/clinic-final.
- New mock state is process-local, matching the existing mock domain; it resets on backend restart. Real student/medicine source systems are not connected. Django account credentials were not changed.


## Password dialog focus fix (Desktop copy, 2026-10-19)

The shared Modal focus effect previously depended on an inline onClose callback. Background integration refreshes changed that callback and reran focus initialization, selecting the close button while the user typed. Focus initialization/cleanup now run only when the modal mounts/unmounts; an Effect Event reads the latest keyboard-close callback so pending-submit guards remain current. Initial focus prefers an enabled form field, and the Tab loop excludes disabled/hidden inputs.

`frontend/tests/modal-focus.spec.js` passed (11.1 seconds). It uses intercepted API fixtures, types slowly across a confirmed integration refresh, checks the typed value and focused field, verifies Tab/Shift+Tab wrapping, prevents Escape from closing a pending password update, and verifies Escape/focus restoration after the request finishes. No real account password is submitted or changed. Frontend lint and production build passed. Changes are local and unpushed.
