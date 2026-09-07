# TICKET-083 - Defer Audio Analysis During Source Import

**Ticket ID:** TICKET-083
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-008
**Feature:** FEAT-024
**Capability links:** CAP-002, CAP-005, CAP-012
**Status:** complete
**Horizon:** future
**Priority:** 1
**Owner:** repository implementation in the active worktree
**Approval:** User-authorized by the 2026-08-28 request to create, implement,
review, measure, and run the full validation set; execution remains subject to
the configured gates.
**Last updated:** 2026-09-07
**Source paths:** `framestudio/app_project.py`, `framestudio/operations.py`,
`framestudio/audio.py`, `framestudio/app_helpers.py`,
`framestudio/app_timeline_actions.py`, `framestudio/ffmpeg_playback.py`,
`framestudio/model_project.py`, `tests/test_editor_composition.py`,
`tests/test_editor_audio.py`, `tests/test_editor_operations.py`,
`README.md`, `.github/aidd-config.yml`
**Dependencies:** TICKET-081; metadata probing; existing source-level audio
policy; project persistence; export-time audio gate; playback generation
checks
**Risks:** stale background results could overwrite a replaced project,
editing could race with project mutation, pending audio could be presented as
ready, playback refresh could lose position or play state, and total analysis
work could be accidentally removed rather than deferred
**Affected surfaces:** GTK source import and project reopen, project
attachment, background audio analysis, audio status feedback, playback
refresh, editing lock state, export gating, persistence, tests, benchmarks,
documentation, and evidence
**Evidence path:** `evidence/ticket-083-defer-audio-analysis-during-import.md`
**Change control:** CHG-009
**Path history:** created at
`tickets/open/TICKET-083-defer-audio-analysis-during-import.md`
-> moved to
`tickets/closed/TICKET-083-defer-audio-analysis-during-import.md` on
2026-09-07 after user validation.

## Objective

Make a probed source project usable without waiting for full-file audio
analysis, while preserving the established source-level normalization policy
and all export correctness gates.

## Observable requirements

- Given one or more valid source paths, the editor should attach the project,
  timeline, and initial preview after metadata probing instead of waiting for
  full-file audio analysis.
- Given an attached project whose source audio is pending, the editor should
  show an explicit pending/analyzing state for each source and allow normal
  editing and project persistence.
- Given a background analysis result for a source, the editor should update
  only the matching current project and source, show the terminal decision,
  and refresh playback safely without losing the current position or play
  state.
- Given a replaced or superseded load, a late analysis result should be
  ignored without changing the current project, status, controls, or
  playback.
- Given an audio-analysis failure, the editor should show the explicit failed
  state and diagnostic; it must not report the source as ready or silently
  discard the failure.
- Given pending, stale, or failed audio decisions, export should continue to
  use `ensure_project_audio_analysis` and either complete explicit analysis or
  surface its existing failure behavior before rendering.
- Given an existing saved project with pending or stale audio decisions,
  reopening should not make project attachment wait on full-file analysis; the
  same explicit background and export-gating behavior should apply.
- Given the same source, policy, and media, the resulting terminal audio
  decision should remain equivalent to the existing full-file
  `legacy-concat-v1` behavior.
- Given the same representative media set, the evidence should report time to
  usable project before and after separately from total audio-analysis time.

## Scope

- Separate metadata probing/project attachment from source-level audio
  analysis in the GTK import and project-reopen lifecycle.
- Add generation- and project-identity-safe background completion for
  per-source analysis without mutating the project from the worker thread.
- Update editing-lock and control/status behavior so only active probing or
  export blocks editing.
- Refresh audio status and playback inputs safely when decisions become
  terminal, preserving position, play/pause state, and stale-frame rejection.
- Preserve export-time analysis, persisted decision shape, source fingerprints,
  full-file statistics, source preservation, and explicit errors.
- Add focused lifecycle regressions, repeat the existing suite, run repository
  checks and static analysis, and record before/after import measurements.

## Explicit non-goals

- Replacing the full-file audio analyzer or changing normalization targets,
  histogram resolution, policy version, or gain calculation.
- Adding a new dependency, audio cache, concurrency pool, or remote service.
- Removing the initial preview decode or changing timeline rendering semantics.
- Changing CLI audio analysis behavior or legacy media command behavior.
- Claiming universal import latency or eliminating total audio-analysis work.

## Protected behaviors

Existing one-source and mixed-source editing, source-level audio decisions,
audio filter behavior, project compatibility, atomic saves, export-time
analysis and verification, playback generation safety, source preservation,
structured errors, and legacy scripts remain unchanged.

## Validation

- Focused import lifecycle, audio status, playback refresh, stale-result, and
  export-gating tests.
- Existing `python3 -m unittest discover -s tests`.
- Existing `python3 -m py_compile ...`, `make check`, `make contract`,
  `make smoke`, and configured `make quality`/static-analysis commands.
- Same synthetic one-source, long-source, and multi-source timing protocol
  before and after implementation.
- Target-workstation GUI import with one and multiple local videos, including
  visible pending/analyzing/terminal audio status and an export attempt before
  and after analysis completion.
- Explicit records for unavailable GTK display, remote checks, target media,
  or other environment-dependent coverage.

## User-validation plan

- **Setup:** run `make editor ARGS="--source <video>"` on the target Linux
  workstation with FFmpeg and the normal FrameStudio environment available.
- **Steps:** import one long video and then multiple videos; observe that the
  project and timeline attach promptly; edit, save, and reopen while audio
  analysis is pending; observe each source's pending/analyzing/ready/failed
  state; attempt export during and after analysis.
- **Expected visible result:** the editor becomes usable after metadata
  probing, the timeline is interactive, audio status is truthful and updates
  per source, and export never treats pending or failed analysis as ready.
- **Expected persisted/external result:** saved project state retains valid
  pending or terminal decisions, completed analysis uses the existing policy,
  and an exported file remains verified and source-safe.
- **Failure paths:** invalid media, missing audio, FFmpeg analysis failure,
  replaced load, stale fingerprint, playback refresh failure, cancellation,
  and export attempted with unresolved audio remain explicit and recoverable.
- **Evidence response:** return `PASS`, `FAIL`, `BLOCKED`, or approved
  `NOT APPLICABLE` with observed time to usable project, audio states,
  export behavior, and environment limitations.

## Definition of done

- All observable requirements have focused regression evidence.
- The protected full-file audio policy and export gate remain intact.
- Before/after measurements show time to usable project and total analysis
  time separately.
- Existing tests, checks, smoke, contract, and applicable quality/review gates
  have terminal evidence, with historical findings separated from introduced
  findings.
- Target-workstation user validation is terminal before this ticket moves to a
  closed path.
