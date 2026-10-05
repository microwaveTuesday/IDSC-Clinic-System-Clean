# IDSC Clinic System API Reference

This document summarizes the verified API contract of the Clinic module on `fix/pre-main-integration`.

The authoritative machine-readable contract is:

```text
openapi.yaml
```

Runtime schema:

```text
GET /api/schema/
```

Canonical Swagger UI:

```text
/docs
```

---

## 1. Contract Baseline

| Property | Verified value |
|---|---:|
| API version | `1.0.0` |
| OpenAPI version | `3.1.0` |
| Business namespace | `/api/v1/` |
| Authentication namespace | `/api/auth/` |
| Paths | `29` |
| Operations | `45` |
| Public operations | `3` |
| Protected operations | `42` |
| Session authentication | Yes |
| Problem Details errors | Yes |

Development server:

```text
http://127.0.0.1:8000
```

---

## 2. Domain Ownership

The API preserves strict College Management System ownership boundaries.

### Registrar-owned students

Registrar owns:

- student identity;
- student profile;
- course and section; and
- `student_id`.

Clinic exposes read-only Registrar-backed student projections through:

```text
GET /api/v1/students/
GET /api/v1/students/{student_id}/
```

Clinic does **not** create, update, or delete Registrar students.

`student_id` is an opaque external string identifier, for example:

```text
2026-0001
```

### Clinic-owned resources

Clinic owns:

- `HealthRecord`
- `Consultation`
- `HealthStatus`
- `MedicineDispensation`

### Inventory-owned medicine data

Inventory owns:

- medicine catalog;
- stock;
- `medicine_id`; and
- stock transactions.

Clinic exposes read-only medicine projections and coordinates stock changes through its Inventory boundary.

### Faculty and Student Portal

Faculty and Student Portal receive authenticated read-only health-status projections.

---

## 3. Authentication and Security

The default DRF permission is:

```text
IsAuthenticated
```

The default authentication mechanism is Django session authentication through:

```text
ClinicSessionAuthentication
```

### Public operations

Exactly three operations are public:

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/auth/csrf/` | Obtain CSRF token |
| `POST` | `/api/auth/login/` | Create authenticated session |
| `GET` | `/api/v1/health` | Health check |

All other canonical operations are protected.

### Session flow

Typical flow:

```text
GET /api/auth/csrf/
    -> csrftoken

POST /api/auth/login/
    -> credentials + X-CSRFToken
    -> sessionid cookie

protected request
    -> sessionid
    -> X-CSRFToken for unsafe methods

POST /api/auth/logout/
    -> session invalidated
