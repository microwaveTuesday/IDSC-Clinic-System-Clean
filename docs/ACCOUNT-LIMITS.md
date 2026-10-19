# Staff pagination and administrator capacity

Staff management displays at most ten accounts per page, with Previous/Next buttons, the current page, total pages and the visible account range. Search includes all staff accounts and resets to page one. Deleting the last row on a page clamps the directory to the last remaining page. Role permissions are unchanged.

`GET /api/v1/users/` now explicitly uses the existing Clinic pagination envelope: `count`, `page`, `page_size`, `total_pages`, `results`. The default page size is 10 and the maximum is 10; larger requests are clamped to 10. Smaller page sizes remain supported. `page` is one-based, ordering is by username, and an invalid/out-of-range page returns 400. This is a documented change from the earlier unpaginated Staff directory array. Frontend `listAll` supports the envelope and loads all pages before applying search and displaying ten rows.

`POST /api/v1/admins/` allows at most five regular Admin accounts, including inactive Admins. Owners are excluded from this count. At capacity the API returns 409 Problem Details and explains that an Admin must be deleted before another can be created. Deactivation does not free a slot; deleting an Admin does. The capacity check runs inside the creation transaction, locking the shared administrator role before counting and inserting. A write lock is acquired before counting for SQLite as well. Existing installations above five Admins are preserved; creation stays blocked until fewer than five remain.

The Owner sees the administrator count out of five, a disabled Add administrator button at capacity and an explanation that inactive accounts still count. Server enforcement applies even if a client bypasses that button. Staff and Admin permissions retain the Owner/Admin/Staff hierarchy.

Nine backend tests exercise the fifth/sixth boundary, inactive accounts, owner exclusion, existing over-limit data, deletion/replacement, ten-row default/maximum, exact/empty pages, and deleted last pages. The browser boundary story uses an isolated database with an Owner and eleven seedstaff_00 through seedstaff_10 fixtures, verifies Staff pagination/search/deletion and the five-Admin cap/deactivation/deletion/replacement flow. Temporary Admins are cleaned up by the story. Existing staff-management browser stories search their fixture username so they work with paginated directories.

For isolated browser validation, Vite accepts `CLINIC_API_TARGET` (default http://127.0.0.1:8002), and Playwright accepts `CLINIC_TEST_BASE_URL` (default http://127.0.0.1:5173). Normal development URLs are unchanged. Run the boundary story against the documented disposable fixtures, not existing user accounts.

This feature did not add paths; the current overall inventory is 45 paths / 72 operations (5 public, 67 protected). The original backend contract tests and original Postman collection are unchanged.
