# TICKET-052 - Build Export Planning Panel

**Ticket ID:** TICKET-052
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-007
**Feature:** FEAT-021
**Capability links:** CAP-005, CAP-011, CAP-012
**Status:** complete
**Closure:** user-approved on 2026-08-26 after implementation, testing,
review, and acceptance of the export planning panel; unavailable remote and
target-specific checks remain recorded as accepted warnings.
**Horizon:** future
**Priority:** 5
**Owner:** repository planning; maintainer identity is not recorded
**Approval:** user-authorized on 2026-08-24 to create the PHASE-007 planning
set; implementation requires TICKET-048 through TICKET-051 and configured
ticket-execution approval
**Provider:** auto; base and target branches are not configured in
`.github/aidd-config.yml`
**Source paths:** `docs/planning/features/closed/FEAT-021-planning-export-destination-and-estimates.md`,
`docs/planning/tickets/closed/TICKET-049-persist-and-expose-frame-rate-policy.md`,
`docs/planning/tickets/closed/TICKET-050-choose-export-destination-and-smart-name.md`,
`docs/planning/tickets/closed/TICKET-051-calibrate-export-processing-time-estimates.md`,
`resolve_editor/app.py`, `resolve_editor/app_export.py`,
`resolve_editor/app_ui.py`, `.github/aidd-config.yml`
**Dependencies:** TICKET-049, TICKET-050, and TICKET-051; existing GTK
application lifecycle and export progress panel
**Risks:** dense controls can hide safety information, stale estimates can
mislead the user, and a dialog can accidentally start work before confirmation
**Affected surfaces:** GTK export page/dialog, target-FPS controls, destination
selection, smart naming, estimate summary, validation messages, cancel/start
flow, tests, and screenshots
**Evidence path:** `evidence/phase-007-export-planning.md`
**Protected behaviors:** export remains explicit, cancelable, source-safe, and
verified; the current non-enhanced path remains available
**Last updated:** 2026-08-26
**Path history:** created at
`tickets/open/TICKET-052-build-export-planning-panel.md` ->
`tickets/closed/TICKET-052-build-export-planning-panel.md`

## Outcome

The user can review and confirm a complete export plan before any media
processing begins.

## Scope

- Replace immediate export start with a dedicated page or dialog.
- Present destination folder and proposed filename controls.
- Present lowest input FPS, highest input FPS, custom FPS, and 60 FPS choices.
- Present the enhancement toggle and the resolved eligible-input summary.
- Show input-file count, edited duration, target FPS, enhancement duration,
  interpolation estimate, rendering/encoding estimate, verification estimate,
  total estimate, assumptions, and confidence.
- Recalculate the plan when relevant controls change.
- Disable confirmation when the policy, destination, or estimate inputs are
  invalid, and preserve state when the user cancels.

## Explicit non-goals

- Implementing the interpolation engine.
- Adding unrelated editing controls or changing the output profile.
- Hiding unavailable backend or permission failures.

## Observable requirements

- Given a loaded project, clicking Export should open the planning surface
  instead of starting FFmpeg immediately.
- Given valid settings, the panel should show all requested summary values
  before enabling confirmation.
- Given a changed rate or enhancement toggle, the estimate and filename should
  update consistently.
- Given an invalid destination or unsupported policy, confirmation should be
  blocked with an actionable reason.
- Given cancellation, no output process should start and no project data should
  change.

## Commands and quality gates

- `python3 -m unittest discover -s tests`
- `make check`
- `make quality PYTHON=.venv/bin/python`
- Target-workstation GTK interaction and window-only evidence

## Functionality flows

- Open the panel for one-source and mixed-source projects.
- Select each rate option, toggle enhancement, change the destination, and
  verify all displayed values update.
- Cancel, submit an invalid destination, and confirm that no process starts.

## User validation before closure

Use a disposable mixed-rate project, open Export, review every requested
field, change the target and enhancement options, and cancel once. Confirm
that the panel is understandable and no output begins before confirmation.
Return `PASS`, `FAIL`, or `BLOCKED` with window-only evidence.

## Definition of done

- The complete export plan is visible and validated before execution.
- Destination, target FPS, enhancement, naming, estimates, and safety state
  are coherent.
- Cancel and invalid-input paths are covered without side effects.

## Closure

TICKET-052 was closed on 2026-08-26 after the user confirmed the completed
ticket set was approved, accepted, and tested.
