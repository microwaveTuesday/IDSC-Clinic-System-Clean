# One-time Owner registration

On a fresh database, migrate and start the backend and frontend. The first screen registers the single system Owner. Username, password and confirmation are required; names and email are optional. Password validators match the password-change flow. Success immediately signs in and opens Dashboard. Logout, reload and other browsers then show the shared login for Owner, Admin and Staff.

## Backend contract

- GET `/api/auth/setup/`: public, no-store response `{ "owner_registration_available": true }` only before setup. No account details are exposed.
- POST `/api/auth/owner/register/`: public first-run operation requiring CSRF cookie/header. Accepts `username`, `password`, `confirm_password`, optional `first_name`, `last_name`, `email`. Returns 201 with message and authenticated Owner user; starts a Django session.
- Invalid fields/passwords return 400 Problem Details; missing CSRF returns 403; completed or competing setup returns 409. Role/privilege fields cannot create a different role.
- A transaction locks the singleton registration row. A database unique index allows only one superuser, including bulk writes. The permanent Owner reference prevents deletion and keeps setup closed even after an out-of-band role change. Ordinary model saves also reject second Owners and deactivation/demotion of the registered Owner.
- `createsuperuser` remains an optional first-setup CLI alternative, and also closes website registration. It cannot create a second Owner.

## Existing installations

Migration `authentication.0002_single_owner_registration` adopts the existing Owner. If a development database contains multiple legacy superusers, it prefers clinic_owner, then demo_admin, then a non-legacy Owner; other former Owners are retained as inactive Staff. Their records remain. Existing sessions are cleared when multiple Owners are normalized. Back up the authentication database before migrating and review legacy development accounts. Owner username/password changes remain available in Settings. Never delete the database to reopen registration on a real installation.

The Desktop installation was backed up privately before migration. It was subsequently reset at the operator's request, and first-run registration was verified before handing it back. Database backups and local account data are ignored by Git. A newly cloned installation with a fresh database will show registration.

First setup must be completed by the intended operator before exposing a fresh installation publicly. Registrar/Inventory business mock data still resets on backend restart; this feature persists Owner/authentication state in the framework database.

## Validation

- 16 new backend tests pass with the configured password hashing: CSRF, validation, session creation, permanent closure, role enforcement, singleton database constraint and Owner protection.
- Full backend regression: 273 tests pass with a test-only fast password hasher override; production settings remain unchanged.
- Two simultaneous registration requests against an isolated SQLite database returned 201 and 409; exactly one Owner existed afterward.
- Fresh-install browser test passed registration/mismatch handling, automatic Dashboard, logout, reload, normal login and another browser seeing login. Run `owner-registration.spec.js` with `CLINIC_TEST_FIRST_RUN=1` only against a freshly migrated isolated database.
- Frontend lint/build and static OpenAPI lint pass. Static and runtime contracts contain 45 paths and 72 operations.

## Empty local mock startup

Set `CLINIC_EMPTY_START=1` in the private `backend/.env` to start Clinic records, mock Registrar students and mock Inventory medicines empty rather than loading demonstration samples. It does not erase authentication accounts. The Desktop reset cleared the authentication database separately after saving a recovery backup outside the repository. The environment file, database, accounts and recovery backups are not committed.

Without this option, the existing demonstration seeds remain available. Run regression tests with `CLINIC_EMPTY_START=0` to exercise their standard fixtures.
