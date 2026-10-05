
# Clinic System Data Model



## 1. Purpose



This document defines the data model of the IDSC Clinic System and explains how Clinic-owned data is represented during the midterm implementation and how the retained Django ORM models support the finals direction.



The most important distinction is that the current midterm business API does not persist Clinic-owned business records through Django ORM. Runtime Clinic business data is stored in `MockClinicRepository`.



Django ORM models and migrations are retained as the persistent data design for a later database-backed repository.



## 2. Domain Ownership Rules



The data model follows strict module ownership boundaries.



### Registrar-owned data



Registrar owns:



- student identity;

- student profile;

- course and section information; and

- `student_id`.



Clinic stores `student_id` only as an opaque external reference.



### Clinic-owned data



Clinic owns:



- `HealthRecord`;

- `Consultation`;

- `HealthStatus`; and

- `MedicineDispensation`.



### Inventory-owned data



Inventory owns:



- medicine catalog;

- medicine stock;

- `medicine_id`;

- Inventory stock transactions; and

- `inventory_transaction_id`.



Clinic stores Inventory identifiers only when required to reference an external medicine or transaction.



### Faculty and Student Portal



Faculty and Student Portal receive read-only health-status projections. They do not own or persist Clinic health-status records.



## 3. Runtime and Persistent Representations



The repository contains two related representations of Clinic business data.



### Midterm runtime representation



The active midterm business path is:



```text

ClinicService

    -> MockClinicRepository

    -> in-memory Python records

```



The mock repository is implemented in:



`backend/clinic/data/clinic.py`



It stores mutable in-memory records for the four Clinic-owned resources.



### Retained persistent representation



The retained Django ORM model design is implemented in:



`backend/clinic/models.py`



These models are not the active persistence mechanism for the midterm Clinic business API. They define the future database-backed representation that can be used behind the same service/repository boundary during finals.



## 4. External Identifier Strategy



External module identifiers are intentionally stored as strings rather than database foreign keys.



This applies to:



- `student_id` from Registrar;

- `medicine_id` from Inventory;

- `inventory_transaction_id` from Inventory; and

- `rollback_transaction_id` from Inventory.



This design prevents Clinic from taking database ownership of Registrar or Inventory entities.



Conceptually:



```text

Registrar Student

    -- student_id --> Clinic HealthRecord

    -- student_id --> Clinic Consultation

    -- student_id --> Clinic HealthStatus

    -- student_id --> Clinic MedicineDispensation



Inventory Medicine

    -- medicine_id --> Clinic MedicineDispensation



Inventory Transaction

    -- inventory_transaction_id --> Clinic MedicineDispensation

```



These are logical integration relationships, not Django foreign-key relationships.



## 5. HealthRecord



`HealthRecord` stores Clinic-owned persistent medical profile information associated with a Registrar student.



### Fields



| Field | Type / Shape | Ownership | Notes |

|---|---|---|---|

| `health_record_id` | integer / BigAutoField | Clinic | Primary identifier; read-only through the API |

| `student_id` | string, max 100 | Registrar reference | Indexed opaque Registrar identifier |

| `blood_type` | string, max 10 | Clinic | Controlled by blood-type choices |

| `allergies` | text | Clinic | Optional text |

| `medical_history` | text | Clinic | Optional text |

| `current_medications` | text | Clinic | Optional text |

| `height_cm` | decimal(5,2), nullable | Clinic | Must be positive; API also limits to 300 cm |

| `weight_kg` | decimal(5,2), nullable | Clinic | Must be positive; API also limits to 500 kg |

| `created_at` | datetime | Clinic | Generated timestamp; read-only |

| `updated_at` | datetime | Clinic | Generated timestamp; read-only |



### Blood-type choices



Supported values are:



- `A+`

- `A-`

- `B+`

- `B-`

- `AB+`

- `AB-`

- `O+`

- `O-`

- `Unknown`



