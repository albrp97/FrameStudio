# Evidence - PHASE-009 Efficient Export Pipeline

**Tickets:** TICKET-102, TICKET-103, TICKET-104  
**Status:** verifying  
**Last updated:** 2026-09-09

## Outcome

FrameStudio now has a measured adaptive preparation route for enhanced
exports. Compatible retained segments from one source can be normalized in a
single FFmpeg process while remaining separate output artifacts, so
interpolation never receives a stream that crosses a deleted boundary. The
existing per-segment route remains selectable with
`pipeline_strategy="per-segment"` and remains the fallback for ineligible
upscale/restoration work.

## Implementation evidence

- `framestudio/export_strategy.py` derives compatible active source runs from
  source identity, source/target rate, rate action, and upscale profile.
- `framestudio/export_smart_render.py` builds independent filter branches and
  output maps for grouped preparation, then reuses the existing per-segment
  interpolation, cache, verification, and publication contracts.
- Grouped preparation accepts only supported rate actions. Unsupported or
  unknown actions stay on the existing explicit error path instead of being
  allowed to bypass validation.
- The normalization filter graph is shared by the concatenating and grouped
  builders. Video-only multi-segment normalization is covered explicitly.
- `framestudio/export_interpolation.py` validates and persists the internal
  `adaptive` or `per-segment` strategy without passing it to interpolation or
  restoration backends.
- `benchmarks/efficient_export_pipeline_benchmark.py` compares both routes
  with equivalent generated mixed-source inputs, repeated measurements, source
  hashes, output metadata, process counts, stage timing, boundary samples,
  intermediate storage, and resource observations.
- `tests/test_editor_export_execution.py` exercises adaptive generated-media
  export and cancellation/reopen/resume. The resume functionality test proves
  grouped source preparation is not run again after its artifacts are cached.

## Benchmark evidence

The machine-readable and Markdown reports are:

- `evidence/efficient-export-pipeline-benchmark.json`
- `evidence/efficient-export-pipeline-benchmark.md`

The three interleaved repetitions on the generated mixed-source fixture
selected `adaptive`:

| Metric | Per-segment baseline | Adaptive |
|---|---:|---:|
| Median wall time | 68.2237 s | 67.8984 s |
| Wall-time change | — | -0.3253 s (-0.48%) |
| FFmpeg processes | 11 | 8 |
| Normalization processes | 3 | 2 |
| Production interpolation calls | 2 | 2 |
| Boundary-safe | yes | yes |
| Source preserved | yes | yes |

Both outputs were 1920x1080 H.264 `yuv420p`, 60 FPS, 240 frames, approximately
4.021 seconds, with AAC stereo audio at 48 kHz. The deleted green range was
absent at the sampled red/blue boundary.

This result is fixture- and workstation-specific. The operating-system file
cache was not flushed between repetitions, GPU values are point-in-time
observations, and the interpolation-process metric includes FFmpeg
artifact-preflight work. A comparable RVE grouped benchmark was not run
because the current adaptive route intentionally keeps restoration per
segment.

## Verification

- The unsupported-rate regression test failed before the fix because grouped
  preparation bypassed the expected error, then passed after the guard was
  added.
- `python3 -m unittest discover -s tests` — 470 tests passed after the fix.
- `python3 -m unittest
  tests.test_editor_export_execution.EditorExportExecutionTests.test_cancelled_enhanced_export_reuses_completed_interpolation_after_resume`
  — passed; grouped preparation ran once across cancellation and resume.
- Focused export regression tests — 42 passed.
- Repository compilation — passed.
- Repository formatting and Ruff lint — passed.
- Repository complexity check — passed.
- Repository duplication check — passed with the reviewed baseline.
- Mypy — passed for all configured source, benchmark, and tool targets.
- Dependency boundary check — passed.
- `pip-audit` — no known vulnerabilities found.
- Bandit security analysis — passed.
- Churn analysis — passed.
- CLI contract tests — 39 passed.
- Generated-media smoke flow — passed.
- `git diff --check` — passed.

## User validation

Technical evidence is complete. The earlier user validation PASS was
superseded by the scoped unsupported-rate guard, so the real-project check
must be repeated before closing the active tickets.

1. Use a project with two retained segments from one source separated by a
   deleted range, plus a second source with a different frame rate or
   dimensions.
2. Export once with the normal export controls and confirm the output plays,
   has the expected duration and 1920x1080/target-FPS metadata, preserves
   audio, and contains no deleted-range content.
3. Cancel or close the export after preparation or interpolation has produced
   checkpoints.
4. Reopen the same project and destination, choose **Resume**, and confirm
   that completed preparation/interpolation work is reused rather than
   repeated.
5. Inspect the final output around the deleted boundary and confirm source
   files are unchanged.

Expected response: `PASS`, `FAIL`, `BLOCKED`, or approved `NOT APPLICABLE`,
with any observed output path or limitation.

## Superseding review and validation evidence

- Review finding: grouped preparation could bypass the explicit unsupported
  rate-decision error when a run contained multiple segments.
- Baseline reproduction: the new regression test failed because no
  `ExportExecutionError` was raised.
- Fix: grouped preparation now accepts only `interpolate`, `passthrough`,
  `convert`, and `convert-down` actions. Unsupported or unknown actions use
  the existing per-segment validation path.
- Focused verification: 42 export regression tests passed, including the
  unsupported-rate regression and grouped cancellation/resume functionality.
- Complete verification after the fix: `make quality PYTHON=.venv/bin/python
  NPX=npx` passed with 470 tests, compilation, formatting, lint, mypy,
  complexity, duplication baseline, dependency checks, `pip-audit`, Bandit,
  churn, and `git diff --check`.
- Post-fix CLI contract tests — 39 passed.
- Post-fix generated-media smoke flow — passed.
- User validation: the maintainer repeated the real-project mixed-source
  export, deleted-boundary, source-preservation, and cancel/reopen/resume
  checks after the fix and returned `PASS`.
- The earlier PASS was superseded by the fix and is not used as current
  evidence.

## Review readiness

Technical evidence, local quality gates, review remediation, and user
validation are terminal. The active tickets remain in `open/` with
`verifying` evidence until the configured delivery operation is performed.
No commit, remote check, push, or pull request has been started for this
worktree, so those delivery gates remain outstanding.
