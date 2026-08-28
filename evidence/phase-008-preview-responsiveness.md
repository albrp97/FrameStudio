# PHASE-008 / FEAT-024 Preview Responsiveness Evidence

Tickets: TICKET-061, TICKET-062, TICKET-063, TICKET-064  
Branch: `ticket/phase-008-responsive-preview-media-strategy`  
Evidence record: append-only during this workstream

## Scope and protected flows

Research, benchmark, and narrowly scoped preview scheduling/cache work only.
Protected play/pause, seek, timeline selection/split positioning, mixed-source
preview, source preservation, export, persistence, and legacy scripts.

## Entries

### TICKET-061 — Lossless Cut architecture research

- **Command/steps:** shallow clone of `https://github.com/mifi/lossless-cut.git`
  outside the repository; inspect revision, `package.json`, `LICENSE`,
  `useVideo.ts`, `useThumbnails.ts`, `MediaSourcePlayer.tsx`, and
  `useTimelineScroll.ts`.
- **Expected:** revision-pinned, license-aware, source-linked notes without
  vendoring.
- **Observed:** revision
  `e1f4348637575bb21fe9bc2ba70e0f9a70cbafaf`; `package.json` declares
  `GPL-2.0-only`; `LICENSE` is GPL version 2. Preview uses latest-target
  smooth seeking, debounced/abortable thumbnail generation, bounded
  MediaSource buffering, and periodic stream resynchronization.
- **Status:** passedWithConcerns
- **Artifacts:** `docs/specs/preview-responsiveness-strategy.md`
- **Accepted warning:** external patterns are Chromium/MediaSource-specific
  and are hypotheses, not copied implementation.
- **Cleanup:** disposable checkout removed after capture.

### TICKET-062/TICKET-063 — Reproducible baseline and candidate benchmark

- **Command:** generate two 1-second, 320x180, 10 FPS H.264 fixtures with
  FFmpeg, then run:
  `PYTHONPATH=. python3 -m benchmarks.preview_responsiveness --source ... --duration 1
  --frame-rate 10 --repetitions 2 --output ...`
- **Expected:** comparable cold/repeated baseline and bounded-cache candidate
  results across cursor, click, seek, scroll, and rapid pointer traces.
- **Observed:** one-source and mixed-source JSON outputs contain per-request
  latency, requested/displayed positions, timeout failures, cache
  hit/miss/eviction counts, stale frames, cancellation/coalescing counts, and
  decoder failure probe results. Cold misses were roughly 29/32 ms; warm
  candidate hits were roughly 0.01 ms median. First misses were not improved.
- **Status:** passedWithConcerns
- **Artifacts:**
  `evidence/phase-008-preview-benchmark-one-source.json`,
  `evidence/phase-008-preview-benchmark-mixed-source.json`,
  `benchmarks/preview_responsiveness.py`
- **Coverage gap:** no GTK display was available; benchmark measures backend
  request-to-callback latency, not compositor paint latency.

### TICKET-064 — Adoption and regressions

- **Implementation:** add `PreviewFrameCache`, expose backend preview metrics,
  cache completed frames, preserve generation-based stale-frame rejection, and
  retain the existing playback contract.
- **Focused tests:** `python3 -m unittest
  tests.test_editor_preview_strategy tests.test_editor_ffmpeg_playback
  tests.test_editor_playback tests.test_editor_timeline`
- **Expected:** ordinary playback/seek remains functional; repeated requests
  use the bounded cache; obsolete decoded frames are not displayed.
- **Observed:** 30 tests passed, including ordinary play/pause/seek, seek
  recovery, latest-request delivery, cache hit/eviction, and stale-frame
  accounting.
- **Status:** passedWithConcerns
- **Artifacts:** `resolve_editor/preview_strategy.py`,
  `resolve_editor/ffmpeg_playback.py`, `tests/test_editor_preview_strategy.py`,
  `tests/test_editor_ffmpeg_playback.py`,
  `docs/specs/preview-responsiveness-strategy.md`
- **Limit:** target-workstation GTK interaction and paint timing remain
  unavailable and require user validation.

## Additional verification

- `python3 -m py_compile resolve_editor/preview_strategy.py
  resolve_editor/ffmpeg_playback.py benchmarks/preview_responsiveness.py
  tests/test_editor_preview_strategy.py` — passed.
- Existing playback/timeline baseline before edits — 27 tests passed.
- `python3 -m unittest discover -s tests` after edits — 273 tests passed.
- Configured Ruff checks were attempted for the owned files but are blocked by
  the environment (`No module named ruff`); no formatter/linter claim is made.
- Configured static analysis and GTK/display smoke were not run in this
  workstream because the shared worktree contains unrelated user changes and
  no display validation was available.

## Readiness

The measured candidate is adopted because it materially reduces repeated
nearby preview requests while preserving the existing stale-frame and failure
behavior. The related tickets were later closed after the linked regressions
and user-validation handoff were accepted. No universal latency claim is made.

