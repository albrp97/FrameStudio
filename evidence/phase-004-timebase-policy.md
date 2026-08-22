# Delivery Evidence: TICKET-020

- Phase: `PHASE-004` - Combining Mixed-Source Footage
- Feature: `FEAT-011` - Arranging and Editing a Mixed-Source Timeline
- Ticket: `TICKET-020` - Define Mixed-Source Timebase and Placement Semantics
- Status: `verifying`
- Branch: `ticket/phase-004-mixed-source-footage`
- Evidence path: `evidence/phase-004-timebase-policy.md`

## Approved and implemented policy

- The canonical project timebase is `1/1000000` timeline ticks.
- Seconds-to-ticks conversion uses deterministic half-up rounding.
- Mixed sources are placed sequentially with ripple enabled by default.
- Each block owns a source interval and timeline interval; movement does not
  alter source coverage or block-owned state.
- Copy/paste inserts fresh identities at the requested timeline cursor while
  preserving relative order and cloned state.
- Splitting creates fresh child identities that inherit deletion state and
  block-owned state.
- Deleted blocks remain visible, are excluded from edited duration, and remain
  reversible.
- Mixed output duration is the sum of included block durations after timeline
  placement and validation.

## Evidence entries

### INVARIANTS-001

- Evidence: `resolve_editor/model.py`,
  `tests/test_editor_mixed_source.py`, and
  `docs/planning/reviews/CHG-001-atomic-segment-block-editing.md`.
- Observed: Mixed-source identity, timebase, placement, split inheritance,
  copy/paste fresh identity, movement, deletion, and duration invariants pass.
- Status: `passed`

### SCENARIO-001

- Flow: Apply the atomic sequence from `s1 s2 s3 s4`, including deletion,
  copy/paste, insertion at the beginning, and movement.
- Observed: CLI and domain results preserve source intervals and produce fresh
  pasted IDs while keeping the original blocks independent.
- Status: `passed`

### USER-001

- Required: Maintainer confirmation of ordering, ripple, gap, and duration
  choices against the documented examples.
- Status: `pending`
