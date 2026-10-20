# Backup and restore

Backups contain medical records, account hashes, sessions and replay responses.
Keep them encrypted, access-controlled and outside Git/public CI artifacts.
The verification exercise uses only synthetic data and deletes its temporary
physical backups. No backup is uploaded by CI.

## Reproducible isolated exercise

From the repository root, install `backend/requirements-finals.txt`, then:

```powershell
$env:CLINIC_DISPOSABLE="1"
python scripts/verify_restore.py
```

By default this creates separate temporary SQLite source and restored databases.
It migrates the source, creates all four clinical resource types through the
service, physically backs up Clinic and the separate Inventory file, restores
both, checks migration compatibility/system settings, reads through the
persistent application repository, verifies the deduction reference and stock,
checks a database constraint, and verifies rollback restores stock only once.

For PostgreSQL set `DB_ENGINE=django.db.backends.postgresql`, `DB_NAME`, `DB_USER`,
`DB_PASSWORD`, `DB_HOST`, `DB_PORT` to a disposable validation server. The account
needs CREATEDB for the exercise. Use matching `pg_dump`/`pg_restore` binaries in
PATH. The script creates unique `verification_source_*`/`verification_restore_*`
databases, uses `pg_dump -Fc` and `pg_restore --exit-on-error --no-owner`, then
drops only its own unique databases. Never give this test real student data.

## Operator backup

1. Stop incoming writes and stop the single application worker. This is required
   for a consistent pair of Clinic and simulated Inventory snapshots.
2. PostgreSQL: use `pg_dump -Fc -f <private-backup> <database>` with connection
   credentials supplied privately (a restricted service file or environment).
   SQLite: use `sqlite3.Connection.backup()` to a new protected file, never an
   uncoordinated live filesystem copy. Use the same SQLite backup API for the
   separate mock Inventory ledger.
3. Record application revision, Django migration state, database versions, UTC
   time and cryptographic checksums in a private manifest. Store the signing
   secret privately and separately. Define institutional retention/access rules.
4. Restore into new databases/files first, never over the only working database.
   Use `pg_restore --exit-on-error --no-owner` for PostgreSQL; copy a quiesced
   SQLite backup into a new file. Keep restored Inventory paired with Clinic.
5. Point an isolated application at restored stores, run `migrate --check` and
   `check`, verify known records/references, stock and rollback using synthetic
   acceptance data. Do not run the destructive demo fixture writer on real data.
6. Review newer migrations before applying them. Take another backup, migrate
   explicitly, rerun checks, then switch traffic. Keep a documented rollback copy.

The supplied exercise proves current-schema restoration and constraints, not
arbitrary compatibility with every future schema. Restore drills and private
off-host backup monitoring remain operator responsibilities.
