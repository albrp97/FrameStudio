# TICKET-102 - Benchmark Efficient Export Pipeline Candidates

**Ticket ID:** TICKET-102
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-009
**Feature:** FEAT-030
**Capability links:** CAP-005, CAP-011, CAP-012
**Status:** verifying
**Horizon:** future
**Priority:** 1
**Owner:** repository implementation in the active worktree
**Approval:** user-authorized by the 2026-09-09 export-optimization request
**Last updated:** 2026-10-16
**Source paths:** `docs/planning/features/open/FEAT-030-benchmarking-and-selecting-efficient-export-pipelines.md`,
`benchmarks/render_strategy_benchmark.py`, `framestudio/export_smart_render.py`,
`framestudio/export_interpolation.py`, `framestudio/export_cache.py`,
`tests/test_editor_export_execution.py`, `.github/aidd-config.yml`,
`benchmarks/multitrack_render_benchmark.py`,
`benchmarks/multitrack_architecture_benchmark.py`,
`evidence/multitrack-render-results.json`
**Dependencies:** protected export baseline; FFmpeg/ffprobe; representative
media or reproducible fixtures; target-workstation resource probes
**Risks:** fixture bias, warm/cold cache differences, unavailable RVE rows,
and visual quality requiring human review
**Affected surfaces:** benchmark protocol, candidate runners, resource
collection, output verification, reports, and evidence
**Evidence path:** `evidence/efficient-export-pipeline-benchmark.md`
**Protected behaviors:** exact timeline order, hard boundaries, output
metadata, audio, source preservation, cleanup, and resumable identity
**Path history:** created at
`tickets/open/TICKET-102-benchmark-efficient-export-pipeline-candidates.md`

## Outcome

The repository contains comparable benchmark data for the current route and
the safe candidate export pipelines, including a bounded recommendation for
production implementation.

### Current measured selection

The four requested research tracks and isolated individual/combined prototypes
are complete. Three-trial production-policy comparisons select bounded video
decoder/filter concurrency, equal triplicate scale sharing, and repeated audio
input reuse. The representative generated large graph improves from 11.468 s
to 8.027 s (30.0% less time); the triplicate fixture improves from 2.525 s to
1.776 s (29.7% less time). AI-heavy/resume fixtures show only small additional
gains. Do not extrapolate these numbers to the paused full real project.

The original baseline exposed a one-frame-interval timestamp correctness
defect. Failed 45/56-frame rows remain recorded; measured comparisons use the
same correctness-only repaired baseline. Alternative lossless track/chunk
architectures and seek/NVDEC combinations were measured and retained as
experiments, not silently enabled as production routes.

Protocol, scopes, limitations, raw-report hashes and exact trial data are in
the ticket evidence and `evidence/multitrack-render-results.json`. The exact
configured Rubber Duck profile approved bounded integration. Final integrated
functionality/quality review and delivery gates remain TICKET-104's ownership;
this record remains open.

## Scope

- Define representative source metadata, retained/deleted ranges, transforms,
  triplicate composition, audio policy, target FPS, upscale policy, output
  profile, and verification checks.
- Compare current per-segment processing with grouped/source-run and
  enhancement-order candidates where runnable.
- Measure wall time, stage time, FFmpeg/interpolation/restoration invocation
  counts, CPU, memory, GPU observations, storage, metadata, playability,
  boundary behavior, source hashes, cleanup, and resume reuse.
- Publish machine-readable and Markdown reports with failed/unavailable rows
  and evidence limits.

## Explicit non-goals

- Changing production routing in this ticket.
- Claiming universal performance.
- Adding dependencies or committing generated media without an explicit
  artifact decision.

## 2026-10-16 renewed multitrack comparison

The user explicitly authorizes four initial parallel research tracks: two
GPT-6.1 Sol workers for repository architecture and experiment design, and two
Haiku 5.5 high-reasoning workers for community/papers and professional-editor
prior art. This task-level worker selection does not change the configured
automatic-validation profile.

Compare the current dirty-worktree implementation, not an older committed
renderer, with viable individual candidates and compatible combinations.
Keep generated inputs and outputs isolated from the user's paused full export.
Record source revision and the existing uncommitted baseline. Preserve the
PHASE-010 / CHG-013 contract in `docs/specs/multi-track-editing-contract.md`.

Workloads cover synchronized track composition, repeated/unique ranges,
changing layouts and intentional gaps; standalone track/source reels remain
full-canvas with normal source audio. Fix equivalent source ranges, frame
rate, dimensions, codec/quality settings, audio decisions, and enhancement
policy across compared rows. Separate fresh application-cache runs, warm
checkpoint reuse, and interrupted/resumed runs. Do not call an OS page-cache
warm run a disk-cold benchmark. Measure repeated wall-clock results and relevant
process, resource and disk costs; report unavailable measurements explicitly.

Before selection, compare exact decoded frames where equivalence is promised,
metadata/frame count/duration, hard boundaries, audio behavior, source hashes,
failure cleanup, and resume reuse. A faster row with altered quality or output
semantics is not an eligible winner. Publish citations, measured speedups,
rejected combinations, and hardware/workload limits in the existing evidence
report. This refinement does not introduce a new phase or editing capability.

## Observable acceptance criteria

- Given one protocol, all runnable strategies receive equivalent inputs and
  output gates.
- Given each run, the report includes the required metrics and status.
- Given a deleted boundary, the report records whether interpolation and
  composition are boundary-safe.
- Given the results, the recommendation identifies the fastest acceptable
  candidate and why alternatives are rejected or deferred.

## Validation

- Run `python3 -m unittest discover -s tests`.
- Run the benchmark harness on the target workstation and representative
  media, using repeated cold/warm runs where practical.
- Probe outputs with FFmpeg/ffprobe and compare source hashes before/after.
- Record unavailable runtime, hardware, or visual checks explicitly.

## User-validation plan

- **Setup:** open the Markdown/JSON report, candidate outputs, metadata
  probes, and boundary/visual-review artifacts.
- **Steps:** compare equivalent timestamps, hard cuts, motion, faces/text,
  focus/triplicate composition, audio, and timing/size/resource tables.
- **Expected result:** the recommendation is reproducible and does not hide
  failed, unsafe, or unavailable rows.
- **Failure paths:** missing metrics, invalid outputs, source changes, or
  cleanup failures block acceptance.
- **Cleanup:** retain reports/evidence and remove generated media after review.
- **Evidence response:** return `PASS`, `FAIL`, `BLOCKED`, or approved
  `NOT APPLICABLE` with report paths.
