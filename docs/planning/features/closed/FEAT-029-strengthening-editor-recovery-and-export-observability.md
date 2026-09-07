# FEAT-029 - Strengthening Editor Recovery and Export Observability

**Feature ID:** FEAT-029
**Parent links:** OBJ-001, SCOPE-001, PHASE-008
**Capability links:** CAP-002, CAP-003, CAP-004, CAP-005, CAP-006, CAP-012
**Status:** complete
**Horizon:** future
**Priority:** 1
**Owner:** repository implementation in the active worktree
**Approval:** User-authorized by requests to create, implement, test, and
review the editor recovery, timeline, playback, export, progress, and
upscale-count improvements without waiting for separate ticket approval.
General resumable-export planning was authorized by the 2026-09-06 request;
execution remains subject to the configured gates.
**Last updated:** 2026-09-07
**Source paths:** `vision.md`, `docs/specs/project-scope.md`,
`docs/specs/capability-map.md`,
`docs/planning/phases/closed/PHASE-008-optimizing-responsive-preview-and-media-strategy.md`,
`docs/planning/features/closed/FEAT-024-optimizing-cursor-driven-preview.md`,
`framestudio/persistence.py`, `framestudio/app_project.py`,
`framestudio/timeline.py`,
`framestudio/export_console.py`, `framestudio/app_playback.py`,
`framestudio/app_export.py`, `framestudio/graphics.py`,
`framestudio/ffmpeg_playback.py`, `framestudio/model_timeline.py`,
`tests/test_editor_graphics.py`, `tests/test_editor_composition.py`,
`framestudio/export_cache.py`, `framestudio/export_smart_render.py`,
`framestudio/export_interpolation.py`, `framestudio/export_delivery.py`,
`tests/test_editor_export_panel.py`, `tests/test_editor_export_cache.py`,
`tests/test_editor_export_execution.py`, `tests/test_editor_performance.py`,
`docs/planning/reviews/CHG-010-generalize-export-resume-across-cancellation-and-restarts.md`,
`.github/aidd-config.yml`
**Dependencies:** TICKET-083 source/project lifecycle; existing versioned
project persistence; fixed timeline and output contracts; safe atomic export;
validated enhanced-render route
**Change control:** CHG-010 extends the enhanced-only retry scope to
fingerprinted resumable sessions across ordinary and enhanced export routes.
**Risks:** autosave may overwrite the wrong recovery state, high zoom may
break viewport mapping, composition refresh may lose playback position, stale
intermediates may be reused after a source or policy change, and human
progress output must not corrupt machine-readable CLI output
**Affected surfaces:** GTK project lifecycle, persistence, timeline geometry
and controls, triplicate preview refresh, enhanced-export cache lifecycle,
CLI and GUI progress reporting, tests, evidence, and documentation
**Planned tickets:** TICKET-084, TICKET-085, TICKET-086, TICKET-087, TICKET-088,
TICKET-089, TICKET-090, TICKET-091, TICKET-092, TICKET-093, TICKET-094,
TICKET-095, TICKET-096, TICKET-097, TICKET-098, TICKET-099, TICKET-100,
TICKET-101
**Evidence paths:** `evidence/ticket-084-editor-autosave.md`,
`evidence/ticket-085-timeline-fit-and-unlimited-zoom.md`,
`evidence/ticket-086-triplicate-playhead-preservation.md`,
`evidence/ticket-087-resumable-enhanced-export.md`,
`evidence/ticket-088-staged-export-progress.md`,
`evidence/ticket-089-keep-playback-running-when-seeking-timeline.md`,
`evidence/ticket-090-keep-export-planning-responsive.md`,
`evidence/ticket-091-report-upscale-count-and-preserve-render-route.md`,
`evidence/ticket-092-avoid-wayland-vulkan-swapchain-warning.md`,
`evidence/ticket-093-fix-enhanced-export-frame-count-and-cache-reuse.md`,
`evidence/ticket-094-improve-video-only-playback-and-audio-analysis-coalescing.md`,
`evidence/ticket-095-keep-last-clip-deletion-responsive.md`,
`evidence/ticket-096-report-fps-enhancement-count.md`,
`evidence/ticket-097-add-safe-post-export-actions-and-failure-logs.md`,
`evidence/ticket-098-export-session-checkpoints.md`,
`evidence/ticket-099-resumable-export-execution.md`,
`evidence/ticket-100-export-resume-controls.md`,
`evidence/ticket-101-cli-export-resume-contract.md`
**Path history:** created at
`features/open/FEAT-029-strengthening-editor-recovery-and-export-observability.md`
-> moved to
`features/closed/FEAT-029-strengthening-editor-recovery-and-export-observability.md`
on 2026-09-07 after all child tickets and user validation completed.

## Outcome

FrameStudio protects the user's current edit from a process failure, lets the
timeline scale to the requested working range, keeps the live editing
position stable across triplicate changes, resumes expensive enhanced-export
work after a failure, and exposes the same export stages clearly to both
interactive terminal users and automation. It also lets ordinary and
enhanced exports continue from validated checkpoints after cancellation, late
failure, application restart, or project reopen.

## Scope

