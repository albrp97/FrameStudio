# FEAT-024 - Optimizing Cursor-Driven Preview and Source Attachment

**Feature ID:** FEAT-024
**Parent links:** OBJ-001, SCOPE-001, PHASE-008
**Capability links:** CAP-002, CAP-005, CAP-012
**Status:** complete
**Reopening:** reopened under CHG-009 on 2026-08-28 for a focused source
attachment and background audio-analysis follow-up. The existing preview
research and implementation remain protected.
**Horizon:** future
**Priority:** 1
**Owner:** repository planning; maintainer identity is not recorded
**Approval:** user-authorized on 2026-08-26 to break down PHASE-008; ticket
execution remains separately gated by the configured approval policy
**Last updated:** 2026-09-07
**Source paths:** `docs/planning/phases/closed/PHASE-008-optimizing-responsive-preview-and-media-strategy.md`,
`docs/specs/future-product-direction.md`, `framestudio/app_playback.py`,
`framestudio/ffmpeg_playback.py`, `framestudio/timeline.py`,
`framestudio/timeline_geometry.py`, `tests/test_editor_playback.py`,
`tests/test_editor_timeline.py`, `framestudio/app_project.py`,
`framestudio/operations.py`, `framestudio/audio.py`,
`tests/test_editor_composition.py`, `.github/aidd-config.yml`
**Dependencies:** PHASE-006 preview and focus behavior; current FFmpeg raw-frame
playback; target-workstation media access; disposable Lossless Cut research
checkout
**Risks:** seek latency, stale frames, decoder contention, cache invalidation,
codec/keyframe differences, and benchmark bias can make a local improvement
look generally reliable
**Affected surfaces:** GTK playback lifecycle, source import attachment,
background audio analysis, audio status feedback, preview seeking and
caching, benchmark tooling, documentation, and regression tests
**Evidence path:** `evidence/ticket-083-defer-audio-analysis-during-import.md`
**Planned tickets:** TICKET-061, TICKET-062, TICKET-063, TICKET-064, TICKET-083
**Path history:** `features/open/FEAT-024-optimizing-cursor-driven-preview.md`
-> `features/closed/FEAT-024-optimizing-cursor-driven-preview.md`
-> reopened under CHG-009 at
`features/open/FEAT-024-optimizing-cursor-driven-preview.md`
-> moved to
`features/closed/FEAT-024-optimizing-cursor-driven-preview.md` on 2026-09-07
after all child tickets and user validation completed.

## Outcome

Timeline cursor movement, clicking, and scrolling provide a fresher preview
with measured lower interaction latency than the current implementation on
the representative target-workstation media set, while a successfully probed
project becomes usable before full-file source audio analysis completes.

## Scope

- Inspect the preview and seeking approach used by Lossless Cut without
  copying implementation code or adding it as a dependency.
- Measure the current editor before changing the preview path.
- Experiment with multiple candidate strategies using the same interactions
  and media.
- Select and document the best-supported strategy, including when the current
  path should remain in use.
- Attach projects after metadata probing, run source-level audio analysis in
  the background, and expose pending, analyzing, ready, and failed states
  without changing the established audio policy.

## Explicit non-goals

- Reimplementing the full Lossless Cut application.
- Guaranteeing a fixed latency across all codecs, disks, machines, or media.
- Changing export behavior, output profiles, or source files.
- Adding a background service or remote media-processing dependency.
- Replacing the full-file audio policy, adding a new audio-analysis
  dependency, or weakening export-time analysis and verification.

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
- Given a probed source project, the editor should attach the project and
  expose its timeline before background audio analysis completes.
- Given independent source-analysis completion, the matching current project
  should receive the terminal decision and refresh its audio status and
  playback without stale work changing a replaced project.
- Given a failed or stale audio analysis, the editor should show the explicit
  terminal state and export should still require a valid terminal decision
  rather than treating pending audio as ready.

## Validation and evidence

- Disposable, revision-pinned Lossless Cut research notes with license
  attribution and applicable patterns.
- Baseline and candidate benchmark output with the same media and interaction
  sequence.
- Playback/timeline regression tests and target-workstation preview evidence.
- Import-lifecycle regression tests and before/after time-to-usable-project
  measurements, with total audio-analysis time recorded separately.
- Explicit unavailable-environment and codec limitations.

## Protected behaviors

Play/pause, seek, timeline selection, split positioning, source preservation,
mixed-source composition, and legacy media scripts remain unchanged unless a
focused regression demonstrates the selected preview change is required.
The existing source-level audio policy, persisted decision schema,
fingerprint staleness checks, export-time `ensure_project_audio_analysis`,
and explicit failure behavior remain unchanged.

## Definition of done

- The preview baseline and candidate strategy measurements are reproducible.
- A strategy is selected or the evidence explains why the current strategy
  remains the default.
- The selected behavior is covered by focused regressions and documented for
  future maintenance.
- Source import reaches a usable project after probing, background audio
  completion is generation-safe, and the measured improvement is recorded
  without claiming total analysis time was eliminated.
- No external checkout or unreviewed copied code becomes a runtime dependency.
