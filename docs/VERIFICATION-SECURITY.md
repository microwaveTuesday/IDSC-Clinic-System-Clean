# Verification security review

This pass combines source review of the current trust boundaries with executable
negative regressions and dependency checks. It is not penetration-test,
compliance, production or complete WCAG certification. The earlier plugin audit
is historical; this report does not claim a new independent plugin scan.

| Surface reviewed | Control and evidence |
| --- | --- |
| Login/session/CSRF | Django database sessions, explicit anonymous login/setup CSRF, DRF session CSRF; existing auth suite; malformed/oversized credentials now return 400 before authentication |
| Owner setup | Permanent latch, transaction/unique constraints, PostgreSQL simultaneous-claim regression; privately claim before exposure |
| Roles/object targets | Owner/Admin/Staff checks, lifecycle target locks, protected Owner/self, five Admin cap, ten Staff per page; existing hierarchy/lifecycle/permission tests plus roleless resource negatives |
| Medical data | Authenticated Clinic roles, no anonymous medical projections, no-store responses; frontend clears workspace on expired background session |
| Passwords/deactivation | Validators and current-password verification; database session revocation; existing lifecycle/password tests |
| Injection/mass assignment | ORM/parameterized SQLite queries; explicit serializer field lists; no frontend raw HTML execution found in reviewed API rendering |
| Replay/stock | Actor/method/path scope, payload digest conflict, authorization before replay, retained tombstones, independent durable-provider ambiguity fence; concurrent/expired/crash tests |
| Audit/error privacy | Metadata-only route-template audit; unexpected exception values and tracebacks removed from operational error logs; regression proves a synthetic private value is absent from response/log |
| Production/CORS/proxy | Explicit hosts/long secret, secure cookies/HTTPS/HSTS, no wildcard CORS; forwarded HTTPS trusted only with explicit opt-in behind isolated proxy; production config tests |
| Dependencies | Locked Python resolution and npm lockfile; pip-audit/npm audit in CI; results in VERIFICATION-RESULTS.md |
| Delivery | Read-only Actions token, SHA-pinned actions, synthetic isolated fixtures, count-only uploaded artifact; protected push destination |

Verified improvements address credential type/length validation, indefinite
replay exposure, error-value logging, ambiguous Inventory retries and expired
frontend sessions. No critical/high exploitable issue was established by this
review. That statement is bounded by these reviewed surfaces and tests; it is
not a guarantee that no undiscovered vulnerability exists.

## Replay retention

`REPLAY_RETENTION_HOURS` defaults to 24 (positive integer). Expired responses are
never served. Run `python manage.py purge_replay_bodies` at least hourly using an
operator scheduler. It removes expired response JSON but retains scope/key/
fingerprint/status/time tombstones, clinical history, audit and incidents.
Expired retries return 409 and cannot create another dispense. Reducing the
retention window immediately restricts replay. Application DB access remains
privileged; encrypt disks/backups and restrict database operators.

## Institutional decisions and residual controls

The institution must approve clinical/audit retention, encrypted backup handling,
private logging/incident procedures, identity verification for first Owner and
access reviews. No real medical data was used. Local cache throttling is per
direct peer IP, not distributed abuse prevention. The supplied proxy can group
clients under one peer limit. A trusted-IP/shared-cache policy needs institutional
deployment design. Durable mock journals are not a replacement for genuine
provider-side transaction lookup. Hosted HTTPS/load testing, secret rotation,
tamper-evident off-host logs and independent penetration testing remain unverified.
