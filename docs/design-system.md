# Clinic System Design System

## 1. Purpose

This document records the design-system evidence that is verifiably present in the Clinic System repository and defines how the frontend must be synchronized with the final Clinic visual design.

This document intentionally separates two things:

1. the frontend styling and components that are actually implemented in this repository today; and
2. the final Clinic/Figma/class design system that must be synchronized when its authoritative source is available to the repository.

The repository must not claim a completed Clinic design system when the committed frontend does not yet contain one.

The current frontend source is a React + Vite starter implementation. It provides a small set of reusable CSS tokens and interaction patterns, but it does not represent the finished Clinic user interface.

This distinction is important for project accuracy, documentation integrity, and final handoff.

---

## 2. Documentation Status

### Verified repository status

The current `frontend/src` implementation contains:

- `App.jsx`
- `App.css`
- `index.css`
- `main.jsx`
- starter image and SVG assets

The committed UI still displays starter content such as:

- `Get started`
- `Explore Vite`
- `Learn more`
- Vite community links
- React and Vite logos
- a demo counter button

Therefore:

**The committed frontend is not the final Clinic interface.**

The styles documented below are the verified repository baseline only.

They must not be presented as evidence that the high-fidelity Clinic prototype has already been implemented in code.

---

## 3. Source-of-Truth Rules

The project uses the following source-of-truth hierarchy for visual design:

1. The approved class design system and the team's final high-fidelity Figma prototype define the intended Clinic visual language.
2. The committed frontend implementation is evidence of what has actually been coded.
3. This document records repository evidence and synchronization rules between those sources.

If Figma and the current frontend disagree, the disagreement must be documented and resolved deliberately.

Do not silently invent missing colors, spacing values, components, states, or layouts.

Do not describe a component as implemented unless it exists in the committed frontend source.

---

## 4. Current Frontend Technology

The current frontend implementation uses:

- React
- Vite
- JavaScript / JSX
- CSS

The main application component is located at:

`frontend/src/App.jsx`

Global styling is primarily defined in:

`frontend/src/index.css`

Application-level styling is defined in:

`frontend/src/App.css`

---

## 5. Verified Global Design Tokens

The current global CSS uses custom properties under `:root`.

These tokens are implementation evidence, not proof of the final Clinic brand system.

### 5.1 Light-mode color tokens

| Token | Verified value | Current role |
|---|---|---|
| `--text` | `#6b6375` | default body text |
| `--text-h` | `#08060d` | headings and emphasized text |
| `--bg` | `#fff` | page background |
| `--border` | `#e5e4e7` | borders and separators |
| `--code-bg` | `#f4f3ec` | inline code background |
| `--accent` | `#aa3bff` | interactive accent |
| `--accent-bg` | `rgba(170, 59, 255, 0.1)` | accent surface |
| `--accent-border` | `rgba(170, 59, 255, 0.5)` | accent hover/focus border |
| `--social-bg` | `rgba(244, 243, 236, 0.5)` | link/button surface |

The light-mode shadow token is:

`rgba(0, 0, 0, 0.1) 0 10px 15px -3px, rgba(0, 0, 0, 0.05) 0 4px 6px -2px`

### 5.2 Dark-mode color tokens

The current frontend supports system-driven dark mode through:

`@media (prefers-color-scheme: dark)`

Verified dark-mode values are:

| Token | Verified value |
|---|---|
| `--text` | `#9ca3af` |
| `--text-h` | `#f3f4f6` |
| `--bg` | `#16171d` |
| `--border` | `#2e303a` |
| `--code-bg` | `#1f2028` |
| `--accent` | `#c084fc` |
| `--accent-bg` | `rgba(192, 132, 252, 0.15)` |
| `--accent-border` | `rgba(192, 132, 252, 0.5)` |
| `--social-bg` | `rgba(47, 48, 58, 0.5)` |

The dark-mode shadow token is:

`rgba(0, 0, 0, 0.4) 0 10px 15px -3px, rgba(0, 0, 0, 0.25) 0 4px 6px -2px`

### 5.3 Token status

These values are verified implementation tokens.

They should be treated as **provisional frontend tokens** until they are compared with the approved Clinic/Figma design system.

If the final design system uses different values, the frontend tokens should be updated intentionally and this document should be synchronized in the same change.

---

## 6. Typography Baseline

### 6.1 Font families

The current global CSS defines:

| Token | Verified stack |
|---|---|
| `--sans` | `system-ui, 'Segoe UI', Roboto, sans-serif` |
| `--heading` | `system-ui, 'Segoe UI', Roboto, sans-serif` |
| `--mono` | `ui-monospace, Consolas, monospace` |

No custom Clinic font family is currently committed.

