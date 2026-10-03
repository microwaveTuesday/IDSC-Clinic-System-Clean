# IDSC Clinic System


The **IDSC Clinic System** is the Clinic module of the College Management System (CMS).


The system provides clinic-owned health information management, consultations, health statuses, medicine dispensation, reporting, authentication, and integrations with other CMS modules.


---


## 1. Project Overview


The Clinic backend is implemented using:


- Python

- Django

- Django REST Framework

- PostgreSQL

- drf-spectacular

- django-cors-headers


The frontend uses React and Vite.


### API baseline


| Item | Value |
|---|---|
| OpenAPI version | 3.1.0 |
| API paths | 29 |
| API operations | 45 |
| Public operations | 3 |
| Protected operations | 42 |
| Business API | `/api/v1/` |
| Authentication API | `/api/auth/` |
| OpenAPI schema | `/api/schema/` |
| Swagger UI | `/api/schema/swagger-ui/` |
| ReDoc | `/api/schema/redoc/` |
| Django Admin | `/admin/` |


### Verification baseline


| Evidence | Result |
|---|---:|
| Permanent Django tests | 167 |
| Permanent Django tests passed | 167 |
| Permanent Django tests failed | 0 |
| Postman requests | 45 |
| Newman requests executed | 45 |
| Newman failed requests | 0 |
| Newman assertions | 46 |
| Newman failed assertions | 0 |


---


## 2. System Scope and Domain Ownership


### Registrar


The Registrar owns:


- Student identity

- Student profile

- Course and section

- `student_id`


The Clinic consumes student information through the Registrar integration. The current implementation uses `MockRegistrarService` with deterministic student data; it does not call a live Registrar API.


### Clinic


The Clinic owns:


- Health records

- Consultations

- Health statuses

- Medicine dispensations

- Clinic reports

- Clinic user management


### Inventory


Inventory owns:


- Medicine catalog

- Medicine stock

- `medicine_id`

- `inventory_transaction_id`


The Clinic references Inventory-owned medicine information rather than owning the inventory stock domain. The current implementation uses `MockInventoryService` with deterministic in-memory medicine data, stock, and transactions; it does not call a live Inventory API. Mock stock and transactions reset when the service is recreated.


### Student Portal and Faculty


The Clinic provides read-only health-status integration projections for:


- Student Portal

- Faculty


---


## 3. Technology Stack


### Backend


- Python

- Django

- Django REST Framework

- drf-spectacular

- django-cors-headers

- psycopg

- python-dotenv


### Database


- PostgreSQL


### Frontend


- React

- Vite

- JavaScript / JSX


### API and development tooling


- Git

- Postman

- Newman

- Swagger UI

- ReDoc


---


## 4. System Architecture


```text

React / Vite Frontend

        |

        | HTTP / JSON

        v

Django + Django REST Framework

        |

        +------------------------------+

        |                              |

        v                              v

Clinic Domain                   External Integrations

        |                       Registrar

        |                       Inventory

        |                       Student Portal

        |                       Faculty

        v

PostgreSQL

```


---


## 5. Repository Structure


```text

IDSC-Clinic-System-Clean/

|

+-- backend/

|   +-- authentication/

|   +-- clinic/

|   +-- config/

|   +-- manage.py

|   +-- requirements.txt

|

+-- docs/

|   +-- TEST-EVIDENCE.md

|

+-- frontend/

|

+-- gen/

|

+-- openapi.yaml

+-- README.md

+-- API.md

+-- SETUP.md

```


---


## 6. Backend Configuration


The backend uses Django settings located at:


`backend/config/settings.py`


Important configuration includes:


- Django REST Framework

- Session authentication

- CSRF middleware

- CORS support

- PostgreSQL database configuration

- OpenAPI schema generation

- Authentication and permission defaults


The default REST authentication class is:


`authentication.authentication.ClinicSessionAuthentication`


The default REST permission is:


`rest_framework.permissions.IsAuthenticated`


---


## 7. Database Architecture


The production-oriented database engine is PostgreSQL.


The Clinic domain uses Django ORM models and migrations.


Database ownership follows the Clinic domain boundary.


External identifiers are retained as integration references:


- `student_id`

- `medicine_id`

- `inventory_transaction_id`


The Clinic does not take ownership of Registrar or Inventory master data.


---


## 8. Clinic Domain Models


The principal Clinic-owned domain models are:


