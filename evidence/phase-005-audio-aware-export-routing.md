# Delivery Evidence: TICKET-035

**Feature:** FEAT-015
**Phase:** PHASE-005
**Branch:** `ticket/phase-005-source-audio-delivery`
**Evidence status:** verifying; technical evidence is terminal and user
validation is required before closure
**Recorded:** 2026-08-22

## Evidence entries

### E-035-001 - Explainable route selection

- **Category:** implementation
- **Requirement:** Source-level audio changes and mixed-source composition
  select a validated fallback route; eligible unchanged one-source edits
  retain stream copy.
- **Command or source:** `resolve_editor/export_planning.py`,
  `tests/test_editor_audio_delivery.py`
- **Expected:** Route and every material reason are exposed before execution.
- **Observed:** Gain changes add the source-level normalization reason; fixed
  canvas and mixed-source conditions add their own reasons; unchanged eligible
  one-source audio remains stream-copy eligible.
- **Status:** passed

### E-035-002 - Safe mixed export

- **Category:** functionality
- **Steps:** Imported disposable landscape and portrait sources, analyzed both
  source decisions, and exported the mixed project through the CLI.
- **Expected:** Output is published only after verification, with fixed
  dimensions, expected duration, audio profile, and source preservation.
- **Observed:** Verified fallback output was H.264/AAC at 1920x1080, 48 kHz
  stereo, two seconds. SHA-256 values for both source files were identical
  before and after export.
- **Status:** passed

### E-035-003 - Timestamp regression fix

- **Category:** regression
- **Requirement:** Trimmed audio must not expand the output duration.
- **Expected:** Each trimmed audio branch resets PTS before resampling and
  concatenation.
- **Observed:** `asetpts=PTS-STARTPTS` is emitted immediately after `atrim`;
  the real mixed export duration was exactly two seconds.
- **Status:** passed

### E-035-004 - Complete regression and quality

- **Category:** gate
- **Commands:** `make check`; `make contract`; `make smoke`; `make quality
  PYTHON=.venv/bin/python`
- **Expected:** Export, CLI, source-safety, and legacy workflows remain green.
- **Observed:** 178 tests, 26 CLI contract tests, smoke, and all local quality
  analyzers passed.
- **Status:** passedWithConcerns
- **Accepted warning:** Provider-side checks cannot run without a configured
  remote or upstream.

### E-035-005 - User validation

- **Category:** userValidation
- **Steps:** Export one fast-path and one fallback project, inspect route
  explanations and progress, validate metadata, then trigger a safe failed or
  cancelled attempt and confirm the last valid output and sources remain.
- **Expected:** The user returns a terminal result with notes.
- **Observed:** Awaiting user validation.
- **Status:** blocked
- **Blocker:** Required user confirmation has not been recorded.

## Readiness

Route planning, fallback execution, verification, cleanup, and source
preservation are technically evidenced. User-facing export and failure-path
confirmation remain open.

### E-035-006 - User validation confirmation

- **Category:** userValidation
- **Requirement:** Confirm fast/fallback route explanations, verified output,
  failure cleanup, and source preservation.
- **Observed:** The user explicitly stated, “all the tickets open are
  validated,” which includes TICKET-035's export routing and safety behavior.
- **Status:** passed

## Readiness (superseding E-035-001 through E-035-006)

TICKET-035 has terminal implementation, automated, real-media, and
user-validation evidence. Remote checks remain unavailable because no
upstream is configured.
