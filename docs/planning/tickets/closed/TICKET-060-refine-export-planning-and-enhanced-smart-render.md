# TICKET-060 - Refine Export Planning and Enhanced Smart Render

**Ticket ID:** TICKET-060
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-007
**Feature:** FEAT-021
**Capability links:** CAP-005, CAP-011, CAP-012
**Status:** complete
**Closure:** user-approved on 2026-08-26 after the export-panel, fallback,
smart-render, frame-count, and performance-mode changes were implemented,
tested, reviewed, and accepted; unavailable remote and target-specific checks
remain recorded as accepted warnings.
**Horizon:** future
**Priority:** 1
**Owner:** repository implementation in the active worktree
**Approval:** user-reported and implementation-authorized on 2026-08-24
**Provider:** auto; base and target branches are not configured in
`.github/aidd-config.yml`
**Source paths:** `framestudio/app_export.py`,
`framestudio/export_panel.py`, `framestudio/export_estimates.py`,
`framestudio/fps_policy.py`, `framestudio/interpolation.py`,
`framestudio/export_interpolation.py`, `framestudio/export_delivery.py`,
`framestudio/performance.py`, `framestudio_concat.py`,
`tests/test_editor_export_panel.py`, `tests/test_editor_fps_policy.py`,
`tests/test_editor_export_execution.py`, `tests/test_editor_performance.py`,
and the user-reported export-panel behavior
**Dependencies:** TICKET-048 through TICKET-058 implementation surfaces;
existing output-policy, backend-validation, verification, and source-safety
boundaries
**Risks:** a friendlier fallback could hide a missing preferred backend,
defaults could change persisted-project behavior, direct enhanced publication
could bypass an output-policy requirement if its eligibility checks are
incomplete, and power-profile restoration could be missed on a terminal
export path
**Affected surfaces:** GTK export planning panel, target-FPS defaults,
dynamic FPS labels, backend fallback messaging, estimate presentation,
output-size estimation, temporary system performance-profile handling,
enhanced export dispatch, output verification, tests, README behavior
documentation, and evidence
**Evidence path:** `evidence/refine-export-planning-and-enhanced-smart-render.md`
**Last updated:** 2026-08-26
**Path history:** `tickets/open/TICKET-060-refine-export-planning-and-enhanced-smart-render.md`
-> `tickets/closed/TICKET-060-refine-export-planning-and-enhanced-smart-render.md`
**Protected behaviors:** source files and prior valid outputs remain
unchanged; exports remain atomic, verified, cancelable, and destination-safe;
legacy scripts, CLI contracts, audio decisions, fixed 1920x1080 output, and
ordinary stream-copy/fallback routes remain intact

## Outcome

The export planning surface presents a compact, understandable plan with
usable defaults and a validated fallback when the preferred interpolation
environment is unavailable. A single compatible, uncut source uses the
interpolation output directly when enhancement is required instead of being
encoded a second time. Enhanced edits use the legacy concat-first smart-render
sequence so motion enhancement runs once on the prepared timeline master rather
than once per original source range.

## Scope

- Make new export planning default to 60 FPS with enhancement enabled while
  preserving explicit persisted policy values.
- Name the lowest and highest FPS choices with their resolved rates.
- Replace the multiline assumptions-heavy summary with a compact summary or
  table that clearly shows inputs, final duration, estimated processing time,
  and estimated output size.
- Automatically select the explicit FFmpeg interpolation fallback when the
  preferred RVE environment is unavailable and the fallback validates; report
  that fallback without blocking a valid export.
- Prepare each source's retained timeline content with lossless stream-copy
  cuts, normalize each source once using its persisted audio decision, and
  concatenate the prepared sources at the slowest input FPS before enhancement.
- Run one FPS enhancement pass on the unified prepared master, preserving the
  existing direct smart-render path when a complete source already satisfies the
  output profile.
- Keep estimator assumptions available to machine-readable planning/evidence
  surfaces without displaying them as a wall of text in the panel.
