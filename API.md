# Clinic backend API reference

Current branch: improvement/clinic-final-10of10. Canonical machine-readable contract: [openapi.yaml](openapi.yaml). Runtime schema: `/api/schema/`; Swagger: `/docs`; ReDoc: `/api/schema/redoc/`. Development backend: http://127.0.0.1:8002.

OpenAPI 3.1.0: **45 paths, 72 operations, 5 public, 67 protected**. The table below includes every canonical operation; compatibility aliases are excluded.

## Authentication and access

Use Django sessions through ClinicSessionAuthentication. GET `/api/auth/csrf/` supplies a csrfToken and cookie. POST login with username/password and X-CSRFToken; retain session cookies. Fetch a fresh CSRF token before unsafe requests, including after login/registration rotation. Public POST operations also require CSRF.

GET `/api/auth/setup/` returns only `owner_registration_available`, with no-store caching. POST `/api/auth/owner/register/` accepts username/password/confirm_password and optional first_name/last_name/email. Success returns 201 with user and starts a session. Completed or competing setup returns 409. Registration cannot reopen after logout, deactivation or an out-of-band Owner role change. See [OWNER-REGISTRATION.md](docs/OWNER-REGISTRATION.md).

Owner is the single superuser; CLINIC_ADMIN manages Staff only; CLINIC_STAFF uses clinic features. Only Owner manages Admins and operates mock external workspaces. Django is_staff is not a clinic role. Signed-in accounts without a clinic role cannot access clinic features. Faculty/Student Portal projections require authentication and expose status only.

## Complete operation inventory

