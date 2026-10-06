# ADR 0004: Use Session Authentication with CSRF and Credentialed CORS

## Status

Accepted

## Context

The Clinic backend and frontend run separately during local development.

The frontend is expected to call the Django API while preserving authenticated session state.

Session authentication requires CSRF protection for unsafe requests and credential-aware CORS configuration when frontend and backend origins differ.

The backend also needs clear distinction between authentication failure and permission failure.

## Decision

The current Clinic application uses Django/DRF session authentication as the midterm authentication mechanism.

The backend configuration will:

- use `ClinicSessionAuthentication` as the default DRF authentication class;
- require authenticated access by default unless an endpoint is explicitly public;
- preserve Django `CsrfViewMiddleware`;
- issue a CSRF token through the authentication API;
- require CSRF protection for unsafe session-authenticated requests;
- allow credentialed CORS only for the approved local Vite origins;
- trust the same local Vite origins for CSRF;
- keep public operations explicit rather than making the API broadly anonymous.

Approved local frontend origins are:

- `http://localhost:5173`
- `http://127.0.0.1:5173`

## Rationale

Django sessions are already integrated with Django authentication and provide an appropriate midterm mechanism for a browser-based frontend.

CSRF protection is required because browsers automatically attach session cookies.

Restricting CORS to known local frontend origins is safer and more representative of the intended architecture than allowing all origins.

## Consequences

### Positive

- Browser authentication uses standard Django session behavior.
- CSRF enforcement protects unsafe authenticated requests.
- Unauthorized and forbidden conditions can be represented distinctly.
- Local React/Vite development is supported with credentials.
- Public endpoint exposure remains explicit.

### Trade-offs

- Frontend requests must obtain and send CSRF tokens correctly.
- Cross-system finals integration may require a different trust mechanism from browser session authentication.
- CORS and CSRF origin lists must be updated deliberately when deployment origins change.

## Implementation Evidence

Relevant source:

- `backend/config/settings.py`
- `backend/authentication/authentication.py`
- `backend/authentication/views.py`
- `backend/authentication/urls.py`
- `backend/authentication/permissions.py`

Verified settings include:

- `ClinicSessionAuthentication`
- default `IsAuthenticated`
- `CsrfViewMiddleware`
- `CORS_ALLOW_CREDENTIALS = True`
- explicit local Vite CORS origins
- explicit local Vite CSRF trusted origins

Verified tests cover:

- CSRF token issuance;
- rejection of login without required CSRF;
- login with CSRF;
- authenticated session access;
- logout;
- canonical 401 Problem Details after logout;
- role-based permission behavior.

## Invariants

1. Do not remove CSRF protection merely to simplify frontend requests.
2. Do not enable wildcard credentialed CORS.
3. Public endpoints must remain explicitly designated.
4. Protected operations must keep authentication metadata consistent with runtime behavior.
5. Finals cross-module trust may replace the midterm session boundary, but it must be designed explicitly.

## Related Documentation

- `docs/architecture.md`
- `docs/integration.md`
- `docs/TEST-EVIDENCE.md`
- `openapi.yaml`
