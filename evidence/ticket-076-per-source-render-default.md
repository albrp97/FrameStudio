# TICKET-076 Per-Source Render Default Evidence

**Phase:** PHASE-008  
**Feature:** FEAT-026  
**Ticket:** TICKET-076  
**Branch:** `ticket/phase-008-responsive-preview-media-strategy`  
**Base revision:** `93b49e8`  
**Evidence started:** 2026-08-26

## Planning chain

`OBJ-001 -> SCOPE-001 -> CAP-005/CAP-011/CAP-012 -> PHASE-008 ->
FEAT-026 -> TICKET-076`

## Acceptance coverage

- Enhanced export uses per-source, native-rate preparation and independent
  interpolation by default.
- Retained segments are assembled in timeline order with stream copy when
  compatible.
- Incompatible joins use the verified fallback path.
- Video-only output removes discarded audio before stream-copy assembly so
  frame-rate metadata is not affected by audio timestamps.
- Cancellation, verification, cleanup, and source preservation remain
  protected.

## Evidence entries

### E-076-IMPLEMENTATION-001 - Per-source enhanced route and video-only join fix

- **Timestamp:** 2026-08-26
- **Category:** implementation
- **Requirement:** Use Strategy B for enhanced export and keep video-only
  stream-copy joins valid when intermediates contain audio.
- **Observed:** The enhanced dispatcher selects per-source preparation;
  retained segments are interpolated independently and joined in timeline
  order. Video-only assembly now remuxes audio-bearing intermediates with
  `-map 0:v:0 -an -c:v copy` before concat-demuxer stream copy, and validates
  frame count and duration before accepting the join.
- **Status:** passed
- **Source references:** `resolve_editor/export_interpolation.py`,
  `resolve_editor/export_smart_render.py`,
  `tests/test_editor_smart_render.py`,
  `tests/test_editor_export_execution.py`

### E-076-REGRESSION-001 - Focused smart-render and export tests

- **Timestamp:** 2026-08-26
- **Category:** regression
- **Command:** `python3 -m unittest tests.test_editor_smart_render
  tests.test_editor_export_execution`
- **Expected:** Smart-render routing, timeline-order enhanced assembly,
  fallback behavior, cancellation, source preservation, and export
  regressions pass.
- **Observed:** 21 tests passed.
- **Status:** passed

### E-076-FUNCTIONALITY-001 - Generated video-only stream-copy regression

- **Timestamp:** 2026-08-26
- **Category:** functionality
- **Command:** `python3 -m unittest
  tests.test_editor_export_execution.EditorExportExecutionTests.test_video_only_assembly_stream_copies_audio_bearing_segments`
- **Expected:** Two generated H.264/AAC segments assembled under a video-only
  policy produce a video-only H.264 MP4 with correct 10 FPS metadata, about
  two seconds of duration, and unchanged source bytes.
- **Observed:** The generated-media flow passed; the output had no audio,
  H.264 video, 10/1 FPS, expected duration, and both sources were unchanged.
- **Status:** passed
- **Source references:** `tests/test_editor_export_execution.py`

### E-076-GATE-001 - CLI contract and generated-media smoke

- **Timestamp:** 2026-08-26
- **Category:** gate
- **Commands:** `make contract`; `make smoke`
- **Expected:** CLI contracts and generated-media editor smoke flows pass.
- **Observed:** 31 CLI contract tests passed and generated-media smoke
  completed successfully.
- **Status:** passed

### E-076-QUALITY-001 - Configured local quality suite

- **Timestamp:** 2026-08-26
- **Category:** staticAnalysis
- **Command:** `make quality PYTHON=.venv/bin/python`
- **Expected:** Configured tests, compilation, formatting, lint, type,
  complexity, duplication, dependency, security, and churn gates pass.
- **Observed:** 312 tests, compilation, diff checks, Ruff formatting/lint,
  mypy, and complexity checks passed. jscpd reported 35 duplicate groups,
  553 duplicated lines, 2.1442% duplication against the configured 2.0%
  threshold, and `newClones: 0`; the command stopped at the duplication gate,
  so later dependency, audit, security, and churn stages did not run in this
  invocation.
- **Status:** failed
- **Failure:** The configured duplication threshold is not terminally green.
- **Accepted warning:** The report identifies no new clones relative to its
  baseline; the remaining overlap is concentrated in existing export delivery
  and interpolation orchestration.
- **Artifacts:** `evidence/static-analysis/jscpd-report.json`,
  `evidence/static-analysis/baseline.json`

## Readiness

The implementation and focused/generated-media evidence are complete. The
ticket remains open and is not delivery-ready because configured local
duplication quality is failing and required user validation and review have
not been recorded. No commit, remote publication, or pull request has been
created.

## User-validation handoff

- **Setup:** Use the affected project under `~/Videos` with enhancement
  enabled and a new output path. Preserve the original source files.
- **Steps:** Export the project, watch the progress panel through preparation,
  interpolation, assembly, and verification, then inspect the output with
  `ffprobe`. Confirm the output plays, retains the expected visual timeline
  order, and has the expected audio presence for the project policy.
- **Video-only check:** If the project is configured without final audio,
  confirm the output has no audio stream and reports the selected FPS rather
  than an unexpected fractional rate.
- **Safety check:** Confirm the original media is unchanged and cancellation
  or failure leaves no published partial output.
- **Return:** `PASS`, `FAIL`, or `BLOCKED`, with the output path and any
  observed error or metadata details.

### E-076-USER-VALIDATION-001 - User-confirmed manual validation

- **Timestamp:** 2026-08-28T08:06:41+02:00
- **Category:** userValidation
- **Requirement:** The enhanced per-source route, timeline-order assembly,
  video-only handling, and protected export behavior are manually validated.
- **Steps:** The user stated, "you can close all the tickets i manually
  validated everything and you can then /aidd-commit".
- **Observed:** The user reports that the ticket behavior was manually
  validated. This response did not include a per-ticket output path,
  metadata capture, or separate failure-path notes.
- **Status:** passed
- **Accepted warning:** This entry satisfies the user-validation response
  only; the failed configured duplication gate and missing terminal delivery
  evidence remain unresolved.

### E-076-READINESS-002 - Current delivery state after user validation

- **Timestamp:** 2026-08-28T08:06:41+02:00
- **Category:** gate
- **Requirement:** Do not close or deliver the ticket while required quality,
  review, and delivery evidence remains nonterminal.
- **Observed:** User validation is recorded as passed. The configured
  duplication gate remains failed, the branch is not ticket-dedicated, no
  paths are staged, and no commit or remote delivery exists.
- **Status:** blocked
- **Blocker:** A scoped reviewed commit cannot be created until the failed
  quality gate and commit-scope/branch prerequisites are resolved.