## Remediation addendum — 2026-08-26

The contextual review findings were addressed with regression-first changes:

- Playback callbacks now carry their playback generation through GTK's queued
  frame delivery. A queued frame from a replaced backend is discarded before
  texture creation.
- Preview process registration and cancellation are serialized under the
  preview condition. Obsolete requests are rejected before process creation,
  and a process cannot become visible after cancellation has inspected the
  registration slot.
- Cached frames retain their decoded timestamp while cache hits are presented
  at the requested cursor position through
  `VideoFrame.decoded_position_seconds`.

Focused regression tests cover all three cases:

```sh
python3 -m unittest tests.test_editor_composition \
  tests.test_editor_ffmpeg_playback tests.test_render_strategy_benchmark \
  tests.test_editor_preview_strategy
```

The focused suite passed 47 tests. The regenerated one-source and mixed-source
preview benchmark artifacts record the requested, displayed, and decoded
positions, including warm-cache behavior. The complete repository suite passed
280 tests, `make contract` passed 30 CLI contract tests, `make quality
PYTHON=.venv/bin/python` passed, and `make smoke` passed.

GTK interaction and visual paint latency still require the configured
target-workstation user-validation handoff; automated backend timing does not
replace that check.

## Remediation addendum — 2026-08-26 (final verification)

The preview benchmark now derives a terminal status from every trace
condition, failed sample count, rapid-pointer delivery, and the intentional
decoder-failure probe. It returns a nonzero exit status when any required
condition fails. A regression test covers failed trace samples, and the
render benchmark now rejects non-positive target FPS values both through its
CLI and callable API.

The regenerated one-source and mixed-source benchmark artifacts both report:

```text
status: passed
failed_samples: 0 for every condition
failure_probe.reported: true
```

The final repository verification passed 290 tests, the 30-test CLI contract
suite, generated-media smoke, compilation, formatting, lint, mypy, complexity,
duplication, dependency, audit, security, and churn checks. The target
workstation GTK interaction and visual paint checks remain a user-validation
requirement; no display-based claim is made here.

## Remediation addendum - 2026-08-26 (cancellation and publication safety)

The final contextual review identified three export-safety risks in the
protected delivery path: FFmpeg cancellation could wait indefinitely while no
progress output was available, VapourSynth teardown used unbounded waits after
termination, and final cancellation could race with atomic publication.

Failing regressions were added first for each boundary. The implementation now
uses a cancellation watcher for silent FFmpeg progress pipes, bounded
terminate-then-kill escalation for FFmpeg and VapourSynth processes, bounded
post-termination waits for RVE/VapourSynth paths, and one GUI-to-publication
cancellation lock covering the final source check and `os.replace`.

The focused remediation command passed four tests:

```sh
python3 -m unittest \
  tests.test_editor_export_execution.EditorExportExecutionTests.test_ffmpeg_cancellation_uses_bounded_process_termination \
  tests.test_editor_export_execution.EditorExportExecutionTests.test_publication_lock_rejects_cancellation_before_replacing_destination \
  tests.test_editor_performance.EditorPerformanceModeTests.test_cancel_export_waits_for_publication_lock \
  tests.test_fps.FpsTests.test_vapoursynth_cancellation_uses_bounded_process_termination
```

The final repository quality command passed 304 tests, compilation,
formatting, lint, mypy, complexity, duplication, dependency checks,
dependency audit, security, and churn. The CLI contract suite passed 31 tests,
the generated-media smoke flow passed, and regenerated one-source,
mixed-source, and render-strategy benchmark artifacts reported terminal
`passed` statuses.

**Status:** passedWithConcerns

**Artifacts:** `resolve_editor/export_process.py`,
`resolve_editor/export_delivery.py`, `resolve_editor/export_interpolation.py`,
`resolve_editor/app_export.py`, `resolve_fps.py`,
`tests/test_editor_export_execution.py`, `tests/test_editor_performance.py`,
`tests/test_fps.py`, `evidence/phase-008-preview-benchmark-one-source.json`,
`evidence/phase-008-preview-benchmark-mixed-source.json`,
`evidence/phase-008-render-strategy-comparison.json`

**Remaining gaps:** no repository remote or upstream is configured, and
target-workstation GTK interaction, physical focus gestures, visual preview
freshness, and real RVE/model-quality validation still require user or
environment-specific evidence.

## User-validation addendum - 2026-08-26

The requested target-workstation validation covered timeline scrubbing,
clicking, scrolling, direct focus controls, save/reopen persistence, export
cancellation, normal export, and source preservation.

**User response:** `PASS`

**Status:** passed

No separate evidence paths were supplied with the response. The response is
terminal for the required user-validation gate; the remote/upstream and
real-RVE/model-quality limitations remain explicit.
