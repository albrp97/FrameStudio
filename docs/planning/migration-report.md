# Planning Lifecycle Migration Report

**Migration:** flat/inline planning records to open/closed lifecycle records  
**Status:** complete with existing delivery findings preserved  
**Owner:** repository planning; maintainer identity is not recorded  
**Approval:** user-approved on 2026-08-21 after the migration inventory, with
the clarification that phases, features, and tickets each use one index plus
separate `open/` and `closed/` record directories  
**Configuration:** `.github/aidd-config.yml`  
**Target revision:** working tree after the approved migration  

## Scope and source of truth

This migration changed only planning organization. The authoritative planning
hierarchy remains:

`objective -> scope -> capability -> phase -> feature -> ticket`

The source records were:

- `docs/planning/phases.md`, containing seven inline phase records.
- `docs/planning/features.md`, containing six inline feature records and two
  feature-index metadata sections.
- `docs/planning/backlog.md`, containing two backlog metadata sections and
  ticket summaries.
- `docs/planning/tickets/`, containing eleven flat ticket records before the
  approved moves.

The synchronized indexes remain `docs/planning/phases.md`,
`docs/planning/features.md`, and `docs/planning/backlog.md`. Individual
records now live below their configured lifecycle directories.

## Configuration applied

The existing lifecycle configuration was preserved and used:

- `docs/planning/phases/open/` and `docs/planning/phases/closed/`
- `docs/planning/features/open/` and `docs/planning/features/closed/`
- `docs/planning/tickets/open/` and `docs/planning/tickets/closed/`
- `{id}-{slug}.md` naming
- move-on-status-change
- synchronized indexes
- path-history preservation

No repository-specific commands, gates, provider settings, approval policy,
or unrelated configuration was changed.

## Migration inventory

### Phases

| ID | Source section | Original status | Normalized status | Parent links | Destination | Action |
|---|---|---|---|---|---|---|
| PHASE-001 | `docs/planning/phases.md`, inline `PHASE-001` | confirmed | open | OBJ-001, SCOPE-001 | `docs/planning/phases/open/PHASE-001-opening-and-resuming-a-source-edit.md` | extract record and add migration source note |
| PHASE-002 | `docs/planning/phases.md`, inline `PHASE-002` | confirmed | open | OBJ-001, SCOPE-001 | `docs/planning/phases/open/PHASE-002-cutting-and-exporting-one-source-safely.md` | extract record and add migration source note |
| PHASE-003 | `docs/planning/phases.md`, inline `PHASE-003` | confirmed | open | OBJ-001, SCOPE-001 | `docs/planning/phases/open/PHASE-003-repeating-the-basic-edit-through-agents.md` | extract record and add migration source note |
| PHASE-004 | `docs/planning/phases.md`, inline `PHASE-004` | confirmed | open | OBJ-001, SCOPE-001 | `docs/planning/phases/open/PHASE-004-combining-mixed-source-footage.md` | extract record and add migration source note |
| PHASE-005 | `docs/planning/phases.md`, inline `PHASE-005` | confirmed | open | OBJ-001, SCOPE-001 | `docs/planning/phases/open/PHASE-005-balancing-sources-and-delivering-consistent-media.md` | extract record and add migration source note |
| PHASE-006 | `docs/planning/phases.md`, inline `PHASE-006` | confirmed | open | OBJ-001, SCOPE-001 | `docs/planning/phases/open/PHASE-006-focusing-and-composing-important-action.md` | extract record and add migration source note |
| PHASE-007 | `docs/planning/phases.md`, inline `PHASE-007` | confirmed | open | OBJ-001, SCOPE-001 | `docs/planning/phases/open/PHASE-007-producing-validated-60-fps-edits.md` | extract record and add migration source note |

### Features

| ID | Source section | Original status | Normalized status | Parent links | Destination | Action |
|---|---|---|---|---|---|---|
| FEAT-001 | `docs/planning/features.md`, inline `FEAT-001` | confirmed | open | OBJ-001, SCOPE-001, PHASE-001 | `docs/planning/features/open/FEAT-001-opening-a-supported-source-as-a-non-destructive-project.md` | extract record and add migration source note |
| FEAT-002 | `docs/planning/features.md`, inline `FEAT-002` | confirmed | open | OBJ-001, SCOPE-001, PHASE-001 | `docs/planning/features/open/FEAT-002-controlling-playback-and-navigating-the-source-timeline.md` | extract record and add migration source note |
| FEAT-003 | `docs/planning/features.md`, inline `FEAT-003` | confirmed | open | OBJ-001, SCOPE-001, PHASE-001 | `docs/planning/features/open/FEAT-003-saving-and-reopening-the-source-edit-foundation.md` | extract record and add migration source note |
| FEAT-004 | `docs/planning/features.md`, inline `FEAT-004` | confirmed | open | OBJ-001, SCOPE-001, PHASE-002 | `docs/planning/features/open/FEAT-004-removing-unwanted-portions-from-one-source.md` | extract record and add migration source note |
| FEAT-005 | `docs/planning/features.md`, inline `FEAT-005` | confirmed | open | OBJ-001, SCOPE-001, PHASE-002 | `docs/planning/features/open/FEAT-005-exporting-a-verified-edited-video.md` | extract record and add migration source note |
| FEAT-006 | `docs/planning/features.md`, inline `FEAT-006` | confirmed | open | OBJ-001, SCOPE-001, PHASE-002 | `docs/planning/features/open/FEAT-006-preserving-and-recovering-saved-cut-decisions.md` | extract record and add migration source note |

