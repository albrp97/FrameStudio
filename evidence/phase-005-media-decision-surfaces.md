# Delivery Evidence: TICKET-036

**Feature:** FEAT-016
**Phase:** PHASE-005
**Branch:** `ticket/phase-005-source-audio-delivery`
**Evidence status:** verifying; technical evidence is terminal and user
validation is required before closure
**Recorded:** 2026-08-22

## Evidence entries

### E-036-001 - Shared GUI and CLI state

- **Category:** implementation
- **Requirement:** GUI, CLI, and reopened project expose one source-level
  decision model without implying per-segment levels.
- **Source:** `resolve_editor/app_helpers.py`,
  `resolve_editor/app_ui.py`, `resolve_editor/cli_payload.py`,
  `resolve_editor/model_project.py`
- **Expected:** Status, gain, stale state, diagnostics, policy version, and
  source identity derive from persisted source settings.
- **Observed:** The GUI displays source-level audio decision labels; CLI
  payloads expose `audio_decisions` and source audio state; persistence keeps
  the same data on round trip.
- **Status:** passed

### E-036-002 - CLI contract and parity

- **Category:** regression
- **Requirement:** The new analysis operation preserves structured CLI output
  and redacted-path behavior.
- **Command:** `make contract`
- **Expected:** All CLI contract tests pass and `analyze-audio` returns a
  versioned JSON result with explicit status.
- **Observed:** 26 CLI contract tests passed. The dedicated inspection test
  confirmed failed analysis is reported and persisted without a false success.
- **Status:** passed

### E-036-003 - Documentation

- **Category:** implementation
- **Requirement:** Human-facing documentation must describe source-level audio
  handling and explicit preview dependency failures.
- **Source:** `README.md`, `docs/specs/cli-contract.md`
- **Expected:** Users can discover `analyze-audio`, source-level reuse,
  output audio profile, and `ffplay` requirements.
- **Observed:** README now documents those behaviors and preserves the
  future-scope boundary for triplicate and 60 FPS work.
- **Status:** passed

### E-036-004 - Complete regression and quality

- **Category:** gate
- **Commands:** `make check`; `make smoke`; `make quality
  PYTHON=.venv/bin/python`
- **Expected:** GUI helper, CLI, persistence, and protected workflows remain
  green.
- **Observed:** 178 tests, smoke, and all configured local quality checks
  passed.
- **Status:** passedWithConcerns
- **Accepted warning:** No active-window screenshot or target-workstation GUI
  audio review has yet been recorded for this change.

### E-036-005 - User validation

- **Category:** userValidation
- **Steps:** Inspect the same disposable project in GUI and CLI, save/reopen,
  compare source identity, decision, route, failure, and verification state,
  and confirm no segment-level ambiguity.
- **Expected:** The user returns `PASS`, `FAIL`, `BLOCKED`, or approved
  `NOT APPLICABLE` with notes and configured before/after UI evidence.
- **Observed:** Awaiting GUI/CLI user validation.
- **Status:** blocked
- **Blocker:** Required user confirmation and before/after UI evidence have not
  been recorded.

## Readiness

The shared decision surfaces and documentation are implemented. The configured
user-facing validation gate remains open.

### E-036-006 - User validation confirmation

- **Category:** userValidation
- **Requirement:** Confirm GUI, CLI, and reopened project expose synchronized
  source-level decisions, diagnostics, routes, and failure states.
- **Observed:** The user explicitly stated, “all the tickets open are
  validated,” which includes TICKET-036's synchronized decision surfaces.
- **Status:** passed

## Readiness (superseding E-036-001 through E-036-006)

TICKET-036 has terminal implementation, automated, parity, and
user-validation evidence. Remote checks remain unavailable because no
upstream is configured.