| Method | Path | Required access |
| --- | --- | --- |
| GET | `/api/auth/csrf/` | Public; CSRF for POST |
| POST | `/api/auth/login/` | Public; CSRF for POST |
| POST | `/api/auth/logout/` | Authenticated |
| POST | `/api/auth/username/change/` | Authenticated |
| GET | `/api/v1/admins/` | Owner |
| POST | `/api/v1/admins/` | Owner |
| POST | `/api/auth/password/change/` | Authenticated |
| GET | `/api/auth/me/` | Authenticated |
| GET | `/api/v1/health` | Public; CSRF for POST |
| GET | `/api/v1/dashboard/` | Owner, Admin, Staff |
| GET | `/api/v1/students/` | Owner, Admin, Staff |
| GET | `/api/v1/students/{student_id}/` | Owner, Admin, Staff |
| GET | `/api/v1/health-records/` | Owner, Admin, Staff |
| POST | `/api/v1/health-records/` | Owner, Admin, Staff |
| GET | `/api/v1/health-records/{health_record_id}/` | Owner, Admin, Staff |
| PUT | `/api/v1/health-records/{health_record_id}/` | Owner, Admin, Staff |
| PATCH | `/api/v1/health-records/{health_record_id}/` | Owner, Admin, Staff |
| DELETE | `/api/v1/health-records/{health_record_id}/` | Owner, Admin |
| GET | `/api/v1/consultations/` | Owner, Admin, Staff |
| POST | `/api/v1/consultations/` | Owner, Admin, Staff |
| GET | `/api/v1/consultations/{consultation_id}/` | Owner, Admin, Staff |
| PUT | `/api/v1/consultations/{consultation_id}/` | Owner, Admin, Staff |
| PATCH | `/api/v1/consultations/{consultation_id}/` | Owner, Admin, Staff |
| DELETE | `/api/v1/consultations/{consultation_id}/` | Owner, Admin |
| GET | `/api/v1/health-statuses/` | Owner, Admin, Staff |
| POST | `/api/v1/health-statuses/` | Owner, Admin, Staff |
| GET | `/api/v1/health-statuses/{status_id}/` | Owner, Admin, Staff |
| PUT | `/api/v1/health-statuses/{status_id}/` | Owner, Admin, Staff |
| PATCH | `/api/v1/health-statuses/{status_id}/` | Owner, Admin, Staff |
| DELETE | `/api/v1/health-statuses/{status_id}/` | Owner, Admin |
| GET | `/api/v1/medicines/` | Owner, Admin, Staff |
| GET | `/api/v1/medicines/{medicine_id}/` | Owner, Admin, Staff |
| GET | `/api/v1/medicine-dispensations/` | Owner, Admin, Staff |
| POST | `/api/v1/medicine-dispensations/` | Owner, Admin, Staff |
| GET | `/api/v1/medicine-dispensations/{dispensation_id}/` | Owner, Admin, Staff |
| DELETE | `/api/v1/medicine-dispensations/{dispensation_id}/` | Owner, Admin |
| POST | `/api/v1/medicine-dispensations/{dispensation_id}/rollback/` | Owner, Admin, Staff |
| GET | `/api/v1/reports/clinic-visits/` | Owner, Admin, Staff |
| GET | `/api/v1/reports/health-records/` | Owner, Admin, Staff |
| GET | `/api/v1/reports/medicine-inventory/` | Owner, Admin, Staff |
| GET | `/api/v1/reports/medicine-dispensations/` | Owner, Admin, Staff |
| GET | `/api/v1/integrations/faculty/health-status/{student_id}/` | Owner, Admin, Staff |
| GET | `/api/v1/integrations/student-portal/health-status/{student_id}/` | Owner, Admin, Staff |
| GET | `/api/v1/users/` | Owner, Admin |
| POST | `/api/v1/users/` | Owner, Admin |
| GET | `/api/v1/users/{user_id}/` | Owner, Admin |
| PUT | `/api/v1/users/{user_id}/` | Owner, Admin |
| PATCH | `/api/v1/users/{user_id}/` | Owner, Admin |
| DELETE | `/api/v1/users/{user_id}/` | Owner, Admin |
| POST | `/api/v1/users/{user_id}/activate/` | Owner, Admin |
| POST | `/api/v1/users/{user_id}/deactivate/` | Owner, Admin |
| DELETE | `/api/v1/admins/{user_id}/` | Owner |
| GET | `/api/v1/admins/{user_id}/` | Owner |
| PUT | `/api/v1/admins/{user_id}/` | Owner |
| PATCH | `/api/v1/admins/{user_id}/` | Owner |
| POST | `/api/v1/admins/{user_id}/deactivate/` | Owner |
| POST | `/api/v1/admins/{user_id}/activate/` | Owner |
| GET | `/api/v1/inventory-notifications/` | Owner, Admin, Staff |
| POST | `/api/v1/inventory-notifications/` | Owner, Admin, Staff |
| GET | `/api/v1/mock/inventory/medicines/` | Owner |
| POST | `/api/v1/mock/inventory/medicines/` | Owner |
| PATCH | `/api/v1/mock/inventory/medicines/{medicine_id}/` | Owner |
| DELETE | `/api/v1/mock/inventory/medicines/{medicine_id}/` | Owner |
| POST | `/api/v1/mock/inventory/restock-requests/{request_id}/fulfill/` | Owner |
| GET | `/api/v1/mock/registrar/students/` | Owner |
| POST | `/api/v1/mock/registrar/students/` | Owner |
| PATCH | `/api/v1/mock/registrar/students/{student_id}/` | Owner |
| GET | `/api/v1/restock-requests/` | Owner, Admin, Staff |
| POST | `/api/v1/restock-requests/` | Owner, Admin, Staff |
| POST | `/api/v1/students/import/` | Owner, Admin, Staff |
| GET | `/api/auth/setup/` | Public; CSRF for POST |
| POST | `/api/auth/owner/register/` | Public; CSRF for POST |

## Credentials and account lifecycle

Password change accepts current_password/new_password/confirm_password; username change accepts current_password/new_username. Both operate only on the signed-in account. Password validation, matching confirmation and a different new password are required. Username validation trims, normalizes Unicode and checks case-insensitive duplicates. Password changes retain the current session; other sessions expire on their next request.

Admin creation requires the Owner current_password, username/password/confirm_password, optional first_name/last_name/email. New accounts receive CLINIC_ADMIN, never superuser privileges. Maximum five Admins includes inactive accounts and excludes Owner; capacity returns 409 until one is deleted. Staff creation creates Staff only. Management edits support username/first_name/last_name/email, not role or privilege changes.

Account DELETE requires JSON current_password and returns 204. Owner manages Admins; Owner/Admin manage Staff. Staff routes exclude Admin/Owner targets. Registered Owner cannot be deleted, deactivated or demoted. Owner can remove the last regular Admin. Deactivation revokes sessions; activation does not revive them. Account deletion preserves Clinic medical records.

