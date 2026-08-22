# FEAT-002 — Controlling Playback and Navigating the Source Timeline

**Feature ID:** FEAT-002
**Parent links:** OBJ-001, SCOPE-001, PHASE-001
**Capability links:** CAP-002, CAP-012
**Status:** verifying
**Previous closure:** user-approved on 2026-08-22 after successful
implementation, review evidence, and target-workstation validation; remote
checks remain unavailable and are recorded as an accepted warning.
**Reopened:** user-reported on 2026-08-22 to correct timeline playback pacing
after a cursor seek.
**Path history:** `features/open/FEAT-002-controlling-playback-and-navigating-the-source-timeline.md`
-> `features/closed/FEAT-002-controlling-playback-and-navigating-the-source-timeline.md`
-> `features/open/FEAT-002-controlling-playback-and-navigating-the-source-timeline.md`
**Horizon:** first
**Owner:** repository planning; maintainer identity is not recorded
**Approval:** user-approved on 2026-08-21 as part of PHASE-001 planning
**Source paths:** `vision.md`, `docs/specs/project-scope.md`,
`docs/specs/capability-map.md`, `docs/planning/features.md`,
`docs/planning/phases/open/PHASE-001-opening-and-resuming-a-source-edit.md`,
`.github/aidd-config.yml`
**Migration source:** `docs/planning/features.md`, inline section
`FEAT-002 — Controlling Playback and Navigating the Source Timeline`;
migrated on 2026-08-21 with the feature content preserved.
**Affected surfaces:** editor interface, playback backend, timeline state,
source metadata, user-facing error handling, and manual GUI test harness

## Outcome

Given an opened source project, the user can view the source in real time,
play or pause it after seeking, and understand the current position and
duration in the primary editor interface.

### Included

- Present a real-time preview for the opened source.
- Provide play, pause, and seek controls.
- Pace preview frames at the configured output rate after timeline cursor
  seeks so the visible video advances instead of jumping to the latest frame.
- Show a timeline representation with current position and source duration.
- Keep preview position and timeline state synchronized.
- Surface buffering, seek limitations, unavailable backends, and playback
  failures clearly.

### Explicit non-goals

- Split, delete, move, copy, paste, or export operations.
- Multiple sources, multiple tracks, mixed timebases, or composition.
- Final visual polish that does not improve playback comprehension or
  responsiveness.

### Dependencies and risks

- Depends on FEAT-001 source identity and metadata.
- Requires the PHASE-001 decision for GUI/runtime, playback backend,
  packaging/setup, and known limitations.
- Seeking may be delayed or approximate for variable-frame-rate or
  keyframe-bound media.
- Preview performance and timeline timing may vary by source and workstation.

### Acceptance outcomes

- Given an opened supported source, the preview can play and pause without
  losing the project source state.
- Given a timeline cursor seek followed by play, successive preview frames
  advance at approximately the configured frame rate.
- Given a valid position, seeking updates the preview and timeline position
  or reports an explicit limitation.
- The interface presents source duration and current position consistently.
- Given a playback or backend failure, the editor exposes an actionable
  error and preserves the last valid state.

### Evidence plan

- Unit tests for playback/timeline state transitions where the selected
  runtime permits.
- A generated-media regression test for real-time frame pacing after seek.
- Manual target-workstation smoke test covering play, pause, seek, duration,
  and a representative source.
- Record backend versions, seek accuracy limitations, and unavailable
  environment-dependent checks.

### Protected behavior

The existing curses workflows and media-processing scripts remain callable;
the editor does not silently replace their commands or behavior.
