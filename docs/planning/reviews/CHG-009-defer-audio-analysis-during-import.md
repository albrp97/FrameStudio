# CHG-009 - Defer Audio Analysis During Source Import

**Change ID:** CHG-009
**Type:** Material planning change
**Status:** approved-and-applied
**Date:** 2026-08-28
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Parent links:** PHASE-008, FEAT-024
**Owner:** repository planning and implementation in the active worktree
**Approval:** User-authorized by the request to create, implement, review, and
measure the source-import responsiveness ticket.
**Affected IDs:** PHASE-008, FEAT-024, TICKET-083
**Evidence path:** `evidence/ticket-083-defer-audio-analysis-during-import.md`
**Source paths:** `framestudio/app_project.py`, `framestudio/operations.py`,
`framestudio/audio.py`, `framestudio/app_helpers.py`,
`framestudio/app_timeline_actions.py`, `tests/test_editor_composition.py`,
`tests/test_editor_audio.py`, `.github/aidd-config.yml`

## Request and classification

The source-import worker currently performs full-file source-level audio
analysis before attaching the probed project to the editor. The analysis
decodes every audio sample and can take seconds or minutes for long or
multiple sources, even though metadata probing and timeline construction are
already sufficient to show a usable project.

This is a material planning change because it reopens the completed
PHASE-008/FEAT-024 subtree and changes the import lifecycle boundary. It does
not change the approved objective, first-horizon scope, audio policy
semantics, output policy, or source-preservation guarantees.

## Approved decision

Reopen PHASE-008 and FEAT-024, then add TICKET-083 to attach a successfully
probed project before full-file audio analysis completes. Run source-level
analysis in the background, publish explicit pending/analyzing/ready/failed
states on the GTK main thread, and apply results only to the matching current
project and load generation. Keep export-time `ensure_project_audio_analysis`
as the correctness gate, and retain the existing full-file
`legacy-concat-v1` analysis policy in this ticket.

## Impact

- **Planning:** move PHASE-008 and FEAT-024 from `closed/` to `open/` while
  preserving stable IDs and path history; add TICKET-083 under FEAT-024.
- **Runtime:** separate metadata-ready project attachment from background
  audio completion for new imports and saved projects with pending or stale
  decisions.
- **UI:** unlock editing after metadata probing, show truthful per-source audio
  status, and report analysis failures without false readiness.
- **Correctness:** preserve generation/project-identity checks, playback
  refresh safety, export analysis and failure gates, persistence schema, and
  source-level audio semantics.
- **Evidence:** compare time to usable project before and after, and record
  total background analysis time separately.

## Explicit non-goals

- Replacing or approximating the existing full-file audio policy.
- Adding NumPy, a new audio-analysis dependency, or a new background service.
- Removing export-time analysis or allowing pending/failed audio to appear
  ready.
- Changing source media, project schema, timeline semantics, output profiles,
  or legacy CLI/media workflows.

## Replan decision

Approved and applied on 2026-08-28. The smallest affected subtree is reopened:
PHASE-008 and FEAT-024 are active; FEAT-025 through FEAT-028 and their closed
ticket records remain unchanged. Execution is owned by TICKET-083 and remains
subject to its baseline, evidence, review, local-quality, remote-check, and
user-validation gates.

## Traceability

- Reopened phase: `docs/planning/phases/open/PHASE-008-optimizing-responsive-preview-and-media-strategy.md`
- Reopened feature: `docs/planning/features/open/FEAT-024-optimizing-cursor-driven-preview.md`
- New ticket: `docs/planning/tickets/open/TICKET-083-defer-audio-analysis-during-import.md`
- Evidence: `evidence/ticket-083-defer-audio-analysis-during-import.md`
