# FEAT-020 - Choosing Target Frame-Rate Delivery

**Feature ID:** FEAT-020
**Parent links:** OBJ-001, SCOPE-001, PHASE-007
**Capability links:** CAP-005, CAP-011, CAP-012
**Status:** complete
**Closure:** user-approved on 2026-08-26 after TICKET-048 and TICKET-049
passed implementation, automated validation, review, and user acceptance;
unavailable remote and target-specific checks remain recorded as accepted
warnings.
**Horizon:** future
**Priority:** 1
**Owner:** repository planning; maintainer identity is not recorded
**Approval:** user-authorized on 2026-08-24 to break down PHASE-007; ticket
execution remains separately gated by the configured approval policy
**Source paths:** `vision.md`, `docs/specs/project-scope.md`,
`docs/specs/capability-map.md`,
`docs/specs/future-product-direction.md`,
`docs/planning/phases/closed/PHASE-007-producing-validated-60-fps-edits.md`,
`docs/specs/cli-contract.md`, `.github/aidd-config.yml`
**Dependencies:** PHASE-005 audio/output policy; PHASE-006 timeline and
segment timing semantics; source frame-rate metadata; versioned project
settings
**Risks:** a project-level target can conflict with per-source rates, custom
rates can be unsupported by the interpolation backend, and unclear scope can
make preview, export, and CLI decisions diverge
**Affected surfaces:** export policy, project output settings, source
metadata, GUI export controls, CLI payloads, validation, tests, and
documentation
**Evidence path:** `evidence/phase-007-target-fps-policy.md`
**Planned tickets:** TICKET-048, TICKET-049
**Last updated:** 2026-08-26
**Path history:** created at
`features/open/FEAT-020-choosing-target-frame-rate-delivery.md` ->
`features/closed/FEAT-020-choosing-target-frame-rate-delivery.md`

## Outcome

The user can choose a deterministic output frame-rate policy for an edited
project and clearly enable or disable motion enhancement for that export.

## Scope

- Offer the lowest input frame rate, highest input frame rate, custom positive
  frame rate, and 60 FPS as explicit output choices.
- Show the source rates that inform the lowest and highest choices.
- Make the enhancement toggle explicit and describe which edited media it
  applies to when source rates differ.
- Define handling for sources already at the target rate, sources above the
  target rate, deleted blocks, and mixed-source timelines.
- Persist the selected policy without changing existing projects that do not
  opt into enhancement.
- Keep the same normalized decision available to the GUI, project file, and
  CLI.

## Explicit non-goals

- Implementing motion interpolation or changing the established delivery
  codecs.
- Treating frame duplication or blending as motion enhancement.
- Adding arbitrary per-clip frame-rate effects or keyframed timing.
- Expanding the project beyond the approved local Linux workflow.

## Observable requirements

- Given multiple source frame rates, the export controls should show
  deterministic lowest and highest choices and their resolved rational rates.
- Given a custom rate that is invalid or unsupported by the selected policy,
  the application should reject it with a visible, structured reason.
- Given enhancement disabled, the export should retain the existing verified
  non-enhanced route.
- Given enhancement enabled, the project and CLI should expose the same target
  rate, scope, and backend-policy inputs before processing begins.

## Validation intent

- Exercise one-source and mixed-source projects with different frame rates.
- Save and reopen each policy combination and compare GUI, project, and CLI
  representations.
- Verify that disabled enhancement remains compatible with existing exports.
- Record unresolved backend or scope limitations instead of inferring support.

## Protected behaviors

Existing project schema compatibility, source-level audio decisions, fixed
1920x1080 output, safe partial-output publication, legacy script commands,
source preservation, and current non-enhanced exports remain unchanged.

## Definition of done

- The target-rate and enhancement policy is observable, validated, and
  persisted.
- Scope behavior for mixed rates and already-target-rate inputs is explicit.
- GUI and CLI policy representations agree.
- Invalid or unavailable choices fail visibly without changing project state.

## Closure

FEAT-020 was closed on 2026-08-26 after its child tickets and linked evidence
were accepted as tested by the user.
