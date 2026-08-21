# FEAT-002 — Controlling Playback and Navigating the Source Timeline

**Feature ID:** FEAT-002  
**Parent links:** OBJ-001, SCOPE-001, PHASE-001  
**Capability links:** CAP-002, CAP-012  
**Status:** confirmed  
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

Given an opened source project, the user can view the source in
real time, play or pause it, seek through it, and understand the current
position and duration in the primary editor interface.

### Included

- Present a real-time preview for the opened source.
- Provide play, pause, and seek controls.
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
- Given a valid position, seeking updates the preview and timeline position
  or reports an explicit limitation.
- The interface presents source duration and current position consistently.
- Given a playback or backend failure, the editor exposes an actionable
  error and preserves the last valid state.

### Evidence plan

- Unit tests for playback/timeline state transitions where the selected
  runtime permits.
- Manual target-workstation smoke test covering play, pause, seek, duration,
  and a representative source.
- Record backend versions, seek accuracy limitations, and unavailable
  environment-dependent checks.

### Protected behavior

The existing curses workflows and media-processing scripts remain callable;
the editor does not silently replace their commands or behavior.
