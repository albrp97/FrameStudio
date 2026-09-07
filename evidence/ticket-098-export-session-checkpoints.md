# TICKET-098 Evidence - Persist Resumable Export Session Checkpoints

**Status:** verifying
**Date:** 2026-09-06
**Repository:** `/home/ghiki/code/FrameStudio`
**Branch:** `ticket/defer-audio-analysis-during-import`
**Planning chain:** OBJ-001 -> SCOPE-001 -> PHASE-008 -> FEAT-029 -> TICKET-098
**Change control:** CHG-010

## Scope and requirements

The ticket requires a versioned, destination-scoped export-session manifest
with atomic writes, request identity, validated stage artifacts, safe
invalidation, concurrent-session protection, and cleanup only after verified
publication. The manifest must preserve the last valid checkpoint after
cancellation, failure, or process termination and must reject changed or
unsafe requests.

Affected implementation:

- `framestudio/export_session.py`
- `framestudio/export_cache.py`
- `framestudio/export_delivery.py`
- `framestudio/export_ffmpeg.py`
- `framestudio/export_interpolation.py`
- `tests/test_editor_export_session.py`
- `tests/test_editor_export_cache.py`
- `tests/test_editor_export_execution.py`

## Baseline and implementation

The existing enhanced-intermediate cache contract was preserved. The new
session layer adds a schema-versioned manifest at
`.<destination-name>.framestudio-session/manifest.json`, an artifact
directory, an ownership lock, request fingerprints, stage state, cancellation
and failure state, artifact validation, atomic replacement, and explicit
discard/restart operations.

Each stage is persisted only after its artifact is created or copied,
validated, fingerprinted, and kept beneath the session root. A changed
source, project snapshot, timeline, destination, policy, runtime, or FFmpeg
and FFprobe identity produces an explicit mismatch instead of unsafe reuse.
Successful verified publication removes the session only at the terminal
cleanup boundary.

## Verification

| Requirement or flow | Command or steps | Expected | Observed | Status |
|---|---|---|---|---|
| Manifest round-trip, validation, invalidation, locking, cleanup | `python3 -m unittest tests.test_editor_export_session tests.test_editor_export_cache` | Persistence and safety tests pass | 15 tests passed | passed |
| Ordinary checkpoint survives cancellation | `python3 -m unittest tests.test_editor_export_execution.EditorExportExecutionTests.test_cancelled_stream_copy_reuses_completed_cuts_after_resume` | `cut-0` remains valid and final publication removes session state | Generated 3-second media completed `cut-0`, resumed without rerunning it, produced verified output, preserved source bytes, and removed the session | passed |
| Enhanced checkpoint remains independently reusable | `python3 -m unittest tests.test_editor_export_execution.EditorExportExecutionTests.test_cancelled_enhanced_export_reuses_completed_interpolation_after_resume` | Completed interpolation remains available after cancellation and is reused | Real FFmpeg `minterpolate` processing retained the first interpolation artifact; resume processed only the incomplete segment, verified output, removed cache after success, and preserved source bytes | passed |
| Process termination leaves a readable checkpoint | `python3 -m unittest tests.test_editor_cli_export.EditorCliExportTests.test_export_resumes_after_cli_process_restart` | A restarted process can discover and reuse the last committed checkpoint | The CLI was interrupted after `cut-0`; no final output was exposed, `--resume` reused the checkpoint, produced valid 3-second output, and left no matching FFmpeg process | passed |
| Source preservation | Included in generated-media ordinary, enhanced, and CLI flows | Source media remains byte-identical | Source bytes matched the pre-export snapshot in all three flows | passed |
| Full repository regression | `make PYTHON=.venv/bin/python test` | Existing behavior remains functional | 453 tests ran; 452 passed and one known fixture error remains in `test_empty_edit_refresh_stops_preview_without_reporting_an_error` because its `SimpleNamespace` lacks `_update_playback_controls` | passedWithConcerns |

## Quality gates

| Gate | Command | Result | Status |
|---|---|---|---|
| Compilation | `make PYTHON=.venv/bin/python compile` | Python sources compiled successfully | passed |
| CLI contract | `make PYTHON=.venv/bin/python contract` | 38 CLI contract tests passed | passed |
| Generated-media smoke | `make PYTHON=.venv/bin/python smoke` | Smoke flow passed | passed |
| Formatting | `make PYTHON=.venv/bin/python format-check` | 93 files already formatted | passed |
| Lint | `make PYTHON=.venv/bin/python lint` | All Ruff checks passed | passed |
| Type checking | `make PYTHON=.venv/bin/python type-check` | Mypy reported no issues in all configured targets | passed |
| Security | `make PYTHON=.venv/bin/python security` | Bandit completed successfully; report at `evidence/static-analysis/bandit.json` | passed |
| Dependency boundaries | `make PYTHON=.venv/bin/python dependency-check` | Dependency check passed; report at `evidence/static-analysis/dependencies.json` | passed |
| Dependency audit | `make PYTHON=.venv/bin/python dependency-audit` | No known vulnerabilities found; report at `evidence/static-analysis/pip-audit.json` | passed |
| Diff integrity | `make diff-check` | No whitespace errors | passed |
| Complexity | `make PYTHON=.venv/bin/python complexity` | Existing `run_benchmark` complexity is 16 versus threshold 15 in unchanged `benchmarks/restoration_benchmark.py` | passedWithConcerns |
| Duplication | `make PYTHON=.venv/bin/python duplication` | Repository duplication is 2.2% versus threshold 2.0%; report records `newClones=0` | passedWithConcerns |
| Churn | `make PYTHON=.venv/bin/python churn` | Churn report generated at `evidence/static-analysis/churn.json` | passed |

## User validation

Manual target-workstation validation is still required. The user must
exercise a long export, cancel it, inspect the destination-adjacent manifest,
change a source or export option, and confirm that the changed request is
rejected rather than reusing stale artifacts. The same request must then
resume and remove the session only after verified publication.

**Status:** blocked pending user response and target-workstation evidence.

## Readiness

The technical requirements and automated persistence flows are satisfied.
The ticket remains open and `verifying` because configured user validation is
not terminal. The known fixture error, unchanged benchmark complexity
finding, and zero-new-clone duplication warning are recorded concerns rather
than evidence of a resumable-export regression.

### User-validation closeout - 2026-09-07

- **User response:** `PASS` — the user confirmed the implemented ticket set
  is good.
- **Observed:** The user accepted the resumable-session behavior, including
  checkpoint persistence, resume, restart/discard controls, and cleanup.
- **Status:** passed; this supersedes the earlier blocked validation state.
