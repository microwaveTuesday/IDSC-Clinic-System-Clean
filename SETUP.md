# IDSC Clinic System — Developer Setup Guide

This guide describes the verified **midterm integration setup** for the Clinic module on `fix/pre-main-integration`.

The current backend deliberately separates **Clinic business data** from **Django framework infrastructure**:

```text
HTTP route
   |
   v
DRF view/controller
   |
   v
ClinicService
   |
   v
MockClinicRepository
   |
   v
in-memory Clinic business records
```

Django still uses a small local SQLite database for authentication, groups, permissions, sessions, and admin support.

---

## 1. Current Runtime Architecture

### Clinic business data

The midterm default is:

```text
CLINIC_DATA_BACKEND=mock
```

Clinic-owned business resources are held in `MockClinicRepository`:

- `HealthRecord`
- `Consultation`
- `HealthStatus`
- `MedicineDispensation`

They are **not persisted through Django ORM during the midterm workflow**.

### Django framework database

The default database engine is SQLite.

Its default file is:

```text
backend/framework.sqlite3
```

SQLite is used only for Django framework infrastructure such as:

- authentication;
- `CLINIC_ADMIN` and `CLINIC_STAFF` groups;
- permissions;
- sessions;
- admin support; and
- migration bookkeeping.

The SQLite file is ignored by Git.

### Finals database direction

PostgreSQL is an **opt-in finals configuration**, not the midterm default.

PostgreSQL support uses:

```text
backend/requirements-finals.txt
```

and environment variables such as:

```ini
DB_ENGINE=django.db.backends.postgresql
POSTGRES_DB=clinic_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=<local-development-password>
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

Do not switch to the finals database mode unless the team intentionally begins the database-backed finals repository work.

---

## 2. Domain Ownership

The setup must preserve the College Management System ownership boundaries.

### Registrar owns

- student identity;
- student profile;
- course and section; and
- `student_id`.

Clinic consumes Registrar student information through an integration boundary.

`student_id` is a **Registrar-owned opaque external identifier**. Clinic does not generate student identities and does not own student lifecycle CRUD.

### Clinic owns

- `HealthRecord`;
- `Consultation`;
- `HealthStatus`; and
- `MedicineDispensation`.

### Inventory owns

- medicine catalog;
- medicine stock;
- `medicine_id`; and
- Inventory stock transactions.

Clinic records Inventory transaction identifiers only for orchestration, audit, compensation, and rollback.

### Faculty and Student Portal

Clinic exposes restricted read-only health-status projections to Faculty and Student Portal.

---

## 3. Prerequisites

Install:

- Git
- Python 3.13-compatible environment
- Node.js and npm for Newman/frontend workflows
- VS Code or another editor

Docker and PostgreSQL are **not required for the current midterm mock-data workflow**.

They are only relevant if the team intentionally switches to the finals PostgreSQL configuration.

---

## 4. Clone and Open the Project

```powershell
git clone https://github.com/microwaveTuesday/IDSC-Clinic-System-Clean.git
cd IDSC-Clinic-System-Clean
```

For integration work, use the reviewed integration branch rather than `main`:

```powershell
git switch fix/pre-main-integration
```

Never push directly to `main`.

---

## 5. Create and Activate the Virtual Environment

From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

A successful activation shows:

```text
(.venv)
```

in the PowerShell prompt.

---

## 6. Install Midterm Backend Dependencies

```powershell
pip install -r backend\requirements.txt
```

The midterm dependency set includes:

- Django
- Django REST Framework
- django-cors-headers
- python-dotenv
- drf-spectacular

`psycopg` is intentionally excluded from the normal midterm requirements.

For the finals PostgreSQL direction only:

```powershell
pip install -r backend\requirements-finals.txt
```

---

## 7. Environment Configuration

The backend loads optional environment values from:

```text
backend/.env
```

A minimal local midterm configuration can be:

```ini
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CLINIC_DATA_BACKEND=mock
DB_ENGINE=django.db.backends.sqlite3
DB_NAME=framework.sqlite3
```

The defaults already select `mock` Clinic data and SQLite framework infrastructure, so these values are mainly useful when making the local configuration explicit.

Do not commit `.env` secrets.

---

## 8. Initialize Django Framework Infrastructure

The first local run needs Django's framework tables for authentication and sessions.

For the midterm workflow, apply only the framework/authentication migrations:

```powershell
cd backend

