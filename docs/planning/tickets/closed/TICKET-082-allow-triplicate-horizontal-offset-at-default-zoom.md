# TICKET-082 - Allow Triplicate Horizontal Offset at Default Zoom

**Ticket ID:** TICKET-082
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-008
**Feature:** FEAT-025
**Capability links:** CAP-003, CAP-009, CAP-010, CAP-012
**Status:** complete
**Horizon:** future
**Priority:** 2
**Owner:** repository implementation in the active worktree
**Approval:** User-requested composition correction; execution remains subject
to the configured evidence, review, user-validation, and delivery gates
**Last updated:** 2026-08-28
**Source paths:** `docs/planning/features/open/FEAT-025-streamlining-segment-focus-modifications.md`,
`docs/planning/tickets/closed/TICKET-067-correct-zoomed-focus-coordinate-bounds.md`,
`docs/planning/tickets/closed/TICKET-068-verify-focus-control-persistence-and-parity.md`,
`resolve_editor/composition.py`, `resolve_editor/composition_render.py`,
`resolve_editor/app_timeline_actions.py`, `resolve_editor/operations.py`,
`tests/test_editor_composition.py`, `tests/test_editor_cli_parity.py`,
`tests/test_editor_persistence.py`, `.github/aidd-config.yml`
**Dependencies:** existing focus bounds and triplicate composition semantics;
versioned project persistence; deterministic CLI focus operation
**Risks:** default-zoom crops use a narrower triplicate slot than normal
segments, and changing shared bounds could affect normal focus controls or
portrait preserve-resolution rendering
**Affected surfaces:** transform validation, GTK focus controls, CLI and
project persistence, preview/export filter graphs, and generated-media tests
**Evidence path:** `evidence/ticket-082-triplicate-default-zoom-offset.md`
**Path history:** created at
`tickets/open/TICKET-082-allow-triplicate-horizontal-offset-at-default-zoom.md`
-> moved to
`tickets/closed/TICKET-082-allow-triplicate-horizontal-offset-at-default-zoom.md`
**Protected behaviors:** existing normal transforms, 2x/4x focus bounds,
triplicate linkage, fixed 1920x1080 output, source preservation, and safe
export

## Objective

Allow a triplicated segment at the default `1.0x` zoom to select a different
horizontal source region so the repeated content can be moved left or right.

## Observable requirements

- Given an enabled triplicate segment at `1.0x` zoom, the focus X control and
  CLI operation should accept bounded negative and positive offsets and the
  shared triplicate crop should move horizontally.
- Given the default zoom with no triplicate composition, existing normal
  rendering and focus behavior should remain unchanged.
- Given zoom `2.0x` or `4.0x`, the established fixed-canvas offset bounds and
  coordinate mapping should remain unchanged.
- Given a saved project containing a default-zoom triplicate offset,
  save/reopen and CLI inspection should preserve the same transform and group
  linkage.
- Given an out-of-range default-zoom offset, the existing clamp/error
  contract should preserve valid project state.

## Scope

- Extend the default-zoom horizontal bounds needed by the triplicate crop.
- Keep vertical default-zoom offsets unavailable because the triplicate crop
  already spans the output height.
- Expose the resulting range through the existing GTK controls and shared
  domain/CLI operation.
- Add filter-graph, persistence, CLI-parity, and generated-media coverage.

## Explicit non-goals

- Changing triplicate slot layout, output dimensions, or role ordering.
- Adding arbitrary translation independent of source cropping.
- Changing zoom `2.0x` through `8.0x` coordinate semantics.
- Adding a new project schema version or a second offset field.

## Validation

- Focused composition, operations, CLI-parity, persistence, and UI-control
  tests for default-zoom horizontal offsets.
- Existing `make test`, `make contract`, `make smoke`, and `make check`.
- A target-workstation triplicate preview/export check with left, centered,
  and right default-zoom positions, including source-preservation evidence.

## User-validation plan

- **Setup:** open a project with a landscape or portrait segment and enable
  triplicate mode.
- **Steps:** leave Zoom at `1.00x`, move X to negative and positive values,
  inspect the preview, save/reopen, and repeat through the CLI.
- **Expected result:** the triplicated source region moves left or right while
  the three-column layout remains intact.
- **Failure paths:** disabled X control, unchanged preview, inverted movement,
  broken linkage, lost persistence, invalid crop, or source modification
  block the ticket.
- **Cleanup:** restore X to zero or remove only temporary project/output
  artifacts.
- **Evidence response:** return `PASS`, `FAIL`, `BLOCKED`, or approved
  `NOT APPLICABLE` with observed positions and output metadata.
- **Pass criteria:** default-zoom horizontal movement is visible and remains
  consistent across GUI, CLI, persistence, preview, and export.

## Definition of done

- Default-zoom triplicate horizontal offsets are bounded, persisted, and
  rendered consistently.
- Existing focus and triplicate regression coverage remains passing.
- Required technical and user-validation evidence is terminal before closure.

## Closure

TICKET-082 is complete. The user confirmed the default-zoom triplicate
horizontal-offset behavior was manually validated and requested closure of
all tickets on 2026-08-28. Existing remote-parity and target-workstation
limitations remain documented in the evidence record.
