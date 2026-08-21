# PHASE-001 - Opening and Resuming a Source Edit

**Phase ID:** PHASE-001  
**Parent links:** OBJ-001, SCOPE-001  
**Capability links:** CAP-001, CAP-002, CAP-004, CAP-012  
**Sequence:** 1  
**Status:** confirmed  
**Horizon:** first  
**Owner:** repository planning; maintainer identity is not recorded  
**Approval:** user-approved on 2026-08-21 before feature generation  
**Source paths:** `vision.md`, `docs/specs/project-scope.md`,
`docs/specs/capability-map.md`, `docs/planning/phases.md`,
`docs/planning/repo-map.md`, `.github/aidd-config.yml`  
**Migration source:** `docs/planning/phases.md`, inline section
`PHASE-001 - Opening and Resuming a Source Edit`; migrated on 2026-08-21
with the phase content preserved.  
**Affected surfaces:** source import, media probing, GTK interface, FFmpeg
playback, project persistence, timeline state, and user-facing errors  

## Outcome

The user can open one supported video in the editor, view it in
real time, navigate its timeline, save the project, and reopen it with the
same source and state.

### Included

- Select the GUI/runtime and playback approach for the target Linux
  workstation, with evidence-based rationale.
- Import one source video and inspect the metadata needed by playback and
  export.
- Provide the primary editor view with real-time playback, play, pause, seek,
  current position, source duration, and timeline representation.
- Define and implement the initial versioned project representation for one
  source.
- Save and reopen the project without modifying the source.
- Surface missing media, unavailable tools, unsupported input, and playback
  failures clearly.

### Explicit non-goals

- Split, delete, reorder, or export behavior beyond what is required to prove
  the foundation.
- Multiple sources, multiple tracks, mixed-media normalization, composition,
  audio normalization, or FPS enhancement.
- Final GUI polish that does not improve the foundation outcome.

### Entry conditions

- OBJ-001, SCOPE-001, and CAP-MAP-001 are approved.
- The first-horizon one-source boundary is unchanged.
- The target workstation has `python3`, `ffmpeg`, and `ffprobe`.
- A decision record identifies the selected GUI/runtime and playback approach,
  its packaging/setup path, and known limitations.
- The project schema defines source identity, versioning, and behavior for a
  missing or moved source.
- A manual real-media smoke-test source is available without adding private
  media to the repository.

### Exit conditions

- One supported source can be imported and played through the primary
  interface with reliable play/pause/seek behavior on the target workstation.
- The timeline and preview expose consistent current position and duration.
- A save/reopen round trip restores source reference and edit foundation state.
- An invalid source or unavailable playback/tool path produces an explicit
  actionable error.
- Original media remains unchanged.
- Automated project/source/playback-state tests and target-workstation
  playback/persistence evidence are recorded.
- Existing repository tests remain green.

### Dependencies and risks

- Depends on the current FFmpeg/ffprobe toolchain and an unresolved GUI and
  playback decision.
- Real-time seeking may expose latency or variable-frame-rate limitations.
- Project paths may become stale when source files move.
- A poor initial schema could make future multi-source and linked-instance
  features difficult to add.

### Validation and evidence

- Project and source-model unit tests.
- Playback control and timeline-state tests where the chosen runtime permits.
- Manual target-workstation test using representative local media.
- Persistence round-trip evidence and source-preservation evidence.
- Record selected stack, versions, setup, and known limitations.

### Protected surfaces

`resolve_media.py`, `resolve_concat.py`, `resolve_fps.py`, their existing
commands, current tests, source-safe output behavior, and research documents
remain available and unchanged unless a separately approved change requires
otherwise.