```

A failed anonymous request to a protected endpoint returns `401` and:

```http
WWW-Authenticate: Session
```

---

## 4. CSRF and CORS

CSRF middleware remains enabled.

Unsafe session-authenticated requests require CSRF protection.

Approved local credentialed CORS origins:

```text
http://localhost:5173
http://127.0.0.1:5173
```

Wildcard credentialed CORS is not part of the verified configuration.

---

## 5. Standard Problem Details Error Contract

Errors use `application/problem+json`.

Canonical fields:

```json
{
  "type": "https://clinic.example/problems/not-found",
  "title": "Not Found",
  "status": 404,
  "detail": "The requested resource was not found.",
  "instance": "/api/v1/example/",
  "code": "not_found"
}
```

Validation errors may additionally include:

```json
{
  "errors": {
    "field": [
      "Validation message."
    ]
  }
}
```

Verified Problem Details status families include:

- `400 Bad Request`
- `401 Unauthorized`
- `403 Forbidden`
- `404 Not Found`
- `409 Conflict`
- `422 Unprocessable Entity`

---

## 6. Documentation Routes

| Purpose | Path |
|---|---|
| API discovery | `/` |
| Dynamic OpenAPI | `/api/schema/` |
| Canonical Swagger UI | `/docs` |
| Swagger compatibility alias | `/docs/` |
| ReDoc | `/api/schema/redoc/` |

The canonical Swagger path is `/docs`.

---

## 7. Health and Dashboard

### Health

```http
GET /api/v1/health
```

Access: public.

Exact response:

```json
{
  "status": "ok"
}
```

The runtime compatibility alias `/api/v1/health/` may also respond successfully, but it is intentionally excluded from the canonical OpenAPI operation inventory.

### Dashboard

```http
GET /api/v1/dashboard/
```

Access: Clinic staff/admin.

Returns Clinic dashboard information aggregated through the service/integration layer.

---

## 8. Authentication Endpoints

| Method | Endpoint | Access | Description |
|---|---|---|---|
| `GET` | `/api/auth/csrf/` | Public | Obtain CSRF token |
| `POST` | `/api/auth/login/` | Public | Log in and create session |
| `GET` | `/api/auth/me/` | Authenticated | Current session user |
| `POST` | `/api/auth/logout/` | Authenticated | End session |

---

## 9. Registrar Student Projection

| Method | Endpoint | Access | Description |
|---|---|---|---|
| `GET` | `/api/v1/students/` | Clinic staff/admin | List Registrar-backed student projections |
| `GET` | `/api/v1/students/{student_id}/` | Clinic staff/admin | Retrieve one student projection |

These operations are read-only.

---

## 10. Health Records

| Method | Endpoint | Access |
|---|---|---|
| `GET` | `/api/v1/health-records/` | Clinic staff/admin |
| `POST` | `/api/v1/health-records/` | Clinic staff/admin |
| `GET` | `/api/v1/health-records/{health_record_id}/` | Clinic staff/admin |
| `PUT` | `/api/v1/health-records/{health_record_id}/` | Clinic staff/admin |
| `PATCH` | `/api/v1/health-records/{health_record_id}/` | Clinic staff/admin |
| `DELETE` | `/api/v1/health-records/{health_record_id}/` | Clinic staff/admin |

Example create request:

```json
{
  "student_id": "2026-0001",
  "blood_type": "O+",
  "allergies": "None",
  "medical_history": "None",
  "current_medications": "",
  "height_cm": "170.00",
  "weight_kg": "65.00"
}
```

Clinic validates the Registrar-owned `student_id` through the Registrar integration boundary before student-dependent writes.

---

## 11. Consultations

| Method | Endpoint | Access |
|---|---|---|
| `GET` | `/api/v1/consultations/` | Clinic staff/admin |
| `POST` | `/api/v1/consultations/` | Clinic staff/admin |
| `GET` | `/api/v1/consultations/{consultation_id}/` | Clinic staff/admin |
| `PUT` | `/api/v1/consultations/{consultation_id}/` | Clinic staff/admin |
| `PATCH` | `/api/v1/consultations/{consultation_id}/` | Clinic staff/admin |
| `DELETE` | `/api/v1/consultations/{consultation_id}/` | Clinic staff/admin |

Example create request:

```json
{
  "student_id": "2026-0001",
  "chief_complaint": "Headache",
  "assessment": "Mild tension headache",
  "treatment": "Rest and hydration",
  "notes": "Return if symptoms worsen"
}
```

---

## 12. Health Statuses

| Method | Endpoint | Access |
|---|---|---|
| `GET` | `/api/v1/health-statuses/` | Clinic staff/admin |
| `POST` | `/api/v1/health-statuses/` | Clinic staff/admin |
| `GET` | `/api/v1/health-statuses/{status_id}/` | Clinic staff/admin |
| `PUT` | `/api/v1/health-statuses/{status_id}/` | Clinic staff/admin |
| `PATCH` | `/api/v1/health-statuses/{status_id}/` | Clinic staff/admin |
| `DELETE` | `/api/v1/health-statuses/{status_id}/` | Clinic staff/admin |

Stored status values:

```text
CLEARED
RESTRICTED
UNDER_OBSERVATION
```

`NOT_AVAILABLE` is an integration projection state, not a stored Clinic status.

---

## 13. Inventory Medicine Projection

| Method | Endpoint | Access |
|---|---|---|
| `GET` | `/api/v1/medicines/` | Clinic staff/admin |
| `GET` | `/api/v1/medicines/{medicine_id}/` | Clinic staff/admin |

These are read-only Inventory-backed projections.

Example external identifier:

```text
MED-0001
```

---

## 14. Medicine Dispensations

| Method | Endpoint | Access |
|---|---|---|
| `GET` | `/api/v1/medicine-dispensations/` | Clinic staff/admin |
| `POST` | `/api/v1/medicine-dispensations/` | Clinic staff/admin |
| `GET` | `/api/v1/medicine-dispensations/{dispensation_id}/` | Clinic staff/admin |
| `POST` | `/api/v1/medicine-dispensations/{dispensation_id}/rollback/` | Clinic staff/admin |

Creation orchestration:

```text
validate Registrar student
    -> deduct Inventory stock
    -> receive inventory_transaction_id
    -> create Clinic dispensation
