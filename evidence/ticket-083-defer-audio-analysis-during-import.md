# TICKET-083 - Defer Audio Analysis During Source Import

**Status:** verifying
**Branch:** `ticket/defer-audio-analysis-during-import`
**Base:** `main` at `2702d68`
**Change control:** `CHG-009`
**Ticket:** `TICKET-083`
**Evidence record:** append-only during this ticket

## Scope and protected flows

Separate metadata-ready project attachment from full-file source-level audio
analysis for GTK source import and project reopen. Preserve the existing
`legacy-concat-v1` policy, persisted decision shape, source fingerprint
staleness checks, export-time `ensure_project_audio_analysis` gate, playback
generation safety, project persistence, source preservation, and legacy
commands.

## Requirements under verification

- Attach a probed project and usable timeline before full-file audio analysis
  completes.
- Publish explicit per-source pending, analyzing, ready, and failed states.
- Apply background results only to the matching current project and generation.
- Preserve playback position/play state when terminal audio decisions refresh
  preview inputs.
- Keep export analysis and failure behavior explicit for unresolved decisions.
- Preserve terminal audio decisions and full-file policy semantics.
- Demonstrate before/after time to usable project separately from total
  analysis time.

## Baseline

### Protected implementation state

At ticket start, `_load_source_worker()` probes sources, then calls
`analyze_project_audio()` before `_finish_source_load()` attaches the project.
`attach_project()` and `load_project_path()` also call
`ensure_project_audio_analysis()` synchronously. Editing remains locked while
`_source_load_in_progress` is true.

### Prior local measurements to reproduce

These measurements were captured during root-cause investigation before this
ticket branch was created. They are provisional until the same protocol is
rerun and command details are appended below:

| Scenario | Probe time | Audio-analysis time | Time to usable project |
|---|---:|---:|---:|
| Three synthetic 120-second H.264/AAC sources | ~0.096 s | ~10.330 s | blocked until analysis completed |
| One synthetic 120-second H.264/AAC source | not isolated | ~3.552 s | blocked until analysis completed |
| One synthetic 600-second H.264/AAC source | not isolated | ~17.689 s | blocked until analysis completed |
| One synthetic 10-second source, first preview frame | not applicable | not applicable | ~0.045 s after attachment |

These are local synthetic results, not universal performance claims.

### Baseline command set

The exact repeatable benchmark commands and fixture descriptions will be
recorded here before source edits. Required repository gates are:

```sh
python3 -m unittest discover -s tests
python3 -m py_compile resolve_media.py resolve_concat.py resolve_fps.py tests/*.py
make check
make contract
make smoke
make quality
```

Configured commands that are unavailable or fail because of the environment
must be recorded as warnings rather than treated as passes.

## Entries

### Planning and baseline initialization — 2026-08-28

- **Observed:** CHG-009 reopened PHASE-008 and FEAT-024. TICKET-083 was
  created in the configured open directory on the dedicated ticket branch.
- **Status:** in progress
- **Next evidence:** rerun the protected baseline, then add failing lifecycle
  regressions before implementation.

### Protected baseline results — 2026-08-28

- **Command:** `make test`
  - **Observed:** passed serially; 369 tests passed.
- **Command:** `python3 -m py_compile resolve_media.py resolve_concat.py
  resolve_fps.py tests/*.py`
  - **Observed:** passed.
- **Command:** repository CLI contract suite
  - **Observed:** passed; 35 tests passed.
- **Command:** concurrent baseline test runs
  - **Observed:** one intermittent failure occurred in
    `tests/test_editor_export_execution.py:284`
    (`test_mixed_enhanced_export_prepares_and_interpolates_each_timeline_segment`);
    a subsequent serial run passed all 369 tests. This is recorded as a
    pre-existing/intermittent baseline observation and is not changed by this
    ticket.
- **Command:** `make quality`
  - **Observed:** repository tests passed during the quality run, but the gate
    stopped because Ruff is unavailable (`No module named ruff`). Ruff
    availability is an environment limitation, not a passed quality result.
- **Status:** baseline recorded; implementation may proceed with the
  intermittent test and Ruff limitation carried forward.

### Implementation and focused regressions — 2026-08-28

- **Implementation:** GTK import and project reopen attach after metadata
  probing; per-source full-file audio analysis remains in a background worker
  with generation, project, source, and fingerprint checks.
- **Implementation:** Background audio analysis is cancellation-aware and
  serialized through a per-window lock. Export planning uses that same lock,
  forwards its cancellation event through `plan_project_export` and
  `ensure_project_audio_analysis`, and converts cancellation into the
  existing explicit `ExportPlanningError` path.
- **Implementation:** Window close invalidates the audio-analysis generation
  and signals cancellation before stopping playback, preventing late worker
  callbacks from touching a closed window.
