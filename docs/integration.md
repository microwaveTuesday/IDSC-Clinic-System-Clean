
# Clinic System Integration Architecture



## 1. Purpose



This document defines how the Clinic module integrates with the other modules of the College Management System while preserving clear domain ownership.



The integration model is intentionally designed around service boundaries rather than shared database ownership.



The Clinic module owns medical data and clinic workflow records.



Registrar owns student identity and profile data.



Inventory owns medicine catalog data, medicine stock, and inventory stock transactions.



Faculty and Student Portal consume restricted read-only health-status projections from Clinic.



For the midterm implementation, Registrar and Inventory are represented by deterministic mock integration services. The service boundaries are structured so those mocks can later be replaced by real REST clients without changing Clinic routes or Clinic domain ownership.



This document reflects the implementation on the `fix/pre-main-integration` branch after the Phase 4.8 OpenAPI public-security normalization fix.



---



## 2. Integration Principles



The Clinic integration architecture follows these rules:



1. Each CMS module owns its own domain data.

2. Clinic does not duplicate Registrar student master data.

3. Clinic does not own Inventory medicine master data or stock.

4. External records are referenced by opaque identifiers.

5. Integration access occurs through explicit service boundaries.

6. Clinic-owned routes delegate business orchestration to `ClinicService`.

7. Midterm mocks preserve the same conceptual boundaries intended for final live APIs.

8. Read-only projections remain read-only.

9. Cross-module failures are translated into the Clinic API error contract.

10. Module-to-module authentication can evolve without changing domain ownership.



The required dependency direction remains:



```text

routes -> views -> services -> integration/data boundaries

```



External module data must not bypass the integration services and become locally owned Clinic master data.



---



## 3. Canonical Domain Ownership



### Registrar owns



- student identity

- student profile

- course

- section

- student enrollment/status projection used by Clinic

- `student_id`



### Clinic owns



- `HealthRecord`

- `Consultation`

- `HealthStatus`

- `MedicineDispensation`

- Clinic reports derived from Clinic-owned data

- Clinic authentication and staff-management behavior



### Inventory owns



- medicine catalog

- medicine name and generic name

- medicine unit

- current medicine stock

- reorder level

- stock transaction history

- `medicine_id`

- `inventory_transaction_id`



### Faculty and Student Portal



Faculty and Student Portal do not own Clinic health-status records.



They receive only the restricted read-only health-status projection exposed by Clinic.



---



## 4. Current Midterm Integration Topology



The current implementation is intentionally local and deterministic for the midterm.



```text

                         College Management System



    +----------------+                        +----------------+

    |   Registrar    |                        |   Inventory    |

    |  mock boundary |                        |  mock boundary |

    +--------+-------+                        +--------+-------+

             |                                         |

             | student projection                      | medicine / stock

             | student validation                      | stock transaction

             v                                         v

       +-----------------------------------------------------+

       |                  ClinicService                      |

       |                                                     |

       |  HealthRecord       Consultation                    |

       |  HealthStatus       MedicineDispensation            |

       +----------------------+------------------------------+

                              |

                              | restricted read-only

                              | health-status projection

                    +---------+----------+

                    |                    |

                    v                    v

             +-------------+      +----------------+

             |   Faculty   |      | Student Portal |

             +-------------+      +----------------+

```



The Registrar and Inventory boxes are integration boundaries even though they currently use in-process mock services.



The final implementation can replace these mock services with HTTP clients while preserving the same Clinic-facing interfaces.



---



## 5. Registrar Integration Boundary



The Registrar integration implementation is located at:



```text

backend/clinic/services/registrar.py

```



The current boundary is implemented by:



```text

MockRegistrarService

```



The service exposes student information to Clinic without making Clinic the owner of that information.



### 5.1 Student projection



The Registrar projection contains:



- `student_id`

- `first_name`

- `last_name`

- `course`

- `section`

- `status`



These fields are serialized by `StudentSerializer` as a read-only projection.



`StudentSerializer` is deliberately a plain DRF serializer rather than a Clinic `ModelSerializer`.



That design prevents Clinic from accidentally creating or mutating Registrar-owned student records through a Clinic ORM model.



### 5.2 Registrar-backed Clinic endpoints



Clinic exposes Registrar-backed read-only student routes:



```text

GET /api/v1/students/

GET /api/v1/students/{student_id}/

```



The list route supports integration-side filtering such as:



- search

- status

- course

- section



The detail route resolves a single Registrar-owned student identifier.



### 5.3 Student validation



Clinic validates Registrar ownership before creating or changing Clinic records that depend on a student.



