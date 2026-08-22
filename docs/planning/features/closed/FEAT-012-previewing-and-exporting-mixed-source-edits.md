# FEAT-012 - Preview and Export Mixed-Source Edits

**Feature ID:** FEAT-012
**Parent links:** OBJ-001, SCOPE-001, PHASE-004
**Capability links:** CAP-002, CAP-005, CAP-007, CAP-012
**Status:** complete
**Closure:** user-approved on 2026-08-22 after successful implementation,
review evidence, and target-workstation validation; remote checks remain
unavailable and are recorded as an accepted warning.
**Path history:** `features/open/FEAT-012-previewing-and-exporting-mixed-source-edits.md`
-> `features/closed/FEAT-012-previewing-and-exporting-mixed-source-edits.md`
**Horizon:** future
**Priority:** 3
**Owner:** repository planning; maintainer identity is not recorded
**Approval:** user-authorized on 2026-08-21 to continue with PHASE-004 ticket planning
**Source paths:** `vision.md`, `docs/specs/project-scope.md`,
`docs/specs/capability-map.md`,
`docs/planning/phases/open/PHASE-004-combining-mixed-source-footage.md`,
`docs/specs/future-product-direction.md`, `.github/aidd-config.yml`
**Dependencies:** FEAT-010 source metadata; FEAT-011 timeline semantics;
approved fixed 1920x1080 canvas and established render profile
**Risks:** aspect-ratio surprises, preview latency, timestamp drift, loss of
stream-copy eligibility, invalid fallback output, fixed-canvas scaling cost,
and hardware-specific rendering behavior
**Affected surfaces:** playback/composition preview, output-profile policy,
export planner/executor, validation, persistence, CLI, GUI, and tests
**Evidence path:** `evidence/phase-004-mixed-source-preview-export.md`
**Planned tickets:** TICKET-024, TICKET-025, TICKET-026, TICKET-027

## Outcome

The user can preview a project on a fixed 1920x1080 project canvas and export a
verified one-source or composed mixed-source result using the established
render profile.

## Included

- Use a fixed 1920x1080 output canvas with contain scaling and letterboxing.
- Apply the same fixed canvas to one-source preview/export; retain stream copy
  only when the source already matches the canvas.
- Preserve deterministic current timing and timestamp behavior without making
  60 FPS enhancement a current requirement.
- Use the established render profile for container, codecs, audio, and pixel
  format.
- Show source boundaries and the composed result during playback.
- Report when fixed-canvas composition requires rendering and stream copy is
  unavailable.
- Export through a temporary-output, validation, and atomic-publication
  boundary.
- Preserve source-level and segment-level settings in project and CLI state.

## Explicit non-goals

- Automatic per-input audio-level normalization beyond preserving or
  explicitly reporting source audio.
- Triplicate portrait/focused-action layouts, reusable visual modifications,
- source-driven codec/container selection, or 60 FPS enhancement.
- Hardware-specific performance claims without target-workstation evidence.

## Acceptance outcomes

- Given mixed dimensions and orientations, the preview and output use a
  1920x1080 canvas without silently cropping or stretching sources.
- Given mixed frame rates or timestamps, current timing remains deterministic
  and visible while 60 FPS enhancement remains deferred.
- Given a one-source or mixed-source edit, the exporter uses the established
  render profile, verifies the output, and reports why fixed-canvas rendering
  requires re-encoding when applicable.
- Given a preview, export, or validation failure, original sources, project
  state, and the last valid output remain intact.

## Evidence plan

- Output-policy and route-selection tests.
- Generated and representative mixed-source playback/export fixtures.
- Manual preview, metadata, duration, source-preservation, and failure
  recovery evidence.

## Protected behavior

The existing one-source final-duration calculation, temporary-output cleanup,
atomic publication, and CLI progress/error contract remain unchanged. The
one-source preview and verified output now use the fixed project canvas.