- **Regression command:** `python3 -m unittest
  tests.test_editor_composition tests.test_editor_performance
  tests.test_editor_audio`
  - **Observed:** 69 tests passed, including export serialization and
    cancellation while waiting for analysis, close-time invalidation, source
    replacement, changed-fingerprint rejection, and live playback-position
    preservation.
- **Status:** implementation complete; focused regressions passed.

### Protected repository gates — 2026-08-28

- **Command:** `make check && make contract && make smoke`
  - **Observed:** `make check` passed 385 tests, compilation, and diff
    checks; `make contract` passed 35 tests; generated-media editor smoke
    flows passed.
- **Benchmark protocol:** Three synthetic 120-second H.264/AAC sources at
  320x180 and 10 FPS were generated outside the repository. Metadata probing
  and project creation, terminal full-file analysis, and the legacy
  probe-plus-analysis sequence were measured separately.
  - **Observed:** probe/project attachment proxy `0.095 s`; background audio
    analysis `10.468 s`; legacy blocking sequence `10.574 s`; time to usable
    project reduction `99.1%`. All three terminal decisions were `ready`.
  - **Limitation:** This is a local synthetic measurement and the
    attachment proxy does not include target-workstation first-frame decode
    latency. Total audio-analysis work remains unchanged.
- **Status:** protected functional and benchmark evidence passed.

### Final static analysis and review — 2026-08-28

- **Command:** `make quality PYTHON=.venv/bin/python`
  - **Observed:** 385 tests, compilation, diff checks, Ruff format check,
    Ruff lint, and all configured mypy targets passed.
  - **Blocked at:** existing C901 finding
    `benchmarks/restoration_benchmark.py:1794` (`run_benchmark`, complexity
    `16 > 15`). The file is outside this ticket's changed scope.
- **Command:** `make -k complexity duplication dependency-check
  dependency-audit security churn PYTHON=.venv/bin/python`
  - **Observed:** dependency boundaries passed with no findings; pip-audit
    reported no known vulnerabilities; Bandit reported zero findings.
    Churn completed with no changed-ticket file in its top hotspot output.
  - **Duplication:** jscpd reported `2.0674%` against the configured `2.0%`
    threshold, with `newClones: 0`; the reported clones are pre-existing and
    no changed ticket file was identified as a new clone.
  - **Status:** passed with existing-debt concerns; no introduced actionable
    static-analysis finding.
- **Review:** The second review findings for concurrent export analysis and
  close-time analyzer invalidation were fixed with focused regressions. The
  repository dependency graph remains acyclic and the changed surfaces have
  no new security findings.
- **Status:** technical review complete with the existing complexity and
  duplication warnings explicitly retained.

### User-validation handoff — 2026-08-28

- **Required environment:** target Linux workstation with GTK 4/PyGObject,
  FFmpeg, and representative local media.
- **Steps:** import one long source and then multiple sources; confirm the
  project and timeline attach after metadata probing; edit, save, and reopen
  while audio analysis is pending; observe per-source pending/analyzing and
  terminal or failed states; start export during analysis and cancel it;
  export after analysis completes; close the editor while analysis is active.
- **Expected:** the editor is usable before full-file audio analysis,
  status remains truthful per source, export waits or cancels explicitly
  without concurrent analysis, close prevents late callbacks, and playback
  remains stable after terminal audio refresh.
- **Current status:** blocked pending maintainer/user confirmation and remote
  checks. Agent-run live functionality evidence is recorded below; it does not
  replace the configured user-validation gate.

### Agent functionality validation - 2026-08-28

- **Purpose:** functionality and regression validation of the GTK import,
  persistence, playback, export, and close lifecycle on the target Linux
  workstation.
- **Environment:** Wayland desktop with GTK 4/PyGObject, FFmpeg, ffprobe,
  CUDA/TensorRT RVE integration, and `grim` screenshots. Generated fixtures
  were kept outside the repository.
- **Representative data:** one 90-second 320x180 10 FPS source and two
  30-second sources at 180x320 12 FPS and 640x360 15 FPS. The combined
  timeline displayed 2:30 and three source blocks.
- **One-source import:** the editor attached a usable preview and timeline
  for the long source, then reached a terminal `ready` audio decision. Evidence:
  `evidence/screenshots/ticket-083-live-one-source.png`.
- **Multi-source import and pending state:** all three clips attached while
  audio status showed `analyzing` per source, with the timeline interactive.
  Evidence: `evidence/screenshots/ticket-083-live-multi-pending.png`.
- **Save while pending:** the project was saved while two sources were still
  analyzing; the persisted project retained three `pending` audio decisions.
  Evidence: `evidence/screenshots/ticket-083-live-multi-save-pending-confirmed.png`.