`MockRegistrarService.validate_student_for_clinic(student_id)` performs two responsibilities:



1. confirm that the student exists in Registrar;

2. confirm that the student is currently `ACTIVE` for new Clinic operations.



The current mock includes both active and graduated examples so this rule can be tested deterministically.



### 5.4 Registrar integration errors



The Registrar boundary defines:



```text

StudentNotFoundError

StudentUnavailableError

```



Typical translation at the Clinic API layer is:



- missing Registrar student -> HTTP 404 Problem Details

- known but unavailable/inactive student -> HTTP 422 Problem Details



The API therefore preserves a distinction between a nonexistent external identity and a real student who cannot participate in a new Clinic operation.



---



## 6. Inventory Integration Boundary



The Inventory integration implementation is located at:



```text

backend/clinic/services/inventory.py

```



The current boundary is implemented by:



```text

MockInventoryService

```



Clinic never owns the medicine catalog, stock balance, or Inventory transaction ledger.



### 6.1 Medicine projection



The Inventory projection contains:



- `medicine_id`

- `name`

- `generic_name`

- `unit`

- `quantity_in_stock`

- `reorder_level`

- `is_low_stock`

- `status`



These fields are serialized by `MedicineSerializer` as a read-only external projection.



### 6.2 Inventory-backed Clinic endpoints



Clinic exposes Inventory-backed read-only routes:



```text

GET /api/v1/medicines/

GET /api/v1/medicines/{medicine_id}/

```



The list route supports filtering and ordering without transferring ownership of the medicine records to Clinic.



### 6.3 Stock operations used by Clinic



The current Inventory boundary exposes operational methods used by the Clinic dispensing workflow:



```text

check_stock(medicine_id, quantity)

deduct_stock(medicine_id, quantity)

restore_stock(transaction_id)

```



`deduct_stock` validates:



- quantity is at least 1;

- medicine exists;

- medicine is active;

- sufficient stock is available.



On success it reduces Inventory-owned stock and creates an Inventory transaction identifier such as:



```text

INV-TX-0001

```



`restore_stock` reverses the stock effect of a previous deduction and returns a new rollback transaction identifier.



### 6.4 Inventory integration errors



The Inventory boundary defines:



```text

MedicineNotFoundError

MedicineUnavailableError

InsufficientStockError

InventoryTransactionNotFoundError

```



These are translated by Clinic views into the Clinic API error model.



Typical mappings include:



- missing medicine -> HTTP 404

- unavailable medicine -> HTTP 422

- insufficient stock -> HTTP 422

- missing rollback transaction -> HTTP 422

- repeated rollback conflict -> HTTP 409



---



## 7. Clinic-Owned Medicine Dispensation Workflow



`MedicineDispensation` is owned by Clinic even though it references Registrar and Inventory identifiers.



The public Clinic operation is:



```text

POST /api/v1/medicine-dispensations/

```



The request includes Clinic workflow data such as:



- `student_id`

- `medicine_id`

- `quantity`

- `reason`



The orchestration is delegated to `ClinicService.create_dispensation`.



### 7.1 Creation sequence



The sequence is:



```text

Client

  |

  | POST medicine dispensation

  v

Clinic View

  |

  | validated request

  v

ClinicService

  |

  | validate student_id

  v

Registrar boundary

  |

  | ACTIVE student confirmed

  v

ClinicService

  |

  | deduct_stock(medicine_id, quantity)

  v

Inventory boundary

  |

  | inventory_transaction_id

  v

ClinicService

  |

  | create Clinic-owned dispensation

  v

Clinic data layer

  |

  v

201 response

```



The critical ownership distinction is:



- Registrar confirms the student reference;

- Inventory owns the stock mutation;

- Clinic owns the dispensation record.



Clinic stores `inventory_transaction_id` as an external reference for auditability and rollback.



---



## 8. Dispensation Compensation and Rollback



Cross-module workflows can partially succeed.



The implementation therefore includes explicit compensation behavior.



### 8.1 Compensation during creation



If Inventory successfully deducts stock but Clinic persistence fails afterward, `ClinicService.create_dispensation` attempts to restore the Inventory stock using the newly created Inventory transaction identifier.



Conceptually:



```text

Inventory deduction succeeds

          |

          v

Clinic persistence fails

          |

          v

ClinicService calls Inventory restore_stock

```



The original Clinic persistence failure remains the primary failure even if compensation also encounters an error.



This prevents the error-reporting layer from hiding the original failure that triggered compensation.



### 8.2 Explicit rollback operation



Clinic also exposes:



```text

POST /api/v1/medicine-dispensations/{dispensation_id}/rollback/

```



