# Delivery Evidence: TICKET-028

- Phase: `PHASE-002` - Cutting and Exporting One Source Safely
- Feature: `FEAT-004` - Removing Unwanted Portions from One Source
- Ticket: `TICKET-028` - Restore One-Source Block Movement
- Status: `verifying`
- Branch: `main`
- Evidence path: `evidence/one-source-block-movement.md`

## Requirement

Given a one-source timeline split into three blocks, moving the selected middle
block with `Shift+Left` or `Shift+Right` changes only its timeline position.
The block keeps its source interval, identity, deletion state, owned state,
display color, and duration.

## Baseline

- Before the fix, the GUI and CLI rejected one-source movement with
  `Block movement requires a mixed-source timeline`.
- The regression tests were added before implementation and failed against that
  mixed-source-only guard.

## Automated evidence

### MODEL-001 - One-source movement and placement

- Evidence: `tests/test_editor_model.py`
- Observed: One-source blocks can be reordered, retain source intervals and
  state, persist explicit timeline placement, treat boundary moves as no-ops,
  and split correctly after movement.
- Status: `passed`

### CLI-001 - Shared movement and persistence

- Evidence: `tests/test_editor_cli_parity.py`
- Observed: CLI movement persists the reordered timeline placement and restores
  the same order and duration.
- Status: `passed`

### PLAYBACK-001 - Reordered one-source preview

- Evidence: `tests/test_editor_ffmpeg_playback.py`
- Observed: The composed playback backend accepts a one-source reordered
  timeline and follows timeline order while reading preserved source ranges.
- Status: `passed`

### FOCUSED-001 - Regression suite

- Command: `python3 -m unittest tests.test_editor_model tests.test_editor_cli_parity tests.test_editor_ffmpeg_playback`
- Observed: 39 tests passed.
- Status: `passed`

### GATES-001 - Repository checks

- Commands:
  - `make check PYTHON=.venv/bin/python`
  - `make contract PYTHON=.venv/bin/python`
  - `make smoke PYTHON=.venv/bin/python`
  - `make quality PYTHON=.venv/bin/python`
- Observed: All configured local checks passed, including tests,
  compilation, diff checks, contract checks, generated-media smoke flows,
  formatting, lint, type checking, complexity, duplication, dependency,
  security, and churn checks.
- Status: `passed`

## Target-workstation evidence

### GUI-001 - Move the selected middle block

- Project: disposable six-second one-source project split into three
  two-second blocks.
- Steps:
  1. Focus the Resolve Editor window.
  2. Select the middle block (`Clip 2`, `00:02 - 00:04`).
  3. Press `Shift+Left`.
- Expected: The selected block moves before its neighbor without changing its
  source interval, color, or duration.
- Observed: The purple middle block moved to the first timeline position, the
  green block moved to the second position, the status reported
  `Moved 1 selected block(s) left`, and the selected block remained
  `00:02 - 00:04`.
- Evidence:
  - `evidence/screenshots/one-source-movement-before.png`
  - `evidence/screenshots/one-source-movement-middle-selected.png`
  - `evidence/screenshots/one-source-movement-after.png`
- Status: `passedWithConcerns`
- Concern: Maintainer confirmation is still required for the complete
  save/reopen and split-after-move workflow on the target workstation.

### USER-001 - Maintainer validation

- Flow: Split a disposable one-source video into three blocks, move the
  selected middle block with `Shift+Left` and `Shift+Right`, confirm its
  source range, color, and duration remain attached, save and reopen, and
  split the moved block.
- Result: Maintainer selected `PASS` through the validation handoff.
- Status: `passed`

## Readiness

- Automated regression and local quality evidence: `passed`
- Target-workstation movement screenshot: `passed`
- Remote checks: unavailable; no remote or upstream is configured
- User validation: `passed`
- Ticket status: `verifying` pending configured delivery closeout
