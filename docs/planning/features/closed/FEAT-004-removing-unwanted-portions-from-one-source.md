# FEAT-004 - Removing Unwanted Portions from One Source

**Feature ID:** FEAT-004
**Parent links:** OBJ-001, SCOPE-001, PHASE-002
**Capability links:** CAP-003, CAP-012
**Status:** complete
**Closure:** user-approved on 2026-08-22 after successful implementation,
review evidence, and target-workstation validation; remote checks remain
unavailable and are recorded as an accepted warning.
**Path history:** `features/open/FEAT-004-removing-unwanted-portions-from-one-source.md`
-> `features/closed/FEAT-004-removing-unwanted-portions-from-one-source.md`
**Horizon:** first
**Owner:** repository planning; maintainer identity is not recorded
**Approval:** user-approved on 2026-08-21 as part of PHASE-002 planning
**Source paths:** `vision.md`, `docs/specs/project-scope.md`,
`docs/specs/capability-map.md`, `docs/planning/features.md`,
`docs/planning/phases/open/PHASE-002-cutting-and-exporting-one-source-safely.md`,
`.github/aidd-config.yml`
**Migration source:** `docs/planning/features.md`, inline section
`FEAT-004 - Removing Unwanted Portions from One Source`; migrated on
2026-08-21 with the feature content preserved.
**Affected surfaces:** segment model, timeline editing, duration display,
project state, playback position, and source-preservation behavior

## Outcome

Given one opened source, the user can split at a selected playhead position,
mark unwanted segments for deletion, reorder segment blocks, and see the
edited duration update without changing the original media.

### Included

- Define stable segment identity and the source timeline coordinate model.
- Split at the playhead or a selected timeline position.
- Represent ordered segments and deletion state non-destructively.
- Delete and restore segments while preserving valid ordering and boundaries.
- Move selected segment blocks left or right while preserving their source
  ranges and block-owned state.
- Show the resulting edited duration after repeated operations.
- Surface frame-accuracy, keyframe, timestamp, and variable-frame-rate
  limitations explicitly.

### Explicit non-goals

- Multiple source videos, multiple tracks, mixed-media normalization, or
  triplicate composition.
- Copy/paste, reusable modifications, or advanced effects.
- Export command execution beyond the state required by the export feature.
- Destructive source modification or deletion.

### Dependencies and risks

- Depends on the PHASE-001 project schema and playback timebase.
- Requires approved cut boundary, gap/ripple, and final-duration semantics.
- Keyframe boundaries and variable-frame-rate timestamps may prevent exact
  frame-accurate stream-copy cuts.

### Acceptance outcomes

- Given a valid playhead position, splitting creates two valid ordered
  segments.
- Given a segment selected for deletion, the edited duration excludes it and
  remains correct after repeated changes.
- Given invalid or boundary positions, the editor reports the reason and
  preserves the last valid edit.
- Given ordered one-source segments, moving a selected block left or right
  changes only its position while preserving its identity, state, color, and
  source interval.
- Given any edit operation, the original source remains unchanged.

### Evidence plan

- Unit tests for segment invariants, split/delete behavior, duration, and
  invalid-range recovery, and one-source block movement.
- Generated-media integration tests for representative cut boundaries.
- Manual target-workstation split/delete/duration/source-preservation flow.
