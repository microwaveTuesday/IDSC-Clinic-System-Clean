# ADR 0006: Integrate Through a Clean Phase 7-Based Branch and Reviewed Pull Request

## Status

Accepted

## Context

The repository contains historical feature branches and cumulative phase branches.

Several legacy feature branches are superseded, rejected, or retained only as references.

Merging them wholesale into `main` would risk reintroducing obsolete implementations and conflicts with the canonical integration baseline.

The project also requires visible Git history and review rather than a single uncontrolled final push.

## Decision

`phase7/tests-contract-validation` is the canonical source branch to preserve and improve.

Integration work is performed on the clean branch:

`fix/pre-main-integration`

The project will:

- preserve the cumulative phase history;
- avoid wholesale merges of legacy feature branches;
- cherry-pick or reimplement only specifically verified work when necessary;
- never push directly to `main`;
- update `main` only through a reviewed Pull Request;
- require final validation gates before merge;
- preserve canonical Phase 7 while integration fixes are developed and reviewed.

Legacy branch treatment remains:

- `feat/update-student-crud` — rejected;
- `feature/session-authentication` — dead / no unique work;
- `feature/medicine-dispensing` — superseded;
- `feature/inventory-registrar-integration` — reference only;
- `feature/dashboard-reports` — superseded;
- `for-faculty-student-portal-api-endpoints` — superseded.

## Rationale

A clean integration branch minimizes accidental regression and makes the final PR reviewable.

Preserving Phase 7 provides a stable known-good reference.

PR-only main integration supports teammate review and protects the final branch from direct uncontrolled changes.

## Consequences

### Positive

- The canonical source remains recoverable.
- Legacy code is not reintroduced accidentally.
- Integration changes have explicit commit history.
- Review can focus on a clean cumulative diff.
- Final merge gates can be enforced before `main` changes.

### Trade-offs

- Integration requires deliberate verification before each commit.
- Some legacy work may need to be manually compared rather than merged.
- Documentation and final testing must be completed before the PR can merge.

## Required Final Merge Gates

Before the final PR is merged:

- full automated tests pass;
- OpenAPI validates;
- Redocly lint passes;
- Swagger `/docs` works;
- Problem Details behavior is verified;
- Postman collection is verified;
- documentation is synchronized;
- teammate review/approval is obtained;
- `main` protection is enabled as required.

## Implementation Evidence

Verified integration history includes:

- cleanup of tracked IDE/generated artifacts;
- canonical health and Swagger route fixes;
- mock-data/service/repository architecture;
- OpenAPI contract normalization;
- public-operation security normalization;
- regression test and lint validation;
- controlled pushes only to `fix/pre-main-integration`.

## Invariants

1. Never push directly to `main`.
2. Never force-push the integration branch as part of normal workflow.
3. Never wholesale-merge rejected or superseded legacy branches.
4. Preserve canonical Phase 7 as a reference until the reviewed final integration is complete.
5. Final merge requires the documented validation gates and teammate approval.

## Related Documentation

- `docs/architecture.md`
- `docs/TEST-EVIDENCE.md`
- root `README.md` after Phase 5.6 synchronization
