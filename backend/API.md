# Clinic API documentation

The maintained API reference is [API.md](../API.md), backed by
[openapi.yaml](../openapi.yaml) and runtime `/api/schema/` (OpenAPI 3.1).
Swagger is `/docs`; ReDoc is `/api/schema/redoc/`.

Business routes use `/api/v1/`; authentication uses `/api/auth/`.
Django sessions and CSRF protect mutations. There is no HTTP Basic authentication
or anonymous access to medical records. Owner/Admin/Staff permissions are
specified in [ROLE-HIERARCHY.md](../docs/ROLE-HIERARCHY.md).
Registrar identities are read-only Clinic projections. Only the explicitly
labelled Owner mock workspace simulates Registrar changes.

The earlier unversioned student CRUD and AllowAny reference was obsolete and has
been replaced by this pointer to the canonical contract.
