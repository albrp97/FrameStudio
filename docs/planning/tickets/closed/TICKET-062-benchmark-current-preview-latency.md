# TICKET-062 - Benchmark Current Preview Latency

**Ticket ID:** TICKET-062
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-008
**Feature:** FEAT-024
**Capability links:** CAP-002, CAP-005, CAP-012
**Status:** complete
**Closure:** closed on 2026-08-26 after reproducible one-source and mixed-source
baseline measurements were recorded; backend timing and unavailable GTK paint
timing remain separate evidence boundaries.
**Horizon:** future
**Priority:** 1
**Owner:** repository planning; maintainer identity is not recorded
**Approval:** user-authorized on 2026-08-26 for PHASE-008 planning; execution
requires the configured preimplementation and approval gates
**Last updated:** 2026-08-26
**Source paths:** `docs/planning/features/closed/FEAT-024-optimizing-cursor-driven-preview.md`,
`docs/planning/tickets/closed/TICKET-061-research-lossless-cut-preview-architecture.md`,
`framestudio/app_playback.py`, `framestudio/ffmpeg_playback.py`,
`framestudio/timeline.py`, `benchmarks/`, `tests/test_editor_playback.py`,
`tests/test_editor_timeline.py`, `.github/aidd-config.yml`
**Dependencies:** TICKET-061 research notes; representative local media;
repeatable pointer-event or harness input; target workstation
**Risks:** cold versus warm cache, codec/keyframe layout, display timing, and
manual event generation can make measurements noisy or incomparable
**Affected surfaces:** benchmark harness, preview instrumentation, playback
tests, evidence, and baseline documentation
**Evidence path:** `evidence/phase-008-preview-responsiveness.md`
**Path history:** `tickets/open/TICKET-062-benchmark-current-preview-latency.md`
-> `tickets/closed/TICKET-062-benchmark-current-preview-latency.md`
**Protected behaviors:** benchmark instrumentation must not change normal
playback, timeline navigation, export, or source-media handling

## Outcome

The project has a reproducible current-preview baseline for cursor movement,
timeline clicks, seeks, and scrolling, including latency and frame-freshness
measurements.

## Scope

- Define representative one-source and mixed-source media cases.
- Replay the same interaction traces against the current preview.
- Measure request-to-visible-frame latency, stale-frame frequency, dropped or
  coalesced requests, and relevant CPU/GPU or decoder observations.
- Report warm/cold-cache conditions and measurement variability.

## Explicit non-goals

- Changing preview behavior or adding a production cache.
- Treating one media file or one run as a universal result.
- Measuring export performance in this ticket.

## Observable requirements

- Given a fixed media and interaction trace, repeated runs should produce
  comparable baseline metrics and clearly state variability.
- Given a requested position, the report should distinguish the requested
  position from the frame actually displayed.
- Given a failed seek or unavailable playback tool, the benchmark should
  report the failure rather than omit the sample.

## Definition of done

- The benchmark inputs, environment, metrics, and run procedure are recorded.
- Current baseline results include pointer movement, click, seek, and scroll
  workflows.
- Results are suitable for comparison with TICKET-063 candidates.
- No production behavior is changed.

## User-validation plan

- **Setup:** use the target workstation, representative media, and the
  documented benchmark command or harness.
- **Steps:** run the same trace for the documented repetitions and inspect
  latency, stale-frame, and failure columns.
- **Expected result:** the baseline is repeatable enough to compare strategies.
- **Failure paths:** missing media, display/runtime limitations, or noisy
  samples are recorded with their effect on confidence.
- **Cleanup:** remove temporary traces and generated preview artifacts.
- **Evidence response:** return the baseline table and environment conditions.
- **Pass criteria:** TICKET-063 can use the baseline without changing its
  measurement method.

## Closure

TICKET-062 was closed after the documented media, traces, latency fields,
frame-freshness fields, failure probe, and cache conditions were captured in
the preview evidence. The lack of compositor-paint timing is retained as a
limitation rather than treated as a pass.