python manage.py migrate contenttypes --noinput
python manage.py migrate auth --noinput
python manage.py migrate admin --noinput
python manage.py migrate sessions --noinput
python manage.py migrate authentication --noinput
```

The `authentication` migration creates the required Clinic roles:

- `CLINIC_ADMIN`
- `CLINIC_STAFF`

### Why the migrations are targeted

The repository retains Clinic ORM migrations for the finals database direction, but Clinic business data currently uses `MockClinicRepository`.

Therefore, the verified midterm integration workflow intentionally keeps Clinic domain migrations unapplied.

You can inspect migration state with:

```powershell
python manage.py showmigrations
```

Expected architectural result:

```text
Django framework/authentication migrations -> applied
Clinic domain migrations                   -> unapplied for midterm runtime
CLINIC_DATA_BACKEND                        -> mock
```

---

## 9. Create a Local Clinic Administrator

Session-authenticated API testing requires a Django user with the correct Clinic role.

The Postman collection contains local development variables named:

```text
username
password
```

The validated Newman flow uses a local account matching those variables and assigned to `CLINIC_ADMIN`.

You may create the account through Django shell or another controlled local setup process. Do not commit local credentials.

Verify the account is:

- active;
- able to authenticate with the Postman collection credentials; and
- a member of `CLINIC_ADMIN`.

---

## 10. Run Django System Checks

From `backend`:

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
```

Verified integration expectations:

```text
System check identified no issues
No changes detected
```

---

## 11. Run Automated Tests

From `backend`:

```powershell
python manage.py test --verbosity 1
```

Verified permanent baseline:

```text
Found 167 test(s).
Ran 167 tests
OK
```

The Django test runner creates and destroys its own test database.

---

## 12. Start the Backend

From `backend`:

```powershell
python manage.py runserver 127.0.0.1:8000
```

The local backend is then available at:

```text
http://127.0.0.1:8000
```

---

## 13. Canonical Runtime Routes

| Purpose | Route |
|---|---|
| API discovery | `/` |
| Authentication namespace | `/api/auth/` |
| Business API namespace | `/api/v1/` |
| Canonical health endpoint | `/api/v1/health` |
| Dynamic OpenAPI schema | `/api/schema/` |
| Canonical Swagger UI | `/docs` |
| ReDoc | `/api/schema/redoc/` |
| Django admin | `/admin/` |

Canonical health request:

```http
GET /api/v1/health
```

Exact response:

```json
{
  "status": "ok"
}
```

A runtime `/api/v1/health/` compatibility alias may respond successfully, but `/api/v1/health` is the canonical OpenAPI operation.

---

## 14. Authentication Flow

The backend uses Django session authentication.

Public operations are:

```text
GET  /api/auth/csrf/
POST /api/auth/login/
GET  /api/v1/health
```

Protected requests use the `sessionid` cookie.

Unsafe session-authenticated requests also require CSRF protection.

Typical browser/Postman flow:

```text
GET /api/auth/csrf/
    -> receive csrftoken

POST /api/auth/login/
    -> send credentials + CSRF token
    -> receive authenticated session

protected /api/v1/... requests
    -> send session cookie
    -> include CSRF token on unsafe methods

POST /api/auth/logout/
    -> terminate session
```

---

## 15. CORS and Frontend Development

Credentialed CORS is restricted to:

```text
http://localhost:5173
http://127.0.0.1:5173
```

These origins are also trusted CSRF origins.

Do not disable CSRF and do not enable wildcard credentialed CORS just to simplify development.

The currently committed frontend is still a React/Vite starter and is not evidence of the final Clinic high-fidelity interface.

---

## 16. OpenAPI and Swagger Verification

Open the canonical Swagger UI:

```text
http://127.0.0.1:8000/docs
```

Dynamic schema:

```text
http://127.0.0.1:8000/api/schema/
```

