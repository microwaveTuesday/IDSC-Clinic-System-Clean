# IDSC Clinic Management System

School final project: a React/Vite clinic website connected to a Django API, with Owner/Admin/Staff accounts and mock Registrar/Inventory workspaces.

Current branch: [improvement/clinic-final-10of10](https://github.com/corpeadmin/IDSC-Clinic-System/tree/improvement/clinic-final-10of10). Branch selection history: [CONSOLIDATION-AUDIT.md](docs/CONSOLIDATION-AUDIT.md). Use a reviewed PR for changes to main.

## Run in VS Code

Full instructions: [SETUP.md](SETUP.md). From the project root in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements.txt
cd backend
$env:CLINIC_DATA_BACKEND="database"
python manage.py migrate --noinput
python manage.py runserver 127.0.0.1:8002
```

Keep Django running. Open another terminal at the project root:

```powershell
cd frontend
npm ci
npm run dev
```

Open the Vite address, normally [http://localhost:5173](http://localhost:5173). Vite forwards `/api` to `http://127.0.0.1:8002`. Both servers must run. Keep the browser hostname consistent because localhost and 127.0.0.1 use separate cookies.

A fresh database shows **Register the system Owner**. Creation signs in automatically and opens Dashboard. Logout and later visits show the shared Owner/Admin/Staff login. Existing installations keep their Owner; registration stays closed. There is no committed default password. Optional CLI first setup with `createsuperuser` also closes registration. The API and database block a second Owner. See [OWNER-REGISTRATION.md](docs/OWNER-REGISTRATION.md).

## Roles and account management

| Capability | Owner | Admin | Staff |
| --- | --- | --- | --- |
| Clinic features, dispensing/rollback and reports | Yes | Yes | Yes |
| Request restocks and read Inventory notifications | Yes | Yes | Yes |
| Create/edit/activate/deactivate/delete Staff | Yes | Yes | No |
| List/create/edit/activate/deactivate/delete Admins | Yes | No | No |
| Delete clinical records and dispensing history | Yes | Yes | No |
| Operate Mock Registrar/Inventory and fulfill restocks | Yes | No | No |
| Change own username/password in Settings | Yes | Yes | Yes |
| Delete/deactivate/demote registered Owner | No | No | No |

Permissions are enforced by the backend, including direct API requests. Owner is the single Django superuser; Admin/Staff use CLINIC_ADMIN/CLINIC_STAFF. Django is_staff is not the clinic role.

- Maximum **five Admin accounts**, including inactive accounts and excluding Owner. Delete one to free capacity; deactivation does not free it. Owner can remove the last regular Admin.
- Staff management has search and Previous/Next controls, maximum **ten accounts per page**, enforced by the API.
- Admin creation verifies the Owner password. Account deletion verifies the acting user's current password. Deactivation revokes sessions; reactivation requires fresh login. Account deletion preserves medical records.
- Username/password changes verify the current password. New passwords must match confirmation, differ from the current password and pass Django validators. Password changes retain the current session; other sessions expire on their next request.
- Light/dark mode is available. Password dialogs retain typing focus during background refresh.

Details: [roles](docs/ROLE-HIERARCHY.md), [account limits](docs/ACCOUNT-LIMITS.md), [account management](docs/ACCOUNT-MANAGEMENT.md), [lifecycle](docs/ACCOUNT-LIFECYCLE.md), [password changes](docs/PASSWORD-CHANGE.md).

## Students and clinical records

Registrar owns student identity, course, section and enrollment status. **Get student** accepts only the Registrar student ID and opens the current profile without duplicating identity. Owner adds/edits students and enrollment status in **Mock Registrar**. The website refreshes projections every five seconds and on focus.

Only ACTIVE students can receive new health records, consultations, health statuses or medicine dispensations. GRADUATED, DROPPED_OUT and INACTIVE students retain readable history, but the API rejects new records even from an already-open form. Returning to ACTIVE restores eligibility.

Health-record and consultation display numbers are consecutive per student and recompute after deletion. Internal API IDs remain stable and are never renumbered/reused. Display #1 is a position, not an API identifier.

## Medicine stock and restocking

Inventory owns catalog, stock and transactions. Owner uses **Mock Inventory** to add/edit medicines and stock or delete unused medicines. Transactions or pending restocks prevent deletion; use INACTIVE where history must remain.

New medicines appear in the Clinic projection. Catalog changes/deliveries generate notifications with separate read receipts per user. Users request ALL active medicines with a quantity per medicine, or SELECTED medicines with individual quantities. Requests remain PENDING until Owner fulfills them in Mock Inventory. Fulfillment validates all lines before changing stock and prevents duplicate delivery.

Dispensing reduces stock. **Roll back** returns stock and marks the entry ROLLED_BACK. **Delete dispensing history** removes the Clinic entry only: it does not restore stock or remove Inventory transactions. Reports reflect remaining history. See [EXTERNAL-WORKFLOWS.md](docs/EXTERNAL-WORKFLOWS.md).

## Architecture, storage and limitations

```text
React -> Django API -> ClinicService -> MockClinicRepository
                           |       |
                       Registrar Inventory
                       mock      mock
```

| Data | Storage | Backend restart |
| --- | --- | --- |
| Accounts, hashes, roles, sessions, permanent Owner registration | Django database; SQLite default | Retained |
| Clinic records, consultations, statuses, dispensing history | Process memory | Reset |
| Mock Registrar profiles/status edits | Process memory | Reset |
| Mock Inventory catalog/stock/transactions, restocks, notifications | Process memory | Reset |

Browser reloads retain server state. Default startup loads sample data. Private `backend/.env` option `CLINIC_EMPTY_START=1` starts all mock stores empty on each restart; it does not erase accounts or reopen registration. Populate through Owner mock workspaces. Use one backend process for demonstrations.

Set CLINIC_DATA_BACKEND=database to select the tested persistent ORM repository on SQLite or PostgreSQL. Health records, consultations, health statuses and dispensations then survive backend restarts. Keep CLINIC_DATA_BACKEND=mock for isolated demonstrations. Registrar/Inventory identities and stock remain external, process-local mocks. See [DATABASE.md](docs/DATABASE.md).

Real Registrar/Inventory adapters are not implemented. Adding a URL alone cannot connect them. See [REAL-SYSTEM-INTEGRATION.md](docs/REAL-SYSTEM-INTEGRATION.md). Faculty/Student Portal demonstration routes require active Clinic roles; real provider/student identity binding is unavailable.

## API and documentation

| Item | Value |
| --- | --- |
| Namespaces | /api/auth/ and /api/v1/ |
| Static contract | [openapi.yaml](openapi.yaml) |
| Runtime schema | http://127.0.0.1:8002/api/schema/ |
| Swagger / ReDoc | http://127.0.0.1:8002/docs and /api/schema/redoc/ |
| OpenAPI 3.1.0 inventory | 45 paths; 72 operations; 5 public; 67 protected |
| Health | GET /api/v1/health returns exactly {"status":"ok"} |

Public operations: health, CSRF acquisition, login, setup status and first-Owner registration. Registration only works before setup. Login/registration still require CSRF. Other operations require a session and appropriate role. Unsafe requests use X-CSRFToken; the frontend includes cookies and obtains fresh tokens before writes.

[API.md](API.md) lists all operations/access rules. Errors use Problem Details with type/title/status/detail/instance/code and optional field errors. General paginated lists default to 20/max 100; Staff accounts default/max 10. Admin directory is unpaginated and limited by the five-account rule.

## Validation

Inside backend with the virtual environment active:

```powershell
$env:CLINIC_EMPTY_START="0"
$env:CLINIC_DATA_BACKEND="mock"
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test --noinput
python manage.py spectacular --file ../schema.generated.yaml --validate
```

Inside frontend:

```powershell
npm run lint
npm run build
npx playwright install chromium
```

Browser tests mutate accounts/data. Use disposable databases and credentials; [frontend/README.md](frontend/README.md) explains first-run setup and special fixtures. Configure local credentials/base URL for collections in postman/.

Latest improvement evidence (20 October 2026): baseline273 tests passed; expanded PostgreSQL suite294 passed with normal hashing. SQLite294 discovered:292 passed and2 PostgreSQL-only concurrency tests skipped. Six Newman collections:173 requests/190 assertions, zero failures. Browser stories, PostgreSQL/application restart persistence, production configuration, dependency advisories, frontend lint/build, schemas and accessibility checks are detailed in [IMPROVEMENT-VALIDATION.md](docs/IMPROVEMENT-VALIDATION.md). Failed intermediate checks and their fixes are recorded there.

Conditional database writes use If-Match or X-Record-Version. Optional Idempotency-Key receipts protect coordinated mutations; the frontend deduplicates inflight writes and retries a network failure with the same key for60 seconds. Audit logs retain metadata without passwords/medical bodies. Unresolved partial Inventory failures create operator reconciliation incidents; inspect them in Owner's Django administration. See [DEPLOYMENT.md](docs/DEPLOYMENT.md), [FINAL-DEMO.md](docs/FINAL-DEMO.md) and [KNOWN-LIMITATIONS.md](docs/KNOWN-LIMITATIONS.md).

## Files and further reading

- backend/authentication/: sessions, roles, accounts, Owner registration.
- backend/clinic/: API, services, repository, mocks and tests.
- frontend/src/ and frontend/tests/: website and Playwright workflows.
- postman/: original and feature collections.
- [Architecture](docs/architecture.md), [domain model](docs/data-model.md), [integration sequences](docs/integration.md), [design system](docs/design-system.md).

Keep credentials, .env, databases/backups, virtual environments, dependencies and generated outputs out of Git. Use the submission branch and a reviewed PR for main.
