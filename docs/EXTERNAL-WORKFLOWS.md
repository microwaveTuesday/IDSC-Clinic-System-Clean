# Registrar, Inventory and clinical-history workflows

## Record numbers and deletion permissions

Health-record and consultation labels on the student page are consecutive per student, starting at #1 and recomputing after deletion. Consultation search retains the numbering from that student's complete current list. Internal health_record_id and consultation_id remain stable, unique API identifiers; they are not reset or reused. This avoids sending an existing edit/delete link to a different record. The visible label is a position, not an API ID.

DELETE on health records, consultations, health statuses and medicine dispensations requires Owner or Admin. Staff receive 403 even when calling the API directly; the website hides those delete controls. The clinical create/edit/read permissions remain unchanged. DELETE /api/v1/medicine-dispensations/{dispensation_id}/ returns 204 and removes Clinic history only. It never changes Inventory stock or deletes its transaction. Roll back is the separate stock-return action, and must be used before deleting an entry when stock should be restored. Reports reflect the remaining Clinic history.

The earlier contract deletion tests now explicitly use an Admin for authorized deletion. The old dispensing DELETE-not-exposed test now verifies Staff is forbidden; this is an intentional policy/API extension. Other contract checks remain in place.

## Get student and Registrar updates

Students includes a Get student form accepting only student_id. POST /api/v1/students/import/ returns the current Registrar profile or 404. It opens that student's records without creating a second identity/profile. Clinic's list/detail projections read the same Registrar source, so edits, enrollment status and new students appear automatically. The website checks these projections every five seconds and on focus; an already open student page updates its name, course/section and status.

Creation still validates the student's CURRENT Registrar status on every server request. GRADUATED, DROPPED_OUT and INACTIVE students cannot receive new health records, consultations, health statuses or medicine dispensations (422), including through direct API calls or an already-open form. Their existing history remains readable. Reverting the Registrar status to ACTIVE restores eligibility.

Owner navigation includes Mock Registrar. It can add students and edit profile fields or set ACTIVE / GRADUATED / DROPPED_OUT / INACTIVE. Student ID is immutable. Clinic's ordinary student endpoints remain read-only.

## Inventory, notifications and delivery

Owner navigation includes Mock Inventory. It can add/edit catalog medicines and stock, and delete unused medicines. Medicine ID is immutable. Negative stock/quantities and invalid statuses are rejected. Medicines referenced by Inventory transactions must be made INACTIVE instead of deleted so stock history is retained. Pending restock requests also prevent catalog deletion.

New medicines are immediately available through Clinic's read-only medicine projection. Add/edit/delete and fulfillment generate notifications. Each Clinic user has separate read receipts. Unread notifications appear on the Medicine stock page and in a notice on other pages; marking them read affects only the signed-in user.

Medicine stock provides restock requests for ALL active medicines (quantity per medicine) or SELECTED medicines (individual quantities). Requests start PENDING and do not change stock. Mock Inventory lists incoming requests with a Fulfill action. Fulfillment validates every line before changing any stock, adds the requested amounts and Inventory stock transactions, then marks the request FULFILLED. Repeated fulfillment returns 409 and never credits stock twice. Inactive/missing medicines or an exceeded stock limit block the complete delivery without partial updates. Clinic users can submit/view requests; only Owner operates the mock Inventory fulfillment workspace.

## API additions

All require a Clinic session; writes require X-CSRFToken.

| Route | Methods | Role |
| --- | --- | --- |
| /api/v1/students/import/ | POST | Owner, Admin, Staff |
| /api/v1/mock/registrar/students/ | GET, POST | Owner |
| /api/v1/mock/registrar/students/{student_id}/ | PATCH | Owner |
| /api/v1/mock/inventory/medicines/ | GET, POST | Owner |
| /api/v1/mock/inventory/medicines/{medicine_id}/ | PATCH, DELETE | Owner |
| /api/v1/restock-requests/ | GET, POST | Owner, Admin, Staff |
| /api/v1/mock/inventory/restock-requests/{request_id}/fulfill/ | POST | Owner |
| /api/v1/inventory-notifications/ | GET, POST | Owner, Admin, Staff |
| /api/v1/medicine-dispensations/{dispensation_id}/ | DELETE | Owner, Admin |

Selected request example: {"mode":"SELECTED","items":[{"medicine_id":"MED-0001","quantity":25}]}. All request example: {"mode":"ALL","quantity":100}. Notification acknowledgment: {"notification_ids":["the notification ID"]}.

The mock API/workspaces are controlled independently by MOCK_WORKSPACES_ENABLED and can be used with Clinic database mode. Like the pre-existing Clinic mock repository, Registrar/Inventory demo mutations, requests and notifications are in process memory; Clinic records are persistent when CLINIC_DATA_BACKEND=database and reset when the backend restarts. Use one development backend process for this demonstration. These are school-project mock external systems, not connections to a real Registrar or Inventory installation. Account credentials remain in Django's database.

Current schema inventory: 45 paths, 72 operations (5 public, 67 protected). New backend tests cover direct permission checks, enrollment transitions, current projections, notifications/receipts, selected/all delivery, duplicate and atomic fulfillment, catalog safeguards, authentication/CSRF and stock-preserving history deletion. Browser evidence is recorded in INTEGRATION-VALIDATION.md.

Optional CLINIC_EMPTY_START=1 starts all mock stores empty rather than loading samples; accounts persist separately. Real adapters remain future work: [REAL-SYSTEM-INTEGRATION.md](REAL-SYSTEM-INTEGRATION.md).
