# TICKET-064 - Adopt and Document Responsive Preview Strategy

**Ticket ID:** TICKET-064
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-008
**Feature:** FEAT-024
**Capability links:** CAP-002, CAP-005, CAP-012
**Status:** complete
**Closure:** closed on 2026-08-26 after the selected preview behavior,
regressions, documentation, and target-workstation user validation were
accepted; GTK paint timing remains a documented limitation.
**Horizon:** future
**Priority:** 3
**Owner:** repository planning; maintainer identity is not recorded
**Approval:** user-authorized on 2026-08-26 for PHASE-008 planning; execution
requires the configured preimplementation and approval gates
**Last updated:** 2026-08-26
**Source paths:** `docs/planning/features/closed/FEAT-024-optimizing-cursor-driven-preview.md`,
`docs/planning/tickets/closed/TICKET-062-benchmark-current-preview-latency.md`,
`docs/planning/tickets/closed/TICKET-063-experiment-with-preview-rendering-strategies.md`,
`resolve_editor/app_playback.py`, `resolve_editor/ffmpeg_playback.py`,
`resolve_editor/timeline.py`, `README.md`, `tests/test_editor_playback.py`,
`.github/aidd-config.yml`
**Dependencies:** TICKET-063 comparison evidence; review of regressions and
target-workstation behavior
**Risks:** a local winner may regress an unmeasured codec or increase memory
use; a no-change decision may be correct but should not hide the evidence
**Affected surfaces:** default preview scheduling/caching, playback
regressions, documentation, benchmark evidence, and maintenance guidance
**Evidence path:** `evidence/phase-008-preview-responsiveness.md`
**Path history:** `tickets/open/TICKET-064-adopt-and-document-responsive-preview-strategy.md`
-> `tickets/closed/TICKET-064-adopt-and-document-responsive-preview-strategy.md`
**Protected behaviors:** play/pause, seek, timeline selection, split
positioning, mixed-source preview, source safety, and legacy scripts

## Outcome

The editor uses the best-supported preview strategy measured in PHASE-008,
or retains the current strategy with an explicit evidence-based rationale.

## Scope

- Review TICKET-063 results and select the default using latency, freshness,
  reliability, resource cost, and compatibility.
- Integrate the selected strategy behind the existing playback contract.
- Add focused regressions for event coalescing, stale frames, seek recovery,
  and ordinary playback.
- Document the measured environment, tradeoffs, and known limitations.

## Explicit non-goals

- Claiming universal performance.
- Rewriting unrelated playback or export architecture.
- Adding an external application or dependency.

## Observable requirements

- Given the documented interaction traces, the selected default should match
  the strategy and conditions recorded in the evidence.
- Given ordinary playback and seeks, existing controls and frame timing should
  remain functional.
- Given no candidate materially improves the baseline, the current strategy
  should remain the default and the reasons should be documented.

## Definition of done

- A default or no-change decision is explicit and source-linked.
- Focused regressions cover the adopted behavior and protected controls.
- README or the relevant maintenance documentation records the strategy and
  measurement boundary.
- The benchmark evidence is sufficient for future comparisons.

## User-validation plan

- **Setup:** run the selected preview on the target workstation with the
  baseline media and trace.
- **Steps:** move the cursor back and forth, click, seek, scroll, and play
  normally; compare visible behavior with the recorded measurements.
- **Expected result:** the preview feels fresher without breaking navigation or
  presenting silent failure.
- **Failure paths:** decode, seek, memory, or stale-frame regressions block
  adoption and remain recorded.
- **Cleanup:** remove benchmark-only flags and temporary artifacts.
- **Evidence response:** return the decision, before/after metrics, and
  limitations.
- **Pass criteria:** the default is reproducible, tested, and documented.

## Closure

TICKET-064 was closed after the bounded preview cache, request coalescing,
generation-safe stale-frame handling, focused regressions, documentation, and
the user's `PASS` validation were recorded in the linked evidence.
