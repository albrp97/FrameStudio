# Delivery Evidence: TICKET-032

**Feature:** FEAT-014
**Phase:** PHASE-005
**Branch:** `ticket/phase-005-source-audio-delivery`
**Evidence status:** verifying; technical evidence is terminal and user
validation is required before closure
**Recorded:** 2026-08-22

## Evidence entries

### E-032-001 - Source-scoped persistence

- **Category:** implementation
- **Requirement:** One decision is stored per source and survives save/reopen
  without becoming segment state.
- **Command or source:** `framestudio/model_project.py`,
  `framestudio/operations.py`, `tests/test_editor_audio.py`
- **Expected:** Source settings contain measurements, decision, policy version,
  diagnostics, audio metadata, and source fingerprint.
- **Observed:** Decisions persist under
  `project.source_settings[source_id]["audio"]`; split, copy, and paste tests
  retain one source decision and do not create per-segment decisions.
- **Status:** passed

### E-032-002 - Failure and stale states

- **Category:** functionality
- **Requirement:** Unsupported, failed, and changed-source states are explicit.
- **Command:** `python3 -m unittest tests.test_editor_audio`
- **Expected:** Missing audio is `not-applicable`, missing codec metadata is
  `unsupported`, failed FFmpeg analysis is `failed`, and changed source
  fingerprints trigger reanalysis.
- **Observed:** The focused audio tests passed for all four cases, including
  relinked-source fingerprint refresh.
- **Status:** passed

### E-032-003 - CLI persistence flow

- **Category:** regression
- **Requirement:** CLI analysis reports and persists the same source-level
  decision contract.
- **Command:** `python3 -m unittest tests.test_editor_cli_inspection`
- **Expected:** `analyze-audio` emits structured JSON and save/reopen restores
  the explicit decision status.
- **Observed:** CLI inspection tests passed; the failure state was emitted and
  recovered after reopening.
- **Status:** passed

### E-032-004 - Complete regression and quality

- **Category:** gate
- **Commands:** `make check`; `make contract`; `make quality
  PYTHON=.venv/bin/python`
- **Expected:** Protected editor, CLI, persistence, and legacy-script flows
  remain green.
- **Observed:** 178 tests passed, 26 CLI contract tests passed, and the full
  configured quality suite passed.
- **Status:** passedWithConcerns
- **Accepted warning:** No remote or upstream is configured.

### E-032-005 - User validation

- **Category:** userValidation
- **Steps:** Open a disposable mixed-source project, inspect both source
  decisions, split and reorder one source, save/reopen, and confirm each
  source retains one recoverable decision.
- **Expected:** The user returns a terminal validation result with notes.
- **Observed:** Awaiting user validation.
- **Status:** blocked
- **Blocker:** Required user confirmation has not been recorded.

## Readiness

Source decision analysis, persistence, deterministic serialization, failure
states, and stale-source refresh are implemented and tested. Closure remains
blocked by required user validation and unavailable remote checks.

### E-032-006 - User validation confirmation

- **Category:** userValidation
- **Requirement:** Confirm source-scoped analysis, persistence, stale-source
  handling, and explicit failure states.
- **Observed:** The user explicitly stated, “all the tickets open are
  validated,” which includes TICKET-032's source decision and persistence
  behavior.
- **Status:** passed

## Readiness (superseding E-032-001 through E-032-006)

TICKET-032 has terminal implementation, automated, and user-validation
evidence. Remote checks remain unavailable because no upstream is configured.
