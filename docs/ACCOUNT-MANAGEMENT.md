# Username and account management

## Own username

POST /api/auth/username/change/ accepts new_username/current_password, acts only on the signed-in account and returns the updated session user. It verifies the current password on the locked account, validates length/characters, trims and Unicode-normalizes the name, and rejects case-insensitive duplicates or unchanged names. Session remains authenticated; subsequent login uses the new name. Settings provides field errors and immediate profile refresh.

## Managed accounts

Only Owner can list/create/edit Admins through /api/v1/admins/ and its detail routes. Owner and Admin manage Staff through /api/v1/users/. Staff cannot administer accounts. Direct requests enforce the same rules. Owner is excluded from these directories; ordinary account routes cannot create a second Owner.

Admin creation accepts username/password/confirm_password/current_password and optional first_name/last_name/email. Owner current password and strong matching new password are required. Created account receives CLINIC_ADMIN only, never superuser or Django staff privileges. Maximum five includes inactive Admins; Owner is excluded. Staff creation remains Staff-only.

Managed edits support username/first_name/last_name/email. Role/group/privilege/password/activation fields cannot be used to bypass dedicated flows. Activation/deactivation and permanent deletion use separate endpoints. DELETE requires acting user current_password and CSRF, returns 204 and preserves Clinic medical records.

All operations require sessions and appropriate roles; writes require X-CSRFToken. Invalid fields return 400 Problem Details; unauthorized authenticated users 403; anonymous callers 401. See [API.md](../API.md), [ROLE-HIERARCHY.md](ROLE-HIERARCHY.md), [ACCOUNT-LIMITS.md](ACCOUNT-LIMITS.md) and [ACCOUNT-LIFECYCLE.md](ACCOUNT-LIFECYCLE.md).

## Validation

Backend account/username tests and browser stories cover validation, direct authorization, session retention, account editing and login. Tests require disposable Owner credentials, not a regular Admin for Admin-management stories. postman/Account-management.postman_collection.json is a mutating feature collection; use an isolated database. Latest recorded results are in [CURRENT-VALIDATION.md](CURRENT-VALIDATION.md); earlier stage results remain in [INTEGRATION-VALIDATION.md](INTEGRATION-VALIDATION.md).
