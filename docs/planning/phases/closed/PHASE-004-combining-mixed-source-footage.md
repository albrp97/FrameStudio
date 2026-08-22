# PHASE-004 - Combining Mixed-Source Footage

**Phase ID:** PHASE-004
**Parent links:** OBJ-001, SCOPE-001
**Capability links:** CAP-002, CAP-003, CAP-005, CAP-007, CAP-012
**Sequence:** 4
**Status:** complete
**Closure:** user-approved on 2026-08-22 after successful implementation,
review evidence, and target-workstation validation; remote checks remain
unavailable and are recorded as an accepted warning.
**Path history:** `phases/open/PHASE-004-combining-mixed-source-footage.md`
-> `phases/closed/PHASE-004-combining-mixed-source-footage.md`
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
atomic segment-block movement and copy/paste, selection, mixed-media preview,
normalization, export, and persistence

## Outcome

The user can build one composed timeline from multiple videos with different
dimensions, orientations, frame rates, codecs, and audio characteristics while
preserving clear order, timing, final duration, atomic segment-block behavior,
and a fixed 1920x1080 project render canvas.

### Included

- Import several source videos into one project.
- Represent clip identity, order, source boundaries, gaps, and timeline
  placement.
- Treat segments as atomic blocks that can move left/right without changing
  their source ranges or owned state.
- Copy and paste one or several blocks at an explicit timeline cursor with
  fresh segment identities, preserved relative order, and unchanged originals.
- Split blocks into fresh child identities that inherit the parent's
  segment-owned state, including any state fields reserved for later visual
  modifications.
- Preserve each block's display color through movement, copy/paste,
  delete/restore, and persistence; split children receive fresh colors.
- Select several segments for shared timeline operations.
- Preview the composed result in real time with clear source boundaries.
- Contain-scale mixed inputs into the fixed 1920x1080 canvas without silently
  stretching or cropping them.
- Use the established render profile for output container, codecs, audio, and
  pixel format rather than deriving those settings from input codecs.
- Preserve deterministic current timing while deferring 60 FPS enhancement to
  PHASE-007.
- Export a valid composed result using the fastest applicable path.
- Preserve source-level versus segment-level settings.

### Explicit non-goals

- Triplicate focused-action composition.
- Authoring or cleaning visual modification bundles; PHASE-004 preserves
  block-owned state so PHASE-006 can define those controls.
- Automatic per-input audio-level handling beyond preserving or explicitly
  reporting source audio.
- 60 FPS enhancement and a final 60 FPS timing policy.
- Full multi-track professional-NLE behavior unless separately approved.

### Entry conditions

- PHASE-003 has a stable project/CLI identity and error contract.
- A multi-source timeline/timebase model is approved.
- Atomic block movement, insertion, copy/paste, and split-inheritance rules
  are explicit.
- Representative mixed-dimension and mixed-frame-rate media is available
  locally for testing.
- The fixed 1920x1080 output canvas, timing, ordering, gap, and established
  render profile are explicitly defined.

### Exit conditions

- Multiple sources with deliberately different media parameters can be
  ordered, previewed, edited, and reopened without losing identity.
- Moving, copying, pasting, splitting, and deleting blocks updates final
  duration correctly while preserving source identity and block state.
- The exporter uses the fixed 1920x1080 canvas and established render profile
  and produces verified output.
- Mixed-source playback, persistence, CLI, and export evidence exists.
- Original sources remain unchanged and existing workflows remain functional.

### Dependencies and risks

- Depends on timeline model and project schema from the first horizon.
- Mixed timebases, variable frame rates, aspect ratios, and audio clocks may
  introduce sync or duration drift.
- Copy/paste and split operations can duplicate identities or silently drop
  segment-owned state if clone rules are incomplete.
- Fixed-canvas composition removes stream-copy eligibility for mixed output and
  increases render cost.

### Validation and evidence

- Mixed-source project/timeline invariant tests.
- Generated and representative real-media integration tests.
- Manual playback, ordering, block movement/copy/paste, final-duration,
  save/reopen, and export evidence.
- Output metadata and normalization decision evidence.

## Current delivery state

- TICKET-018 through TICKET-029 completed local implementation, contract,
  quality, real-media, and applicable target-workstation verification.
- CHG-002 replaced the prior maximum-dimension mixed-output policy with a fixed
  1920x1080 render canvas; mixed output-policy and export evidence reflect this
  revision.
- GUI evidence is captured under `evidence/screenshots/` and the per-ticket
  records under `evidence/phase-004-*.md`.
- The user approved closure on 2026-08-22. The completed Phase 4 records moved
  to `closed`; unavailable configured remote checks remain an accepted warning.