The sequence is:



1. Clinic retrieves the owned dispensation record.

2. Clinic verifies that the record is not already rolled back.

3. Clinic verifies that an Inventory transaction reference exists.

4. Inventory restores stock using the original transaction reference.

5. Inventory returns a rollback transaction identifier.

6. Clinic records the dispensation as rolled back.



The Clinic record therefore retains both the original external transaction and the rollback transaction for auditability.



### 8.3 Rollback conflict rules



The API distinguishes several failure conditions:



- dispensation does not exist -> 404

- already rolled back -> 409

- no Inventory transaction available -> 422

- external Inventory transaction missing -> 422

- Inventory reports repeated restore conflict -> 409



---



## 9. Health-Status Integration for Faculty and Student Portal



Clinic owns `HealthStatus` records.



Faculty and Student Portal receive a restricted projection rather than direct access to the full Clinic record.



The two routes are:



```text

GET /api/v1/integrations/faculty/health-status/{student_id}/

GET /api/v1/integrations/student-portal/health-status/{student_id}/

```



Both routes use the shared `HealthStatusIntegrationView` behavior through dedicated endpoint classes.



### 9.1 Projection fields



The read-only projection contains:



- `student_id`

- `status`

- `remarks`

- `effective_at`



The projection is serialized with:



```text

HealthStatusProjectionSerializer

```



No mutation endpoints are exposed to Faculty or Student Portal through this boundary.



### 9.2 Latest status lookup



The integration calls:



```text

ClinicService.latest_health_status_for_student(student_id)

```



That service first verifies the student through Registrar and then obtains the latest Clinic-owned health status from the Clinic repository.



### 9.3 NOT_AVAILABLE projection state



If Registrar confirms the student exists but Clinic has no health-status record, the integration returns a projection using:



```text

status = NOT_AVAILABLE

remarks = null

effective_at = null

```



`NOT_AVAILABLE` is an integration response state.



It is intentionally not one of the persistent `HealthStatus` database choices.



This separates an absence of Clinic status information from an actual medical status such as `CLEARED`, `RESTRICTED`, or `UNDER_OBSERVATION`.



---



## 10. Authentication and Cross-System Trust



The current midterm implementation uses authenticated Django sessions for the Faculty and Student Portal integration projection endpoints.



The concrete endpoint classes use:



```text

permission_classes = [IsAuthenticated]

```



The public operations in the dynamic OpenAPI contract are limited to:



```text

GET /api/v1/health

GET /api/auth/csrf/

POST /api/auth/login/

```



The Faculty and Student Portal health-status integration routes are protected operations.



### 10.1 Midterm trust model



For the midterm, an authenticated Clinic session is the trust mechanism for calling these projections.



### 10.2 Finals trust model



A dedicated cross-system trust mechanism can replace the session-based boundary when the modules are connected as independently deployed systems.



Possible implementation mechanisms may include a service credential or another approved module-to-module authentication scheme.



The important architectural constraint is that changing transport authentication must not change data ownership.



Faculty and Student Portal must remain read-only consumers of Clinic-owned health status.



---



## 11. Integration Error Translation



External integration failures are translated into Clinic API responses instead of leaking internal Python exception types.



The Clinic API uses standardized Problem Details for error responses.



Canonical fields include:



- `type`

- `title`

- `status`

- `detail`

- `instance`

- `code`



Integration-related failures therefore participate in the same API error model as Clinic-owned failures.



### 11.1 Typical integration mappings



| Integration failure | Clinic API behavior |

|---|---|

| Registrar student not found | 404 Not Found |

| Registrar student unavailable | 422 Unprocessable Entity |

| Inventory medicine not found | 404 Not Found |

| Inventory medicine unavailable | 422 Unprocessable Entity |

| Inventory stock insufficient | 422 Unprocessable Entity |

| Inventory transaction missing | 422 Unprocessable Entity |

| Dispensation already rolled back | 409 Conflict |

| Protected integration called anonymously | 401 Problem Details |

| Authenticated caller lacks required Clinic role on staff-only operations | 403 Problem Details |



The exact response schemas are defined by the canonical OpenAPI contract and the custom Clinic exception handler.



---



## 12. External Identifier Contract



Cross-module references are intentionally represented as opaque identifiers.



### 12.1 Registrar identifier



```text

student_id

```



Clinic stores this value in Clinic-owned records but does not define a local foreign key to a Registrar student table.



### 12.2 Inventory identifiers



```text

medicine_id

inventory_transaction_id

rollback_transaction_id

```



`medicine_id` identifies Inventory-owned medicine master data.



`inventory_transaction_id` identifies the stock deduction associated with a Clinic-owned dispensation.