- **Reopen and terminal state:** reopening the saved pending project reattached
  the timeline immediately, displayed per-source analysis, and later reached
  three terminal `ready` decisions with an explicit completion status.
  Evidence: `evidence/screenshots/ticket-083-live-reopen-pending.png` and
  `evidence/screenshots/ticket-083-live-multi-terminal.png`.
- **Playback:** play and pause worked after terminal analysis; the paused
  position remained visible at approximately 00:16. Evidence:
  `evidence/screenshots/ticket-083-live-playback-running-corrected.png` and
  `evidence/screenshots/ticket-083-live-playback-paused.png`.
- **Export cancellation:** the export plan was opened from a pending-project
  reopen, the export started with the validated RVE/TensorRT route, and the
  live cancel control produced `Export cancelled`. No final output or partial
  export directory remained. Evidence:
  `evidence/screenshots/ticket-083-live-export-started.png` and
  `evidence/screenshots/ticket-083-live-export-cancelled-accepted.png`.
  The dialog had reached terminal audio state by the capture point, so the
  pending-wait path remains covered by the focused regression suite rather
  than claimed from this screenshot.
- **Close during analysis:** closing immediately after a pending reopen
  terminated the editor and left no FFmpeg or RVE worker process. Evidence:
  `evidence/screenshots/ticket-083-live-close-during-analysis.png`.
- **Completed export after analysis:** the no-enhancement, lowest-FPS export
  completed in 19.87 seconds; the verified output was 150.0 seconds,
  1920x1080 H.264/AAC at 10 FPS, and all three source fixtures remained
  present. The output was kept outside the repository.
- **Observed concern:** one multi-source playback refresh displayed the
  explicit warning `Audio preview failed (ffplay status 1, ffmpeg status -9)`
  while the video preview, position, and play/pause controls continued to
  operate. This is recorded as a target-environment concern, not silently
  converted to a pass.
- **Additional environment concern:** a transient compositor
  `Application Not Responding` dialog appeared while opening export planning.
  The panel later became responsive and the export proceeded, but the event
  was not reproducibly isolated from the desktop environment, so it is not
  treated as a clean pass for GUI responsiveness.
- **Automation note:** one pointer-automation attempt produced a duplicated
  destination filename in an RVE temporary path after the click initially
  landed in the filename field. This is unconfirmed as a product defect and
  is excluded from acceptance evidence.
- **Agent flow status:** `passedWithConcerns`; automated and live evidence
  covers the implementation behavior, but the configured maintainer/user
  response is still required.
- **Required response:** return `PASS`, `FAIL`, `BLOCKED`, or approved
  `NOT APPLICABLE` for the user-validation handoff above. Remote checks also
  remain unavailable because this ticket branch is unpublished.

### Superseding final regression and static-analysis evidence - 2026-09-03

- **Focused command:** `.venv/bin/python -m unittest
  tests.test_editor_composition tests.test_editor_export_cache
  tests.test_editor_export_console tests.test_editor_export_execution
  tests.test_editor_persistence tests.test_editor_timeline
  tests.test_editor_cli_export`
  - **Observed:** 113 tests passed.
- **Full quality command:** `make quality PYTHON=.venv/bin/python`
  - **Observed:** 404 tests passed, compilation, diff checks, format, lint,
    and all configured mypy targets passed.
  - **Status:** blocked by the pre-existing
    `benchmarks/restoration_benchmark.py:1794` C901 finding
    (`run_benchmark`, complexity `16 > 15`).
- **Remaining analyzer collection:** `make -k complexity duplication
  dependency-check dependency-audit security churn
  PYTHON=.venv/bin/python`
  - **Observed:** duplication passed at `1.9899%` against the `2.0%`
    threshold with `newClones: 0`; dependency boundaries passed; pip-audit
    reported no known vulnerabilities; Bandit reported zero findings; churn
    completed.
  - **Artifacts:** `evidence/static-analysis/jscpd-report.json`,
    `evidence/static-analysis/dependencies.json`,
    `evidence/static-analysis/pip-audit.json`,
    `evidence/static-analysis/bandit.json`,
    `evidence/static-analysis/churn.json`
  - **Status:** passedWithConcerns because the repository-wide complexity
    gate remains blocked by existing debt outside this ticket.

## Updated readiness

Final regression and analyzer evidence is terminal for the changed behavior.
User validation and required remote checks remain open; the existing
repository-wide complexity finding is retained explicitly.

### User-validation closeout - 2026-09-07

- **User response:** `PASS` — the user confirmed the implemented ticket set
  is good.
- **Status:** passed; this supersedes the earlier pending user-validation
  state.
