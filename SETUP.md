# Run the clinic project in VS Code

Applies to `improvement/clinic-final-verification` in microwaveTuesday/IDSC-Clinic-System-Clean. See [README.md](README.md) for features and storage limits.

## Open the project

Use Python 3.13, Node.js/npm compatible with the frontend lockfile, Git and VS Code. Validation used Python 3.13 and Node 24. Docker/PostgreSQL are not required for the mock runtime.

For a new checkout:

```powershell
git clone --branch improvement/clinic-final-verification https://github.com/microwaveTuesday/IDSC-Clinic-System-Clean.git
cd IDSC-Clinic-System-Clean
code .
```

If you already have the Desktop copy, open that folder instead. Commands below start at the project root unless stated otherwise.

## Backend: first terminal

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements.txt
cd backend
$env:CLINIC_DATA_BACKEND="database"
$env:INVENTORY_BACKEND="durable_mock"
python manage.py migrate --noinput
python manage.py check
python manage.py runserver 127.0.0.1:8002
```

Apply all committed migrations. Back up existing databases before migration. The singleton-Owner migration adopts an existing Owner and retains extra legacy Owners as inactive Staff. See [OWNER-REGISTRATION.md](docs/OWNER-REGISTRATION.md). Clinic ORM tables may exist, and CLINIC_DATA_BACKEND selects mock memory or database persistence.

If PowerShell blocks activation, use `.venv\Scripts\python.exe` from the root, or `..\.venv\Scripts\python.exe` inside backend, instead of python. Activation is optional when invoking the interpreter directly.

## Frontend: second terminal

Keep Django running. Open another terminal at the project root:

```powershell
cd frontend
npm ci
npm run dev
```

Open Vite's address, normally http://localhost:5173. Keep the hostname consistent: localhost and 127.0.0.1 have separate cookies. Both origins on port 5173 are approved. If Vite selects another port, stop the duplicate process or explicitly configure the new origin in Django CORS/CSRF settings.

## First Owner and later login

A fresh database shows **Register the system Owner**. Username, strong password and confirmation are required; names/email are optional. Registration signs in and opens Dashboard. Logout shows shared login. A second Owner is blocked by the API and database.

Existing installations keep their Owner and show login. There is no default committed Owner account/password. Change your credentials in Settings. For authorized local recovery use `python manage.py changepassword <username>`; keep the database intact. Optional CLI first setup with `createsuperuser` can provision the single Owner before opening the website.

Owner manages up to five Admins and all Staff. Admins manage Staff only. See [ROLE-HIERARCHY.md](docs/ROLE-HIERARCHY.md).

## Optional local environment

Private `backend/.env`, ignored by Git:

```ini
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CLINIC_DATA_BACKEND=database
INVENTORY_BACKEND=durable_mock
DB_ENGINE=django.db.backends.sqlite3
DB_NAME=framework.sqlite3
CLINIC_EMPTY_START=0
```

DB_NAME is relative to backend unless absolute. Accounts, permanent Owner registration and sessions persist there. Clinic data persists with CLINIC_DATA_BACKEND=database; mock Clinic/Registrar and default Inventory reset on restart; optional durable_mock Inventory persists. Empty-start 0 loads samples; 1 starts mock records/students/medicines empty. Owner populates the mock workspaces. This setting does not clear accounts.

For a fresh-registration demonstration, use a separate new database. Set DB_NAME to an unused test filename before migration and start the isolated backend on another port.

To change Vite's backend target, set it before starting Vite:

```powershell
$env:CLINIC_API_TARGET="http://127.0.0.1:8001"
npm run dev
```

Start Django on the same port. Restart Vite after target changes. This target is the Clinic backend, not an external Registrar/Inventory URL.

## Daily start

Optional durable_mock uses backend/mock-inventory.sqlite3, separate from Clinic.
Back up both with writes stopped. Default Inventory remains mock when the setting
is omitted. Registrar remains process-local. See docs/INVENTORY-RECOVERY.md,
docs/BACKUP-RESTORE.md and docs/DEPLOYMENT.md for HTTPS container startup.

Backend terminal: activate the environment, enter backend, run `python manage.py runserver 127.0.0.1:8002`. Frontend terminal: enter frontend and run `npm run dev`. Apply new migrations after updates. Ctrl+C stops each server. Browser reload retains mock state; backend restart resets process-local mocks, while database Clinic and optional durable_mock Inventory persist.

## Validation

Inside backend:

```powershell
$env:CLINIC_EMPTY_START="0"
$env:CLINIC_DATA_BACKEND="mock"
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test --noinput
python manage.py spectacular --file ../schema.generated.yaml --validate
```

The runner creates/removes a test database. The inherited baseline had 294 tests; current counts are in docs/VERIFICATION-RESULTS.md; normal password hashing can take several minutes. See [CURRENT-VALIDATION.md](docs/CURRENT-VALIDATION.md) for recorded conditions.

Inside frontend:

```powershell
npm run lint
npm run build
npx playwright install chromium
```

Read [frontend/README.md](frontend/README.md) before browser tests: they mutate accounts/data and need disposable Owner credentials, seeded mocks and special fixtures. First-registration tests need a separate unclaimed database.

Open http://127.0.0.1:8002/docs with Django running. Runtime schema: `/api/schema/`; ReDoc: `/api/schema/redoc/`. Static [openapi.yaml](openapi.yaml) has 45 paths, 72 operations, 5 public/67 protected. Canonical health `GET /api/v1/health` returns exactly `{"status":"ok"}`. See [API.md](API.md).

Import collections from postman/ into Postman. Set baseUrl to http://127.0.0.1:8002 and disposable local credentials. The original collection has 45 requests; feature collections cover passwords, accounts, roles and external workflows. Historical results are linked from [CURRENT-VALIDATION.md](docs/CURRENT-VALIDATION.md).

## Troubleshooting

| Symptom | Check |
| --- | --- |
| Setup/login cannot load | Both servers running; Vite target matches Django port |
| Login works on one hostname only | Keep localhost or 127.0.0.1 consistent; cookies differ |
| CSRF 403 | Approved origin, retained cookies and fresh token before writes; keep CSRF enabled |
| Login appears instead of registration | Database has an Owner or completed registration latch |
| Empty students/medicines | Empty-start setting; populate Owner mock workspaces |
| Records disappear after Django restart | Business storage is in memory; accounts persist separately |
| Cannot create clinical record | Registrar must currently mark student ACTIVE |
| Cannot add Admin | Owner only; five accounts including inactive is the maximum |
| Cannot remove Owner | Intentional protection; edit own credentials in Settings |

## Remaining work and Git

Real external adapters remain future work. Persistent Clinic storage is now implemented: select CLINIC_DATA_BACKEND=database and migrate. See [DATABASE.md](docs/DATABASE.md). See [REAL-SYSTEM-INTEGRATION.md](docs/REAL-SYSTEM-INTEGRATION.md).

Keep credentials, .env, databases, backups, virtual environments and generated outputs out of commits. Use the submission branch and a reviewed PR for main.


## Persistent final-project mode

In backend/.env set CLINIC_DATA_BACKEND=database. SQLite works with the standard requirements and existing DB_NAME. For PostgreSQL install requirements-finals.txt and provide private DB_ENGINE/DB_NAME/DB_USER/DB_PASSWORD/DB_HOST/DB_PORT. Run all migrations before startup. Mock Registrar/Inventory workspaces remain available independently of Clinic persistence. See [DATABASE.md](docs/DATABASE.md) and [DEPLOYMENT.md](docs/DEPLOYMENT.md).
