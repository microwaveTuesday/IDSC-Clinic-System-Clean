# Final demonstration guide

1. Start a migrated disposable database with CLINIC_DATA_BACKEND=database. SQLite is sufficient for a classroom demo; PostgreSQL was separately verified. Start Django on8002 and Vite on5173. Keep both terminals open.
2. Use a new authentication database for first setup. Register the single Owner; Dashboard opens automatically. Logout and reload show shared login. A second registration attempt is rejected.
3. Create Admin and Staff through Administration. Demonstrate Owner-only Admin management, five-Admin capacity including inactive accounts, ten-row Staff pages, deactivation/reactivation and password-confirmed deletion. Staff has no Administration access.
4. In Mock Registrar create a test student. Get student using only student ID. Edit profile/status and observe refresh. Mark GRADUATED/DROPPED_OUT and show new clinical creation is blocked while history remains readable.
5. Create/edit health records, consultations and health statuses. Delete as Owner/Admin and show consecutive display labels; explain stable API IDs. Keep two edit tabs open in database mode to demonstrate stale-edit409 protection.
6. In Mock Inventory add a medicine. Observe the Clinic catalog and notification. Submit selected/all restocks, fulfill once as Owner, verify stock and duplicate-delivery protection.
7. Dispense, roll back and verify stock. Explain that deleting dispensing history removes history only and never returns stock. Review reports and statuses.
8. Change own username/password in Settings, confirm continued current session and subsequent login. Toggle light/dark mode and resize to mobile; test keyboard focus/Escape in a dialog.
9. Restart the backend and reload: Clinic database records survive, but external mock stock/transactions reset. Demonstrate this limitation honestly. Use scripts/verify_persistence.py only with a disposable validation database for the separate PostgreSQL restart proof.
10. Show Swagger/ReDoc, test evidence and Owner's read-only audit trail/reconciliation queue. Explain that no real Registrar/Inventory connectivity is claimed.

Run commands: [SETUP.md](../SETUP.md). Storage/ERD: [DATABASE.md](DATABASE.md). Exact executed checks and intermediate fixes: [IMPROVEMENT-VALIDATION.md](IMPROVEMENT-VALIDATION.md). Remaining limits: [KNOWN-LIMITATIONS.md](KNOWN-LIMITATIONS.md).
