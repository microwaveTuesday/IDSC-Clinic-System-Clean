# Deployment profile and boundaries

## Verification branch container profile

`deploy/compose.yml` supplies PostgreSQL, one Gunicorn worker, and Caddy HTTPS
serving the production React build and Django static files. Backend/database
ports are private; only localhost HTTPS is published. PostgreSQL and simulated
Inventory use separate named volumes. No real external connectivity is claimed.

Set private `SECRET_KEY` (random, at least 50 characters) and `DB_PASSWORD` in the
operator environment, then run from the repository root:

```text
docker compose -f deploy/compose.yml config --quiet
docker compose -f deploy/compose.yml up --build --detach --wait
```

Open `https://localhost`. Caddy uses an internal CA for controlled staging; install
its root certificate in the demo machine's trust store after verifying its origin.
Never disable TLS verification. CI trusts only its disposable proxy certificate.
Public institutional deployment requires approved certificates/DNS and review.

Startup applies migrations and collects static files before starting Gunicorn.
Back up before upgrading. The healthcheck queries setup status through the DB.
Review logs privately. `TRUST_PROXY_HTTPS=1` is appropriate only with the private
backend and trusted proxy overwriting forwarded protocol; never expose that
backend directly. Schedule `purge_replay_bodies` hourly.

Shutdown: `docker compose -f deploy/compose.yml down` preserves volumes. Do not
add `--volumes` on an installation you need; it is only for disposable CI cleanup.
Back up both stores with writes stopped: [BACKUP-RESTORE.md](BACKUP-RESTORE.md).
One worker is intentional because Registrar/default mocks and login cache remain
process-local.

The deployment CI job builds both images, verifies trusted HTTPS/session/CSRF,
registers a synthetic Owner, writes records, restarts the backend and checks stock,
references and rollback. The actual outcome is in VERIFICATION-RESULTS.md;
configuration alone is not evidence. Public hosted deployment remains unverified.

## Earlier improvement profile

This is a school final-project runtime. No live Registrar/Inventory adapter, hosted TLS deployment or disaster-recovery exercise is claimed.

## Preparation

1. Use the clean repository improvement/clinic-final-10of10 branch. Install requirements-finals.txt for PostgreSQL and run migrations after backing up existing data.
2. Configure CLINIC_DATA_BACKEND=database and private PostgreSQL connection values. Registrar/Inventory remain mocks and must use a single application worker for shared demo state. Do not scale the mock provider across independent workers.
3. Complete Owner registration privately before exposing the application. First setup is a first-claim capability, not a public identity-verification process. Save the credentials privately; later registration is permanently closed.
4. Build the frontend with npm ci and npm run build. Serve frontend/dist with a web server and route same-origin /api to Django. Vite preview alone is not the API proxy. Configure static files for Django administration.
5. Put a production WSGI/ASGI server behind HTTPS with an explicit reverse-proxy trust policy. Do not use Django runserver as an internet deployment. An example topology is HTTPS reverse proxy -> one application worker -> PostgreSQL. This topology was documented, not hosted or load-tested here.

## Required production settings

```ini
DEBUG=False
SECRET_KEY=privately-generated-random-value-at-least-50-characters
ALLOWED_HOSTS=clinic.your-school.example
CLINIC_DATA_BACKEND=database
CORS_ALLOWED_ORIGINS=https://clinic.your-school.example
CSRF_TRUSTED_ORIGINS=https://clinic.your-school.example
```

Replace example values; never commit actual secrets. DEBUG=False fails startup without a private long secret or explicit non-wildcard hosts. Secure session/CSRF cookies, HTTPS redirect, HSTS and JSON-only API rendering are enabled. `python manage.py check --deploy` passed with explicit validation settings. Actual certificate/proxy behavior was not exercised. Configure forwarded-protocol trust only for an independently trusted proxy; otherwise HTTPS redirection may loop behind TLS termination.

Production login throttling is10/minute per direct peer IP. Arbitrary X-Forwarded-For is not trusted. The default cache is process-local; a shared cache and trusted client-IP design are required before multi-worker deployment. Behind a proxy the peer-based limit may group users together. This is documented operational work, not a distributed anti-abuse guarantee.

SMTP is selected in the production profile, but no email workflow/provider delivery was tested. Supply EMAIL_HOST if email is later used. Maintain database backups, least-privilege credentials, log access controls and a tested restore procedure.

## Operator reconciliation

Owner can view metadata AuditEvent records and IntegrationIncident entries in Django administration. A compensation or post-restore record failure produces503 and a durable incident. Check the Inventory ledger before retrying. Mark resolved only after the external and Clinic states are reconciled; the checkbox itself does not repair stock. No live provider contract means automated real-world reconciliation cannot be claimed.

See [KNOWN-LIMITATIONS.md](KNOWN-LIMITATIONS.md), [DATABASE.md](DATABASE.md) and [REAL-SYSTEM-INTEGRATION.md](REAL-SYSTEM-INTEGRATION.md).