### Tickets

| ID | Original path | Original status | Normalized status | Parent links | Destination | Action |
|---|---|---|---|---|---|---|
| TICKET-001 | `docs/planning/tickets/TICKET-001-editor-foundation-contract.md` | complete | closed | PHASE-001, FEAT-001 | `docs/planning/tickets/closed/TICKET-001-editor-foundation-contract.md` | move existing record |
| TICKET-002 | `docs/planning/tickets/TICKET-002-open-supported-source.md` | complete | closed | PHASE-001, FEAT-001 | `docs/planning/tickets/closed/TICKET-002-open-supported-source.md` | move existing record |
| TICKET-003 | `docs/planning/tickets/TICKET-003-playback-control-state.md` | complete | closed | PHASE-001, FEAT-002 | `docs/planning/tickets/closed/TICKET-003-playback-control-state.md` | move existing record |
| TICKET-004 | `docs/planning/tickets/TICKET-004-preview-timeline-interaction.md` | complete | closed | PHASE-001, FEAT-002 | `docs/planning/tickets/closed/TICKET-004-preview-timeline-interaction.md` | move existing record |
| TICKET-005 | `docs/planning/tickets/TICKET-005-versioned-project-persistence.md` | complete | closed | PHASE-001, FEAT-003 | `docs/planning/tickets/closed/TICKET-005-versioned-project-persistence.md` | move existing record |
| TICKET-006 | `docs/planning/tickets/TICKET-006-save-reopen-recovery.md` | complete | closed | PHASE-001, FEAT-003 | `docs/planning/tickets/closed/TICKET-006-save-reopen-recovery.md` | move existing record |
| TICKET-007 | `docs/planning/tickets/TICKET-007-segment-model-and-cut-semantics.md` | complete | closed | PHASE-002, FEAT-004 | `docs/planning/tickets/closed/TICKET-007-segment-model-and-cut-semantics.md` | move existing record |
| TICKET-008 | `docs/planning/tickets/TICKET-008-split-delete-editor-workflow.md` | complete | closed | PHASE-002, FEAT-004 | `docs/planning/tickets/closed/TICKET-008-split-delete-editor-workflow.md` | move existing record |
| TICKET-009 | `docs/planning/tickets/TICKET-009-persist-cut-state-recovery.md` | complete | closed | PHASE-002, FEAT-006 | `docs/planning/tickets/closed/TICKET-009-persist-cut-state-recovery.md` | move existing record |
| TICKET-010 | `docs/planning/tickets/TICKET-010-export-plan-selection.md` | complete | closed | PHASE-002, FEAT-005 | `docs/planning/tickets/closed/TICKET-010-export-plan-selection.md` | move existing record |
| TICKET-011 | `docs/planning/tickets/TICKET-011-verified-safe-export.md` | needs-review | complete | PHASE-002, FEAT-005 | `docs/planning/tickets/closed/TICKET-011-verified-safe-export.md` | move existing record; later gated, then completed by explicit user authorization |

## Status normalization

The configured lifecycle mapping was applied without changing record meaning:

| Original status | Lifecycle classification | Records |
|---|---|---|
| confirmed | open | PHASE-001 through PHASE-007; FEAT-001 through FEAT-006 |
| complete | closed | TICKET-001 through TICKET-011 current lifecycle state |
| needs-review | open | TICKET-011 at migration time |
| gated | open | TICKET-011 intermediate lifecycle state |
| blocked | open | none |
| cancelled | closed | none |

## Preserved metadata and findings

- `FEAT-INDEX-001` and `FEAT-INDEX-002` remain in `features.md` as feature
  index metadata, not invented feature records.
- `BACKLOG-001` and `BACKLOG-002` remain in `backlog.md` as backlog metadata,
  not invented ticket records.
- The capability map's pre-existing `draft` entries were not silently
  normalized even though the surrounding map is confirmed.
- Existing ticket content, evidence paths, stable IDs, parent links, and
  status values were preserved. Internal references now point to the new
  closed/open ticket paths.
- No phase or feature was closed because all were `confirmed`.
- The legacy flat ticket directory is empty after the approved moves. No
  additional legacy planning source or `plan.md` was discovered.

## Validation evidence

The final read-only review confirmed:

- seven phase records exist in `phases/open/`, with no duplicate phase IDs;
- six feature records exist in `features/open/`, with no duplicate feature IDs;
- eleven complete tickets exist in `tickets/closed/`, including TICKET-011;
- no individual ticket records remain in `tickets/open/`;
- indexes list every phase, feature, and ticket with current relative paths;
- no ticket references the old flat `docs/planning/tickets/` path;
- phase, feature, and ticket parent links resolve to the existing planning
  hierarchy;
- status/path classification is consistent for all individual records;
- application code, delivery evidence, and unrelated project files were not
  changed by this migration.

The configured remote checks remain unavailable in the repository, as already
recorded by the active export ticket; this is a pre-existing delivery finding,
not a planning-structure migration failure.

## Post-migration lifecycle update

TICKET-011 moved from `needs-review` to `gated` after the maintainer confirmed
the documented target-workstation export flow, then to `complete` and the closed
directory after explicit user authorization. Its stable ID, parent links,
original migration status, evidence, and file identity were preserved; the
current status and path are synchronized in the ticket record, backlog
indexes, and evidence record. Remote checks and required screenshot artifacts
remain unavailable and are not claimed as passed.