### HealthRecord


Stores student health-record information.


### Consultation


Stores clinic consultation / visit information.


### HealthStatus


Stores the student's current clinic health-status information.


### MedicineDispensation


Stores medicine dispensation transactions performed by the Clinic.


---


## 9. Authentication and Authorization


The system uses Django session authentication.


Authentication components include:


- CSRF token endpoint

- Login

- Logout

- Current-user endpoint

- Session authentication

- Clinic staff permissions

- Clinic administrator permissions


Permission classes include:


- `IsClinicStaff`

- `IsClinicAdmin`


Protected business endpoints require authentication.


Authorization is enforced through DRF permission classes and view-level permissions. `IsClinicStaff` accepts members of `CLINIC_STAFF` or `CLINIC_ADMIN`, and superusers. `IsClinicAdmin` accepts members of `CLINIC_ADMIN` and superusers. Logout, current-user information, and the Faculty and Student Portal projections require authentication without a Clinic role restriction.


---


## 10. API Architecture


The API is divided into two primary namespaces.


### Authentication API


```text

/api/auth/

```


Used for:


- CSRF token

- Login

- Logout

- Current-user information


### Business API


```text

/api/v1/

```


Used for:


- Clinic health data

- Consultations

- Health statuses

- Medicine operations

- Reports

- Integrations

- User management


---


## 11. API Endpoint Reference


The method and path inventory below is generated from `openapi.yaml`. Access labels also reflect the implementation permission classes described in Section 9.


### Authentication Endpoints

| Method | Endpoint | Access | Description |
|---|---|---|---|
| `GET` | `/api/auth/csrf/` | Public | Get CSRF token |
| `POST` | `/api/auth/login/` | Public | Log in to the Clinic system |
| `POST` | `/api/auth/logout/` | Authenticated | Log out of the Clinic system |
| `GET` | `/api/auth/me/` | Authenticated | Get current Clinic user |

### Health and Dashboard

| Method | Endpoint | Access | Description |
|---|---|---|---|
| `GET` | `/api/v1/health/` | Public | Check Clinic API health |
| `GET` | `/api/v1/dashboard/` | Clinic staff or administrator | Get Clinic dashboard |

### Student Integration

| Method | Endpoint | Access | Description |
|---|---|---|---|
| `GET` | `/api/v1/students/` | Clinic staff or administrator | List students |
| `GET` | `/api/v1/students/{student_id}/` | Clinic staff or administrator | Get student |

### Health Records

| Method | Endpoint | Access | Description |
|---|---|---|---|
| `GET` | `/api/v1/health-records/` | Clinic staff or administrator | List health records |
| `POST` | `/api/v1/health-records/` | Clinic staff or administrator | Create health record |
| `GET` | `/api/v1/health-records/{health_record_id}/` | Clinic staff or administrator | Get health record |
| `PUT` | `/api/v1/health-records/{health_record_id}/` | Clinic staff or administrator | Replace health record |
| `PATCH` | `/api/v1/health-records/{health_record_id}/` | Clinic staff or administrator | Partially update health record |
| `DELETE` | `/api/v1/health-records/{health_record_id}/` | Clinic staff or administrator | Delete health record |

### Consultations

| Method | Endpoint | Access | Description |
|---|---|---|---|
| `GET` | `/api/v1/consultations/` | Clinic staff or administrator | List consultations |
| `POST` | `/api/v1/consultations/` | Clinic staff or administrator | Create consultation |
| `GET` | `/api/v1/consultations/{consultation_id}/` | Clinic staff or administrator | Get consultation |
| `PUT` | `/api/v1/consultations/{consultation_id}/` | Clinic staff or administrator | Replace consultation |
| `PATCH` | `/api/v1/consultations/{consultation_id}/` | Clinic staff or administrator | Partially update consultation |
| `DELETE` | `/api/v1/consultations/{consultation_id}/` | Clinic staff or administrator | Delete consultation |

### Health Status

| Method | Endpoint | Access | Description |
|---|---|---|---|
| `GET` | `/api/v1/health-statuses/` | Clinic staff or administrator | List health statuses |
| `POST` | `/api/v1/health-statuses/` | Clinic staff or administrator | Create health status |
| `GET` | `/api/v1/health-statuses/{status_id}/` | Clinic staff or administrator | Get health status |
| `PUT` | `/api/v1/health-statuses/{status_id}/` | Clinic staff or administrator | Replace health status |
| `PATCH` | `/api/v1/health-statuses/{status_id}/` | Clinic staff or administrator | Partially update health status |
| `DELETE` | `/api/v1/health-statuses/{status_id}/` | Clinic staff or administrator | Delete health status |

