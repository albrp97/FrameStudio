# FEAT-019 - Delivering Focused Compositions Safely

**Feature ID:** FEAT-019
**Parent links:** OBJ-001, SCOPE-001, PHASE-006
**Capability links:** CAP-005, CAP-009, CAP-010, CAP-012
**Status:** complete
**Closure:** user-approved on 2026-08-23 after TICKET-044 through TICKET-047
passed implementation, automated and real-media verification, shared
target-workstation validation, review, and local delivery gates; remote checks
remain unavailable and are recorded as an accepted warning.
**Horizon:** future
**Priority:** 3
**Owner:** repository planning; maintainer identity is not recorded
**Approval:** user-authorized on 2026-08-22 to break down PHASE-006 and
authorize ticket implementation; the completed outcome was confirmed by the
user on 2026-08-23
**Source paths:** `vision.md`, `docs/specs/project-scope.md`,
`docs/specs/future-product-direction.md`,
`docs/planning/phases/open/PHASE-006-focusing-and-composing-important-action.md`,
`docs/planning/features.md`, `docs/specs/cli-contract.md`,
`.github/aidd-config.yml`
**Dependencies:** FEAT-017 transform state; FEAT-018 linked groups;
PHASE-005 delivery policy; fixed 1920x1080 output contract
**Risks:** preview and export can diverge, project migrations can lose linked
state, composition can invalidate stream copy, and an unverified output can
be exposed as complete
**Affected surfaces:** project schema, GUI controls, CLI payloads, preview
composition, FFmpeg render planning, output verification, source safety,
tests, documentation, and evidence
**Evidence path:** `evidence/phase-006-focused-composition-delivery.md`
**Planned tickets:** TICKET-044, TICKET-045, TICKET-046, TICKET-047
**Last updated:** 2026-08-23
**Path history:** `features/open/FEAT-019-delivering-focused-compositions-safely.md`
-> `features/closed/FEAT-019-delivering-focused-compositions-safely.md`

## Outcome

Focused segment modifications and linked triplicate compositions survive
save/reopen, remain inspectable through the GUI and CLI, and produce a
verified source-safe 1920x1080 output.

## Scope

- Persist transform bundles, triplicate groups, layout parameters, and
  versioned migration state.
- Keep GUI, CLI, reopened projects, preview, and export backed by the same
  domain representation.
- Route composed edits through the established safe fallback render when
  stream copy cannot preserve the requested visual changes.
- Verify dimensions, duration, streams, playability, placement, and source
  preservation before atomic publication.
- Provide end-to-end evidence for portrait and vertically focused landscape
  workflows, including failure and cancellation safety.

## Explicit non-goals

- Changing the established codec/container/render profile without approved
  evidence.
- Automatic FPS enhancement, audio-policy redesign, or arbitrary effects.
- Claiming visual equivalence from metadata alone.
- Publishing output before independent validation.

## Observable requirements

- Given a modified or triplicate project, save/reopen should restore all
  transform and linked-group state without changing source intervals.
- Given the same project, GUI and CLI inspection should expose equivalent
  modification values, group identities, and status.
- Given a composed edit, preview and final render should use the same
  coordinate and layout policy on the fixed 1920x1080 canvas.
- Given composition requires decoding, the exporter should explain the route
  and use the validated fallback rather than unsafe stream copy.
- Given encode, verification, cancellation, or publication failure, source
  media, project state, and the last valid output should remain intact.
- Given a successful export, dimensions, duration, streams, playability, and
  visual placement should satisfy the approved verification contract.

## Validation intent

- Exercise project round trips, CLI parity, preview, export, and failure
  cleanup with disposable portrait and vertical-action fixtures.
- Compare GUI and CLI state before and after save/reopen.
- Inspect output with ffprobe and review window-only visual evidence.
- Confirm original source hashes and the last valid output survive failures.

## Protected behavior

Existing project-schema compatibility, source identity, segment colors and
ordering, audio decisions, fixed 1920x1080 output, atomic publication,
structured errors, source preservation, and legacy scripts remain unchanged.

## Definition of done

- Transform and triplicate state round-trips through the project schema.
- GUI and CLI expose the same focused-composition domain state.
- Preview and verified output use the approved layout and safe render route.
- Automated, real-media, visual, source-safety, and user-validation evidence
  covers every PHASE-006 exit condition.

## Closure

TICKET-044 through TICKET-047 satisfy the focused-composition delivery
outcome under the reviewed PHASE-006 delivery checkpoint. Provider-side
checks remain unavailable because no remote or upstream is configured.
