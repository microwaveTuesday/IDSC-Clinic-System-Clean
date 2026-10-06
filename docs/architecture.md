
# Clinic System Architecture



## 1. Purpose



This document defines the current architecture of the IDSC Clinic System, the Clinic module of the College Management System.



It describes the implementation on the canonical integration branch and clearly separates:



- the midterm runtime architecture; and

- the database-backed direction retained for finals.



For the midterm, Clinic-owned business data is stored in memory through `MockClinicRepository`.



The Django database is still used for framework infrastructure such as authentication, users, groups, sessions, permissions, and administration.



## 2. Architectural Principles



The current backend follows these principles:



1. Business endpoints use `/api/v1/`.

2. Authentication endpoints use `/api/auth/`.

3. HTTP concerns remain in views.

4. Business rules remain in `ClinicService`.

5. Clinic business data access remains behind a repository boundary.

6. Midterm Clinic business storage is mock/in-memory.

7. Views must not directly persist Clinic domain models.

8. Registrar remains the source of truth for student identity and profile data.

9. Inventory remains the source of truth for medicine catalog and stock.

10. Clinic owns health records, consultations, health statuses, and medicine dispensations.

11. Faculty and Student Portal receive read-only Clinic health-status projections.

12. A future database repository must preserve the public API and domain ownership boundaries.



## 3. High-Level Architecture



```text

React / Vite Frontend

        |

        | HTTP / JSON

        v

Django + Django REST Framework

        |

        v

URL Routing

        |

        v

Views / Controllers

        |

        v

ClinicService

        |

        +-----------------------------+

        |                             |

        v                             v

MockClinicRepository          Integration Services

        |                     | Registrar

        |                     | Inventory

        v                     |

Clinic in-memory data         v

                        External-owned data

```



The primary request flow for Clinic-owned business resources is:



```text

Request

  -> URL route

  -> Clinic view

  -> serializer validation

  -> ClinicService

  -> MockClinicRepository

  -> in-memory Clinic data

  -> service result

  -> HTTP response

```



## 4. Root Routing Architecture



Root backend routing is defined in:



`backend/config/urls.py`



Important routes include:



| Route | Responsibility |

|---|---|

| `/api/auth/` | Authentication |

| `/api/v1/` | Clinic business API |

| `/api/schema/` | Generated OpenAPI schema |

| `/docs` | Canonical Swagger UI |

| `/docs/` | Swagger compatibility alias |

| `/api/schema/swagger-ui/` | Legacy Swagger compatibility route |

| `/api/schema/redoc/` | ReDoc |

| `/admin/` | Django administration |



The canonical health endpoint is:



`GET /api/v1/health`



Its response is exactly:



```json

{

  "status": "ok"

}

```



`/api/v1/health/` remains available as a runtime compatibility alias but is intentionally excluded from the generated OpenAPI schema.



## 5. Views / Controller Layer



Clinic business views are implemented primarily in:



`backend/clinic/views.py`



The view layer is responsible for:



- receiving HTTP requests;

- extracting path and query parameters;

- validating request bodies;

- applying authentication and permissions;

- invoking `ClinicService`;

- applying pagination where required;

- converting service results into HTTP responses; and

- translating failures into API errors.



The view layer is intentionally prohibited from directly performing Clinic business persistence.



The verified architecture requires zero direct Clinic ORM persistence inside `clinic/views.py`.



Examples of prohibited persistence coupling include:



- direct `.objects` queries;

- `serializer.save()`;

- direct transaction management; and

- direct imports of Clinic persistence models for business operations.



This preserves the intended dependency direction:



```text

routes -> views -> services -> data

```



## 6. Service Layer



Clinic business orchestration is implemented in:



`backend/clinic/services/clinic.py`



The main service is:



`ClinicService`



Its responsibilities include:



- health-record business operations;

- consultation business operations;

- health-status business operations;

- medicine-dispensation business operations;

- student validation through the Registrar boundary;

- medicine and stock coordination through the Inventory boundary;

- dashboard aggregation;

- reporting;

- dispensation rollback coordination; and

- business-level resource-not-found behavior.



`ClinicService` receives a repository dependency.



For the midterm, the default repository is the in-memory `MockClinicRepository`.



The service does not directly depend on Django ORM persistence for Clinic business records.



## 7. Midterm Data Layer



The midterm Clinic repository is implemented in:



`backend/clinic/data/clinic.py`



The repository class is:



`MockClinicRepository`



It stores Clinic-owned resources in memory:



- `HealthRecord`