### Medicine Integration

| Method | Endpoint | Access | Description |
|---|---|---|---|
| `GET` | `/api/v1/medicines/` | Clinic staff or administrator | List medicines |
| `GET` | `/api/v1/medicines/{medicine_id}/` | Clinic staff or administrator | Get medicine |

### Medicine Dispensation

| Method | Endpoint | Access | Description |
|---|---|---|---|
| `GET` | `/api/v1/medicine-dispensations/` | Clinic staff or administrator | List medicine dispensations |
| `POST` | `/api/v1/medicine-dispensations/` | Clinic staff or administrator | Dispense medicine |
| `GET` | `/api/v1/medicine-dispensations/{dispensation_id}/` | Clinic staff or administrator | Get medicine dispensation |
| `POST` | `/api/v1/medicine-dispensations/{dispensation_id}/rollback/` | Clinic staff or administrator | Roll back medicine dispensation |

### Reports

| Method | Endpoint | Access | Description |
|---|---|---|---|
| `GET` | `/api/v1/reports/clinic-visits/` | Clinic staff or administrator | Get clinic visits report |
| `GET` | `/api/v1/reports/health-records/` | Clinic staff or administrator | Get health records report |
| `GET` | `/api/v1/reports/medicine-inventory/` | Clinic staff or administrator | Get medicine inventory report |
| `GET` | `/api/v1/reports/medicine-dispensations/` | Clinic staff or administrator | Get medicine dispensations report |

### External Integration Projections

| Method | Endpoint | Access | Description |
|---|---|---|---|
| `GET` | `/api/v1/integrations/faculty/health-status/{student_id}/` | Authenticated | Get student health status for Faculty |
| `GET` | `/api/v1/integrations/student-portal/health-status/{student_id}/` | Authenticated | Get student health status for Student Portal |

### User Management

| Method | Endpoint | Access | Description |
|---|---|---|---|
| `GET` | `/api/v1/users/` | Clinic administrator | List Clinic staff accounts |
| `POST` | `/api/v1/users/` | Clinic administrator | Create Clinic staff account |
| `GET` | `/api/v1/users/{user_id}/` | Clinic administrator | Get Clinic staff account |
| `PUT` | `/api/v1/users/{user_id}/` | Clinic administrator | Update Clinic staff account |
| `PATCH` | `/api/v1/users/{user_id}/` | Clinic administrator | Partially update Clinic staff account |
| `POST` | `/api/v1/users/{user_id}/activate/` | Clinic administrator | Activate Clinic staff account |
| `POST` | `/api/v1/users/{user_id}/deactivate/` | Clinic administrator | Deactivate Clinic staff account |


---


## 12. Request and Response Conventions


The API uses JSON request and response bodies where applicable.


Common conventions include:


- HTTP status codes

- JSON objects

- Explicit resource identifiers

- ISO-formatted dates and timestamps

- Pagination where configured

- Structured validation errors

- Problem Details responses for standardized API errors


The authoritative endpoint schemas are defined in:


`openapi.yaml`


---


## 13. Validation and Error Handling


The API supports standard HTTP error categories including:


- `400 Bad Request`

- `401 Unauthorized`

- `403 Forbidden`

- `404 Not Found`

- `409 Conflict`

- `422 Unprocessable Entity`


Problem Details responses use structured fields such as:


- `type`

- `title`

- `status`

- `detail`

- `instance`

- `code`


Validation errors are returned using structured JSON responses.


---


## 14. CORS and CSRF


### CORS


The backend supports configured frontend origins.


Credentialed cross-origin requests are enabled where configured.


### CSRF


Django's:


`CsrfViewMiddleware`


is enabled.


Session-based state-changing requests require CSRF protection.


The CSRF endpoint is:


`GET /api/auth/csrf/`


---


## 15. OpenAPI and API Documentation


The API contract is stored in:


`openapi.yaml`


Current contract baseline:


- OpenAPI version is read directly from the contract.

- Documented paths and operations are read directly from the contract.


Runtime documentation endpoints:


```text

/api/schema/

/api/schema/swagger-ui/

/api/schema/redoc/

```


