# FEAT-003 — Saving and Reopening the Source Edit Foundation

**Feature ID:** FEAT-003
**Parent links:** OBJ-001, SCOPE-001, PHASE-001
**Capability links:** CAP-004, CAP-012
**Status:** complete
**Closure:** user-approved on 2026-08-22 after successful implementation,
review evidence, and target-workstation validation; remote checks remain
unavailable and are recorded as an accepted warning.
**Path history:** `features/open/FEAT-003-saving-and-reopening-the-source-edit-foundation.md`
-> `features/closed/FEAT-003-saving-and-reopening-the-source-edit-foundation.md`
**Horizon:** first
**Owner:** repository planning; maintainer identity is not recorded
**Approval:** user-approved on 2026-08-21 as part of PHASE-001 planning
**Source paths:** `vision.md`, `docs/specs/project-scope.md`,
`docs/specs/capability-map.md`, `docs/planning/features.md`,
`docs/planning/phases/open/PHASE-001-opening-and-resuming-a-source-edit.md`,
`.github/aidd-config.yml`
**Migration source:** `docs/planning/features.md`, inline section
`FEAT-003 — Saving and Reopening the Source Edit Foundation`; migrated on
2026-08-21 with the feature content preserved.
**Affected surfaces:** project serialization and migration boundary, editor
open/save flows, filesystem error handling, source model, and future CLI
compatibility

## Outcome

Given an opened source project, the user can save a versioned
machine-readable project and later reopen it with the same source reference,
foundation timeline state, and safe failure behavior.

### Included

- Define the initial versioned project representation for one source.
- Persist source identity, source metadata needed for reopening, and
  foundation playback/timeline state.
- Save through a partial/temporary file and expose the project only after a
  successful write.
- Reopen a saved project and restore its valid state and duration.
- Report invalid, incompatible, missing-source, or moved-source conditions
  without overwriting the last valid project.
- Keep future schema evolution possible without pulling future editing
  features into this phase.

### Explicit non-goals

- Persisting split/delete/export behavior beyond the foundation state needed
  to prove the round trip.
- Multi-source timelines, multiple tracks, triplicate links, transforms,
  audio decisions, or FPS settings.
- Destructive source modification or silent source relinking.

### Dependencies and risks

- Depends on FEAT-001 source identity and the PHASE-001 schema/relinking
  entry decision.
- Depends on an atomic local filesystem write strategy.
- Partial writes, schema incompatibility, and moved sources can otherwise
  lose or misinterpret user state.
- The initial schema must leave room for later segments, source-level
  settings, and linked instances without claiming those features are ready.

### Acceptance outcomes

- Given a valid open project, saving creates a versioned machine-readable
  project without changing the source media.
- Given a saved project, reopening restores the source reference, foundation
  state, and duration.
- Given an invalid project or unavailable source, the editor reports the
  reason and preserves the last valid project state.
- A failed or interrupted save does not replace a previously valid project.

### Evidence plan

- Unit tests for serialization, version checks, round trips, and atomic-save
  failure paths.
- Manual save/reopen smoke test on the target workstation.
- Source-preservation evidence and project-file validity evidence with
  sensitive local paths redacted where possible.

### Protected behavior

Original media remains untouched, existing scripts and tests remain green,
and the editor's project files remain separate from source media.
