# FEAT-030 - Benchmarking and Selecting Efficient Export Pipelines

**Feature ID:** FEAT-030
**Parent links:** OBJ-001, SCOPE-001, PHASE-009
**Capability links:** CAP-005, CAP-011, CAP-012
**Status:** active
**Horizon:** future
**Priority:** 1
**Owner:** repository implementation in the active worktree
**Approval:** user-authorized by the 2026-09-09 request to run reasoned,
metric-based export experiments
**Last updated:** 2026-09-09
**Source paths:** `docs/planning/phases/open/PHASE-009-selecting-and-delivering-efficient-export-pipelines.md`,
`docs/planning/features/closed/FEAT-026-comparing-mixed-fps-render-strategies.md`,
`docs/planning/features/closed/FEAT-028-adding-optional-upscale-enhancement.md`,
`benchmarks/render_strategy_benchmark.py`, `framestudio/export_planning.py`,
`framestudio/export_smart_render.py`, `framestudio/export_interpolation.py`,
`.github/aidd-config.yml`
**Dependencies:** PHASE-008 export baseline; FFmpeg/ffprobe; representative
mixed-source media; target-workstation resource probes; RVE runtime where
available
**Risks:** incomparable fixtures, cold/warm cache effects, model startup,
resource-sampling gaps, and subjective quality observations
**Affected surfaces:** benchmark fixtures, strategy runners, resource
collection, output verification, reports, and evidence
**Evidence path:** `evidence/efficient-export-pipeline-benchmark.md`
**Protected behaviors:** exact timeline order, hard cut boundaries, fixed
delivery profile, source-level audio policy, source preservation, atomic
publication, cleanup, and resumable intermediates
**Feature links:** TICKET-102
**Path history:** created at
`features/open/FEAT-030-benchmarking-and-selecting-efficient-export-pipelines.md`

## Outcome

FrameStudio has a reproducible, metric-backed comparison of export
strategies, including the current baseline and boundary-safe batching
candidates, with a recommendation bounded to the measured workstation and
media set.

## Scope

- Specify representative mixed-source edits and equivalent output policies.
- Run current per-segment, grouped, source/run, and enhancement-order
  candidates when their prerequisites are available.
- Capture timing, process counts, CPU/RAM/GPU, storage, metadata, playability,
  frame boundaries, source hashes, cleanup, and resume behavior.
- Separate machine integrity gates from human visual observations.
- Publish a recommendation and confidence limits without changing production
  routing until the implementation ticket is verified.

## Explicit non-goals

- Universal performance claims.
- Adding model families, dependencies, or unapproved codecs.
- Treating a failed or unavailable strategy as a passing comparison row.
- Replacing the existing production route in this feature.

## Observable acceptance criteria

- Given the same fixture and policy, every runnable candidate receives the
  same retained ranges, transforms, audio decisions, target FPS, upscale
  policy, output profile, and verification checks.
- Given each candidate, the report includes total and stage timings,
  invocation counts, resource observations, intermediate/final storage,
  output metadata, playability, source preservation, cleanup, and status.
- Given deleted boundaries, the report includes explicit boundary checks and
  does not hide unsafe cross-cut interpolation.
- Given unavailable runtime or hardware, the report records a blocked or
  skipped-with-reason row.
- Given the completed comparison, the recommendation names the fastest
  acceptable route and its evidence limits.

## User-validation plan

- **Setup:** open the benchmark report, candidate outputs, metadata probes,
  source-hash record, and any visual-review frames.
- **Steps:** compare matching timestamps around cuts, motion, text, faces,
  focus offsets, triplicate edges, audio transitions, and output metadata.
- **Expected result:** the report identifies a measured winner without
  changing source files or hiding failed/unavailable candidates.
- **Failure paths:** invalid frame count, duration, playability, source hash,
  cleanup, or boundary behavior blocks a pass.
- **Cleanup:** remove generated media after evidence is retained.
- **Evidence response:** return `PASS`, `FAIL`, `BLOCKED`, or approved
  `NOT APPLICABLE` with report and artifact paths.
- **Pass criteria:** all intended rows are runnable or explicitly accounted
  for, and the recommendation is evidence-bounded.

