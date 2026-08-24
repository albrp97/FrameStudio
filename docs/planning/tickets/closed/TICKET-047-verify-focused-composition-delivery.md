# TICKET-047 - Verify Focused Composition Delivery

**Ticket ID:** TICKET-047
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
**Priority:** 10
**Owner:** repository planning; maintainer identity is not recorded
**Approval:** user-authorized on 2026-08-22 to create and implement the
PHASE-006 ticket set; the completed outcome was confirmed by the user on
2026-08-23
**Provider:** auto; base and target branches are not configured in
`.github/aidd-config.yml`
**Source paths:** `docs/planning/features/open/FEAT-017-editing-reusable-visual-focus-controls.md`,
`docs/planning/features/open/FEAT-018-creating-linked-triplicate-compositions.md`,
`docs/planning/features/open/FEAT-019-delivering-focused-compositions-safely.md`,
`docs/planning/phases/open/PHASE-006-focusing-and-composing-important-action.md`,
`AGENTS.md`, `.github/aidd-config.yml`
**Dependencies:** TICKET-039, TICKET-040, TICKET-043, TICKET-045, and
TICKET-046; representative portrait and vertical-action media; target
workstation playback and export access
**Risks:** metadata cannot prove visual correctness, manual focus quality is
subjective, and integrated failures can leave hidden state drift
**Affected surfaces:** end-to-end fixtures, GUI, CLI, persistence, preview,
export, ffprobe verification, source-safety checks, screenshots, and evidence
**Evidence path:** `evidence/phase-006-focused-composition-delivery.md`
**Last updated:** 2026-08-23
**Path history:** `tickets/open/TICKET-047-verify-focused-composition-delivery.md`
-> `tickets/closed/TICKET-047-verify-focused-composition-delivery.md`

## Outcome

PHASE-006 has reproducible evidence that reusable focus controls and linked
triplicate compositions survive the complete GUI/CLI, persistence, preview,
and verified export workflow.

## Scope

- Exercise portrait and landscape vertical-action fixtures through the full
  supported workflow.
- Compare transform values, linked groups, GUI/CLI payloads, save/reopen
  state, preview, route explanations, and final output.
- Verify dimensions, duration, streams, playability, placement, and source
  preservation.
- Perform target-workstation visual review and record measurable versus
  subjective results.
- Repeat supported failure and cancellation paths and verify recovery.

## Explicit non-goals

- Adding behavior not covered by FEAT-017 through FEAT-019.
- Automatic FPS enhancement, arbitrary effects, or full NLE behavior.
- Treating metadata or a fast command alone as visual correctness.

## Observable requirements

- Given the same focused fixture and operation sequence, GUI and CLI should
  produce equivalent state and final duration.
- Given a successful export, output should satisfy approved dimensions,
  duration, streams, playability, placement, and source-safety checks.
- Given manual visual review, evidence should distinguish visual judgment from
  measurable output correctness.
- Given an invalid or failed operation, source files, project state, and last
  valid output should remain intact.

## Commands and quality gates

- `python3 -m unittest discover -s tests`
- `make check`
- `make contract`
- `make smoke`
- `make quality PYTHON=.venv/bin/python`
- Target-workstation playback, screenshots, FFmpeg, and ffprobe checks.

## Functionality flows

- Run the complete portrait triplicate workflow in the GUI and CLI.
- Run a landscape vertical-action workflow with focus adjustments.
- Save/reopen, compare state, export, inspect output, and repeat a failure
  path.

## User validation before closure

Use disposable portrait and vertical-action videos. Confirm focus controls,
linked group behavior, GUI/CLI parity, persistence, preview, output placement,
metadata, playability, and source preservation. Return `PASS`, `FAIL`, or
`BLOCKED` with retained window-only evidence.

## Protected behavior

All existing one-source and mixed-source editing, source-level audio,
project compatibility, fixed 1920x1080 output, safe export, CLI contracts,
legacy scripts, and source preservation remain required baselines.

## Definition of done

- Automated, real-media, visual, GUI/CLI, persistence, output, and
  source-safety evidence is recorded.
- Every PHASE-006 exit condition has terminal evidence or an explicit blocked
  or skipped reason.
- No unsupported FPS, arbitrary effects, or full-compositor behavior is
  claimed.

## Closure

Integrated focused-composition delivery is complete under the reviewed
PHASE-006 delivery checkpoint. Provider-side checks remain unavailable because
no remote or upstream is configured.