### 6.2 Base typography

The root typography declaration is:

- font size: `18px`
- line height: `145%`
- letter spacing: `0.18px`

At viewport widths of 1024px or less, the root font size becomes `16px`.

### 6.3 Heading typography

Current `h1` styling:

- font size: `56px`
- font weight: `500`
- letter spacing: `-1.68px`
- margin: `32px 0`

At 1024px or less:

- font size: `36px`
- margin: `20px 0`

Current `h2` styling:

- font size: `24px`
- line height: `118%`
- letter spacing: `-0.24px`
- margin bottom: `8px`

At 1024px or less:

- font size: `20px`

### 6.4 Inline code typography

Inline code uses the monospace token.

Verified values include:

- font size: `15px`
- line height: `135%`
- padding: `4px 8px`
- border radius: `4px`
- background: `var(--code-bg)`

---

## 7. Layout Baseline

### 7.1 Application root

The current `#root` layout uses:

- width: `1126px`
- max-width: `100%`
- centered horizontal margin
- centered text
- inline borders using `var(--border)`
- minimum height: `100svh`
- column flex layout
- `border-box` sizing

This layout belongs to the starter page and must not be assumed to be the final Clinic application shell.

### 7.2 Center content region

The current `#center` section uses:

- flex column layout
- centered content and items
- gap: `25px`
- flexible growth

At 1024px or less:

- padding: `32px 20px 24px`
- gap: `18px`

### 7.3 Secondary content region

The current `#next-steps` region uses a horizontal flex layout with a top border.

Each child region uses `32px` padding on larger screens and `24px 20px` on smaller screens.

At 1024px or less, the layout changes to a vertical column and centers its text.

### 7.4 Spacer

The current spacer uses:

- height: `88px`
- top border using `var(--border)`

At 1024px or less, the height becomes `48px`.

---

## 8. Responsive Behavior

The verified primary breakpoint is:

`max-width: 1024px`

Current responsive behavior includes:

- smaller root typography
- smaller heading sizes
- reduced margins and spacing
- center-section padding changes
- horizontal sections becoming vertical
- social/documentation links wrapping into multiple rows
- spacer height reduction

No additional Clinic-specific mobile navigation, table adaptation, drawer behavior, responsive form layout, or dashboard grid behavior is currently implemented in the repository.

Those behaviors must be documented only after they exist in Figma or code.

---

## 9. Current Interactive Components

The current repository includes only starter-level interactive patterns.

### 9.1 Counter button

The demo counter uses the `.counter` class.

Verified styling includes:

- font size: `16px`
- padding: `5px 10px`
- border radius: `5px`
- text color: `var(--accent)`
- background: `var(--accent-bg)`
- transparent 2px border
- border-color transition: `0.3s`
- bottom margin: `24px`

Hover state:

- border color becomes `var(--accent-border)`

Keyboard focus state:

- `2px solid var(--accent)` outline
- `2px` outline offset

This is a verified interaction pattern, but it is a demo counter and not a Clinic business component.

### 9.2 Link buttons

The starter documentation/social links use:

- `16px` text
- `6px` border radius
- `var(--social-bg)` background
- `6px 12px` padding
- inline flex alignment
- `8px` gap
- no text decoration
- `0.3s` box-shadow transition

Hover state applies `var(--shadow)`.

At 1024px or less, links expand to the full available item width and center their content.

### 9.3 Hero composition

The starter hero combines:

- one base image
- React logo
- Vite logo
- absolute positioning
- perspective transforms
- rotation and scale transforms

This is starter-brand artwork, not a Clinic design-system component.

---

## 10. Accessibility Evidence

Verified accessibility-positive implementation details include:

- semantic `button` element for the counter
- explicit `type="button"`
- `focus-visible` styling on the counter
- `alt` text on React/Vite images where meaningful
- empty `alt` values on decorative images where used
- SVG icons marked with `role="presentation"` and `aria-hidden="true"`
- system color-scheme support
- responsive behavior at 1024px

### 10.1 Current limitations

The repository does not yet provide evidence for a complete Clinic accessibility system covering:

- Clinic form labels and errors
- accessible tables
- status badge semantics
- modal/dialog focus management
- navigation landmarks for the final Clinic shell
- skip links
- live regions for asynchronous actions
- toast/notification semantics
- keyboard behavior for final complex components

These must not be marked complete until implemented and tested.

---

## 11. Light and Dark Theme Behavior

The current implementation follows the operating-system preference through `prefers-color-scheme`.

There is no repository evidence of:

- a user-controlled theme switch
- persisted theme preference
- Clinic-specific theme settings
- theme synchronization with a user account

The design system should therefore describe dark mode as **system-driven in the current implementation**.

