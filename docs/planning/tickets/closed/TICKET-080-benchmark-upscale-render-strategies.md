# TICKET-080 - Benchmark Upscale Render Strategies

**Ticket ID:** TICKET-080
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-008
**Feature:** FEAT-028
**Capability links:** CAP-005, CAP-011, CAP-012
**Status:** complete
**Horizon:** future
**Priority:** 2
**Owner:** repository implementation in the active worktree
**Approval:** User-authorized by the request to generate the fixtures, render
the requested edit, compare pipeline orderings, and record a recommendation;
execution depends on TICKET-079's implementation and baseline.
**Last updated:** 2026-08-28
**Source paths:** `docs/planning/reviews/CHG-008-add-production-upscale-enhancement.md`,
`docs/planning/features/open/FEAT-028-adding-optional-upscale-enhancement.md`,
`docs/planning/tickets/open/TICKET-079-implement-optional-upscale-enhancement.md`,
`docs/planning/tickets/open/TICKET-076-adopt-per-source-render-strategy.md`,
`benchmarks/render_strategy_benchmark.py`, `FPS-ENHANCEMENT-RESEARCH.md`,
`.github/aidd-config.yml`
**Dependencies:** TICKET-079; FFmpeg/ffprobe; local RVE runtime and weights;
target-workstation storage and GPU; existing benchmark harnesses
**Risks:** fixture generation bias, model warm-up, encoder settings,
temporary storage, hardware-specific timing, subjective quality, and
incomparable failed or unavailable strategies
**Affected surfaces:** benchmark fixtures, render-order harness, GUI/CLI
export commands, output metadata, audio, source-preservation evidence,
machine-readable and Markdown reports, and visual review artifacts
**Evidence path:** `evidence/ticket-080-upscale-render-strategy-benchmark.md`
**Protected behaviors:** source preservation, atomic output, exact timeline
order, fixed output profile, audio policy, FPS integrity, cleanup, and
existing restoration benchmark evidence
**Path history:** created at
`tickets/open/TICKET-080-benchmark-upscale-render-strategies.md` -> moved to
`tickets/closed/TICKET-080-benchmark-upscale-render-strategies.md`

**Execution state:** Technical benchmark execution, report generation, local
quality checks, and source/output integrity gates are complete. Human visual
validation of the retained outputs and review artifacts is pending.

## Outcome

The requested mixed-orientation edit has reproducible measurements for the
relevant render-order strategies, allowing a bounded recommendation based on
speed, quality observations, output size, integrity, and resource evidence.

## Scope

- Generate three 40-second fixtures: 1080p/24 landscape, 480p/30 landscape,
  and 720p/30 portrait.
- Concatenate them, triplicate the portrait source, cut 10 seconds from each,
  and render the resulting 30-second edit.
- Compare applicable orderings of smart render/cut, audio preparation, RVE
  restoration, spatial upscaling, FPS enhancement, concatenation, and final
  encoding.
- Record stage timing, end-to-end timing, output size/bitrate, dimensions,
  frame rate/count, duration, audio, playability, GPU/CPU observations,
  temporary storage, source hashes, and cleanup.
- Record separate visual observations for faces/text, edges, noise, ringing,
  color, cropping, temporal stability, and triplicate behavior.
- Publish redacted JSON and Markdown reports with a recommendation and
  confidence limits in the repository.

## Explicit non-goals

- Universal performance claims or ranking unavailable/non-comparable models.
- Changing production defaults solely from one benchmark run.
- Reusing private source paths or committing generated media without an
  explicit artifact decision.
- Adding a new benchmark dependency or model family.

## Observable acceptance criteria

- Given the requested fixture description, the generated media has the
  declared dimensions, rates, durations, orientation, and source hashes.
- Given the 30-second edit, every attempted strategy receives equivalent
  source ranges, output policy, audio policy, and verification checks.
- Given a runnable strategy, the report separates setup, model/inference,
  scaling, FPS, concatenation, audio, final encode, and total time.
- Given a failed or unavailable strategy, the report retains an explicit row,
  reason, cleanup result, and source-preservation result.
- Given successful outputs, the reports include metadata, playability,
  frame-count, size, and visual-review artifacts.
- Given all results, the recommendation states evidence limits and does not
  silently change production routing.

## Validation

- Run the existing benchmark/unit tests and the requested target-workstation
  real-media executions.
- Probe every output with FFmpeg/ffprobe and verify source hashes before and
  after each run.
- Review contact sheets or fixed timestamp frames separately from measured
  metadata.
- Record unavailable GPU/runtime or visual checks as blocked or
  skipped-with-reason.

## User-validation plan

- **Setup:** open the fixture directory, final edit, strategy outputs,
  contact sheets, JSON report, Markdown report, and evidence record.
- **Steps:** compare the same timestamps across strategies, inspect portrait
  triplicate composition, faces/text, edges, motion, color, cropping, and
  audio; then review the timing and size tables.
- **Expected result:** the recommendation identifies the fastest acceptable
  pipeline and explains quality/size tradeoffs without hiding failed rows.
- **Failure paths:** missing runtime, failed render, invalid output, source
  hash change, or cleanup failure remains explicit and blocks a pass.
- **Cleanup:** remove generated media after review only when the evidence and
  reports are retained.
- **Evidence response:** return `PASS`, `FAIL`, `BLOCKED`, or approved
  `NOT APPLICABLE` with report and artifact paths.
- **Pass criteria:** all requested strategies are attempted or explicitly
  accounted for, outputs are verified, and the recommendation is evidence
  bounded.

## Closure

TICKET-080 is complete. The user confirmed the benchmark fixtures, strategy
outputs, reports, and recommendation were manually validated and requested
closure of all tickets on 2026-08-28. The benchmark's hardware and visual
confidence limits remain documented.