```

If Clinic persistence fails after the Inventory deduction, the service attempts a compensating stock restore.

Explicit rollback restores Inventory stock and records a `rollback_transaction_id`.

Stored Clinic dispensation status values:

```text
COMPLETED
ROLLED_BACK
```

---

## 15. Reports

| Method | Endpoint | Access |
|---|---|---|
| `GET` | `/api/v1/reports/clinic-visits/` | Clinic staff/admin |
| `GET` | `/api/v1/reports/health-records/` | Clinic staff/admin |
| `GET` | `/api/v1/reports/medicine-inventory/` | Clinic staff/admin |
| `GET` | `/api/v1/reports/medicine-dispensations/` | Clinic staff/admin |

Report filters use the schemas documented in `openapi.yaml`.

Invalid dates and invalid date ranges return Problem Details validation errors.

---

## 16. External Health-Status Projections

### Faculty

```http
GET /api/v1/integrations/faculty/health-status/{student_id}/
```

### Student Portal

```http
GET /api/v1/integrations/student-portal/health-status/{student_id}/
```

Access: authenticated.

These routes expose restricted read-only Clinic health-status projections.

They do not expose full health records and do not permit external modules to mutate Clinic data.

---

## 17. Clinic User Administration

These operations require Clinic admin permissions.

| Method | Endpoint |
|---|---|
| `GET` | `/api/v1/users/` |
| `POST` | `/api/v1/users/` |
| `GET` | `/api/v1/users/{user_id}/` |
| `PUT` | `/api/v1/users/{user_id}/` |
| `PATCH` | `/api/v1/users/{user_id}/` |
| `POST` | `/api/v1/users/{user_id}/activate/` |
| `POST` | `/api/v1/users/{user_id}/deactivate/` |

These users are Django framework/authentication accounts, not Registrar student identities.

---

## 18. Pagination

Canonical paginated list envelopes use:

```json
{
  "count": 1,
  "page": 1,
  "page_size": 20,
  "total_pages": 1,
  "results": []
}
```

The OpenAPI 3.1 schema matches this runtime shape.

Legacy `next` and `previous` pagination properties are not part of the canonical Clinic pagination envelope.

---

## 19. Midterm Data Runtime

Clinic business data uses:

```text
CLINIC_DATA_BACKEND=mock
```

and flows through:

```text
route
  -> view/controller
  -> ClinicService
  -> MockClinicRepository
```

SQLite is used only for Django framework infrastructure such as authentication, groups, permissions, sessions, admin, and migration bookkeeping.

The retained Clinic ORM models/migrations describe the finals persistence direction but are not the active midterm Clinic business-data path.

---

## 20. Postman / Newman Baseline

Collection:

```text
postman/IDSC-Clinic-System.postman_collection.json
```

Verified run:

```text
Requests      = 45
Failed        = 0
Test scripts  = 45
Assertions    = 46
Failed        = 0
```

The validated flow covers:

- CSRF acquisition;
- login;
- authenticated session;
- health;
- dashboard;
- Registrar student projections;
- Clinic CRUD;
- Inventory medicine projections;
- dispensation rollback;
- reports;
- Faculty/Student Portal projections;
- Clinic user administration; and
- logout.

---

## 21. Contract Authority

When examples or prose conflict, use this priority:

1. `openapi.yaml` for the canonical API contract;
2. runtime behavior verified by the permanent Django tests;
3. `README.md` and the focused documentation under `docs/`;
4. this API reference.

Do not copy legacy `/api/...` routes or older ownership assumptions back into the current contract.