`rollback_transaction_id` identifies the Inventory stock-restore transaction created during rollback.



### 12.3 Why these are not shared database foreign keys



The modules communicate through API/service contracts rather than a shared relational ownership model.



Using opaque IDs preserves module independence and prevents Clinic migrations from controlling Registrar or Inventory tables.



---



## 13. Read-Only Projection Rules



The following Clinic API surfaces are explicitly read-only projections of external or restricted data:



### Registrar projection



```text

GET /api/v1/students/

GET /api/v1/students/{student_id}/

```



Clinic does not expose create, update, or delete routes for Registrar students.



### Inventory projection



```text

GET /api/v1/medicines/

GET /api/v1/medicines/{medicine_id}/

```



Clinic does not expose general medicine-catalog or stock-editing routes.



Stock changes occur only through the controlled dispensing orchestration boundary.



### Faculty projection



```text

GET /api/v1/integrations/faculty/health-status/{student_id}/

```



### Student Portal projection



```text

GET /api/v1/integrations/student-portal/health-status/{student_id}/

```



Neither downstream health-status projection allows mutation of Clinic-owned data.



---



## 14. Dashboard and Report Integration Usage



The integration services are also used for aggregate Clinic views.



### 14.1 Dashboard



The dashboard combines data from multiple owners:



- total students from Registrar;

- total health records from Clinic;

- medicine stock totals from Inventory;

- low-stock medicine count from Inventory;

- recent activity from Clinic.



This is an aggregation use case, not a transfer of data ownership.



### 14.2 Medicine inventory report



The medicine-inventory report is read through the Inventory integration boundary.



Clinic can report on Inventory data without becoming the authoritative source for medicine stock.



---



## 15. API Route Inventory for Integrations



The canonical integration-related Clinic routes are:



| Method | Route | Source/Consumer | Access |

|---|---|---|---|

| GET | `/api/v1/students/` | Registrar -> Clinic | Clinic staff/admin |

| GET | `/api/v1/students/{student_id}/` | Registrar -> Clinic | Clinic staff/admin |

| GET | `/api/v1/medicines/` | Inventory -> Clinic | Clinic staff/admin |

| GET | `/api/v1/medicines/{medicine_id}/` | Inventory -> Clinic | Clinic staff/admin |

| POST | `/api/v1/medicine-dispensations/` | Clinic -> Registrar + Inventory | Clinic staff/admin |

| POST | `/api/v1/medicine-dispensations/{dispensation_id}/rollback/` | Clinic -> Inventory | Clinic staff/admin |

| GET | `/api/v1/integrations/faculty/health-status/{student_id}/` | Clinic -> Faculty | Authenticated |

| GET | `/api/v1/integrations/student-portal/health-status/{student_id}/` | Clinic -> Student Portal | Authenticated |

| GET | `/api/v1/reports/medicine-inventory/` | Inventory -> Clinic report | Clinic staff/admin |

| GET | `/api/v1/dashboard/` | Registrar + Clinic + Inventory | Clinic staff/admin |



The complete API contains 45 operations. These integration routes are part of that canonical contract.



---



## 16. OpenAPI Contract and Security Metadata



The canonical static contract is:



```text

openapi.yaml

```



The dynamic contract is generated through drf-spectacular.



After Phase 4.8, dynamic and static operation inventories contain the same 45 operations.



Public security is explicitly normalized to:



```text

security: []

```



for exactly three public operations:



```text

GET /api/v1/health

GET /api/auth/csrf/

POST /api/auth/login/

```



All remaining 42 operations are protected.



The Faculty and Student Portal integration operations therefore remain protected by the current authentication configuration.



---



## 17. Midterm Mock Integration Strategy



The midterm requirement allows mock data and does not require live external module services.



The implementation therefore uses:



```text

MockRegistrarService

MockInventoryService

MockClinicRepository

```



These mocks are not treated as permanent domain ownership changes.



They are implementations behind boundaries.



### 17.1 Registrar mock



The Registrar mock provides deterministic student records and validation behavior.



### 17.2 Inventory mock



The Inventory mock provides deterministic medicine stock and transaction behavior.



Its state is in memory and can be reset with service recreation or test setup.



### 17.3 Clinic mock repository



Clinic-owned midterm records use the in-memory `MockClinicRepository` through `ClinicService`.



The final database repository can replace the Clinic mock repository without changing external routes.



---



## 18. Finals Integration Direction



For finals, the architecture should preserve the same boundaries while replacing mock implementations where required.



### Registrar



Replace `MockRegistrarService` with a Registrar REST client implementing equivalent operations such as:



