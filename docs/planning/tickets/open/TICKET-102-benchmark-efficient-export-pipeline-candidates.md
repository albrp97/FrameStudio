# TICKET-102 - Benchmark Efficient Export Pipeline Candidates

**Ticket ID:** TICKET-102
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-009
**Feature:** FEAT-030
**Capability links:** CAP-005, CAP-011, CAP-012
**Status:** active
**Horizon:** future
**Priority:** 1
**Owner:** repository implementation in the active worktree
**Approval:** user-authorized by the 2026-09-09 export-optimization request
**Last updated:** 2026-09-09
**Source paths:** `docs/planning/features/open/FEAT-030-benchmarking-and-selecting-efficient-export-pipelines.md`,
`benchmarks/render_strategy_benchmark.py`, `framestudio/export_smart_render.py`,
`framestudio/export_interpolation.py`, `framestudio/export_cache.py`,
`tests/test_editor_export_execution.py`, `.github/aidd-config.yml`
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