- Publish a single compatible full-source interpolation result without a
  second fallback re-encode, while retaining artifact checks, output
  verification, cancellation, atomic publication, and source preservation.
- Temporarily select the system performance profile for an active editor
  export and restore the exact previous profile after success, failure, or
  cancellation; continue without a profile change when the optional system
  tool is unavailable.

## Explicit non-goals

- Changing the RVE/RIFE algorithm, model, output codec profile, audio
  normalization policy, or fixed project canvas.
- Claiming the FFmpeg fallback is equivalent in quality or performance to RVE.
- Directly publishing interpolated output for cuts, visual modifications,
  mixed-source composition, incompatible dimensions, or incompatible audio
  profiles.
- Removing estimator limitations from CLI/evidence payloads.
- Modifying unrelated timeline, playback, or legacy-script behavior.

## Observable requirements

- Given a new export plan, the initial choice should be 60 FPS and enhancement
  should be enabled.
- Given a project with explicit persisted FPS settings, opening Export should
  retain those settings rather than replacing them with defaults.
- Given source rates, the lowest and highest choices should include the
  resolved rate in their labels.
- Given a valid plan, the panel should clearly show input count, final edited
  duration, estimated processing time, and estimated output size without
  rendering the estimator assumptions as the primary summary.
- Given enhancement enabled and an unavailable preferred RVE environment, the
  panel should use the validated FFmpeg fallback when available and explain
  the selected fallback without disabling Start export.
- Given one compatible full-source uncut input requiring enhancement, the
  execution should run interpolation once and verify/publish that result
  without invoking the ordinary fallback re-encode.
- Given enhanced interpolation is running, FFmpeg progress should reach the
  export worker so the UI advances beyond the initial interpolation event and
  displays current frame/FPS/elapsed information.
- Given an enhanced edit with cuts or multiple sources, retained ranges should
  be cut before any re-encoding, each source's audio gain should be applied once
  to its prepared source result, the prepared sources should be concatenated at
  the slowest input FPS, and interpolation should receive that one unified
  master.
- Given an editor export starts while a system power profile is available, the
  performance profile should be selected for the export and the previous
  profile should be restored after success, error, or cancellation.
- Given the optional system power-profile tool is unavailable, export should
  continue without claiming that performance mode was changed.
- Given cuts, incompatible media, visual modifications, mixed sources, audio
  normalization, cancellation, or a failed artifact/output check, the
  existing safe delivery route and cleanup behavior should remain in force.

## Validation and evidence

- Run the protected repository baseline before implementation.
- Add failing regressions for defaults, named rate labels, compact panel data,
  output-size estimates, backend fallback, and the direct enhancement route.
- Exercise generated media for ordinary stream copy, enhanced direct
  publication, enhanced cut delivery, output verification, cancellation, and
  source preservation, including interpolation progress callbacks.
- Run the configured check, contract, smoke, quality, and review gates;
  record unavailable remote and target-workstation checks explicitly.
- Provide target-workstation GTK validation for the redesigned panel before
  closure.

## Definition of done

- The panel is compact, readable, and exposes the requested duration,
  processing-time, and size information.
- Defaults and dynamic rate labels match the approved behavior while explicit
  saved settings remain stable.
- Missing RVE artifacts no longer make a valid FFmpeg-fallback export
  unusable.
- Eligible single-source enhancement avoids redundant recompilation and still
  passes all existing verification and source-safety boundaries.
- Cut and mixed-source enhanced exports use fast per-source preparation and one
  post-concatenation enhancement pass instead of interpolating original source
  ranges independently.
- Focused regressions, protected gates, review, and user validation are
  evidenced before the ticket can move to delivery.

## Closure

TICKET-060 was closed on 2026-08-26 after the user confirmed the completed
ticket set was approved, accepted, and tested. The existing evidence retains
the explicit fallback and unavailable remote/target-environment warnings.
