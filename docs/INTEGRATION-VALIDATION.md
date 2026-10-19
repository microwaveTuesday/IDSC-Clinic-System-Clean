# Integration validation — 17 October 2026

> Historical stage-by-stage evidence. Counts and branch names below describe the stage when recorded, not the current submission. Latest scope/results: [CURRENT-VALIDATION.md](CURRENT-VALIDATION.md). Current setup: [SETUP.md](../SETUP.md).

## Preserved baseline

Integration base: `195580e` (`origin/fix/pre-main-integration`), tree-equivalent to clean `main` at `f37fd5c`. At initial integration commit `a75cf4b`, the backend, existing tests, contract and original Postman collection were unchanged. The subsequent password-change extension adds a protected endpoint while preserving every original operation.

## Initial integration checks

| Check | Result |
|---|---|
| Django test suite | 167 discovered, 167 passed, zero failures |
| Django configuration check | No issues |
| Migration drift | No changes detected |
| Dynamic schema generation and validation | Passed |
| Static/dynamic inventory | Identical: 29 paths, 45 operations |
| Redocly static and dynamic lint | Both passed |
| Newman collection | 45 requests, 46 assertions, zero failures |
| Canonical `/api/v1/health` | Exact JSON `{"status":"ok"}` |
| `/docs` | HTTP 200 and Swagger markup |
| Unauthenticated protected resource | HTTP 401 and all canonical Problem Details fields |
| Frontend production build | Passed |
| Frontend ESLint | Passed |
| npm dependency audit | Zero vulnerabilities after compatible transitive dependency updates |
| Browser account/mobile flow | Passed: administrator staff creation/editing/deactivation/activation, staff login, hidden admin navigation, backend HTTP 403, desktop rendering and mobile navigation |
| Browser clinical flow | Passed: real session login, health-record create/edit/delete and reload persistence, consultation/status CRUD, dispensing/rollback, report rendering, logout and authenticated endpoint returning 401 afterward |

Both browser stories passed (clinical flow and administrator/staff flow; executed separately after fixes). Desktop (1440×1000) and mobile (390×844) screenshots were inspected.

Backend validation ran on Python 3.13.15; frontend validation used Node 24.21.0 and Chromium through Playwright. Tests used a locally created administrator with a random password, never committed. Newman ran before the fresh browser mock runtime. Test data, sessions, logs and credentials are excluded from Git.

## Browser verification details

The client sends credentialed requests through Vite's `/api` proxy. Every unsafe request first obtains a current CSRF token, so login rotation is respected. Mutation responses are followed by an API refresh, and reload persistence was checked against the same backend process. Backend errors remain visible in the page and editor. A successful write followed by a failed refresh is identified as saved, preventing an accidental duplicate submission.

During implementation, browser testing found and fixed an initial dashboard render before summary data arrived. Frontend checks also identified the legacy Tailwind import without a matching dependency, and rollback's status was corrected to canonical `COMPLETED`. Browser selectors were corrected to follow labeled required inputs and tab roles. These are recorded as fixes, not unresolved validation failures.

## Reproduction

Follow `frontend/README.md` for the two local servers and environment-based browser-test credentials. Run the existing Django suite from `backend`, then generate the dynamic schema with `python manage.py spectacular --file ../schema.generated.yaml --validate`. Lint the static and generated files using the existing `redocly.yaml`. Run the supplied Postman collection with Newman using an isolated administrator and override its username/password variables.

## Release boundaries

This validates integration against the supplied mock backend contract. It does not certify production clinical use, persistent business storage, real Registrar/Inventory connectors, an instructor-approved Figma match, GitHub branch protection or teammate approval. Those remain explicit release decisions. Main was not edited or pushed; consolidation is isolated on `integration/clinic-final`.


## Password-change extension: latest executed validation

