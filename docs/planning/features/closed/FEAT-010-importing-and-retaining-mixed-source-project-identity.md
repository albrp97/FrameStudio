# FEAT-010 - Import and Retain Mixed-Source Project Identity

**Feature ID:** FEAT-010
**Parent links:** OBJ-001, SCOPE-001, PHASE-004
**Capability links:** CAP-007, CAP-012
**Status:** complete
**Closure:** user-approved on 2026-08-22 after successful implementation,
review evidence, and target-workstation validation; remote checks remain
unavailable and are recorded as an accepted warning.
**Path history:** `features/open/FEAT-010-importing-and-retaining-mixed-source-project-identity.md`
-> `features/closed/FEAT-010-importing-and-retaining-mixed-source-project-identity.md`
**Horizon:** future
**Priority:** 1
**Owner:** repository planning; maintainer identity is not recorded
**Approval:** user-authorized on 2026-08-21 to continue with PHASE-004 ticket planning
**Source paths:** `vision.md`, `docs/specs/project-scope.md`,
`docs/specs/capability-map.md`,
`docs/planning/phases/open/PHASE-004-combining-mixed-source-footage.md`,
`docs/specs/future-product-direction.md`, `.github/aidd-config.yml`
**Dependencies:** PHASE-003 project identity and CLI error contract; local
FFmpeg/ffprobe probing; representative mixed-dimension and mixed-frame-rate
media
**Risks:** unstable source identifiers, moved or renamed media, incomplete
metadata, variable-frame-rate ambiguity, and unsafe project migration
**Affected surfaces:** project model, source registry, media probing,
persistence, relinking/errors, CLI, documentation, and tests
**Evidence path:** `evidence/phase-004-mixed-source-import.md`
**Planned tickets:** TICKET-018, TICKET-019

## Outcome

The user can add multiple local videos to one project while preserving each
source's identity, probed media characteristics, source-level settings, and
safe reopen behavior.

## Included

- Define stable source and clip identity for multiple inputs.
- Record dimensions, orientation, frame rate, codec/container, duration, and
  audio-stream metadata needed by later timeline and export decisions.
- Import several sources without overwriting or moving the originals.
- Persist and reopen the multi-source project with clear missing-source and
  relinking behavior.
- Keep source-level settings distinct from later segment-level edits.

## Explicit non-goals

- Automatic per-input audio normalization.
- Triplicate composition, reusable visual transforms, or 60 FPS enhancement.
- Multiple professional-NLE tracks or cloud-backed media management.
- Copy/paste or advanced segment movement beyond the Phase 4 timeline feature.

## Acceptance outcomes

- Given several readable videos with different media parameters, the project
  retains one stable identity and complete probe metadata for each input.
- Given a missing or moved source on reopen, the application reports the
  affected source and preserves the remaining valid project state.
- Given a saved multi-source project, reopening restores source order,
  identity, source-level settings, and all persisted timeline references.
- Given any import or persistence failure, source files and the last valid
  project remain unchanged.

## Evidence plan

- Project-schema and source-registry invariant tests.
- Generated fixtures covering dimensions, orientation, frame rates, codecs,
  audio presence, and missing-source recovery.
- Real-media import and save/reopen smoke evidence with redacted paths.

## Protected behavior

The existing one-source project schema, source-preservation guarantees,
atomic-save behavior, legacy scripts, and Phase 3 CLI contract remain
compatible or migrate explicitly without silently changing their semantics.
