# Owner, Admin and Staff

The website has three roles, enforced by the backend API. Django `is_staff` is not the clinic role. Session login, `/api/auth/me/` and username-change responses include `role`: `OWNER`, `ADMIN`, `STAFF` (or null for an account with no clinic access).

| Capability | Owner | Admin | Staff |
| --- | --- | --- | --- |
| Use clinic features and reports | Yes | Yes | Yes |
| Create/edit/activate/deactivate/delete Staff | Yes | Yes | No |
| List/create/edit/activate/deactivate/delete Admins | Yes | No | No |
| Change own username/password in Settings | Yes | Yes | Yes |
| Delete/deactivate Owner through account management | No | No | No |

## Existing accounts

A fresh installation registers exactly one Owner through the website; registration immediately signs in and then closes permanently. Existing installations adopt their Owner through the singleton-registration migration. Optional CLI createsuperuser is a first-setup alternative only. There are no committed default credentials. CLINIC_ADMIN remains Admin and CLINIC_STAFF remains Staff; Owner has precedence. Owners are excluded from both management directories. Role changes through account-management payloads are rejected. See [OWNER-REGISTRATION.md](OWNER-REGISTRATION.md).

## Backend API

All protected operations require a Django session. All writes require `X-CSRFToken`. These checks run server-side even if a client bypasses the website.

| Route | Methods | Allowed role |
| --- | --- | --- |
| `/api/v1/admins/` | GET, POST | Owner |
| `/api/v1/admins/{user_id}/` | GET, PUT, PATCH, DELETE | Owner |
| `/api/v1/admins/{user_id}/activate/` | POST | Owner |
| `/api/v1/admins/{user_id}/deactivate/` | POST | Owner |
| `/api/v1/users/` | GET, POST | Owner, Admin |
| `/api/v1/users/{user_id}/` | GET, PUT, PATCH, DELETE | Owner, Admin |
| `/api/v1/users/{user_id}/activate/` | POST | Owner, Admin |
| `/api/v1/users/{user_id}/deactivate/` | POST | Owner, Admin |
| `/api/auth/username/change/` | POST | Signed-in user, current password |
| `/api/auth/password/change/` | POST | Signed-in user, current password |

Edits support `username`, `first_name`, `last_name` and `email`. Username validation trims whitespace, normalizes Unicode and rejects case-insensitive duplicates. Edits reject role, group, privilege, password and activation fields. Access changes use their dedicated endpoints. Creating an Admin requires the Owner current password and matching, validated new password. New Admins never receive Django superuser or Django staff privileges.

DELETE requires JSON `{ "current_password": "the acting user's password" }` and returns 204 with no body. Deactivation is reversible and revokes existing sessions; reactivation requires fresh sign-in. Deletion is permanent, revokes sessions, and preserves clinic medical records. Staff endpoints exclude Admins and Owners for every method, including mixed-role accounts. Owners are protected from delete/deactivate, and cannot be edited through management routes. The Owner can remove the last regular Admin because the Owner retains management access.

## Website

Owner sees the Administrators and Staff directories, with create, edit, activate/deactivate and delete controls. Admin sees only Staff management. Staff has no Administration navigation or dashboard management shortcut. Settings and the profile label display the actual clinic role. Owners use Settings for their own username/password.

## Validation

`authentication.tests.test_role_hierarchy` contains twelve role-matrix tests, including direct unauthorized API calls, mixed-role bypass attempts, immutable privileges, Owner credential changes, owner protection and clinical access for all three roles. The existing account-management and lifecycle tests now reflect Owner-only Admin management. The original backend contract tests and original Postman collection are preserved.

`frontend/tests/role-hierarchy.spec.js` exercises Owner editing an Admin, Admin managing Staff, Staff clinical access and denied management, and Admin deleting Staff. `postman/Role-hierarchy.postman_collection.json` provides 42 API requests covering the hierarchy. Use disposable Owner credentials for validation.

Current API inventory: 45 paths, 72 operations; 5 public and 67 protected. This role policy supersedes the earlier extension where Admins could manage other Admins.

Improvement security change: Faculty/Student Portal health-status demonstration endpoints now require active Clinic roles. Roleless authenticated sessions receive403; genuine external provider/subject authorization is not invented. Staff creation now uses Django password validators. See [IMPROVEMENT-VALIDATION.md](IMPROVEMENT-VALIDATION.md).
