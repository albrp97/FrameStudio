# TICKET-007 - Establish the Non-Destructive Segment Model and Cut Semantics

**Ticket ID:** TICKET-007  
**Objective:** OBJ-001  
**Scope:** SCOPE-001  
**Phase:** PHASE-002  
**Feature:** FEAT-004  
**Capability links:** CAP-003, CAP-012  
**Status:** complete  
**Horizon:** first  
**Priority:** 1  
**Owner:** repository planning; implementer is not assigned  
**Approval:** user-approved on 2026-08-21 before execution  
**Provider:** auto; base and target branches are not configured in
`.github/aidd-config.yml`  
**Source paths:** `vision.md`, `docs/specs/project-scope.md`,
`docs/specs/capability-map.md`, `docs/planning/phases.md`,
`docs/planning/features/open/FEAT-004-removing-unwanted-portions-from-one-source.md`,
`docs/planning/tickets/closed/TICKET-006-save-reopen-recovery.md`,
`.github/aidd-config.yml`  
**Dependencies:** PHASE-001 project and timeline model; available source
duration/timebase metadata  
**Risks:** ambiguous frame boundaries, keyframe restrictions, variable-frame-rate
timestamps, accidental gaps or overlaps  
**Affected surfaces:** editor domain model, timeline timebase, project-schema
design, unit tests, cut-semantics documentation  
**Evidence path:** `evidence/segment-model-cut-semantics.md`

## Resolution

The non-destructive segment model and PHASE-002 cut-semantics policy are
implemented and locally verified. The source-time half-open interval,
strict-interior split, retained-segment ripple, edited-duration, stable
identifier, and failure-safe validation rules are documented and tested.

## Decision status

The cut-boundary, gap/ripple, and final-duration policy is accepted for
PHASE-002 implementation and recorded in
`docs/specs/phase-002-cut-semantics.md`. Downstream UI and FFmpeg layers must
use that policy rather than infer different behavior.

## Outcome

The editor has a stable, non-destructive representation of one source split
into ordered segments, including deletion state and the rules used to
calculate the edited duration.

## Scope

- Define stable segment identifiers and source-coordinate boundaries.
- Define whether boundaries are half-open, how source endpoints are handled,
  and how a requested position maps to a decodable frame.
- Define whether deletion ripples retained segments or preserves gaps.
- Represent ordered segments, deletion state, and the original source duration.
- Enforce no-overlap, valid-range, ordering, and duration invariants.
- Provide reversible delete/restore state transitions for future UI use.
- Document keyframe and variable-frame-rate limitations.

## Explicit non-goals

- GTK controls or timeline rendering.
- Export command execution, output validation, or output publication.
- Multiple sources, multiple tracks, clip movement, copy/paste, transforms,
  audio normalization, FPS enhancement, or CLI parity.
- Destructive changes to source media.

## Observable requirements

- Given a valid source duration, the initial segment state covers the source
  exactly and reports the source duration as the edited duration.
- Given a valid interior split position, the model creates exactly two
  ordered segments whose boundaries preserve the source coverage.
- Given a segment deletion or restoration, the edited duration reflects the
  retained segments according to the approved gap/ripple policy.
- Given an invalid, duplicate, or boundary split, the model returns an
  actionable validation error and preserves the last valid state.
- Given any segment edit, the source identity and source media remain
  unchanged.

## Validation and evidence

- Add focused unit tests for segment construction, split/delete/restore,
  ordering, duration, invalid ranges, and repeated operations.
- Run `python3 -m unittest discover -s tests`.
- Run `make check` and `git diff --check`.
- Record the approved cut semantics, test results, and known media limitations
  in `evidence/segment-model-cut-semantics.md`.

## Quality gates

- Baseline command is terminally evidenced before implementation.
- Local tests and compile/check targets pass.
- No configured remote-check infrastructure exists; this remains a
  PR-readiness concern rather than a local pass.

## Protected behavior

Existing scripts, command names, curses workflows, source-safe output
behavior, and all PHASE-001 tests remain available and unchanged unless a
compatibility-preserving model extension is required.

## Definition of done

- Cut-boundary, gap/ripple, and duration semantics are documented and
  approved.
- The segment model exposes stable identities and enforces its invariants.
- Split, delete, restore, and repeated-operation tests are passing.
- Invalid edits preserve the last valid state.
- No UI, export, or later-phase behavior is claimed.

## Completion evidence

- Focused model tests: `python3 -m unittest tests.test_editor_model`
- Initial full local gate: `make check` (64 tests passed, compilation and diff
  checks passed).
- Superseding review-fix gate: `make check` (65 tests passed, compilation and
  diff checks passed).
- Evidence record: `evidence/segment-model-cut-semantics.md`

## Review fix

The candidate-segment replacement path now restores the previous valid tuple
when validation fails. The regression is covered by the 12 focused model tests
and the superseding 65-test local gate.
