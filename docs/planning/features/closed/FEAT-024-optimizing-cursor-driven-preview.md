# FEAT-024 - Optimizing Cursor-Driven Preview

**Feature ID:** FEAT-024
**Parent links:** OBJ-001, SCOPE-001, PHASE-008
**Capability links:** CAP-002, CAP-005, CAP-012
**Status:** complete
**Closure:** closed on 2026-08-26 after the research, baseline, candidate
comparison, bounded preview implementation, regressions, documentation, and
target-workstation user validation were accepted.
**Horizon:** future
**Priority:** 1
**Owner:** repository planning; maintainer identity is not recorded
**Approval:** user-authorized on 2026-08-26 to break down PHASE-008; ticket
execution remains separately gated by the configured approval policy
**Last updated:** 2026-08-26
**Source paths:** `docs/planning/phases/open/PHASE-008-optimizing-responsive-preview-and-media-strategy.md`,
`docs/specs/future-product-direction.md`, `resolve_editor/app_playback.py`,
`resolve_editor/ffmpeg_playback.py`, `resolve_editor/timeline.py`,
`resolve_editor/timeline_geometry.py`, `tests/test_editor_playback.py`,
`tests/test_editor_timeline.py`, `.github/aidd-config.yml`
**Dependencies:** PHASE-006 preview and focus behavior; current FFmpeg raw-frame
playback; target-workstation media access; disposable Lossless Cut research
checkout
**Risks:** seek latency, stale frames, decoder contention, cache invalidation,
codec/keyframe differences, and benchmark bias can make a local improvement
look generally reliable
**Affected surfaces:** GTK playback lifecycle, timeline pointer events,
preview seeking and caching, benchmark tooling, documentation, and regression
tests
**Evidence path:** `evidence/phase-008-preview-responsiveness.md`
**Planned tickets:** TICKET-061, TICKET-062, TICKET-063, TICKET-064
**Path history:** `features/open/FEAT-024-optimizing-cursor-driven-preview.md`
-> `features/closed/FEAT-024-optimizing-cursor-driven-preview.md`

## Outcome

Timeline cursor movement, clicking, and scrolling provide a fresher preview
with measured lower interaction latency than the current implementation on
the representative target-workstation media set.

## Scope

- Inspect the preview and seeking approach used by Lossless Cut without
  copying implementation code or adding it as a dependency.
- Measure the current editor before changing the preview path.
- Experiment with multiple candidate strategies using the same interactions
  and media.
- Select and document the best-supported strategy, including when the current
  path should remain in use.

## Explicit non-goals

- Reimplementing the full Lossless Cut application.
- Guaranteeing a fixed latency across all codecs, disks, machines, or media.
- Changing export behavior, output profiles, or source files.
- Adding a background service or remote media-processing dependency.

## Observable requirements

- Given the same representative media and pointer workflow, the benchmark
  should report comparable baseline and candidate latency and frame-freshness
  measurements.
- Given rapid cursor movement or repeated clicks, the selected strategy
  should avoid presenting an older frame as the current position without
  clearly exposing an unavoidable decode delay.
- Given an unavailable decoder, failed seek, or exhausted cache, the preview
  should report the state and preserve normal editor interaction.
- Given the selected strategy, the implementation and documented tradeoffs
  should match the measured evidence rather than an untested assumption.

## Validation and evidence

- Disposable, revision-pinned Lossless Cut research notes with license
  attribution and applicable patterns.
- Baseline and candidate benchmark output with the same media and interaction
  sequence.
- Playback/timeline regression tests and target-workstation preview evidence.
- Explicit unavailable-environment and codec limitations.

## Protected behaviors

Play/pause, seek, timeline selection, split positioning, source preservation,
mixed-source composition, and legacy media scripts remain unchanged unless a
focused regression demonstrates the selected preview change is required.

## Definition of done

- The preview baseline and candidate strategy measurements are reproducible.
- A strategy is selected or the evidence explains why the current strategy
  remains the default.
- The selected behavior is covered by focused regressions and documented for
  future maintenance.
- No external checkout or unreviewed copied code becomes a runtime dependency.

## Closure

FEAT-024 was closed after TICKET-061 through TICKET-064 reached complete
status. The selected bounded cache/coalescing strategy and its backend timing
limits remain documented in the linked evidence.
