# Current validation record

> Earlier submission background. Current improvement architecture/storage and evidence: [DATABASE.md](DATABASE.md), [IMPROVEMENT-VALIDATION.md](IMPROVEMENT-VALIDATION.md), [KNOWN-LIMITATIONS.md](KNOWN-LIMITATIONS.md).

As of 19 October 2026, submission/clinic-final-project implements the features in [README.md](../README.md). Historical reports retain their stage-specific counts; use this page for latest implementation evidence.

| Check | Recorded result and scope |
| --- | --- |
| Full backend suite | 273 passed with test-only MD5PasswordHasher override for execution speed; production settings unchanged |
| Owner-registration tests | All 16 passed with configured hashing |
| Simultaneous setup | Two requests against isolated SQLite returned 201/409; exactly one Owner |
| Fresh-install browser | Registration validation, automatic Dashboard, logout/reload/login and second-browser login-only passed |
| Modal-focus browser | Password focus across refresh and keyboard close/pending-state regression passed |
| Frontend | ESLint and production build passed |
| Django | System check and migration drift check passed |
| API | Static schema lint and runtime schema generation/validation passed; 45 paths/72 operations, 5 public/67 protected |
| Manual local reset | Empty accounts/sessions/Clinic/Registrar/Inventory and visible registration verified; this check did not create a new Owner |

Earlier clinical/account/external browser and Postman runs are recorded in [INTEGRATION-VALIDATION.md](INTEGRATION-VALIDATION.md), [TEST-EVIDENCE.md](TEST-EVIDENCE.md) and feature documents. They were not all rerun for Owner registration or this documentation update. The original collection's recorded baseline is 45 requests/46 assertions.

Backend tests use CLINIC_EMPTY_START=0 for standard seed fixtures. The faster-hasher suite checks behavior, not production hashing performance; the separate normal-hasher registration run covers configured hashing. Browser fixtures and disposable accounts are described in [frontend/README.md](../frontend/README.md).

Documentation review checks local Markdown links, complete endpoint-table coverage, runtime/static operation equality, stale current counts/branch names and Git whitespace. This does not imply another full browser or Postman run.