- list students

- get student

- validate student availability



### Inventory



Replace `MockInventoryService` with an Inventory REST client implementing equivalent operations such as:



- list medicines

- get medicine

- deduct stock

- restore stock



### Clinic data



Replace or configure the Clinic repository for the final persistent database implementation while keeping `ClinicService` as the orchestration boundary.



### Cross-module authentication



Replace authenticated Clinic-session trust for module-to-module calls with the class-approved service authentication model when that contract is available.



No finals integration should require Clinic to absorb Registrar or Inventory master data ownership.



---



## 19. Integration Failure and Consistency Rules



The integration architecture must preserve the following rules:



1. Never create a Clinic health record for an invalid Registrar identity.

2. Never perform a new Clinic operation for a student rejected by the Registrar availability rule.

3. Never dispense an unknown Inventory medicine.

4. Never dispense an inactive medicine.

5. Never deduct more medicine than Inventory reports as available.

6. Preserve the Inventory deduction transaction on a successful Clinic dispensation.

7. Attempt compensation when Inventory deduction succeeds but Clinic dispensation persistence fails.

8. Never roll back the same Clinic dispensation twice.

9. Preserve rollback transaction references after Inventory stock restoration.

10. Keep Faculty and Student Portal health-status endpoints read-only.

11. Return `NOT_AVAILABLE` only as a projection state when the student exists but no Clinic status exists.

12. Do not convert external identifiers into shared database ownership.



---



## 20. Integration Sequence Summary



### Student-dependent Clinic write



```text

Clinic request

    |

    v

ClinicService

    |

    v

Registrar validation

    |

    +-- missing student ------> 404

    |

    +-- inactive student -----> 422

    |

    v

Clinic-owned operation

```



### Medicine dispensation



```text

Clinic request

    |

    v

Registrar validation

    |

    v

Inventory deduction

    |

    | inventory_transaction_id

    v

Clinic dispensation persistence

    |

    +-- persistence failure --> Inventory compensation attempt

    |

    v

Clinic response

```



### Health-status projection



```text

Faculty / Student Portal request

    |

    v

authentication

    |

    v

Clinic integration endpoint

    |

    v

Registrar student existence check

    |

    v

latest Clinic health status

    |

    +-- none --> NOT_AVAILABLE projection

    |

    v

read-only projection response

```



---



## 21. Integration Invariants



The following are permanent integration invariants unless the project requirements explicitly change:



- Registrar owns student identity/profile.

- Inventory owns medicine catalog/stock.

- Clinic owns HealthRecord, Consultation, HealthStatus, and MedicineDispensation.

- Clinic references external IDs instead of defining cross-module database foreign keys.

- Registrar student routes in Clinic are read-only projections.

- Inventory medicine routes in Clinic are read-only projections.

- Medicine stock mutation is performed through the Inventory integration boundary.

- Clinic stores Inventory transaction references required for dispensation auditability.

- Faculty health-status access is read-only.

- Student Portal health-status access is read-only.

- External integration failures are translated through the Clinic API error contract.

- Midterm mocks may be replaced for finals without changing domain ownership.

- `main` is not updated directly; integration work proceeds through the reviewed integration branch and Pull Request workflow.



---



## 22. Validation Evidence



The project validation baseline includes:



- 167 permanent Django tests passing;

- 22 integration-focused permanent tests recorded in Phase 7 evidence;

- 45 canonical OpenAPI operations;

- 3 explicitly public operations;

- 42 protected operations;

- static OpenAPI validation passing;

- dynamic OpenAPI validation passing;

- static Redocly lint passing;

- dynamic Redocly lint passing;

- auth runtime/OpenAPI semantic parity passing after Phase 4.8;

- Postman collection with 45 requests;

- recorded Newman execution with 45 requests and 46 assertions with zero failures.



Final pre-merge validation will rerun the required automated, OpenAPI, Redocly, Swagger, Problem Details, and Postman gates.



---



## 23. Source Files



Primary integration implementation sources:



```text

backend/clinic/services/registrar.py

backend/clinic/services/inventory.py

backend/clinic/services/clinic.py

backend/clinic/urls.py

backend/clinic/views.py

backend/clinic/serializers.py

backend/clinic/models.py

backend/config/schema.py

openapi.yaml

docs/TEST-EVIDENCE.md

```



---



## 24. Related Documentation



See also:



```text

docs/architecture.md

docs/data-model.md

docs/design-system.md

docs/decisions/

README.md

API.md

SETUP.md

```



`docs/design-system.md`, `docs/decisions/`, and README synchronization are completed in later Phase 5 tasks.
