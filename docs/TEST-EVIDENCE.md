# Phase 7 — Tests & Contract Validation Evidence

## 1. Purpose

This document records the verified testing, contract-validation, regression, lifecycle, and repository-integrity evidence produced during Phase 7 of the IDSC Clinic System backend.

Phase 7 covers:

- automated backend regression testing
- API contract validation
- authentication and permission regression
- integration contract validation
- reports and data consistency
- CORS and browser contract validation
- Postman request coverage
- Newman execution
- database lifecycle verification
- repository and deliverable hygiene

The evidence in this document is based on the validation commands and terminal results produced during Phase 7.

---

## 2. Final Phase 7 Baseline

| Item | Verified Result |
|---|---:|
| Branch | `phase7/tests-contract-validation` |
| Permanent Django tests | 167 |
| Permanent Django tests passed | 167 |
| Permanent Django tests failed | 0 |
| OpenAPI version | 3.1.0 |
| OpenAPI paths | 29 |
| OpenAPI operations | 45 |
| Public operations | 3 |
| Protected operations | 42 |
| `BadGateway` response present | No |
| Postman requests | 45 |
| Postman requests with status assertions | 45 |
| Newman requests executed | 45 |
| Newman failed requests | 0 |
| Newman test scripts | 45 |
| Newman failed test scripts | 0 |
| Newman assertions | 46 |
| Newman failed assertions | 0 |
| Persistent domain database after regression | Clean |
| Temporary artifacts remaining after cleanup | 0 |
| Unstaged tracked changes at final consistency check | 0 |
| Untracked files at final consistency check | 0 |

---

## 3. Permanent Automated Tests

The permanent Django test suite was reorganized into dedicated test modules under:

```text
authentication/tests/
clinic/tests/
```

The permanent suite contains 167 test methods across eight test modules:

| Test module | Test methods |
|---|---:|
| `authentication/tests/test_auth.py` | 11 |
| `clinic/tests/test_consultations.py` | 25 |
| `clinic/tests/test_dispensations.py` | 26 |
| `clinic/tests/test_health_records.py` | 22 |
| `clinic/tests/test_health_statuses.py` | 25 |
| `clinic/tests/test_integrations.py` | 22 |
| `clinic/tests/test_permissions.py` | 17 |
| `clinic/tests/test_reports.py` | 19 |
| **Total** | **167** |

### Verified regression run

Command:

```powershell
python manage.py test --verbosity 1
```

Verified result:

```text
Found 167 test(s).
Ran 167 tests
OK
Destroying test database for alias 'default'...
```

The test suite completed with zero failures and the temporary Django test database was destroyed after execution.

---

## 4. OpenAPI Contract Validation

The canonical OpenAPI contract was validated against the expected Phase 7 structure.

| Contract property | Verified result |
|---|---:|
| OpenAPI version | 3.1.0 |
| Paths | 29 |
| Operations | 45 |
| Public operations | 3 |
| Protected operations | 42 |
| `BadGateway` response | Absent |

The canonical structure check returned:

```text
OPENAPI = 3.1.0
PATHS = 29
OPERATIONS = 45
PUBLIC = 3
PROTECTED = 42
BADGATEWAY PRESENT = False
OPENAPI CANONICAL = True
```

---

## 5. Postman Collection Validation

The final Postman collection contains 45 API requests.

| Validation | Result |
|---|---:|
| Requests | 45 |
| Requests with status assertions | 45 |
| JSON validity | PASS |
| Canonical request count | PASS |

The staged collection was independently read from Git's index and successfully parsed as JSON.

Verified collection metadata:

```text
COLLECTION NAME = IDSC Clinic System API
COLLECTION SCHEMA = https://schema.getpostman.com/json/collection/v2.1.0/collection.json
```

---

## 6. Newman Execution Evidence

The Phase 7 Postman collection was executed through Newman.

| Newman result | Verified result |
|---|---:|
| Requests executed | 45 |
| Failed requests | 0 |
| Test scripts | 45 |
| Failed test scripts | 0 |
| Assertions | 46 |
| Failed assertions | 0 |

The recorded Newman result therefore completed without request failures or failed test assertions.

---

## 7. Authentication and Permission Regression

Authentication and authorization behavior was included in the permanent regression suite.

The permanent authentication test module contains 11 tests, while the permission regression module contains 17 tests.

The Phase 7 suite verifies the documented authentication, permission, and protected-endpoint behavior through automated Django tests.

---

## 8. Integration Contract Validation

Integration behavior was included in the permanent regression suite.

The integration test module contains 22 tests.

The validated integration areas include the Clinic integration endpoints represented by the permanent test suite, including Student Portal, Faculty, Registrar, and Inventory-related contracts.

---

## 9. Reports and Data Consistency

Reports and data-consistency behavior was included in the permanent regression suite.

The reports test module contains 19 tests.

Phase 7 regression also verified that the persistent Clinic domain database remained clean after the final test run.

Verified persistent domain counts:

```text
HealthRecord = 0
Consultation = 0
HealthStatus = 0
MedicineDispensation = 0
DOMAIN DATABASE CLEAN = True
```

---

## 10. CORS and Browser Contract Validation

CORS and browser-contract validation was completed during Phase 7 and is recorded as a completed Phase 7 validation area.

The final Phase 7 evidence baseline therefore records CORS and browser contract validation as part of the completed regression work.

---

## 11. Database Lifecycle Verification

Permanent Django regression uses Django's test database lifecycle.

The final regression run verified:

1. A test database was created.
2. All 167 permanent tests executed successfully.
3. The test database was destroyed after execution.
4. A separate persistent-database check confirmed that Clinic domain tables remained empty.

---

## 12. Repository Integrity and Hygiene

Phase 7 included repository-integrity checks covering staged content, working-tree state, temporary artifacts, and diff integrity.

Final consistency verification recorded:

| Repository check | Result |
|---|---:|
| Current branch | `phase7/tests-contract-validation` |
| Staged files | 18 |
| Unstaged tracked files | 0 |
| Untracked files | 0 |
| Missing required Phase 7 files | 0 |
| Staged/unstaged overlap | 0 |
| Forbidden artifact patterns | 0 |
| Staged diff check | PASS |
| Working-tree diff check | PASS |

Temporary recovery artifacts were removed before the final staged-content audit.

---

## 13. Django and Migration Integrity

The final Phase 7 integrity checks verified the Django project and migration state.

Verified commands:

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
git diff --check
```

Verified results:

```text
System check identified no issues (0 silenced).
No changes detected
Diff-check exit = 0
```

---

## 14. Phase 7 Evidence Summary

Phase 7 produced the following verified evidence:

- 167 permanent Django tests passing.
- 45 canonical OpenAPI operations.
- 29 OpenAPI paths.
- 3 public operations.
- 42 protected operations.
- 45 Postman requests.
- 45 Postman requests with status assertions.
- 45 Newman requests executed.
- 0 Newman request failures.
- 46 Newman assertions.
- 0 Newman assertion failures.
- Clean persistent Clinic domain database after regression.
- No temporary recovery artifacts remaining.
- No unstaged tracked changes at final consistency verification.
- No untracked files at final consistency verification.

These results represent the recorded Phase 7 test and contract-validation evidence before the Phase 7 commit and push stage.

---

## 15. Evidence Status

**Phase 7 test and contract-validation evidence: COMPLETE.**

The evidence document itself must be included in the Phase 7 commit together with the already staged backend tests, OpenAPI contract, and Postman collection.

Phase 7 remains subject to the final commit and push procedure documented as Goal 7.12.