The OpenAPI contract is the reference for API endpoint structure, schemas, parameters, responses, and authentication requirements.


---


## 16. Postman and Automated Testing


Current evidence recorded in `docs/TEST-EVIDENCE.md`:


| Test Area | Result |
|---|---:|
| Permanent Django tests | 167 |
| Permanent Django tests passed | 167 |
| Permanent Django tests failed | 0 |
| Postman requests | 45 |
| Newman requests executed | 45 |
| Newman failed requests | 0 |
| Newman assertions | 46 |
| Newman failed assertions | 0 |


Test evidence should be updated whenever the implementation or API contract changes.


---


## 17. Database Migrations


Clinic migrations currently include:


- `0001_initial.py`

- `0002_alter_student_student_id.py`

- `0003_canonical_clinic_domain.py`

- `0004_enforce_healthrecord_student_id.py`

- `0005_remove_legacy_healthrecord_height.py`


Authentication migrations include:


- `0001_create_clinic_roles.py`


Migrations must remain version-controlled and must not be manually deleted or rewritten after being applied to shared environments.


---


## 18. Development Setup

Follow [SETUP.md](SETUP.md) for PostgreSQL setup, environment configuration, dependency installation, and initial account creation. The commands below assume you are in `backend`, the database is available, and your local environment is configured. Activate the virtual environment using its actual directory name; this example uses `.venv`.


### Activate the virtual environment


From the backend directory:


```powershell

.\.venv\Scripts\Activate.ps1

```


### Install dependencies


```powershell

pip install -r requirements.txt

```


### Run Django checks


```powershell

python manage.py check

```


### Apply migrations


```powershell

python manage.py migrate

```


### Run the development server


```powershell

python manage.py runserver 8000

```


The backend is then available at:


```text

http://127.0.0.1:8000/

```


---


## 19. Verification Checklist


Before considering a change complete, verify:


- [ ] Django checks pass

- [ ] Relevant Django tests pass

- [ ] OpenAPI contract remains valid

- [ ] Endpoint behavior matches OpenAPI

- [ ] Authentication behavior is verified

- [ ] Permission behavior is verified

- [ ] CSRF behavior is verified for session-based writes

- [ ] CORS behavior is verified where applicable

- [ ] Error responses remain structured

- [ ] Database migrations are correct

- [ ] No virtual-environment files are committed

- [ ] No secrets are committed

- [ ] Git status contains only intended changes


---


## 20. Security and Data Integrity


Security-sensitive configuration must not be committed with real credentials.


Committed repository files must not contain:


- Real passwords

- Production secret keys

- Private credentials

- Local virtual environments

- Generated cache files

- Python bytecode


Session authentication and CSRF protection must remain enabled for the applicable application flows.


External master data must remain owned by its responsible CMS module.


---


## 21. Development Rules


### Repository rules


- Work on feature or integration branches.

- Do not merge unfinished work into `main`.

- Keep commit history meaningful.

- Review staged content before committing.


### API rules


- Keep `/api/v1/` as the business API namespace.

- Keep `/api/auth/` for authentication endpoints.

- Update OpenAPI when endpoint behavior changes.

- Do not silently change response contracts.


### Domain rules


- Registrar owns student identity.

- Inventory owns medicine stock.

- Clinic owns health records, consultations, health statuses, and medicine dispensations.

- Student Portal and Faculty receive read-only health-status projections.


### Security rules


- Protected operations require authentication.

- Permissions must be explicit.

- CSRF protection must not be bypassed casually.

- CORS must remain explicitly configured.


---


## 22. Current Project Status


### API Contract


- OpenAPI contract present.

- API paths and operations are derived from the current `openapi.yaml`.

- Public and protected operations are derived from the contract.


### Testing Evidence


- Permanent Django tests: 167

- Passed: 167

- Failed: 0

- Postman requests: 45

- Newman requests executed: 45

- Newman failures: 0

- Newman assertions: 46

- Newman failed assertions: 0


### Documentation State


This README is generated from the current OpenAPI contract and test-evidence file.


It should be regenerated when the API contract or verification baseline changes.


---


**Source of truth files**


- `openapi.yaml`

- `docs/TEST-EVIDENCE.md`

- `backend/config/settings.py`

- `backend/clinic/models.py`

- `backend/clinic/views.py`

- `backend/authentication/`
