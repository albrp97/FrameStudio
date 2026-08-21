# FEAT-001 — Opening a Supported Source as a Non-Destructive Project

**Feature ID:** FEAT-001  
**Parent links:** OBJ-001, SCOPE-001, PHASE-001  
**Capability links:** CAP-001, CAP-012  
**Status:** confirmed  
**Horizon:** first  
**Owner:** repository planning; maintainer identity is not recorded  
**Approval:** user-approved on 2026-08-21 as part of PHASE-001 planning  
**Source paths:** `vision.md`, `docs/specs/project-scope.md`,
`docs/specs/capability-map.md`, `docs/planning/features.md`,
`docs/planning/phases/open/PHASE-001-opening-and-resuming-a-source-edit.md`,
`.github/aidd-config.yml`  
**Migration source:** `docs/planning/features.md`, inline section
`FEAT-001 — Opening a Supported Source as a Non-Destructive Project`;
migrated on 2026-08-21 with the feature content preserved.  
**Affected surfaces:** project/source model, media probing, editor open flow,
error presentation, FFmpeg integration, and protected existing scripts/tests  

## Outcome

Given one supported source video, the user can open it as an
editor project with a clear source identity and the metadata needed by the
preview and timeline, without changing the source.

### Included

- Select or provide one source video to the editor.
- Inspect the source with the available FFmpeg/ffprobe toolchain.
- Establish the initial project identity and source reference.
- Expose the source metadata needed for playback, duration, and later export
  planning.
- Surface missing, unreadable, unsupported, or incomplete source metadata as
  actionable errors.
- Keep project state separate from the original media.

### Explicit non-goals

- Splitting, deleting, reordering, or exporting edited segments.
- Multiple source videos, tracks, mixed-media normalization, or composition.
- Automatic audio-level handling, visual transforms, or FPS enhancement.
- Replacing or removing the existing media-preparation scripts.

### Dependencies and risks

- Depends on the PHASE-001 GUI/runtime and media-access entry decisions.
- Depends on `python3`, `ffmpeg`, `ffprobe`, and a versioned source model.
- Source paths may become stale when files move or are renamed.
- Variable-frame-rate media or incomplete metadata may make duration and
  position semantics ambiguous.

### Acceptance outcomes

- Given a supported source, opening it creates a project with an identifiable
  source reference and the required metadata.
- Given a missing, unreadable, or unsupported source, the editor reports the
  reason and leaves the source and last valid project state unchanged.
- Given a source opened by the editor, the original file remains untouched.

### Evidence plan

- Unit tests for source metadata mapping and project initialization.
- Error-path tests for missing and unsupported media.
- Manual target-workstation import smoke test using representative local
  media, with private paths omitted from durable evidence.
- Record the selected media-tool versions and known metadata limitations.

### Protected behavior

Existing commands, `resolve_media.py`, `resolve_concat.py`,
`resolve_fps.py`, their tests, and source-safe output behavior remain
available and unchanged.