### API validation



The serializer enforces:



- `student_id` cannot be blank;

- `blood_type` must be one of the supported choices;

- `height_cm`, when present, must be greater than 0 and no greater than 300; and

- `weight_kg`, when present, must be greater than 0 and no greater than 500.



### Persistent indexing design



The retained ORM model includes:



- a database index on `student_id`; and

- a composite index on `student_id` and descending `created_at`.



## 6. Consultation



`Consultation` represents a Clinic visit or consultation associated with a Registrar student.



### Fields



| Field | Type / Shape | Ownership | Notes |

|---|---|---|---|

| `consultation_id` | integer / BigAutoField | Clinic | Primary identifier; API read-only |

| `student_id` | string, max 100 | Registrar reference | Indexed opaque student identifier |

| `chief_complaint` | text | Clinic | Required non-blank complaint |

| `assessment` | text | Clinic | Optional assessment |

| `treatment` | text | Clinic | Optional treatment |

| `notes` | text | Clinic | Optional notes |

| `consulted_at` | datetime | Clinic | Generated consultation timestamp; API read-only |

| `created_at` | datetime | Clinic | Generated timestamp; API read-only |

| `updated_at` | datetime | Clinic | Generated timestamp; API read-only |



### API validation



The serializer enforces:



- `student_id` cannot be blank;

- `chief_complaint` cannot be blank; and

- a partial update must contain at least one field.



### Persistent indexing design



The retained ORM model includes:



- a database index on `student_id`; and

- a composite index on `student_id` and descending `consulted_at`.



## 7. HealthStatus



`HealthStatus` stores a Clinic-owned health-status assessment for a student.



### Fields



| Field | Type / Shape | Ownership | Notes |

|---|---|---|---|

| `status_id` | integer / BigAutoField | Clinic | Primary identifier; API read-only |

| `student_id` | string, max 100 | Registrar reference | Indexed opaque student identifier |

| `status` | string, max 32 | Clinic | Controlled by Clinic health-status choices |

| `remarks` | text | Clinic | Optional remarks |

| `effective_at` | datetime | Clinic | Generated effective timestamp; API read-only |

| `created_at` | datetime | Clinic | Generated timestamp; API read-only |

| `updated_at` | datetime | Clinic | Generated timestamp; API read-only |



### Stored status choices



Persistent Clinic status values are:



- `CLEARED`

- `RESTRICTED`

- `UNDER_OBSERVATION`



`NOT_AVAILABLE` is not a stored database choice. It is an integration response state used when a Registrar student exists but Clinic has no health-status record for that student.



### API validation



The serializer enforces:



- `student_id` cannot be blank;

- `status` must be one of the stored Clinic health-status choices; and

- a partial update must contain at least one field.



### Persistent indexing design



The retained ORM model includes:



- a database index on `student_id`;

- a composite index on `student_id` and descending `effective_at`; and

- an index on `status`.



## 8. MedicineDispensation



`MedicineDispensation` is a Clinic-owned audit record describing medicine dispensed to a student.



Medicine catalog and stock remain owned by Inventory.



### Fields



| Field | Type / Shape | Ownership | Notes |

|---|---|---|---|

| `dispensation_id` | integer / BigAutoField | Clinic | Primary identifier; API read-only |

| `student_id` | string, max 100 | Registrar reference | Indexed opaque student identifier |

| `medicine_id` | string, max 100 | Inventory reference | Indexed opaque medicine identifier |

| `quantity` | positive integer | Clinic | Must be at least 1 |

| `reason` | text | Clinic | Optional reason |

| `status` | string, max 20 | Clinic | `COMPLETED` or `ROLLED_BACK`; read-only through create/update input |

| `inventory_transaction_id` | string, max 100 | Inventory reference | Transaction produced by stock deduction; read-only |

| `rollback_transaction_id` | string or null | Inventory reference | Transaction produced by stock restoration; read-only |