Do not document a manual theme switch unless one is added later.

---

## 12. Current Component Inventory

### Implemented starter components/patterns

The repository currently demonstrates:

- application root shell
- hero image composition
- heading hierarchy
- paragraph text
- inline code style
- demo counter button
- documentation/social link buttons
- icon usage
- divider/border patterns
- responsive wrapping
- light/dark tokens

### Not implemented as Clinic components

The current repository does not provide evidence of completed Clinic-specific versions of:

- authentication form
- application header
- sidebar navigation
- dashboard metric cards
- recent-activity list
- student search
- student table
- health-record table
- health-record form
- consultation table
- consultation form
- health-status form
- medicine stock table
- medicine-dispensation form
- report filters
- pagination controls styled for Clinic
- status badges
- validation banners
- confirmation dialogs
- empty states
- loading states
- error states
- toast/notification system

This list is a gap inventory, not a declaration of required visual styling.

The visual details for these components must come from the approved Figma/class design system.

---

## 13. Figma Synchronization Requirement

The project's frontend role requires a complete high-fidelity clickable Figma prototype.

The repository currently does not include enough information to reconstruct that prototype faithfully.

Therefore, before final presentation or frontend implementation sign-off:

1. Obtain the approved Clinic Figma source or exported design specification.
2. Compare its colors with the CSS custom properties in `index.css`.
3. Compare its typography with the current system font stack.
4. Compare its spacing and component radii with the current CSS.
5. Compare its application shell with the starter `#root` layout.
6. Replace starter React/Vite content with actual Clinic screens.
7. Define reusable Clinic component states from the approved design.
8. Update this document with verified final values.
9. Keep Figma, frontend implementation, and this document synchronized.

Until that synchronization occurs, this document must continue to label repository tokens as provisional implementation evidence.

---

## 14. Recommended Token Migration Structure

When the final Figma design system is available, preserve the idea of centralized tokens rather than scattering raw values through components.

A future token structure may include categories such as:

- color
- typography
- spacing
- radius
- border
- shadow
- motion
- layout
- z-index

However, **do not assign new final values in this document without evidence from Figma or approved frontend implementation**.

The current repository already demonstrates centralized color/font tokens and should retain that principle.

---

## 15. Component-State Documentation Rule

Every final Clinic component should document only states that are actually designed or implemented.

Typical state categories to verify later include:

- default
- hover
- focus-visible
- active/pressed
- disabled
- loading
- empty
- error
- success
- selected

The current repository only provides direct evidence for hover and focus-visible behavior on a limited starter component set.

Do not infer complete component states from that small starter example.

---

## 16. Forms and Validation Design Status

The backend contains extensive validation and Problem Details behavior, but the committed frontend does not yet show Clinic forms that present those validation states.

Therefore, this design-system baseline cannot claim verified UI patterns for:

- required-field indicators
- inline field errors
- form-level error summaries
- 400 validation rendering
- 401 authentication errors
- 403 permission errors
- 404 resource errors
- 409 conflict feedback
- 422 business-rule feedback

When those patterns are implemented, they should align with backend error semantics without exposing raw technical payloads unnecessarily to end users.

---

## 17. Data Display Design Status

The final Clinic UI will need to display structured domain data, but repository evidence is currently insufficient to define final presentation rules.

Examples include:

- student projections
- health records
- consultations
- health statuses
- medicine stock
- medicine dispensations
- report results
- user-management records

The final table, card, badge, filter, and pagination patterns must be documented from actual Figma or implemented source.

Do not invent them in this baseline document.

---

## 18. Status and Semantic Color Rule

The backend uses semantic domain states such as:

- `CLEARED`
- `RESTRICTED`
- `UNDER_OBSERVATION`
- `COMPLETED`
- `ROLLED_BACK`

The current frontend does not define verified visual colors for these states.

Therefore:

- do not assign green/red/yellow mappings in this document without approved design evidence;
- do not encode business meaning through color alone;
- when visual status colors are introduced, pair them with readable text labels and sufficient contrast.

---

## 19. Motion and Transition Baseline

The current CSS contains limited motion evidence:

- counter border-color transition: `0.3s`
- link box-shadow transition: `0.3s`
- static transformed hero artwork

There is no verified Clinic motion system for:

- page transitions
- dialogs
- drawers
- loading indicators
- notifications
- expanding sections
- route changes

Future motion values must come from the approved design or implementation rather than being invented here.

---

## 20. Iconography Baseline

The starter implementation uses:

- React logo
- Vite logo
- SVG sprite references under `/icons.svg`
- GitHub/Discord/X/Bluesky starter community icons

These are not evidence of the final Clinic icon library.