- Maintain exactly one current-project autosave outside the normal user-chosen
  project path and offer explicit, source-safe recovery.
- Remove the artificial upper timeline-zoom ceiling and provide an explicit
  30-minute viewport-fit action without changing focus/composition zoom.
- Preserve the live backend/controller playhead and play/pause state when
  triplicate mode is enabled or disabled.
- Persist validated enhanced-export intermediates beside the destination,
  fingerprint requests and source state, reuse valid artifacts on retry, and
  remove them only after verified publication.
- Persist one fingerprinted export session for each destination, checkpoint
  every supported preparation, cutting, interpolation/upscale,
  composition/concatenation, verification, and publication boundary, and
  retain valid checkpoints across cancellation and process restart.
- On a later export invocation or project reopen, identify compatible sessions
  and offer explicit Resume, Start over, or Discard choices without silently
  launching an export.
- Preserve the same resumable-session semantics in the CLI while keeping
  existing JSON Lines and human staged-progress contracts stable.
- Report numbered preparation, rendering/enhancement, concatenation/composition,
  verification, and publication stages to human terminal users while keeping
  JSON Lines output stable for automation.
- Keep timeline seeking and export-plan preparation responsive in the GTK main
  loop.
- Select a supported non-Vulkan GTK renderer by default on Wayland without
  overriding explicit user configuration.

## Explicit non-goals

- Supporting multiple simultaneous autosave slots or silently restoring a
  project on startup.
- Changing the project schema, source relinking policy, fixed output canvas,
  focus-transform bounds, or timeline editing semantics.
- Replacing the existing playback backend or introducing a remote recovery
  service.
- Reusing an intermediate after source, timeline, policy, runtime, or media
  validation changes.
- Silently resuming an export, supporting multiple concurrent sessions for one
  destination, or storing checkpoints remotely.
- Replacing the versioned CLI JSON contract with human-readable output.

## Observable requirements

- Given an attached or edited project, a single autosave should reflect the
  current valid state without changing the normal **Save project** destination.
- Given an available and unchanged autosave, explicit recovery should attach
  it; missing or changed sources should produce a visible error and leave the
  current project untouched.
- Given any project duration, timeline zoom should continue beyond 1200%, and
  the 30-minute fit action should make a 30-minute window span the viewport
  while keeping short projects fully visible.
- Given an enabled or disabled triplicate toggle, the visible playhead and
  playback state should remain at the live position rather than resetting to
  the start.
- Given a failed enhanced export, a retry should validate and reuse completed
  intermediates; changed or corrupted requests should rebuild them, and a
  successful verified publication should remove the cache.
- Given an interactive export, terminal users should see numbered stage
  progress including concatenation/composition and verification; machine
  consumers should continue receiving valid JSON Lines on stdout.
- Given a Wayland editor session without an explicit renderer, GTK should use
  the supported GL renderer and avoid the known non-fatal Vulkan swapchain
  warning; explicit renderer choices remain unchanged.
- Given an enhanced mixed export with fractional segment durations, final
  composition should preserve the exact target frame count and reuse valid
  retained intermediates on retry.
- Given an export is cancelled after a completed stage or fails in a later
  stage, a compatible later invocation should reuse validated earlier
  checkpoints for both ordinary and enhanced routes.
- Given a project is reopened with a compatible pending session, the export
  flow should expose the last completed stage and explicit Resume, Start over,
  and Discard actions without starting work automatically.
- Given a source, project, destination, policy, runtime, or tool identity has
  changed, the session should be rejected with an explicit reason and no
  stale artifact should be reused.
- Given a CLI user requests resume, restart, or discard, the selected action
  should be explicit, source-safe, and compatible with existing JSON Lines
  consumers.

## Validation and evidence

- Focused persistence, lifecycle, timeline, composition, export-cache, and
  console-progress regressions for each ticket.
- Existing repository unit, compile, contract, smoke, quality, static-analysis,
  dependency, security, complexity, duplication, and churn commands.
- Representative GTK/media validation of autosave recovery, 30-minute fit,
  unlimited zoom, triplicate cursor stability, retry reuse, and terminal
  progress.
- Before/after or failure/retry measurements with source-preservation,
  output-verification, and machine-readable-output evidence.
- Cancellation/restart/reopen evidence for ordinary and enhanced exports,
  including stage reuse, invalidation reasons, final cleanup, and a bounded
  time-sliced render continuation.
- Explicit records for unavailable GUI, media, GPU, or remote checks.

## Protected behavior

Existing source import and background audio-analysis safety, project
compatibility, normal save/reopen behavior, playback generation checks,
timeline editing, fixed 1920x1080 delivery, atomic partial-output handling,
verified export, CLI JSON Lines, legacy scripts, and source preservation remain
unchanged.

## Definition of done

- All planned tickets have focused implementation and regression evidence,
  including persistent resumable sessions across cancellation and restart.
- User-visible recovery, timeline, composition, retry, and progress behavior
  has terminal target-workstation validation or an explicit environment
  limitation.
- Existing tests and configured gates pass or record precise blockers.
- The feature index, backlog, evidence links, and ticket statuses are
  synchronized before delivery review.