| `dispensed_at` | datetime | Clinic | Generated timestamp; read-only |

| `rolled_back_at` | datetime or null | Clinic | Set when rollback completes; read-only |

| `created_at` | datetime | Clinic | Generated timestamp; read-only |



### Dispensation status choices



Stored values are:



- `COMPLETED`

- `ROLLED_BACK`



### API validation



The serializer enforces:



- `student_id` cannot be blank;

- `medicine_id` cannot be blank; and

- `quantity` must be greater than or equal to 1.



The following fields are controlled by backend orchestration and are read-only to API clients:



- `dispensation_id`;

- `status`;

- `inventory_transaction_id`;

- `rollback_transaction_id`;

- `dispensed_at`;

- `rolled_back_at`; and

- `created_at`.



### Persistent indexing design



The retained ORM model includes:



- an index on `student_id`;

- an index on `medicine_id`;

- a composite index on `student_id` and descending `dispensed_at`;

- a composite index on `medicine_id` and descending `dispensed_at`; and

- an index on `status`.



## 9. Read-Only External Projections



External module data is represented through plain serializers rather than Clinic ORM models.



### Student projection



`StudentSerializer` represents Registrar-owned student information.



Fields are read-only:



- `student_id`

- `first_name`

- `last_name`

- `course`

- `section`

- `status`



This serializer is deliberately not a `ModelSerializer` and must not create, update, or delete Registrar students.



### Medicine projection



`MedicineSerializer` represents Inventory-owned medicine and stock information.



Fields are read-only:



- `medicine_id`

- `name`

- `generic_name`

- `unit`

- `quantity_in_stock`

- `reorder_level`

- `is_low_stock`

- `status`



This serializer is deliberately not a `ModelSerializer` and must not mutate Inventory master data.



## 10. Health-Status Integration Projection



Faculty and Student Portal receive a restricted read-only health-status representation through `HealthStatusProjectionSerializer`.



Projection fields are:



- `student_id`

- `status`

- `remarks`

- `effective_at`



This projection intentionally exposes a limited Clinic-owned view rather than the complete health record.



## 11. Mock Runtime Record Shapes



`MockClinicRepository` mirrors the important public fields of the Clinic-owned resources using Python dictionaries.



The runtime demonstration seed currently contains:



| Resource | Seed record count |

|---|---:|

| Health records | 2 |

| Consultations | 2 |

| Health statuses | 2 |

| Medicine dispensations | 1 |



The mock repository assigns integer identifiers and runtime UTC timestamps when new records are created.



The repository deep-copies returned records so callers cannot accidentally mutate stored state outside repository operations.



The repository supports:



- `reset()` to restore demonstration seed data; and

- `clear()` to create an empty deterministic store for isolated automated tests.



## 12. Logical Relationship Model



The Clinic data model can be visualized as follows:



```text

REGISTRAR

Student

  student_id

      |

      | external opaque reference

      +-------------------+-------------------+-------------------+

      |                   |                   |                   |

      v                   v                   v                   v

HealthRecord        Consultation        HealthStatus      MedicineDispensation

 health_record_id    consultation_id     status_id         dispensation_id

 student_id          student_id          student_id        student_id

                                                             |

                                                             | medicine_id

                                                             v

                                                         INVENTORY

                                                         Medicine

                                                             |

                                                             | transaction IDs

                                                             v

                                                      Inventory Transaction

```



No cross-module relationship above is implemented as a database foreign key in Clinic.



## 13. Ownership and Referential Integrity



Because external identifiers are not foreign keys, cross-module referential integrity is enforced at the service/integration boundary rather than by the Clinic database schema.



Examples:



- `ClinicService` validates `student_id` through Registrar before student-dependent Clinic writes;

- medicine dispensing coordinates with Inventory before the Clinic dispensation record is created; and

- Inventory transaction identifiers are recorded on the Clinic dispensation for audit and rollback coordination.



