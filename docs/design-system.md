# Clinic frontend design baseline

The integration branch reuses the clinic interface from `corpeadmin/IDSC-Clinic-System` at `de0246d`, selectively importing its layout, CSS and IDSC logo. The former starter UI and browser seed data are replaced. This is repository implementation evidence; final Figma/instructor approval has not been independently verified.

## Implemented interface

- Responsive sidebar and mobile menu, dashboard cards, student search/course filter and detail tabs.
- Clinic-owned health record, consultation and health-status forms; Registrar students remain read-only.
- Inventory medicine catalog projection, stock filtering, dispensing history and confirmed rollback.
- Authenticated account information and backend-authorized staff management.
- Accessible field labels, visible focus outlines, dialog focus trap/Escape dismissal and restored focus.
- Loading state, API errors, disabled mutation submit buttons and delete/rollback confirmation.

## Styling

`frontend/src/index.css` contains the recovered component styles and responsive rules. Colors use semantic CSS variables near the top of the stylesheet. The softened light theme uses sage `#eaf0ec` for the page and `#f4f7f4` for panels. The dark theme uses `#111a16` for the page and `#19251e` for panels, with mint accents and readable muted text. Typography uses DM Sans and Manrope with local sans-serif fallback. The logo is `frontend/src/assets/idsc-logo.png`.

The UI loads data from the server, never from demo seeds. The mock backend limitation is disclosed in the dashboard and setup documentation. The authentication contract does not expose roles; admin navigation is enabled only after `/api/v1/users/` succeeds, while every privileged request is still enforced by the backend.

## Theme preference

The sun/moon switch appears on login and in the application top bar, including mobile. It stores `clinic-theme` locally in the browser and falls back to the operating system preference on first visit. An early script applies the theme before painting to prevent a bright flash. Native form controls respect `color-scheme`; storage restrictions do not prevent switching themes. Dark styling covers tables, forms, dialogs, alerts and navigation as well as the page canvas.

## Verification

See `INTEGRATION-VALIDATION.md` and the Playwright flow in `frontend/tests/clinic.spec.js`. Changes to visual design should update this document and obtain the team’s approval against the authoritative Figma prototype.

Theme update: frontend lint and production build passed. Browser checks verified preference persistence after reload, both palettes, the health editor and the mobile switch, with no browser errors. Desktop and mobile screenshots were inspected.

Settings now includes an accessible password-change dialog with stable input labels, field-error descriptions, password-manager autocomplete, disabled submission while pending, and both light/dark palettes.

Settings now includes Change username with current-password verification and immediate account display updates. Administration shows a separate administrator directory and an Add administrator form with password confirmation and actor reauthentication. The account-creation actions wrap on smaller screens; directory tables scroll horizontally. Account access displays the Clinic role rather than Django's is_staff flag.

Administrator and staff tables now include deactivate/reactivate and Delete controls. Protected administrator rows show a restriction explanation. Deletion confirmations explain permanence and request the acting administrator's password; failures remain in the dialog for correction. Account writes refresh the directories directly.
