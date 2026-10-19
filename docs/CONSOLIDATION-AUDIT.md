# Repository audit and consolidation

Audit date: 17 October 2026 (Asia/Manila). All comparisons use fetched immutable commit IDs below.

## Decision

Use clean `fix/pre-main-integration` (195580e) as the backend/contract baseline. Clean `main` (f37fd5c) has an identical tree and already merged that branch. Phase 7 (1664cd5) is a test/contract milestone, but the later verified integration adds the documented mock service/repository architecture and schema normalization. Preserve the later runtime and all 167 tests.

Legacy `feature/idsc-clinic-ui` (de0246d) is the strongest frontend component source: responsive clinic layout, student details, health editors, medicine projection, settings, staff management and accessible dialogs. Its TSX demo is disconnected from the JSX entry and uses simulated credentials/local mutations; reuse the layout selectively and replace every data/mutation boundary. Do not merge its backend.

## Every remote branch

| Ref | Commit | Ancestor of baseline | Files differing from baseline |
|---|---|---|---:|
| `legacy/feat/update-student-crud` | `1fdc0a0` | False | 135 |
| `legacy/feature/dashboard-reports` | `4e6bab1` | False | 71 |
| `legacy/feature/idsc-clinic-ui` | `de0246d` | False | 142 |
| `legacy/feature/inventory-registrar-integration` | `227a820` | False | 71 |
| `legacy/feature/medicine-dispensing` | `81efff0` | False | 69 |
| `legacy/feature/session-authentication` | `d34dbf7` | True | 68 |
| `legacy/for-faculty-student-portal-api-endpoints` | `a4d5c57` | False | 149 |
| `legacy/main` | `aab84b2` | True | 133 |
| `origin/cleanup/integration-baseline` | `4d9e85c` | True | 131 |
| `origin/feat/update-student-crud` | `1fdc0a0` | False | 135 |
| `origin/feature/dashboard-reports` | `4e6bab1` | False | 71 |
| `origin/feature/inventory-registrar-integration` | `227a820` | False | 71 |
| `origin/feature/medicine-dispensing` | `81efff0` | False | 69 |
| `origin/feature/session-authentication` | `d34dbf7` | True | 68 |
| `origin/fix/pre-main-integration` | `195580e` | True | 0 |
| `origin/for-faculty-student-portal-api-endpoints` | `7577aed` | False | 139 |
| `origin/main` | `f37fd5c` | False | 0 |
| `origin/phase4/domain-backend-structure` | `0146556` | True | 125 |
| `origin/phase5/midterm-mock-api` | `618447d` | True | 123 |
| `origin/phase6/auth-permissions-errors` | `1a4d9d7` | True | 119 |
| `origin/phase7/tests-contract-validation` | `1664cd5` | True | 111 |

## Relevant component history

| Branch family | Finding / disposition |
|---|---|
| session-authentication | Same d34dbf7 in both repos; historical session foundation, superseded by verified authentication/CSRF/role tests. |
| medicine-dispensing | Same 81efff0; historical inventory/dispensing work, superseded by compensation and rollback service tests. |
| update-student-crud | Same 1fdc0a0; legacy student ownership conflicts with Registrar projection contract. Do not import student writes. |
| inventory-registrar-integration | Same 227a820; valuable boundary concepts already incorporated in clean service implementations. |
| dashboard-reports | Same 4e6bab1; strongest historical legacy backend feature set, but clean baseline includes all four reports and stronger tests. |
| faculty/student-portal | Clean 7577aed vs legacy a4d5c57; legacy adds documentation/ERD files, no newer runtime fix. Preserve restricted projection in clean baseline. |
| cleanup, phases 4–6 | Successive clean architecture/auth milestones, ancestors of Phase 7 and verified integration. Do not revert later fixes. |
| legacy main | aab84b2: older API/student CRUD baseline; lacks canonical layering, permissions coverage, contract and test collection. |

## Documentation reconciliation

- Synced Word README agrees with 29 paths / 45 operations, session+CSRF, Registrar/Inventory ownership and mock business storage. Preserve these exactly.
- Handout scope explicitly excludes student identity writes and medicine master/stock management; several older backlog stories contradict that scope. UI offers student/medicine reads and Clinic-owned medical writes only.
- Handout architecture mentions PostgreSQL persistence; verified README and presentation describe a midterm mock runtime. This integration deliberately preserves the verified API/runtime. Persistent business storage and real external Registrar/Inventory connectors remain separate finals work, not silently claimed complete.
- Legacy ERD is historical evidence: shared ownership/older schema must not overwrite canonical external-identifier model.
- The presentation and Word documents report frontend/API integration pending. This branch updates that status with runnable flows and current verification evidence. Synced sources remain untouched.

## Safe consolidation plan and implementation

1. Create `integration/clinic-final` from verified 195580e; compare against main to confirm equivalent base tree.
2. Import only legacy clinic layout/CSS/logo; keep one JSX entry, remove demo seed data and unused starter styling.
3. Route all data through credentialed API client with fresh CSRF token for unsafe requests; retain server permissions, pagination envelopes and Problem Details.
4. Connect health-record, consultation, status and staff editors; add dispensing/rollback and all four reports. Show backend errors and prevent repeated submissions.
5. Run preserved backend tests, schema and migration checks, frontend lint/build, browser integration and Newman. Review evidence before PR; no main push, force push or wholesale legacy merge.

## Operational limits

Business records and mock inventory are process memory and reset on backend restart. Use one backend process for a consistent school demo. Django accounts/sessions use SQLite. Production deployment, durable clinical storage, real external services, instructor Figma sign-off, branch protection and teammate approval are separate release gates. The local Vite proxy supports authenticated development; production must serve the UI and `/api` under one origin or provide an equivalent reverse proxy.
