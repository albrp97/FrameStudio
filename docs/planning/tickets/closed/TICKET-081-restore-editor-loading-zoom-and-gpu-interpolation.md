# TICKET-081 - Restore Editor Loading, Timeline Zoom, and GPU Interpolation

**Ticket ID:** TICKET-081
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-008
**Feature:** FEAT-028
**Capability links:** CAP-002, CAP-005, CAP-011, CAP-012
**Status:** complete
**Horizon:** future
**Priority:** 1
**Owner:** repository implementation in the active worktree
**Approval:** User-requested regression fix; execution remains subject to the
configured evidence, review, user-validation, and delivery gates
**Last updated:** 2026-08-28
**Source paths:** `framestudio/app.py`, `framestudio/app_project.py`,
`framestudio/app_timeline_actions.py`, `framestudio/interpolation.py`,
`framestudio/fps_policy.py`, `framestudio/timeline_geometry.py`,
`framestudio/timeline.py`, `.github/aidd-config.yml`
**Dependencies:** existing PHASE-008 editor lifecycle; validated RVE runtime;
FFmpeg/ffprobe; representative local media
**Risks:** worker/UI races can attach stale projects, sub-100% geometry can
change hit testing, and CPU encoding or fractional-rate normalization can make
GPU inference appear idle
**Affected surfaces:** GTK source import, source/audio probing, status
feedback, timeline zoom geometry, interpolation backend selection, encoder
defaults, tests, and evidence
**Evidence path:** `evidence/ticket-081-editor-responsiveness-and-gpu-interpolation.md`
**Path history:** created at
`tickets/open/TICKET-081-restore-editor-loading-zoom-and-gpu-interpolation.md`
-> moved to
`tickets/closed/TICKET-081-restore-editor-loading-zoom-and-gpu-interpolation.md`
**Protected behaviors:** source preservation, project validation, playback
replacement, timeline selection/seek behavior, exact output timing, atomic
export, legacy FPS commands, and explicit unavailable-backend errors

## Objective

Restore responsive editor feedback and the validated GPU-backed interpolation
route without weakening existing project, playback, or export guarantees.

## Observable requirements

- Given one or more selected source videos, the editor should probe and
  analyze them off the GTK thread and visibly report `Loading clip i/x` with a
  percentage while work is active.
- Given a source-loading failure, the editor should surface the explicit error,
  leave the previous project intact, and clear the loading state.
- Given timeline zoom controls, the timeline should support at least one
  level below `100%` while preserving focus/composition zoom minimums and
  existing seek, selection, and fit behavior.
- Given a supported RVE interpolation export, the editor should use the
  validated GPU encoder profile by default rather than silently selecting the
  CPU `libx264` encoder.
- Given a new project or a project without a persisted upscale decision, the
  render panel should enable eligible-source upscaling by default while
  preserving an explicit persisted opt-out.
- Given a constant-frame-rate source below the target, including a fractional
  conversion such as 23.976-to-60, the editor should use integer GPU RVE
  oversampling followed by exact target-rate normalization rather than CPU
  `minterpolate`.
- Given a variable-frame-rate source or an unavailable RVE runtime, the
  selected fallback or block should remain explicit and reported rather than
  being presented as GPU neural interpolation.
- Given replacement or cancellation during loading, stale worker results
  should not replace the current project or leave controls permanently locked.

## Scope

- Add worker-based source import and GTK-main-thread progress/error
  publication for metadata and audio analysis.
- Add regression coverage for loading state, per-clip progress, and stale
  completion handling.
- Lower only the timeline zoom minimum and add a below-100% zoom level with
  geometry and interaction coverage.
- Make the editor RVE encoder default match the validated direct CLI
  configuration and preserve explicit caller overrides.
- Make eligible-source upscale enhancement enabled by default while preserving
  explicit persisted opt-out behavior.
- Add safe integer-factor GPU oversampling and exact target-rate normalization
  for constant-frame-rate conversions whose factor is not an integer.

## Explicit non-goals

- Changing the separate focus/composition zoom minimum.
- Claiming 100% sustained GPU utilization for every codec, resolution, or
  source frame rate.
- Claiming arbitrary or variable-frame-rate input is supported by the
  fractional GPU path; VFR input remains explicitly unsupported.
- Replacing the validated RVE TensorRT/PyTorch execution split or adding a new
  runtime dependency.
- Changing legacy command names, source files, project schema, or export
  output policy outside the regression fixes.

## Validation

- Focused editor composition, performance, timeline, and interpolation tests.
- Existing `make test`, `make contract`, `make smoke`, and `make check`.
- Existing repository quality/static-analysis commands with pre-existing
  findings separated from introduced findings.
- Target-workstation GUI import with one and multiple local videos, including
  visible progress and final project attachment.
- Target-workstation interpolation exports for integer and fractional
  constant-frame-rate sources, recording the RVE oversampling route, encoder,
  output metadata, exact timing, and GPU observations; separately confirm
  explicit handling of VFR input and the render panel's default upscale state
  and opt-out behavior.

## User-validation plan

- **Setup:** run `make editor ARGS="--source <video>"` on the RTX 5070 Ti
  workstation with the validated RVE environment available.
- **Steps:** import one video and then multiple videos; observe `Loading clip
  i/x` progress; zoom the timeline below and above `100%`; export integer and
  fractional constant-frame-rate sources and inspect the reported
  backend/encoder; inspect a VFR source separately.
- **Expected result:** import remains responsive with truthful progress,
  sub-100% timeline zoom shortens the timeline without changing focus zoom,
  supported interpolation uses RVE plus the GPU encoder, fractional
  conversion reports GPU oversampling and exact normalization, and VFR input
  remains explicitly blocked or falls back.
- **Failure paths:** probe/audio failure, stale completion, cancellation,
  unavailable runtime, invalid output timing, or partial output must remain
  visible and leave no corrupted project or published partial export.
- **Evidence response:** return `PASS`, `FAIL`, `BLOCKED`, or approved
  `NOT APPLICABLE` with the observed backend, encoder, output metadata, and
  limitation.

## Definition of done

- All observable requirements have focused regression evidence.
- Protected editor and export tests remain passing.
- The target-workstation behavior and any environment-dependent limitation
  are recorded.
- User validation is terminal before this ticket is moved to a closed path.

## Closure

TICKET-081 is complete. The user confirmed the editor loading, timeline zoom,
GPU interpolation, and related export behavior were manually validated and
requested closure of all tickets on 2026-08-28. Existing environment and
remote-check limitations remain documented in the evidence record.
