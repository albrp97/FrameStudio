# TICKET-090 - Keep Export Planning Responsive

**Ticket:** TICKET-090
**Feature:** FEAT-029
**Phase:** PHASE-008
**Branch:** `ticket/defer-audio-analysis-during-import`
**Base:** `main` at `2702d68`
**Status:** verifying

## Scope and requirements

Opening export planning for a reopened project must present promptly without
blocking GTK's main loop. Expensive policy/backend validation and estimates
must run in a worker, stale or closed-panel results must be ignored, and
**Start export** must stay disabled until a valid plan is available.

## Entries

### Baseline and failing regression - 2026-09-04

- **Command/steps:** inspect `open_export_planning_panel()` and run the
  asynchronous preparation regression before the implementation change.
- **Expected:** export-panel preparation must not run on the calling GTK/UI
  thread.
- **Observed:** the old implementation called `prepare_export_panel()`
  synchronously before presenting the panel. The new regression initially
  failed because the asynchronous helper did not exist.
- **Status:** failed
- **Failure:** backend/runtime validation and estimates could block the GTK
  main loop and produce an Application Not Responding state.
- **Fix:** present the panel immediately, prepare a project snapshot in a
  daemon worker, return results through `GLib.idle_add`, and gate UI updates
  with generation and closed-panel checks.

### Implementation and focused regression coverage - 2026-09-04

- **Source changes:** `framestudio/app_export.py` adds
  `start_export_panel_preparation()`, explicit error states, generation
  protection, closed-panel protection, and a disabled pending state.
  `tests/test_editor_performance.py` covers worker execution and rejects both
  stale and closed-panel results.
- **Command:** `.venv/bin/python -m unittest
  tests.test_editor_composition tests.test_editor_performance`
- **Expected:** preparation runs off the calling thread; stale and closed
  results are ignored; existing editor behavior remains functional.
- **Observed:** 61 tests passed.
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
  FFmpeg/ffprobe, CUDA/TensorRT RVE integration, and the reopened local
  project supplied for reproduction.
- **Steps:** reopen the project, click **Export video**, observe the panel
  immediately, wait for backend validation and estimates, and observe the
  controls after completion.
- **Expected:** the panel appears promptly, remains responsive while
  preparation runs, shows an explicit preparing state, keeps **Start export**
  disabled until validation completes, and then exposes a valid summary.
- **Observed:** the planning panel appeared immediately with
  `Preparing export plan...` and a disabled **Start export** button. The
  editor process remained mapped and responsive while preparation ran. The
  completed panel displayed the validated folder, six inputs, 12m 46s final
  duration, 60 FPS policy, backend, estimate, and enabled **Start export**
  control. No Application Not Responding dialog appeared.
- **Status:** passed
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

- **Handoff:** validate export planning from the reopened project on the
  normal FrameStudio workflow.
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
