# Remaining limitations

- Registrar and Inventory are mocks. No genuine provider contracts/access were supplied; live connectivity is unavailable. Registrar changes still reset with its process; use seeded students for restart demos.
- Default INVENTORY_BACKEND=mock still resets. Optional durable_mock preserves simulated catalog, stock, transactions, restocks and notifications in a separate ledger. It is not the institutional Inventory System. See INVENTORY-RECOVERY.md.
- Use one application worker while Registrar/default mocks are enabled. Inventory serialization alone does not make all mocks multi-worker services. Load/soak and multi-server behavior remain unverified.
- A crash without a committed Clinic receipt requires manual reconciliation. Durable request fences return 503 instead of repeating an uncertain stock operation. Direct service callers need equivalent orchestration; no distributed exactly-once guarantee is claimed.
- Frontend retry keys live in memory for 60 seconds and do not survive page reload. Never bypass an uncertain operation by supplying a new key.
- Stale-write protection requires If-Match or X-Record-Version; current frontend edits send versions. Header-free legacy writes retain transactional last-write semantics.
- Replay bodies expire after configurable 24 hours. An operator must schedule purge_replay_bodies to remove expired JSON physically. Tombstones remain. Institutional retention, encrypted backups and off-host audit protection need approval.
- First Owner setup must occur privately. Login throttling uses process-local cache/direct peer IP. Shared limiting and trusted client-IP policy remain deployment decisions.
- A private HTTPS container profile and CI smoke job are supplied. See VERIFICATION-RESULTS.md for executed outcomes. No public hosted college deployment, production certification or real student-data governance approval is claimed.
- Axe, keyboard/focus/mobile checks are regression evidence, not full WCAG certification. Dependency audits describe known advisories on the execution date only.
- Physical restore drills prove the current schema with synthetic data, not arbitrary future migrations or a monitored off-host backup service.

The final assessment is in VERIFICATION-RESULTS.md; it is not an official course grade.
