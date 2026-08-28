# TICKET-063 - Experiment with Preview Rendering Strategies

**Ticket ID:** TICKET-063
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-008
**Feature:** FEAT-024
**Capability links:** CAP-002, CAP-005, CAP-012
**Status:** complete
**Closure:** closed on 2026-08-26 after candidate preview strategies were
measured against the shared traces and the bounded cache/coalescing strategy
was selected for adoption.
**Horizon:** future
**Priority:** 2
**Owner:** repository planning; maintainer identity is not recorded
**Approval:** user-authorized on 2026-08-26 for PHASE-008 planning; execution
requires the configured preimplementation and approval gates
**Last updated:** 2026-08-26
**Source paths:** `docs/planning/features/closed/FEAT-024-optimizing-cursor-driven-preview.md`,
`docs/planning/tickets/closed/TICKET-061-research-lossless-cut-preview-architecture.md`,
`docs/planning/tickets/closed/TICKET-062-benchmark-current-preview-latency.md`,
`framestudio/app_playback.py`, `framestudio/ffmpeg_playback.py`,
`framestudio/timeline.py`, `framestudio/timeline_rendering.py`,
`benchmarks/`, `tests/test_editor_playback.py`, `.github/aidd-config.yml`
**Dependencies:** TICKET-061 and TICKET-062; approved experiment boundary;
representative media and target-workstation benchmark access
**Risks:** asynchronous seeks, cache eviction, decoder contention, and
reduced-resolution previews can improve latency while harming freshness or
visual fidelity
**Affected surfaces:** playback scheduling, frame cache or prefetch
experiments, timeline event handling, benchmark harness, and regression tests
**Evidence path:** `evidence/phase-008-preview-responsiveness.md`
**Path history:** `tickets/open/TICKET-063-experiment-with-preview-rendering-strategies.md`
-> `tickets/closed/TICKET-063-experiment-with-preview-rendering-strategies.md`
**Protected behaviors:** experiments must be isolated, reversible, and must
not change export, project persistence, source safety, or legacy scripts

## Outcome

Candidate preview strategies are measured against the current baseline under
the same interactions and media, with enough evidence to select a default.

## Scope

- Turn the Lossless Cut research and baseline into explicit candidate
  hypotheses, such as seek coalescing, bounded frame caching, decode-window
  prefetch, or another evidence-supported approach.
- Implement experiments behind a reversible boundary or harness mode.
- Measure latency, frame freshness, stale-frame behavior, resource cost, and
  failure recovery using TICKET-062's procedure.
- Record results even when a candidate is slower or less reliable.

## Explicit non-goals

- Selecting a winner without comparable measurements.
- Copying external source code or adding a permanent dependency.
- Optimizing export or final-render paths.

## Observable requirements

- Given each candidate and the same trace, the evidence should report the
  same metrics as the baseline.
- Given rapid pointer movement, the candidate should expose whether requests
  are coalesced and which frame is displayed.
- Given a failed or cancelled seek, the candidate should preserve a usable
  editor state and record the recovery behavior.

## Definition of done

- At least the viable candidates from the research are measured or explicitly
  rejected with reasons.
- Results include latency, freshness, resource, and failure observations.
- The experiment boundary can be removed or promoted without hidden state.
- TICKET-064 has enough evidence to choose a default.

## User-validation plan

- **Setup:** use the baseline media, trace, and environment from TICKET-062.
- **Steps:** run each candidate, compare the same metrics, and inspect rapid
  movement, clicks, seeks, and scroll behavior.
- **Expected result:** candidate results are directly comparable and stale
  frames are not silently presented as current.
- **Failure paths:** record candidates that fail to start, seek, decode, or
  recover instead of excluding them without explanation.
- **Cleanup:** disable experimental modes and remove temporary artifacts.
- **Evidence response:** return the comparison table and rejected-candidate
  reasons.
- **Pass criteria:** one or more candidates, including the current path if
  appropriate, have reviewable evidence for TICKET-064.

## Closure

TICKET-063 was closed after the baseline and candidate traces reported
comparable latency, freshness, coalescing, stale-frame, and failure behavior.
The evidence supports bounded caching and latest-request delivery without
claiming universal codec or hardware performance.
