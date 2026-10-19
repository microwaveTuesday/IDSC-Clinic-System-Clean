# Self-service password change

POST `/api/auth/password/change/` adds one authenticated operation. All 45 existing static operations are unchanged; With the later account-management extension, current inventories contain 35 paths / 53 operations, including 3 public and 50 protected operations.

## Contract

Request JSON has three required, write-only strings: `current_password`, `new_password`, `confirm_password` (maximum 1024 characters; whitespace preserved). The server always updates the authenticated user, regardless of additional account identifiers supplied in a request.

The endpoint verifies the current password, checks confirmation and rejects reuse of the current password. It applies the configured Django minimum-length, common-password, numeric-password and user-attribute-similarity validators. Validation errors return HTTP 400 Problem Details with field-specific `errors`. Unauthenticated requests return 401, invalid CSRF returns 403, and methods other than POST return 405. Success returns HTTP 200 with only a message.

The account is re-read under a transaction and row lock before validation. Passwords are hashed using `set_password`. `update_session_auth_hash` rotates and retains the current session; other sessions expire on their next request. No migration or weakened session/CSRF setting is needed.

Official references: [Django password validation](https://docs.djangoproject.com/en/6.1/topics/auth/passwords/) and [session invalidation](https://docs.djangoproject.com/en/6.1/topics/auth/default/#session-invalidation-on-password-change).

## Frontend

Open Settings > Change password. Enter your current password, new password and confirmation. The dialog validates matching confirmation, blocks duplicate submissions, shows backend field errors, clears inputs on success and displays confirmation. A 401 clears an expired session and asks the user to sign in again. Passwords remain in the form/request only and are never written to browser storage. Both themes style the dialog.

## Validation

Thirteen additional backend tests cover authentication, CSRF, wrong-current-password errors, confirmation, reuse, all configured validators, missing/blank fields, length limits, whitespace, password hashing, session rotation, other-session invalidation, old/new login, account isolation and protected write-only schema fields. The latest full suite has 221 passing tests, including 13 password-change, 18 account-management and 23 lifecycle additions; the previous 167 tests are unchanged.

`frontend/tests/password-change.spec.js` uses an isolated account and verifies wrong current password, mismatched confirmation, common-password rejection, successful change, retained session after reload, rejected old-password login and successful new-password login. Cleanup restores the original strong password.

The original Postman collection remains unchanged. `postman/Password-change.postman_collection.json` adds 11 requests that change and restore an isolated account's password. Supply `username`, `password`, and `newPassword`. Use an isolated test account only.

See `INTEGRATION-VALIDATION.md` for execution evidence. Passwords use Django's framework database; Clinic business data remains in the documented mock runtime.