## Clinic and integration rules

- Students and medicines are read-only external projections through ordinary clinic routes. Mock workspace routes simulate external administration and are Owner-only, available with CLINIC_DATA_BACKEND=mock.
- POST students/import accepts student_id only; returns current Registrar data without duplicating identity. New records/consultations/statuses/dispensations require ACTIVE status; graduated/dropped-out/inactive students retain readable history. Ineligible creation returns 422.
- Clinical/history deletion requires Owner/Admin. Visible record numbering is consecutive per student; API identifiers remain stable and are not reused.
- Dispensing validates Registrar eligibility and deducts Inventory stock. Clinic persistence failure triggers attempted compensating stock restore. Explicit rollback restores stock and records the rollback transaction. History DELETE never restores stock.
- Selected restock body: `{"mode":"SELECTED","items":[{"medicine_id":"MED-0001","quantity":25}]}`. All-active request: `{"mode":"ALL","quantity":100}`. PENDING requests do not change stock. Owner fulfillment validates every item before delivery; repeated fulfillment returns 409.
- Inventory notifications have per-user read receipts. POST acknowledgment accepts `{"notification_ids":["notification ID"]}`. Referenced medicines and pending requests have catalog-deletion safeguards.

See [EXTERNAL-WORKFLOWS.md](docs/EXTERNAL-WORKFLOWS.md), [ROLE-HIERARCHY.md](docs/ROLE-HIERARCHY.md) and [REAL-SYSTEM-INTEGRATION.md](docs/REAL-SYSTEM-INTEGRATION.md).

## Pagination and errors

Paginated responses contain count/page/page_size/total_pages/results. General lists default to 20/max 100; users defaults/max 10. Admin directory is an unpaginated list. Consult OpenAPI for each endpoint's filters and response schema.

Errors use application/problem+json with type/title/status/detail/instance/code and optional errors for fields. Common statuses: 400 validation, 401 missing session, 403 permission/CSRF, 404 missing resource, 409 conflict/capacity/completed setup, 422 domain eligibility. CSRF middleware can return its own rejection response before API processing.

## Storage and validation

Accounts, sessions and the permanent Owner reference persist in Django's database. Clinic records persist when CLINIC_DATA_BACKEND=database; mock students/medicines, stock transactions, restocks and notifications remain process-local. CLINIC_EMPTY_START=1 starts mock stores empty; it does not reset accounts. Select database repository mode to use SQLite/PostgreSQL Clinic persistence.

[SETUP.md](SETUP.md) provides commands. [CURRENT-VALIDATION.md](docs/CURRENT-VALIDATION.md) distinguishes latest checks from historical Postman/browser evidence. Original and feature collections are under postman/; use disposable data and configure local credentials/base URL. Request/response field details remain authoritative in openapi.yaml and verified runtime tests.


## Reliability and security extensions

No endpoint paths were removed or added. Coordinated business mutations accept optional Idempotency-Key (ASCII, at most128 characters), scoped to actor+method+path. Successful replay returns the original status/body and Idempotency-Replayed:true; reused key with a different body returns409. Authorization runs before replay. Receipts persist and may contain sensitive response fields: restrict database access and plan retention.

Database-mode clinical updates/deletes accept If-Match from a detail ETag; stale state returns409. Updates can instead use X-Record-Version with the original updated_at ISO timestamp, as the frontend does. Invalid timestamp headers return400. Header-free legacy clients remain supported with transactional serialization; they do not receive optimistic conflict protection.

Medical API responses use Cache-Control:no-store. Staff creation now enforces configured password validators and a1024-character maximum. Roleless sessions cannot read Faculty/Portal health projections. Production login throttling is10/minute per direct client IP using the configured cache; no arbitrary forwarded IP trust. In production use an appropriately shared cache/proxy policy when scaling beyond the supported single mock worker.

Failed stock compensation or post-restore Clinic failure returns503 reconciliation_required and creates a private IntegrationIncident. Owner inspects/resolves incidents via Django administration after checking the Inventory ledger; marking resolved alone does not repair stock. Never blindly retry an unknown external stock outcome. See [KNOWN-LIMITATIONS.md](docs/KNOWN-LIMITATIONS.md).
