# TICKET-042 - Implement Linked Triplicate Composition

**Ticket ID:** TICKET-042
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-006
**Feature:** FEAT-018
**Capability links:** CAP-009, CAP-010, CAP-012
**Status:** complete
**Closure:** user-approved on 2026-08-23 after PHASE-006 implementation,
automated and real-media verification, target-workstation validation, review,
and local delivery evidence; remote checks remain unavailable and are recorded
as an accepted warning.
**Horizon:** future
**Priority:** 5
**Owner:** repository planning; maintainer identity is not recorded
**Approval:** user-authorized on 2026-08-22 to create and implement the
PHASE-006 ticket set; user validation returned PASS on 2026-08-23
**Provider:** auto; base and target branches are not configured in
`.github/aidd-config.yml`
**Source paths:** `docs/planning/tickets/open/TICKET-041-define-triplicate-group-and-layout-policy.md`,
`docs/planning/tickets/open/TICKET-039-implement-segment-focus-controls.md`,
`docs/planning/features/open/FEAT-018-creating-linked-triplicate-compositions.md`,
`docs/planning/phases/open/PHASE-006-focusing-and-composing-important-action.md`,
`framestudio/model_project.py`, `framestudio/app_ui.py`,
`framestudio/operations.py`, `.github/aidd-config.yml`
**Dependencies:** TICKET-041; TICKET-039; approved group and layout policy
**Risks:** one instance can drift from the group, selection can become
misleading, and preview state can diverge from the domain model
**Affected surfaces:** composition model, GUI controls, selection/link
presentation, preview composition, status/error handling, tests, and evidence
**Evidence path:** `evidence/phase-006-triplicate-composition.md`
**Last updated:** 2026-08-23
**Path history:** `tickets/open/TICKET-042-implement-linked-triplicate-composition.md`
-> `tickets/closed/TICKET-042-implement-linked-triplicate-composition.md`

## Outcome

The editor can activate a triplicate group for a segment, present center,
left, and right linked instances, and apply shared X/Y/zoom controls.

## Scope

- Create and remove triplicate groups using the TICKET-041 contract.
- Render or present center, left, and right instances in the editor preview.
- Select or visibly link the three instances when the mode is activated.
- Apply shared X/Y/zoom changes to all group instances.
- Surface unsupported inputs or layout failures through explicit status/error
  handling.

## Explicit non-goals

- Group cloning through split/copy/paste, which belongs to TICKET-043.
- Project persistence, CLI parity, final export, and output verification.
- Automatic focus detection, arbitrary effects, or 60 FPS enhancement.

## Observable requirements

- Given a supported segment, enabling triplicate mode should create exactly
  one center, one left, and one right instance.
- Given an active group, shared X/Y/zoom changes should update all instances
  consistently.
- Given activation or disable, the editor should expose the linked state and
  preserve the source segment's interval.
- Given an unsupported layout or media condition, the editor should report an
  actionable error without silently publishing a partial composition.

## Commands and quality gates

- `python3 -m unittest discover -s tests`
- `make check`
- `make contract`
- `make smoke`
- `make quality PYTHON=.venv/bin/python`

## Functionality flows

- Activate triplicate mode on portrait footage and inspect all three roles.
- Activate it on landscape footage with centered vertical action.
- Change shared focus controls, disable the mode, and verify source interval
  and timeline state are unchanged.

## User validation before closure

Use portrait and vertically focused landscape fixtures. Confirm automatic
linking/selection, center/side placement, shared X/Y/zoom behavior, disable
behavior, and explicit failure handling.

## Protected behavior

Existing timeline selection, segment identity and colors, source-level audio
decisions, fixed 1920x1080 canvas, source preservation, and safe export
boundaries remain unchanged.

## Definition of done

- Triplicate activation and shared controls are implemented against the
  approved policy.
- Preview and composition tests cover success and failure paths.
- Visual user-validation evidence confirms linked behavior.

## Corrective regression

- **Reported flow:** Enable triplicate on a selected segment, then click
  **Play**.
- **Requirement:** Given a paused composed preview whose playhead is inside a
  triplicated segment, clicking **Play** should begin delivering composed
  frames from that position without entering an error state or waiting for
  unrelated earlier timeline blocks to render.
- **Protected flows:** Existing direct playback, mixed-source playback,
  visible timeline seeking, source-level audio decisions, and the fixed
  1920x1080 output remain unchanged.
- **Non-goals:** This correction does not change triplicate layout, transform
  bounds, timeline ordering, or export policy.
- **Evidence path:** `evidence/phase-006-triplicate-composition.md`

## Closure

Linked triplicate composition and the later-segment playback correction are
complete under the reviewed PHASE-006 delivery checkpoint. Provider-side
checks remain unavailable because no remote or upstream is configured.
