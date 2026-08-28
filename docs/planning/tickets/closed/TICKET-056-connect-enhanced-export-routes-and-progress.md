# TICKET-056 - Connect Enhanced Export Routes and Progress

**Ticket ID:** TICKET-056
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-007
**Feature:** FEAT-023
**Capability links:** CAP-005, CAP-006, CAP-011, CAP-012
**Status:** complete
**Closure:** user-approved on 2026-08-26 after implementation, testing,
review, and acceptance of GUI/CLI enhanced export routing and progress;
unavailable remote and target-specific checks remain recorded as accepted
warnings.
**Horizon:** future
**Priority:** 9
**Owner:** repository planning; maintainer identity is not recorded
**Approval:** user-authorized on 2026-08-24 to create the PHASE-007 planning
set; implementation requires TICKET-049, TICKET-052, TICKET-055, and
configured ticket-execution approval
**Provider:** auto; base and target branches are not configured in
`.github/aidd-config.yml`
**Source paths:** `docs/planning/features/closed/FEAT-023-verifying-safe-enhanced-delivery.md`,
`docs/planning/tickets/closed/TICKET-049-persist-and-expose-frame-rate-policy.md`,
`docs/planning/tickets/closed/TICKET-052-build-export-planning-panel.md`,
`docs/planning/tickets/closed/TICKET-055-preserve-audio-and-delivery-profile-during-enhancement.md`,
`framestudio/app.py`, `framestudio/app_export.py`,
`framestudio/cli.py`, `framestudio/cli_export.py`,
`framestudio/export_process.py`, `.github/aidd-config.yml`
**Dependencies:** TICKET-049, TICKET-052, and TICKET-055; validated
interpolation route; existing export worker, cancellation, and progress
boundaries
**Risks:** GUI and CLI can select different routes, progress can mix estimate
and measured values, and cancellation can leave stale state or partial files
**Affected surfaces:** application export orchestration, CLI parser/handler,
backend dispatch, progress events, ETA display, cancellation, errors,
temporary files, tests, and evidence
**Evidence path:** `evidence/phase-007-safe-enhanced-delivery.md`
**Protected behaviors:** structured CLI errors, truthful progress, atomic
publication, partial cleanup, source preservation, and non-enhanced routes
remain intact
**Last updated:** 2026-08-26
**Path history:** created at
`tickets/open/TICKET-056-connect-enhanced-export-routes-and-progress.md` ->
`tickets/closed/TICKET-056-connect-enhanced-export-routes-and-progress.md`

## Outcome

The approved export policy can be executed consistently from the GUI and CLI
with truthful staged progress, cancellation, and failure recovery.

## Scope

- Dispatch enhanced and non-enhanced exports from the persisted policy.
- Connect the export panel's destination, target rate, enhancement state, and
  estimate to the actual route without silently changing values.
- Report interpolation, rendering/encoding, verification, and completion
  stages through the existing progress surfaces.
- Compare measured progress with the pre-export estimate without presenting
  predicted values as completed work.
- Preserve cancellation, partial-file cleanup, destination conflict checks,
  structured CLI JSON Lines, and atomic publication.
- Expose backend, target rate, scope, and route reasons in GUI status and CLI
  results.

## Explicit non-goals

- Adding a second GUI framework or replacing existing public facades.
- Changing the interpolation policy, audio algorithm, or output profile.
- Claiming a successful export before final verification.

## Observable requirements

- Given the same saved policy, GUI and CLI should select equivalent routes and
  expose equivalent target/enhancement values.
- Given an enhanced export, progress should identify the current stage and
  retain an honest ETA or explicitly report that it is unavailable.
- Given cancellation or a backend error, the process should stop, remove
  partial output, and leave project/source/last valid output intact.
- Given enhancement disabled, the existing route should remain selectable and
  successful.

## Commands and quality gates

- `python3 -m unittest discover -s tests`
- `make contract`
- `make smoke`
- `make check`
- `make quality PYTHON=.venv/bin/python`

## Functionality flows

- Run enhanced and ordinary exports from the GUI and inspect progress stages.
- Run equivalent CLI exports and compare JSON settings, route, and result.
- Cancel during interpolation and encoding, then repeat after a failure.

## User validation before closure

Run one enhanced and one ordinary export from the GUI, observe the progress
stages and final status, then repeat the policy through the CLI. Cancel one
run and confirm no partial output or stale success remains. Return `PASS`,
`FAIL`, or `BLOCKED`.

## Definition of done

- GUI/CLI route selection and progress are policy-consistent.
- Cancellation, errors, partial cleanup, and ordinary exports are covered.
- No unverified output is reported as complete.

## Closure

TICKET-056 was closed on 2026-08-26 after the user confirmed the completed
ticket set was approved, accepted, and tested.
