# TICKET-048 - Define Target FPS Selection and Enhancement Scope

**Ticket ID:** TICKET-048
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-007
**Feature:** FEAT-020
**Capability links:** CAP-005, CAP-011, CAP-012
**Status:** complete
**Closure:** user-approved on 2026-08-26 after implementation, testing,
review, and acceptance of the target-FPS policy; unavailable remote and
target-specific checks remain recorded as accepted warnings.
**Horizon:** future
**Priority:** 1
**Owner:** repository planning; maintainer identity is not recorded
**Approval:** user-authorized on 2026-08-24 to create the PHASE-007 planning
set; implementation is not authorized by this planning-only request
**Provider:** auto; base and target branches are not configured in
`.github/aidd-config.yml`
**Source paths:** `docs/planning/phases/closed/PHASE-007-producing-validated-60-fps-edits.md`,
`docs/planning/features/closed/FEAT-020-choosing-target-frame-rate-delivery.md`,
`docs/specs/project-scope.md`, `docs/specs/capability-map.md`,
`docs/specs/cli-contract.md`, `FPS-ENHANCEMENT-RESEARCH.md`,
`framestudio_fps.py`, `framestudio_concat.py`, `.github/aidd-config.yml`
**Dependencies:** PHASE-005 audio/output policy; PHASE-006 timeline and
segment timing semantics; source frame-rate metadata; current versioned
project settings
**Risks:** mixed-rate sources can produce ambiguous eligibility, custom rates
may not be supported by the selected engine, and silent down-conversion can
break timing or user expectations
**Affected surfaces:** output-policy contract, rate resolution, enhancement
scope, project settings, GUI/CLI contracts, tests, documentation, and
evidence
**Evidence path:** `evidence/phase-007-target-fps-policy.md`
**Protected behaviors:** existing non-enhanced exports, source-level audio
decisions, fixed 1920x1080 output, project compatibility, legacy scripts,
and source preservation
**Last updated:** 2026-08-26
**Path history:** created at
`tickets/open/TICKET-048-define-target-fps-selection-and-enhancement-scope.md`
-> `tickets/closed/TICKET-048-define-target-fps-selection-and-enhancement-scope.md`

## Outcome

PHASE-007 has an approved, deterministic contract for selecting an export
frame rate and deciding when motion enhancement is eligible.

## Scope

- Define the four user-facing choices: lowest input FPS, highest input FPS,
  custom positive rational FPS, and 60 FPS.
- Define how the selected rate is resolved for one-source and mixed-source
  projects, including ties and rational values.
- Define the enhancement toggle and its default state.
- Define the initial enhancement scope. The recommended policy is an
  export-level target with source-level eligibility: sources below the target
  may be interpolated, sources already at the target are not synthesized, and
  sources above the target require an explicit non-enhancing conversion rule
  or a visible rejection.
- Define behavior for deleted blocks, edit boundaries, unsupported custom
  rates, variable-frame-rate metadata, and target rates below an input rate.
- Record the policy in a form that can be implemented identically by the GUI,
  project file, and CLI.

## Explicit non-goals

- Implementing interpolation, frame conversion, or export UI.
- Selecting a codec, encoder, or hardware profile.
- Changing the current version-1 CLI contract in this ticket.
- Claiming that every target rate is supported by every backend.

## Observable requirements

- Given source rates, the policy should resolve lowest, highest, custom, and
  60 FPS choices to stable rational values.
- Given an invalid, non-positive, or unsupported custom value, the policy
  should return a structured rejection reason.
- Given enhancement disabled, the policy should select the existing
  non-enhanced export behavior.
- Given mixed source rates, the policy should identify which inputs are
  eligible for enhancement and explain exclusions.
- Given the same project and settings, GUI, project JSON, and CLI policy
  values should be equivalent.

## Commands and quality gates

- `python3 -m unittest discover -s tests`
- `make contract`
- `make check`
- `make quality PYTHON=.venv/bin/python`

## Functionality flows

- Resolve all four rate choices for one-source 29.97 FPS, 60 FPS, and mixed
  29.97/60 FPS fixtures.
- Exercise enhancement on and off, lower-than-source targets, invalid custom
  values, and deleted timeline blocks.
- Compare the normalized policy with the persisted project and CLI payload.

## User validation before closure

Review the policy matrix for one-source and mixed-source projects. Confirm the
four rate choices, enhancement toggle default, handling of already-target-rate
inputs, and behavior for lower or unsupported targets. Return `PASS`, `FAIL`,
or `CHANGES` with the approved scope decision.

## Definition of done

- The target-rate and enhancement-scope contract is written and approved.
- All mixed-rate and invalid-input cases have observable expected outcomes.
- The decision does not alter existing non-enhanced behavior.
- FEAT-020 can proceed to persistence and UI implementation without an
  unresolved scope ambiguity.

## Closure

TICKET-048 was closed on 2026-08-26 after the user confirmed the completed
ticket set was approved, accepted, and tested.
