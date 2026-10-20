# Verification baseline

Starting revision: `3737588c01b6d5bb957d8ad7ca412389c3ca6b81`.
New branch: `improvement/clinic-final-verification`; starting tree matches exactly.
Recorded before implementation: no Actions workflow; operational restore untested;
Inventory/restocks/notifications process-local; successful replay bodies retained
indefinitely; an external side effect can precede a failed Clinic commit.
The previous 294 backend tests and browser/Newman results are historical until rerun.

Preserve separate Registrar/Inventory ownership, existing interface/design and all
baseline tests. No authentic external provider contract or hosted infrastructure
has been supplied. Changes and pushes are restricted to the clean verification
branch. PR #2 and all inherited branches remain unchanged.
