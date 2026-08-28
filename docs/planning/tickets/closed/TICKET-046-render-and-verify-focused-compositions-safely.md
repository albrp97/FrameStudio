# TICKET-046 - Render and Verify Focused Compositions Safely

**Ticket ID:** TICKET-046
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-006
**Feature:** FEAT-019
**Capability links:** CAP-005, CAP-009, CAP-010, CAP-012
**Status:** complete
**Closure:** user-approved on 2026-08-23 after PHASE-006 implementation,
automated and real-media verification, shared target-workstation validation,
review, and local delivery evidence; remote checks remain unavailable and are
recorded as an accepted warning.
**Horizon:** future
**Priority:** 9
**Owner:** repository planning; maintainer identity is not recorded
**Approval:** user-authorized on 2026-08-22 to create and implement the
PHASE-006 ticket set; the completed outcome was confirmed by the user on
2026-08-23
**Provider:** auto; base and target branches are not configured in
`.github/aidd-config.yml`
**Source paths:** `docs/planning/tickets/open/TICKET-044-persist-focused-composition-state.md`,
`docs/planning/tickets/open/TICKET-045-expose-focused-edits-through-cli-and-gui-parity.md`,
`docs/planning/features/open/FEAT-019-delivering-focused-compositions-safely.md`,
`docs/planning/phases/open/PHASE-006-focusing-and-composing-important-action.md`,
`framestudio/export_planning.py`, `framestudio/export_ffmpeg.py`,
`framestudio/export_delivery.py`, `.github/aidd-config.yml`
**Dependencies:** TICKET-044 and TICKET-045; PHASE-005 delivery policy and
fixed 1920x1080 render profile
**Risks:** composition may be routed through unsafe stream copy, transforms
can disagree between preview and output, and failed renders can expose
partial files
**Affected surfaces:** export planning, FFmpeg filters, preview/export parity,
output verification, progress, cleanup, atomic publication, tests, and
evidence
**Evidence path:** `evidence/phase-006-focused-composition-rendering.md`
**Last updated:** 2026-08-23
**Path history:** `tickets/open/TICKET-046-render-and-verify-focused-compositions-safely.md`
-> `tickets/closed/TICKET-046-render-and-verify-focused-compositions-safely.md`

## Outcome

Focused and triplicate edits render through an explainable safe route and
publish only verified 1920x1080 outputs.

## Scope

- Determine when visual modifications require decode and fallback rendering.
- Apply the approved coordinate, aspect-ratio, crop, and layout policy in the
  render filter graph.
- Preserve the established codec/container/audio output profile.
- Verify dimensions, duration, streams, playability, placement, and source
  preservation before atomic publication.
- Retain progress, cancellation, temporary partial-file cleanup, and failure
  recovery behavior.

## Explicit non-goals

- Changing the established delivery profile without approved evidence.
- New composition modes, automatic focus, audio-policy redesign, or FPS
  enhancement.
- Publishing output before independent verification.

## Observable requirements

- Given a focused or triplicate edit, the planner should explain why stream
  copy is unavailable and select the approved fallback route.
- Given portrait or vertical-action input, output should remain 1920x1080 and
  follow the approved aspect-ratio and placement policy.
- Given a successful render, metadata, duration, streams, playability, and
  visual placement should be verified before publication.
- Given an encode, validation, cancellation, or publication failure, sources
  and the last valid output should remain intact.

## Commands and quality gates

- `python3 -m unittest discover -s tests`
- `make check`
- `make contract`
- `make smoke`
- `make quality PYTHON=.venv/bin/python`

## Functionality flows

- Render a modified portrait segment and inspect the output.
- Render a triplicate portrait and vertical-action landscape example.
- Exercise cancellation and validation failure paths and inspect cleanup.

## User validation before closure

Export disposable focused and triplicate projects, inspect route explanations,
metadata, duration, placement, and playability, and confirm source and last
valid output preservation after a failed attempt.

## Protected behavior

Existing output profile authority, source-level audio handling, source
preservation, atomic publication, partial cleanup, progress reporting, legacy
scripts, and ordinary one-source/mixed-source export routes remain unchanged.

## Definition of done

- Preview and render use the approved visual policy and safe fallback route.
- Output and failure-path tests pass with source-preservation evidence.
- User validation confirms verified focused delivery.

## Closure

Focused composition preview/export routing and failure cleanup are complete
under the reviewed PHASE-006 delivery checkpoint. Provider-side checks remain
unavailable because no remote or upstream is configured.