The final Clinic iconography should be documented only when the approved icon source is available.

---

## 21. Image and Asset Rules

Current assets include starter artwork under `frontend/src/assets`.

The repository does not yet provide evidence of a final Clinic image/illustration system.

Final asset documentation should record:

- asset purpose
- source/ownership
- file format
- accessibility alt-text rule
- responsive behavior
- dark-mode behavior where relevant

Starter React/Vite artwork should not remain in the final Clinic product unless deliberately approved.

---

## 22. Design-System Implementation Rules

The following rules apply as the frontend evolves:

1. Prefer reusable tokens over repeated raw values.
2. Prefer reusable components over duplicated markup for the same UI pattern.
3. Keep focus-visible states for keyboard users.
4. Do not remove semantic HTML solely for visual styling convenience.
5. Keep responsive behavior explicit and testable.
6. Document light/dark behavior only when implemented.
7. Do not claim a component exists before it is coded or present in Figma.
8. Do not claim Figma values are implemented until the code matches them.
9. Keep design documentation synchronized with frontend changes.
10. Remove starter content as Clinic screens are implemented.

---

## 23. Repository-to-Design Traceability

### Current source files

| File | Current design-system responsibility |
|---|---|
| `frontend/src/index.css` | global color, typography, theme, root layout tokens |
| `frontend/src/App.css` | starter component/layout interactions |
| `frontend/src/App.jsx` | starter component markup and accessibility attributes |
| `frontend/src/main.jsx` | React application bootstrap |

### Backend-related references

Backend API structure is not a visual-design source of truth, but the frontend should eventually provide clear user-facing experiences for the backend capabilities documented in:

- `openapi.yaml`
- `docs/architecture.md`
- `docs/data-model.md`
- `docs/integration.md`

Visual decisions still belong to the approved frontend/Figma design system.

---

## 24. Verification Checklist for Final Design-System Sync

Before this document can be considered a final Clinic design-system specification, verify all of the following:

- [ ] approved Clinic Figma source is available
- [ ] final Clinic screen inventory is known
- [ ] color tokens are compared against Figma
- [ ] typography is compared against Figma
- [ ] spacing values are compared against Figma
- [ ] radii and borders are compared against Figma
- [ ] shadows are compared against Figma
- [ ] component states are documented
- [ ] responsive behavior is documented
- [ ] form validation states are documented
- [ ] data-table patterns are documented
- [ ] status presentation is documented
- [ ] navigation patterns are documented
- [ ] accessibility behavior is documented
- [ ] starter React/Vite content has been removed or intentionally retained
- [ ] code and Figma are synchronized

Until these checks are complete, this file is a **verified repository design baseline plus synchronization contract**, not a claim of final Clinic visual completion.

---

## 25. Current Verified Design Baseline Summary

The current frontend provides verifiable evidence for:

- centralized light-mode CSS color tokens
- centralized dark-mode CSS color tokens
- system font stacks
- monospace styling
- responsive behavior at 1024px
- a centered maximum-width root layout
- basic border and shadow tokens
- basic hover interactions
- keyboard focus-visible styling
- system-driven dark mode
- starter-level responsive wrapping

The current frontend does **not** provide verifiable evidence for a finished Clinic design system or high-fidelity Clinic screen implementation.

That gap must remain explicit until the approved prototype and implementation are synchronized.

---

## 26. Design-System Invariants

The following invariants must remain true:

1. Documentation must distinguish implemented styles from intended Figma styles.
2. Current starter tokens must not be mislabeled as final Clinic branding.
3. Final visual values must be evidence-based.
4. Accessibility states must not be removed when styling changes.
5. Responsive behavior must remain testable.
6. CSS tokens should remain centralized where practical.
7. Figma and code must be synchronized before final frontend sign-off.
8. Starter Vite/React content must not be presented as Clinic feature completion.
9. Backend domain ownership does not determine visual styling.
10. This document must be updated whenever the actual design system changes materially.

---

## 27. Source Files

Primary frontend evidence:

- `frontend/src/index.css`
- `frontend/src/App.css`
- `frontend/src/App.jsx`
- `frontend/src/main.jsx`

Related project documentation:

- `docs/architecture.md`
- `docs/data-model.md`
- `docs/integration.md`
- `openapi.yaml`

---

## 28. Related Documentation

See also:

- `docs/architecture.md` for backend architectural boundaries
- `docs/data-model.md` for Clinic domain data definitions
- `docs/integration.md` for cross-module integration behavior
- `docs/TEST-EVIDENCE.md` for validated backend test evidence
- root `README.md` for project-level setup and overview after Phase 5.6 synchronization

The final Figma/class design-system source should be linked here when it is available in an authoritative, shareable form.
