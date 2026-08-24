# FEAT-016 - Synchronizing Media Decisions and Verification

**Feature ID:** FEAT-016
**Parent links:** OBJ-001, SCOPE-001, PHASE-005
**Capability links:** CAP-005, CAP-008, CAP-012
**Status:** complete
**Closure:** user-approved on 2026-08-22 after TICKET-036 and TICKET-037
passed implementation, automated, real-media, review, user-validation, and
local delivery gates; remote checks remain unavailable and are recorded as an
accepted warning.
**Horizon:** future
**Priority:** 3
**Owner:** repository planning and implementation in the active worktree
**Approval:** user-authorized on 2026-08-22 to implement and close the
approved PHASE-005 ticket set after validation
**Source paths:** `vision.md`, `docs/specs/project-scope.md`,
`docs/specs/capability-map.md`,
`docs/specs/future-product-direction.md`,
`docs/planning/phases/open/PHASE-005-balancing-sources-and-delivering-consistent-media.md`,
`docs/specs/cli-contract.md`, `.github/aidd-config.yml`
**Dependencies:** FEAT-014 source decisions; FEAT-015 delivery routes;
PHASE-004 GUI/CLI parity and project persistence
**Risks:** GUI, CLI, project state, and rendered output can drift; metadata
alone cannot prove perceived audio balance; manual listening coverage is
environment-dependent
**Affected surfaces:** project schema/state, GUI controls, CLI payloads,
preview, export, output validation, source-preservation checks, and evidence
**Evidence path:** `evidence/phase-005-media-decision-surfaces.md`
**Planned tickets:** TICKET-036, TICKET-037
**Last updated:** 2026-08-22
**Path history:** `features/open/FEAT-016-synchronizing-media-decisions-and-verification.md`
-> `features/closed/FEAT-016-synchronizing-media-decisions-and-verification.md`

## Outcome

The user can inspect the same source-level audio and delivery decisions in the
GUI, CLI, project file, and verified output, with clear evidence when the
media result is safe and consistent.

## Scope

- Expose source-level audio analysis results, applied gain/normalization
  decisions, failures, overrides, and delivery route in project state.
- Keep GUI and CLI inspection/reporting aligned with shared domain behavior.
- Verify audio peaks, expected channels, duration, output metadata, playability,
  and source preservation on representative mixed-source edits.
- Record manual listening and target-workstation limitations explicitly.

## Explicit non-goals

- Introducing a second audio algorithm or delivery profile.
- Per-segment automatic audio decisions.
- Arbitrary mixing controls, professional mastering, visual composition, or
  60 FPS enhancement.

## Observable requirements

- Given a source-level decision, the GUI, CLI, and reopened project should
  expose the same value, status, and source identity.
- Given a completed export, verification should report the applied route,
  expected duration, channels, metadata, playability, and peak safety.
- Given an analysis or export failure, the same structured failure should be
  visible through the applicable interface without a success-shaped fallback.
- Given representative output is reviewed manually, the recorded result should
  distinguish measurable correctness from subjective listening evidence.

## Validation intent

- Run equivalent GUI and CLI inspection and export flows.
- Save/reopen projects and compare source decisions, route selection, duration,
  and output verification.
- Listen to representative outputs and inspect them with ffprobe while
  confirming original source files remain unchanged.

## Protected behavior

Existing project schema compatibility, GUI/CLI parity, fixed output canvas,
source-safe export, atomic publication, structured errors, and legacy helper
scripts remain protected.

## Definition of done

- Source-level audio and delivery decisions are visible and round-trip safely.
- GUI, CLI, persistence, preview, and export evidence agree.
- Measured output and manual listening evidence is recorded with limitations.
- All PHASE-005 exit conditions have terminal evidence or an explicit
  blocked/skipped reason.

## Closure

TICKET-036 and TICKET-037 satisfy the synchronized-decision and verification
outcome. The reviewed local delivery checkpoint is
`6aebb26121eb7e4088b4c3678b670038116be2be`; remote checks remain unavailable.