This allows each CMS module to remain independently deployable and independently authoritative for its own data.



## 14. Read-Only and Server-Controlled Fields



The API differentiates client-provided values from server-controlled values.



### HealthRecord server-controlled fields



- `health_record_id`

- `created_at`

- `updated_at`



### Consultation server-controlled fields



- `consultation_id`

- `consulted_at`

- `created_at`

- `updated_at`



### HealthStatus server-controlled fields



- `status_id`

- `effective_at`

- `created_at`

- `updated_at`



### MedicineDispensation server-controlled fields



- `dispensation_id`

- `status`

- `inventory_transaction_id`

- `rollback_transaction_id`

- `dispensed_at`

- `rolled_back_at`

- `created_at`



This prevents clients from directly forging resource identifiers, lifecycle timestamps, stock transaction identifiers, or rollback state.



## 15. Data Lifecycle



### Health records, consultations, and health statuses



These resources follow normal Clinic-owned CRUD lifecycle operations through `ClinicService` and the active repository.



### Medicine dispensation



Medicine dispensation has an integration-aware lifecycle.



Creation:



```text

validate Registrar student

    -> deduct Inventory stock

    -> obtain inventory_transaction_id

    -> create Clinic dispensation

```



Rollback:



```text

load Clinic dispensation

    -> restore Inventory stock

    -> obtain rollback_transaction_id

    -> mark Clinic dispensation ROLLED_BACK

```



This lifecycle is why Inventory transaction identifiers are part of the Clinic dispensation data model even though Inventory owns the underlying transactions.



## 16. Database Table Names for Finals Direction



The retained ORM model uses these explicit table names:



| Model | Database table |

|---|---|

| `HealthRecord` | `health_records` |

| `Consultation` | `consultations` |

| `HealthStatus` | `health_statuses` |

| `MedicineDispensation` | `medicine_dispensations` |



These tables represent the persistent finals direction and are not the active midterm Clinic business store.



## 17. Storage Configuration Boundary



`CLINIC_DATA_BACKEND` defaults to:



`mock`



The default Django database is SQLite and exists for framework infrastructure.



PostgreSQL remains configurable for the finals direction, but switching the Django database engine alone does not change the active Clinic business repository.



A database-backed Clinic repository must be deliberately wired behind `ClinicService` before Clinic business records become persistent.



## 18. Data-Model Invariants



The following data-model rules must remain true unless an explicit architecture decision changes them:



1. Registrar owns student identity and profile data.

2. Inventory owns medicine catalog, stock, and Inventory transactions.

3. Clinic owns HealthRecord, Consultation, HealthStatus, and MedicineDispensation.

4. External identifiers remain references and do not transfer domain ownership.

5. Registrar and Inventory entities are not represented as Clinic-owned ORM models.

6. Faculty and Student Portal consume read-only Clinic health-status projections.

7. Midterm Clinic business data remains in `MockClinicRepository`.

8. The Django framework database is separate from the current midterm Clinic business store.

9. A future database repository must preserve the same service and public API boundaries.

10. Medicine stock changes remain coordinated through the Inventory boundary.

11. Inventory transaction identifiers on dispensations exist for auditability and rollback coordination.

12. Client requests cannot directly control server-generated IDs, lifecycle timestamps, or Inventory transaction references.



## 19. Source Files



The primary sources for this data model are:



- `backend/clinic/models.py`

- `backend/clinic/serializers.py`

- `backend/clinic/data/clinic.py`

- `backend/clinic/services/clinic.py`

- `backend/config/settings.py`

- `openapi.yaml`

- `docs/architecture.md`



## 20. Related Documentation



This document should be read together with:



- `docs/architecture.md`

- `docs/integration.md`

- `docs/design-system.md`

- `docs/decisions/`

- `API.md`

- `openapi.yaml`

- `docs/TEST-EVIDENCE.md`
