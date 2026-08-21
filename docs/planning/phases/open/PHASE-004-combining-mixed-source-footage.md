# PHASE-004 - Combining Mixed-Source Footage

**Phase ID:** PHASE-004  
**Parent links:** OBJ-001, SCOPE-001  
**Capability links:** CAP-002, CAP-003, CAP-005, CAP-007, CAP-012  
**Sequence:** 4  
**Status:** confirmed  
**Horizon:** future  
**Owner:** repository planning; maintainer identity is not recorded  
**Approval:** user-approved on 2026-08-21 before feature generation  
**Source paths:** `vision.md`, `docs/specs/project-scope.md`,
`docs/specs/capability-map.md`, `docs/planning/phases.md`,
`docs/planning/repo-map.md`, `.github/aidd-config.yml`  
**Migration source:** `docs/planning/phases.md`, inline section
`PHASE-004 - Combining Mixed-Source Footage`; migrated on 2026-08-21 with
the phase content preserved.  
**Affected surfaces:** multi-source import, timeline identity and placement,
clip movement, selection, mixed-media preview, normalization, export, and
persistence  

## Outcome

The user can build one composed timeline from multiple videos
with different dimensions, orientations, frame rates, codecs, and audio
characteristics while preserving clear order, timing, and final duration.

### Included

- Import several source videos into one project.
- Represent clip identity, order, source boundaries, gaps, and timeline
  placement.
- Move clips or segments left/right and keep final duration visible.
- Select several segments for shared timeline operations.
- Preview the composed result in real time with clear source boundaries.
- Define aspect-ratio, scaling, timing, and normalization behavior for mixed
  inputs.
- Export a valid composed result using the fastest applicable path.
- Preserve source-level versus segment-level settings.

### Explicit non-goals

- Triplicate focused-action composition.
- Automatic per-input audio-level handling beyond preserving or explicitly
  reporting source audio.
- 60 FPS enhancement.
- Full multi-track professional-NLE behavior unless separately approved.

### Entry conditions

- PHASE-003 has a stable project/CLI identity and error contract.
- A multi-source timeline/timebase model is approved.
- Representative mixed-dimension and mixed-frame-rate media is available
  locally for testing.
- The output canvas, timing, ordering, gap, and normalization policies are
  explicitly defined.

### Exit conditions

- Multiple sources with deliberately different media parameters can be
  ordered, previewed, edited, and reopened without losing identity.
- Moving clips/segments and deleting them updates final duration correctly.
- The exporter reports required normalization and produces verified output.
- Mixed-source playback, persistence, CLI, and export evidence exists.
- Original sources remain unchanged and existing workflows remain functional.

### Dependencies and risks

- Depends on timeline model and project schema from the first horizon.
- Mixed timebases, variable frame rates, aspect ratios, and audio clocks may
  introduce sync or duration drift.
- Normalization can remove stream-copy eligibility and increase render cost.

### Validation and evidence

- Mixed-source project/timeline invariant tests.
- Generated and representative real-media integration tests.
- Manual playback, ordering, movement, final-duration, save/reopen, and
  export evidence.
- Output metadata and normalization decision evidence.