- `Consultation`

- `HealthStatus`

- `MedicineDispensation`



The repository provides deterministic seed data for runtime demonstrations.



It also provides reset and clear behavior to support repeatable automated tests.



Clinic business records do **not** currently persist to the Django framework database during normal midterm business API execution.



The effective midterm storage flow is:



```text

ClinicService

    |

    v

MockClinicRepository

    |

    v

Python in-memory structures

```



## 8. Framework Database



The backend still requires a Django database for framework infrastructure.



The default development database is:



`backend/framework.sqlite3`



This database supports Django-level concerns including:



- authentication users;

- passwords;

- groups;

- Clinic roles;

- sessions;

- Django admin; and

- framework permissions.



Therefore, the architecture contains two different storage concerns:



```text

Clinic business-domain data

    -> MockClinicRepository

    -> in-memory storage



Django framework infrastructure

    -> Django database

    -> SQLite by default

```



These concerns must not be confused.



`CLINIC_DATA_BACKEND` defaults to `mock`.



## 9. Finals Database Direction



Django ORM models and migrations remain in the repository so the system can move to persistent Clinic business storage during finals.



Clinic ORM models are defined in:



`backend/clinic/models.py`



The retained models represent the Clinic-owned domain.



PostgreSQL can be enabled through database environment configuration.



However, merely configuring PostgreSQL does not by itself replace the midterm repository.



A finals implementation must introduce or activate a database-backed repository behind `ClinicService`.



The desired future flow is:



```text

Request

  -> View

  -> ClinicService

  -> Database-backed Clinic repository

  -> Django ORM

  -> PostgreSQL

```



The service and public API boundaries should remain stable when this transition occurs.



## 10. Domain Ownership



### Registrar



Registrar owns:



- student identity;

- student profile;

- course and section information; and

- `student_id`.



Clinic may reference `student_id`, but Clinic does not become the source of truth for student identity.



### Clinic



Clinic owns:



- `HealthRecord`;

- `Consultation`;

- `HealthStatus`; and

- `MedicineDispensation`.



These resources are part of the Clinic domain regardless of whether they are backed by mock data during midterm or persistent storage during finals.



### Inventory



Inventory owns:



- medicine catalog;

- medicine stock;

- `medicine_id`;

- stock transactions; and

- `inventory_transaction_id`.



Clinic may consume medicine information and coordinate stock operations, but Inventory remains the source of truth for stock.



### Faculty and Student Portal



Clinic exposes read-only health-status projections to:



- Faculty; and

- Student Portal.



These consumers do not receive mutation authority over Clinic-owned health-status data.



## 11. Integration Architecture



### Registrar to Clinic



Before Clinic creates or updates student-dependent Clinic records, the service layer validates the referenced student through the Registrar integration boundary.



Conceptually:



```text

Clinic request

    |

    v

ClinicService

    |

    v

Registrar service

    |

    v

Validate student_id

```



### Clinic to Inventory



Medicine dispensing requires coordination with Inventory.



Dispensation creation follows this conceptual sequence:



```text

Validate student

    |

    v

Request Inventory stock deduction

    |

    v

Receive inventory_transaction_id

    |

    v

Create Clinic MedicineDispensation

```



If Clinic persistence fails after Inventory stock has already been deducted, the service attempts compensating stock restoration.



Dispensation rollback follows the reverse coordination pattern:



```text

Load Clinic dispensation

    |

    v

Use inventory_transaction_id

    |

    v

Restore Inventory stock

    |

    v

Record Clinic rollback state

```



Inventory retains ownership of stock while Clinic retains ownership of the medicine-dispensation record.



### Clinic to Faculty / Student Portal



Clinic exposes read-only health-status projections through dedicated integration endpoints.



The integration deliberately prevents Faculty or Student Portal from becoming owners of Clinic health records.



## 12. Authentication and Authorization Architecture



The backend uses Django session authentication.



The DRF authentication class is:



`authentication.authentication.ClinicSessionAuthentication`



The backend uses Django CSRF protection for state-changing session-authenticated requests.



Authentication capabilities include:



- CSRF token retrieval;

- login;

- logout;

- current-user lookup; and

- Django session handling.



Clinic authorization includes the role groups:



- `CLINIC_STAFF`

- `CLINIC_ADMIN`



Protected business resources require authenticated and authorized access according to their permission classes.



## 13. Error Handling Architecture



The REST framework uses the project custom exception handler:



`clinic.exceptions.custom_exception_handler`



API failures use Problem Details-style JSON.



