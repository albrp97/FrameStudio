# TICKET-108 - Limit FPS Enhancement to Low-Frame-Rate Sources

**Ticket ID:** TICKET-108
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-008
**Feature:** FEAT-029
**Capability links:** CAP-005, CAP-011, CAP-012
**Status:** verifying
**Horizon:** future
**Priority:** 1
**Owner:** repository implementation in the active worktree
**Approval:** User-authorized by the 2026-10-05 `/aidd-fix` request.
**Last updated:** 2026-10-05
**Source paths:** `framestudio/fps_policy.py`,
`framestudio/export_panel.py`, `framestudio/export_interpolation.py`,
`tests/test_editor_fps_policy.py`, `tests/test_editor_export_panel.py`,
`.github/aidd-config.yml`
**Dependencies:** existing source-level frame-rate decisions, 60 FPS target
policy, export-panel count, and per-source interpolation route
**Risks:** an incorrect boundary could interpolate near-60-FPS sources
unnecessarily or skip enhancement for genuinely low-frame-rate sources
**Affected surfaces:** FPS policy decisions, export-panel eligibility count,
processing estimates, and interpolation routing
**Evidence path:** `evidence/ticket-108-fps-enhancement-cutoff.md`
**Protected behaviors:** exact rational frame-rate handling, target-rate
selection, VFR rejection, backend validation, disabled-enhancement conversion,
down-conversion, source preservation, and verified atomic export

## Outcome

FrameStudio enhances only sources below 50 FPS. Sources at or above 50 FPS use
ordinary frame-rate conversion when the selected output rate is higher.

## Scope

- Add one explicit 50 FPS enhancement eligibility boundary to the shared FPS
  policy.
- Keep exact rational comparisons for fractional rates such as 60000/1001 and
  30000/1001.
- Make the export-panel count, estimates, and renderer consume the corrected
  shared decisions without adding parallel UI-only logic.
- Add focused policy regression and export-panel functionality coverage.

## Explicit non-goals

- Changing the selected output FPS, interpolation backend, codec, audio,
  upscale policy, or export destination.
- Changing behavior for sources below 50 FPS, VFR sources, sources matching
  the target, or sources above the target.
- Adding a user-configurable enhancement threshold.

## Observable acceptance criteria

- Given a 60000/1001 FPS source and a 60 FPS output target, FrameStudio should
  use ordinary conversion and should not count the source for FPS enhancement.
- Given a 30000/1001 FPS source and a 60 FPS output target, FrameStudio should
  select interpolation and count the source for FPS enhancement.
- Given a source exactly at 50 FPS, FrameStudio should use ordinary conversion
  because enhancement applies only below 50 FPS.
- Given a mixed 60000/1001 and 30000/1001 FPS project, the export summary
  should report exactly one video to FPS enhance.

## Validation

- Failing-then-passing focused FPS-policy regression.
- Automated export-panel functionality test using mixed exact rational rates.
- Existing FPS policy, export-panel, interpolation, compile, and repository
  unit checks.
- Target-workstation export-window confirmation in guided mode.

## User-validation plan

- **Setup:** Open a project containing one approximately 59.94 FPS video and
  one approximately 29.97 FPS video, with output set to 60 FPS and FPS
  enhancement enabled.
- **Steps:** Open the export window and inspect the export summary.
- **Expected result:** **Videos to FPS enhance** reports `1`; the lower-rate
  source is enhanced and the approximately 59.94 FPS source is not.
- **Failure paths:** the summary reports `2`, reports `0`, or the near-60-FPS
  source is sent through interpolation.
- **Cleanup:** Close the export window without rendering if no output is
  needed.
- **Evidence response:** Return `PASS`, `FAIL`, or `BLOCKED` with the observed
  count and, when available, a window-only screenshot.

## Path history

Created in `docs/planning/tickets/open/` on 2026-10-05.
Moved to `verifying` on 2026-10-05 after focused regressions, the complete
Python suite, compilation, and the automated export-summary functionality test
passed.
