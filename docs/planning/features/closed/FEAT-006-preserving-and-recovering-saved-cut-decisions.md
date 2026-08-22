# FEAT-006 - Preserving and Recovering Saved Cut Decisions

**Feature ID:** FEAT-006
**Parent links:** OBJ-001, SCOPE-001, PHASE-002
**Capability links:** CAP-004, CAP-012
**Status:** complete
**Closure:** user-approved on 2026-08-22 after successful implementation,
review evidence, and target-workstation validation; remote checks remain
unavailable and are recorded as an accepted warning.
**Path history:** `features/open/FEAT-006-preserving-and-recovering-saved-cut-decisions.md`
-> `features/closed/FEAT-006-preserving-and-recovering-saved-cut-decisions.md`
**Horizon:** first
**Owner:** repository planning; maintainer identity is not recorded
**Approval:** user-approved on 2026-08-21 as part of PHASE-002 planning
**Source paths:** `vision.md`, `docs/specs/project-scope.md`,
`docs/specs/capability-map.md`, `docs/planning/features.md`,
`docs/planning/phases/open/PHASE-002-cutting-and-exporting-one-source-safely.md`,
`.github/aidd-config.yml`
**Migration source:** `docs/planning/features.md`, inline section
`FEAT-006 - Preserving and Recovering Saved Cut Decisions`; migrated on
2026-08-21 with the feature content preserved.
**Affected surfaces:** versioned project representation, segment persistence,
save/reopen flows, schema migration, recovery behavior, and source identity

## Outcome

Given a cut project, saving and reopening restores its segment
decisions and edited duration, while failed writes preserve the last valid
project.

### Included

- Extend the versioned project representation with ordered segment and
  deletion state.
- Restore playhead, segment boundaries, deletion state, and edited duration.
- Keep source identity and original media separate from edit state.
- Preserve the last valid project on invalid, interrupted, or failed saves.
- Define compatibility behavior for projects that predate segment state.

### Explicit non-goals

- Multiple-source project schema, multiple tracks, CLI parity, or future
  composition and audio settings.
- Silent source relinking or destructive migration.

### Dependencies and risks

- Depends on FEAT-004 segment identity and the PHASE-001 persistence
  boundary.
- Schema evolution could invalidate earlier projects if compatibility rules
  are not explicit.
- Recovery behavior must not expose a partial project as valid.

### Acceptance outcomes

- Given a saved cut project, reopening restores segment order, deletion state,
  playhead, and edited duration.
- Given an invalid or incompatible project, the editor reports an actionable
  error and preserves the last valid state.
- Given a failed save, the valid project remains reopenable.

### Evidence plan

- Serialization, migration-boundary, round-trip, and failed-write tests.
- Integration tests combining cut state with save/reopen status.
- Manual save/reopen/recovery/source-preservation flow.
