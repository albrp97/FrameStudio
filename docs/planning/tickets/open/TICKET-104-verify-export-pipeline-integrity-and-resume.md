# TICKET-104 - Verify Export Pipeline Integrity and Resume

**Ticket ID:** TICKET-104
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-009
**Feature:** FEAT-031
**Capability links:** CAP-005, CAP-011, CAP-012
**Status:** verifying
**Horizon:** future
**Priority:** 1
**Owner:** repository implementation in the active worktree
**Approval:** user-authorized by the 2026-09-09 export-optimization request
**Last updated:** 2026-10-16
**Source paths:** `docs/planning/features/open/FEAT-031-executing-efficient-resumable-export-pipelines.md`,
`docs/planning/tickets/open/TICKET-103-implement-conditional-grouped-export-route.md`,
`framestudio/export_delivery.py`, `framestudio/export_session.py`,
`framestudio/export_cache.py`, `framestudio/export_console.py`,
`tests/test_editor_smart_render.py`,
`tests/test_editor_interpolation.py`, `tests/test_editor_export_execution.py`,
`tests/test_editor_export_console.py`, `framestudio/timeline.py`,
`tests/test_editor_track_drag.py`,
`tests/test_editor_track_drag_functionality.py`,
`tests/test_editor_keyboard_functionality.py`,
`tests/test_editor_removal_controls_functionality.py`,
`tests/test_editor_precise_preview_functionality.py`, `.github/aidd-config.yml`
**Dependencies:** TICKET-103 implementation; protected baseline; benchmark
evidence; existing user-validation and review gates
**Risks:** tests that validate only units, hidden boundary artifacts, stale
cache reuse, and target-workstation/runtime differences
**Affected surfaces:** functionality tests, generated-media verification,
resume/cancellation, source hashes, evidence, user-validation instructions,
and quality gates
**Evidence path:** `evidence/efficient-export-pipeline-implementation.md`
**Protected behaviors:** exact timeline order, hard boundaries, output
profile, audio, visual composition, source preservation, atomic publication,
cleanup, cancellation, and resumability
**Path history:** created at
`tickets/open/TICKET-104-verify-export-pipeline-integrity-and-resume.md`

## Outcome

Automated functionality evidence and target-workstation checks prove that the
optimized export route is faster for its selected cases without changing
protected output behavior or resumability.

## Scope

- Add automated functionality tests that exercise the grouped route through
  actual route-planning/execution boundaries, not only helper units.
- Verify exact output frame count, duration, dimensions, codecs, audio,
  playability, source hashes, hard-cut boundaries, transform/triplicate state,
  cleanup, and cache/session reuse.
- Record the benchmark winner, implementation evidence, limitations, and the
  exact user-validation handoff.

## Explicit non-goals

- Treating unavailable hardware/runtime or subjective visual review as passed.
- Broad refactoring unrelated to the selected export route.
- Closing the ticket before user validation is returned.

## 2026-10-16 multitrack verification refinement

Verify the selected candidate/combinations against the fresh TICKET-102
baseline and the PHASE-010 / CHG-013 output contract. Include real FFmpeg
functionality tests, not only route-selection units: dynamic 1/2/3/4-panel
layouts, gaps, unequal starts/ends, repeated ranges, transforms/triplicate,
frame/timestamp boundaries, audio pan/mix, and separate track/source reels
where the candidate changes their path.

Verify cancellation during the selected route, completed-artifact reuse,
invalid-artifact rejection, source preservation, final verification before
atomic publication, and truthful global/current progress. Measure cold
application-cache and warm/resumed behavior separately without concurrent
benchmark competitors. Keep the user's full export paused. Record actual
numbers and evidence limits; previous benchmark results are historical, not
proof of the current worktree.

The authoritative automatic mode uses agent-owned functionality evidence and
the configured Rubber Duck validator, never fabricated human validation.
Existing historical user-validation instructions remain above as provenance;
they do not override the configured automatic-mode contract.

## Observable acceptance criteria

- Given one-frame layout intervals, output retains every planned frame with
  contiguous global CFR timestamps, including fractional target rates.
- Given a prior video-clock recipe, a new render invalidates video/mux
  checkpoints without repeating valid native, FPS or independent audio work.
- Given candidate and baseline with equally wrong decoded counts, the benchmark
  rejects them instead of treating matching hashes as sufficient.
- Given a representative generated-media project, the functionality test
  completes the optimized export and verifies the persisted output contract.
- Given a deleted boundary, decoded samples on both sides remain in timeline
  order without cross-boundary interpolation artifacts in the selected route.
- Given cancellation after a completed intermediate, resume reuses that
  artifact and avoids repeating the completed stage.
- Given changed source or policy identity, stale artifacts are not reused.
- Given a long-running stage with progress callbacks below the next percentage
  threshold, human-readable output periodically reports elapsed progress so
  active work is distinguishable from a stalled export.
- Given a long output-frame-count scan with no intermediate FFprobe updates,
  export progress periodically identifies that validation is still running.
- Given a long decoded-output validation scan, human-readable progress
  periodically identifies that decoding is still running.
- Given the completed evidence, the user receives exact setup, steps,
  expected results, failure paths, cleanup, and a `PASS`/`FAIL` response.

## Validation

The continuation request authorizes bounded remediation of the blocking
quality failures discovered during this verification. Given a non-drag
segment press in the shaded start region, seek should snap immediately,
before asynchronous viewport changes and release, while Super bypass and
actual dragging remain unchanged. Cover this with a failing handler regression
and the existing real-pointer functionality charter. Restore missing Xvfb/xauth
only in a signed, session-owned tool directory; do not modify system packages.
The existing preview test's equal-length byte comparison must also specify
strict zip behavior so the configured Ruff gate can run without weakening its
pixel-quality assertions. Keep renderer settings and original export paused.

- Run targeted functionality tests and the full existing unittest suite.
- Run the repository compilation, smoke, contract, and configured quality
  commands that are available.
- Run a real-media target-workstation export/playback check for affected
  media paths; record unavailable checks explicitly.

## User-validation plan

Latest local result on 2026-10-16: the full authenticated-Xvfb `make quality`
passes, with 1032 tests run, 10 skipped and zero failures/errors; all configured
static checks, CLI contracts and GTK smoke pass. The exact configured Rubber
Duck profile approves scoped agent-owned automatic validation and local task
completion. Runtime/remote publication gates remain unresolved, so this same
record remains open in `verifying`, not completed or human-validated. See
`MULTITRACK-20261016-QUALITY-REMEDIATION-VALIDATOR` in the evidence record.

- **Setup:** open the optimized output, baseline output, evidence report, and
  source project on the target workstation.
- **Steps:** inspect timeline order, cuts, motion, faces/text, focus offsets,
  triplicate edges, audio, output metadata, and the cancel/reopen/resume flow.
- **Expected result:** output is visually and technically equivalent where the
  route promises equivalence, and resume skips completed work.
- **Failure paths:** any mismatch, freeze, stale reuse, source modification,
  invalid output, or missing evidence is a failure or blocker.
- **Cleanup:** retain evidence, then remove temporary artifacts after
  publication.
- **Evidence response:** return `PASS`, `FAIL`, `BLOCKED`, or approved
  `NOT APPLICABLE` with paths and observations.
