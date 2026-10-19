# Account activation, deactivation and deletion

Owner manages Admins; Owner/Admin manage Staff. Staff has no account-management access. This policy applies to direct API requests and the website.

| Routes | Methods | Role |
| --- | --- | --- |
| /api/v1/admins/{user_id}/ | GET, PUT, PATCH, DELETE | Owner |
| /api/v1/admins/{user_id}/activate/ | POST | Owner |
| /api/v1/admins/{user_id}/deactivate/ | POST | Owner |
| /api/v1/users/{user_id}/ | GET, PUT, PATCH, DELETE | Owner, Admin |
| /api/v1/users/{user_id}/activate/ | POST | Owner, Admin |
| /api/v1/users/{user_id}/deactivate/ | POST | Owner, Admin |

Writes require session authentication and CSRF. DELETE additionally verifies JSON current_password for the actor and returns 204. Invalid passwords return 400 with field errors; anonymous callers 401; unauthorized callers 403; wrong-role/missing targets 404; conflicting access states 409.

Registered Owner cannot be removed/deactivated/demoted. Self-removal is blocked. Owner can remove the last regular Admin because Owner retains management access. Staff routes exclude Admins/Owners, including mixed-group accounts. Actor/target permissions are rechecked under transaction locks.

Deactivation revokes existing database sessions. Reactivation permits a fresh login without reviving old sessions. Permanent deletion removes the login account and sessions but preserves medical records. Deactivated Admins still count toward the five-account cap; deletion frees capacity.

Administration provides confirmation dialogs, password verification for Delete, disabled protected controls and backend errors. Directory capability fields are UI hints; backend checks remain authoritative. Own username/password changes belong in Settings.

Backend and browser lifecycle/role tests cover these rules. Feature Postman collections mutate accounts and must use disposable credentials/data. Current results: [CURRENT-VALIDATION.md](CURRENT-VALIDATION.md). Details: [ROLE-HIERARCHY.md](ROLE-HIERARCHY.md), [ACCOUNT-LIMITS.md](ACCOUNT-LIMITS.md), [OWNER-REGISTRATION.md](OWNER-REGISTRATION.md).