Verified contract baseline:

```text
OpenAPI version    = 3.1.0
Paths              = 29
Operations         = 45
Public operations  = 3
Protected          = 42
```

The canonical static contract is:

```text
openapi.yaml
```

---

## 17. Postman and Newman

The collection is:

```text
postman/IDSC-Clinic-System.postman_collection.json
```

Canonical collection base URL:

```text
http://127.0.0.1:8000
```

With the backend running and the local Clinic admin provisioned:

```powershell
npx --yes newman run .\postman\IDSC-Clinic-System.postman_collection.json
```

Verified baseline:

```text
Requests executed = 45
Request failures  = 0
Test scripts      = 45
Assertions        = 46
Assertion failures = 0
```

---

## 18. Problem Details Errors

API errors use RFC-style Problem Details with:

```json
{
  "type": "https://clinic.example/problems/example",
  "title": "Example",
  "status": 400,
  "detail": "Human-readable explanation.",
  "instance": "/api/v1/example/",
  "code": "example_code"
}
```

Validation responses may additionally contain an `errors` object.

Verified status families include:

- `400`
- `401`
- `403`
- `404`
- `409`
- `422`

---

## 19. Repository Hygiene

Do not commit local runtime artifacts such as:

- `.venv/`
- `.env`
- `*.sqlite3`
- `__pycache__/`
- `.idea/`
- generated temporary reports

The cleaned integration baseline also excludes the obsolete root `main.py` and generated `gen/` client.

Before committing:

```powershell
git status --short
git diff --check
```

---

## 20. Finals PostgreSQL Direction

PostgreSQL is retained as the finals direction, not the active midterm default.

When the team intentionally begins the database-backed Clinic repository:

1. install `backend/requirements-finals.txt`;
2. configure `DB_ENGINE=django.db.backends.postgresql`;
3. configure the `POSTGRES_*` or equivalent `DB_*` variables;
4. implement/activate a database-backed Clinic repository behind `ClinicService`;
5. review the retained Clinic ORM migrations;
6. apply Clinic migrations only as part of that intentional finals transition;
7. rerun the full automated, OpenAPI, runtime, and integration test gates.

Do not silently switch the midterm API from mock storage to ORM persistence.

---

## 21. Normal Midterm Development Workflow

### Terminal 1 — Backend

```powershell
cd backend
..\.venv\Scripts\Activate.ps1
```

If the virtual environment is already active, skip the activation command.

Then:

```powershell
python manage.py check
python manage.py runserver 127.0.0.1:8000
```

### Terminal 2 — Frontend

```powershell
cd frontend
npm install
npm run dev
```

### Optional API regression

From the repository root:

```powershell
npx --yes newman run .\postman\IDSC-Clinic-System.postman_collection.json
```

---

## 22. Verification Checklist

Before considering the local integration environment healthy:

- [ ] virtual environment is active;
- [ ] midterm backend dependencies are installed;
- [ ] `CLINIC_DATA_BACKEND` resolves to `mock`;
- [ ] SQLite framework infrastructure is initialized;
- [ ] `CLINIC_ADMIN` and `CLINIC_STAFF` groups exist;
- [ ] a local Clinic admin can authenticate;
- [ ] Clinic domain migrations remain unapplied for the midterm runtime;
- [ ] `python manage.py check` passes;
- [ ] all 167 Django tests pass;
- [ ] `GET /api/v1/health` returns exactly `{"status":"ok"}`;
- [ ] `/docs` loads Swagger UI;
- [ ] `/api/schema/` reports OpenAPI 3.1.0;
- [ ] the Postman/Newman collection completes 45 requests and 46 assertions with zero failures;
- [ ] Git working tree contains no accidental runtime artifacts.

---

## 23. Git Integration Rules

The project integration baseline requires:

- `phase7/tests-contract-validation` remains the canonical source branch to preserve;
- legacy feature branches are historical/reference only;
- integration fixes happen on `fix/pre-main-integration`;
- never push directly to `main`;
- protect `main`;
- merge only through a reviewed Pull Request;
- require teammate approval before the final merge.

These rules are part of the release process, not optional workflow suggestions.
