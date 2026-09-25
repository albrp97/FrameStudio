# CHG-011 - Deliver Authorized Existing Worktree Changes

**Change ID:** CHG-011
**Type:** Material planning change
**Status:** approved-and-applied
**Date:** 2026-09-09
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Owner:** repository planning in the active worktree
**Approval:** User-authorized by the request to include all current changes in
the `main` delivery, then explicitly confirmed with “include everything stop
asking me questions.”
**Affected IDs:** PHASE-001, FEAT-002, TICKET-029, PHASE-004, FEAT-011,
TICKET-105, PHASE-008, FEAT-028, FEAT-029, TICKET-106, TICKET-107,
PHASE-009, FEAT-031, TICKET-104
**Evidence paths:** `evidence/space-playback-toggle.md`,
`evidence/ticket-105-randomized-clip-add-order.md`,
`evidence/ticket-106-timeline-wheel-seek-pacing.md`,
`evidence/ticket-107-preserve-resolution-canvas-fit.md`,
`evidence/efficient-export-pipeline-implementation.md`
**Source paths:** `framestudio/app_project.py`, `framestudio/app_helpers.py`,
`framestudio/composition_render.py`, `framestudio/cli.py`,
`framestudio/timeline_order.py`, `framestudio/export_process.py`,
`tests/test_editor_randomized_clip_add.py`, `tests/test_editor_composition.py`,
`docs/planning/phases.md`, `docs/planning/features.md`,
`docs/planning/backlog.md`, `.github/aidd-config.yml`

## Request and classification

The user explicitly authorized delivery of the entire existing worktree to
`main`, not only the active PHASE-009 export ticket and the newly reported
multi-clip randomization defect. The worktree also contains a project-reopen
playback-error correction, a 30-second timeline wheel seek step, and safe
downscaling of oversized preserved-resolution content to the fixed output
canvas. These behaviors touch previously closed PHASE-001, PHASE-004, and
PHASE-008 records, so adding them without reopening their affected planning
subtrees would leave the delivery untraceable.

This is a material planning change because it reopens previously completed
records, adds separately verifiable corrective tickets, and clarifies the
boundary between preserving resolution during enhancement and fitting final
composition to the fixed 1920x1080 canvas. The work remains within
OBJ-001/SCOPE-001 and does not add multi-track editing, new media sources
beyond the existing mixed-source contract, new dependencies, or a new output
profile.

## Approved decision

- Reopen PHASE-001, FEAT-002, and TICKET-029 to verify that project reopen
  reports playback-backend failures while preserving the current project.
- Reopen PHASE-004 and FEAT-011; add TICKET-105 for randomized multi-clip
  import/add order across the GUI, CLI, and retained concat compatibility
  surface.
- Reopen PHASE-008 and FEAT-029; add TICKET-106 for practical 30-second
  timeline-wheel seeking without changing other scroll gestures.
- Reopen PHASE-008 and FEAT-028; add TICKET-107 to fit oversized source
  content into the fixed output canvas without cropping. Preserve the
  no-downscaling requirement for restoration/upscale intermediates; only the
  final fixed-canvas composition may scale oversized content down.
- Keep PHASE-009, FEAT-031, and TICKET-104 active for the existing export
  integrity, resume, and quality remediation work.

The same stable-ID records move from `closed/` to `open/` before receiving
new work. Indexes, path histories, parent links, backlog entries, and evidence
paths must remain synchronized. No phase or feature is closed again until
its new validation and delivery gates are terminal.

## Impact and protected behavior

- **Playback lifecycle:** opening a project that raises
  `PlaybackBackendError` must surface the explicit message without replacing
  the existing valid project state.
- **Timeline ordering:** a multi-source batch is shuffled before it is
  appended/imported, while a single source remains in its normal position and
  existing project edits are preserved.
- **Timeline navigation:** normal wheel input moves the playhead by 30 seconds
  per unit; horizontal, modified, and focus-control scroll behavior remains
  distinct.
- **Composition:** output remains 1920x1080; oversized content is fit to that
  canvas rather than being cropped by the preserve-resolution branch.
  Restoration/upscale intermediates remain protected from unintended
  downscaling.
- **Export:** exact frame-count repair, valid cached-intermediate reuse,
  atomic publication, source preservation, output verification, and resume
  behavior remain mandatory.

## Validation and approval state

The final `make quality PYTHON=.venv/bin/python` run passed 489 tests,
compilation, formatting, Ruff, mypy, complexity, duplication baseline
(1.780%, zero new clones), dependency checks, `pip-audit`, Bandit, and churn.
`make smoke PYTHON=.venv/bin/python` and
`make contract PYTHON=.venv/bin/python` passed; contract ran 39 tests.
Planning path/status/index consistency was checked for all 12 reopened or
newly verifying records. The project-reopen failure path was reproduced and
fixed with a regression test proving the previous project and backend remain
active when candidate preview seeking fails. The final read-only review found
no remaining actionable introduced code findings; the local-to-PR parity and
user-validation gaps remain blockers rather than passes.

The local quality command matches the PR workflow command, but runtime parity
is unavailable: local verification used Python 3.14.7 while the PR workflow
uses the Ubuntu 24.04 system Python 3.12. No PR run exists for the uncommitted
branch. The user returned `PASS` for the combined target-workstation
validation and stated they tested it, but declined to provide the requested
window-only before/after screenshots, per-flow observations, output metadata,
or source-hash results. The PASS is recorded as `passedWithConcerns`; required
UI evidence remains blocked. Remote checks, PR approval, commit, push, PR, and
merge are not claimed as complete.

## Path and history

Created in `docs/planning/reviews/` after the user's explicit authorization
to include the entire current worktree in the requested delivery. Reopened
parent records preserve their stable IDs and append the prior/current paths
rather than being duplicated.
