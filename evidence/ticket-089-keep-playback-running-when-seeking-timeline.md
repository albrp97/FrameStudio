# TICKET-089 - Keep Playback Running When Seeking on the Timeline

**Ticket:** TICKET-089
**Feature:** FEAT-029
**Phase:** PHASE-008
**Branch:** `ticket/defer-audio-analysis-during-import`
**Base:** `main` at `2702d68`
**Status:** verifying

## Scope and requirements

Timeline preview seeks must preserve the prior playback state. A playing
preview must continue from the clicked position, a paused preview must remain
paused, and backend failures must be surfaced without claiming a false playing
state.

## Entries

### Baseline and failing regression - 2026-09-04

- **Command/steps:** inspect `request_timeline_preview()` and run the focused
  playing-seek regression before the implementation change.
- **Expected:** a timeline click while playing leaves the controller in
  `PLAYING`.
- **Observed:** the old path paused the controller for the single-frame
  preview request and never resumed it; the regression failed as expected.
- **Status:** failed
- **Failure:** timeline preview did not restore the previous playing state.
- **Fix:** preserve `was_playing`, pause only for preview decoding, then resume
  through the controller after the preview request succeeds.

### Implementation and focused regression coverage - 2026-09-04

- **Source changes:** `framestudio/app_playback.py` now preserves the prior
  state across preview seeks and reports pause, preview, and resume failures.
  `tests/test_editor_composition.py` covers playing and paused timeline seeks.
- **Command:** `.venv/bin/python -m unittest
  tests.test_editor_composition tests.test_editor_performance`
- **Expected:** playing seeks remain playing, paused seeks remain paused, and
  export-planning regressions remain green.
- **Observed:** 61 tests passed, including both timeline state cases and the
  asynchronous export-planning coverage.
- **Status:** passed

### Protected repository verification - 2026-09-04

- **Commands:** `make check PYTHON=.venv/bin/python`,
  `make contract PYTHON=.venv/bin/python`, and
  `make smoke PYTHON=.venv/bin/python`.
- **Expected:** existing tests, compilation, diff checks, CLI contracts, and
  generated-media GTK smoke flows remain functional.
- **Observed:** 407 repository tests passed; compilation and diff checks
  passed; 35 CLI contract tests passed; generated-media smoke passed.
- **Status:** passed

### Target-workstation functionality validation - 2026-09-04

- **Environment:** target Linux Wayland workstation with GTK 4/PyGObject,
  FFmpeg/ffprobe, and the reopened local project supplied for reproduction.
- **Steps:** open the project, start playback, click a later timeline position,
  observe the transport and position, pause, click another timeline position,
  and observe the transport again.
- **Expected:** the first seek continues playing; the second seek remains
  paused.
- **Observed:** the transport showed `Pause` after the playing seek and the
  position advanced from approximately 00:37 to 09:02. After pausing and
  seeking again, the transport showed `Play` at approximately 11:36.
- **Status:** passed
- **Accepted warning:** the reopened media also displayed an explicit audio
  preview failure warning while video playback and transport controls
  continued. This is retained as an environment/media concern and was not
  converted into a silent pass.
- **Artifacts:** live screen captures were used transiently for validation but
  were not retained because they contained private local source media.

### Static analysis and review - 2026-09-04

- **Commands:** `make quality PYTHON=.venv/bin/python` and
  `make -k complexity duplication dependency-check dependency-audit security
  churn PYTHON=.venv/bin/python`.
- **Observed:** 407 tests, format, lint, typing, duplication, dependency
  boundaries, dependency audit, Bandit, and churn completed. Ruff reports no
  lint or formatting findings for the changed surfaces. Pip-audit reports no
  known vulnerabilities and Bandit reports no findings.
- **Status:** passedWithConcerns
- **Accepted warning:** the repository-wide complexity gate remains blocked by
  the pre-existing `C901` finding at
  `benchmarks/restoration_benchmark.py:1794`
  (`run_benchmark`, complexity `16 > 15`), outside this ticket's scope.

### Maintainer validation - 2026-09-04

- **Handoff:** validate playing and paused timeline seeks on the normal
  FrameStudio workflow.
- **User response:** `PASS`.
- **Status:** passed

## Readiness

Technical, target-workstation, and maintainer validation evidence is complete.
The ticket stays `verifying` because the branch is unpublished and the
configured remote-check gate has not run.

## Open blockers

- Required remote checks are unavailable until the branch is published.
- Existing repository-wide complexity debt remains outside this ticket.

### User-validation closeout - 2026-09-07

- **User response:** `PASS` — the user confirmed the implemented ticket set
  is good.
- **Status:** passed; this supersedes the earlier pending user-validation
  state.