The core error fields are:



```text

type

title

status

detail

instance

code

```



The implementation supports standardized error handling for categories including:



- 400 Bad Request;

- 401 Unauthorized;

- 403 Forbidden;

- 404 Not Found;

- 409 Conflict; and

- 422 Unprocessable Entity.



This gives frontend and integration clients a consistent error structure.



## 14. OpenAPI Architecture



The canonical checked-in API specification is:



`openapi.yaml`



Runtime schema generation uses:



`drf-spectacular`



Canonical documentation endpoints include:



```text

/api/schema/

/docs

/api/schema/redoc/

```



The current validated OpenAPI baseline is:



| Metric | Verified Result |

|---|---:|

| Endpoint/method operations | 45 |

| Unique operation IDs | 45 |

| drf-spectacular warnings | 0 |

| drf-spectacular errors | 0 |

| Static Redocly lint | PASS |

| Dynamic Redocly lint | PASS |



The static and generated specifications have been verified to expose the same endpoint/method inventory.



## 15. Dependency Direction



The required backend dependency direction is:



```text

config.urls / clinic.urls

          |

          v

     Clinic views

          |

          v

     ClinicService

       /       \

      v         v

Clinic data   Integration services

repository   Registrar / Inventory

```



Important dependency rules include:



- routes do not contain business persistence logic;

- views do not persist Clinic domain records directly;

- the service does not depend on HTTP request objects for domain logic;

- the data layer does not import the view layer;

- Registrar master data is not copied into Clinic ownership; and

- Inventory stock is not moved into Clinic ownership.



## 16. Core Architecture Files



| File | Responsibility |

|---|---|

| `backend/config/urls.py` | Root routing and API documentation routes |

| `backend/config/settings.py` | Django, DRF, database, CORS, CSRF and OpenAPI configuration |

| `backend/clinic/urls.py` | Clinic business route definitions |

| `backend/clinic/views.py` | HTTP/controller layer |

| `backend/clinic/serializers.py` | Request and response validation |

| `backend/clinic/services/clinic.py` | Clinic business orchestration |

| `backend/clinic/services/registrar.py` | Registrar integration boundary |

| `backend/clinic/services/inventory.py` | Inventory integration boundary |

| `backend/clinic/data/clinic.py` | Midterm in-memory Clinic repository |

| `backend/clinic/models.py` | Retained ORM domain models |

| `backend/clinic/exceptions.py` | Problem Details exception handling |

| `backend/authentication/` | Authentication and authorization |

| `openapi.yaml` | Canonical API contract |

| `redocly.yaml` | OpenAPI lint configuration |



## 17. Current Runtime Summary



The midterm runtime architecture is:



```text

Frontend

   |

   v

Django REST API

   |

   v

Clinic views

   |

   v

ClinicService

   |

   +----------------------+

   |                      |

   v                      v

MockClinicRepository    Registrar / Inventory services

   |

   v

Clinic in-memory data



Separate framework infrastructure:



Django authentication / groups / sessions / admin

   |

   v

framework.sqlite3

```



The architecture intentionally separates Clinic business-domain storage from Django framework infrastructure.



## 18. Architectural Invariants



The following rules are considered permanent integration rules unless an explicit architecture decision changes them:



1. `/api/v1/health` is the canonical health endpoint.

2. `/docs` is the canonical Swagger UI.

3. Registrar remains the owner of student identity and profile data.

4. Inventory remains the owner of medicine catalog and stock.

5. Clinic remains the owner of HealthRecord, Consultation, HealthStatus, and MedicineDispensation.

6. Faculty and Student Portal consume read-only health-status projections.

7. Clinic views do not directly persist Clinic business resources.

8. Clinic business operations pass through `ClinicService`.

9. Midterm Clinic business data uses mock/in-memory storage.

10. Django framework persistence is separate from Clinic midterm business storage.

11. Finals persistence should be introduced behind the repository/service boundary.

12. The public API contract should remain stable during the mock-to-database transition.

13. Changes are integrated through the clean integration branch.

14. `main` must not receive direct pushes.

15. Final integration must occur through a reviewed Pull Request.



## 19. Related Documentation



This document should be used together with:



- `README.md`

- `API.md`

- `SETUP.md`

- `openapi.yaml`

- `docs/TEST-EVIDENCE.md`

- `docs/data-model.md`

- `docs/integration.md`

- `docs/design-system.md`

- `docs/decisions/`



The last four documentation areas are completed in subsequent Phase 5 tasks.