- 180 Django tests passed: all 167 existing tests plus 13 password-change tests.
- Django check passed; migration drift check found no changes.
- Static and dynamic OpenAPI both validated and passed Redocly lint: 30 paths / 46 operations, 3 public / 43 protected.
- A structural comparison confirmed that every original static path definition remains unchanged; only the new password-change path and request schema were added.
- Original Newman collection: 45 requests / 46 assertions / zero failures, unchanged collection.
- Isolated password-change Newman collection: 11 requests / 13 assertions / zero failures, including change, retained session, rejected old credentials, accepted new credentials and restoration.
- Existing clinical and staff browser stories passed; the new password-change story passed after correcting accessible error labels. Together the three stories cover the original workflows and the new flow.
- Frontend ESLint and production build passed. Password dialogs were inspected on desktop in dark mode and on mobile in light mode.

Newman ran against a separate framework database on port 8001 to avoid modifying the user's demo accounts. Browser password changes used a dedicated isolated account and restored its original password. Existing demo account passwords were not changed.

The endpoint requires current-password verification and CSRF protection and rotates the current session while invalidating other sessions. See `PASSWORD-CHANGE.md` for details. Theme changes and the password extension are local edits on the integration branch until committed/pushed; main remains untouched.


## Username/admin extension: latest validation

The full backend suite passed 198 tests: all 167 original tests, 13 password-change tests, and 18 username/admin tests. Django check passed and migration drift found no changes. Both schemas generated/validated and passed Redocly lint at 32 paths / 49 operations (3 public, 46 protected). Every original static operation definition remains unchanged; password change is retained.

Newman against the isolated framework database passed all three collections: original 45 requests / 46 assertions; password 11 requests / 13 assertions; username/admin 19 requests / 21 assertions. Combined: 75 requests / 80 assertions, zero failures. New administrator creation and username changes were verified using session cookies and CSRF, including actor reauthentication, role permissions and old/new login behavior.

The new browser account story passed admin creation, new-admin access, duplicate-name and wrong-password errors, username changes, retained session and old/new login. Regression testing identified a login navigation race: late initial data loading could override an early Settings click. Navigation now occurs before initial data loading so subsequent user navigation is preserved. Final browser and frontend results are recorded below after the repair.

See `ACCOUNT-MANAGEMENT.md` for the full contract and UI flow. These are local integration-branch edits; main and synced source documents remain untouched.

Final result after the login-navigation repair: all four Playwright stories passed together (2.3 minutes). Frontend ESLint and production build passed. Administrator creation was visually inspected on desktop in dark mode, and the username dialog was inspected on mobile. Existing demo account usernames and passwords were not modified by these tests.


## Account lifecycle extension

All 221 backend tests passed: 167 original tests plus 13 password, 18 account-management and 23 lifecycle additions. Configuration and migration-drift checks passed. Static and dynamic schemas validated and passed Redocly lint at 35 paths / 53 operations (3 public, 50 protected). Original operation definitions remain, with a backward-compatible capability-field extension on the newer admin directory.

All four Newman collections passed in an isolated framework database: original 45 requests / 46 assertions, password 11 / 13, account-management 19 / 21, and lifecycle 22 / 24. Total: 97 requests / 104 assertions, zero failures. Existing demo accounts were not deleted or deactivated by these collections.

The lifecycle browser story checks disabled self controls, cancellation, admin/staff deactivation, denied inactive-account login, reactivation, wrong deletion passwords, permanent deletion, and absence after reload. The first iteration exposed unnecessary full clinical-data refreshes after account mutations; account writes now refresh only the two directories. Stable callbacks keep initial session loading from repeating on renders. Final browser results are recorded below after this repair.

DELETE confirmation requires the acting administrator's password, keeps validation errors visible and does not close until the action succeeds. The service serializes admin lifecycle mutations, rechecks the active actor, revokes database sessions, prevents self/last-admin removal and mixed-role bypass, and protects system administrators. Medical-record preservation and unrelated-session preservation are covered by backend tests. See `ACCOUNT-LIFECYCLE.md`.


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
