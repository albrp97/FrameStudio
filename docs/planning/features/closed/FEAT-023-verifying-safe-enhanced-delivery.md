# FEAT-023 - Verifying Safe Enhanced Delivery

**Feature ID:** FEAT-023
**Parent links:** OBJ-001, SCOPE-001, PHASE-007
**Capability links:** CAP-005, CAP-006, CAP-011, CAP-012
**Status:** complete
**Closure:** user-approved on 2026-08-26 after TICKET-056 through TICKET-058
passed implementation, automated validation, review, and user acceptance;
unavailable remote and target-specific checks remain recorded as accepted
warnings.
**Horizon:** future
**Priority:** 4
**Owner:** repository planning; maintainer identity is not recorded
**Approval:** user-authorized on 2026-08-24 to break down PHASE-007; ticket
execution remains separately gated by the configured approval policy
**Source paths:** `docs/planning/phases/closed/PHASE-007-producing-validated-60-fps-edits.md`,
`docs/specs/cli-contract.md`, `resolve_editor/app.py`,
`resolve_editor/app_export.py`, `resolve_editor/cli.py`,
`resolve_editor/export_delivery.py`, `resolve_editor/export_process.py`,
`.github/aidd-config.yml`
**Dependencies:** FEAT-020 policy; FEAT-021 export planning; FEAT-022
interpolation; existing project persistence, CLI, export verification, and
source-safety boundaries
**Risks:** GUI, CLI, project settings, preview, and final output can drift;
metadata can miss visual artifacts; a failed long render can leave unsafe
partial state
**Affected surfaces:** editor export orchestration, project schema, CLI
contract, progress/ETA, output verification, failure cleanup, regression
tests, target-workstation flows, and delivery evidence
**Evidence path:** `evidence/phase-007-safe-enhanced-delivery.md`
**Planned tickets:** TICKET-056, TICKET-057, TICKET-058
**Last updated:** 2026-08-26
**Path history:** created at
`features/open/FEAT-023-verifying-safe-enhanced-delivery.md` ->
`features/closed/FEAT-023-verifying-safe-enhanced-delivery.md`

## Outcome

Enhanced and non-enhanced exports are reproducible through the GUI and CLI,
publish only verified outputs, and leave the project and source media
recoverable after failure.

## Scope

- Connect the approved target-FPS and enhancement settings to editor export
  planning, execution, progress, cancellation, and final status.
- Persist and expose the same decision through versioned project JSON and the
  deterministic CLI contract.
- Verify frame rate, exact frame count, duration, dimensions, streams,
  playability, audio synchronization, scene-cut policy, and artifact-gate
  results before publication.
- Preserve temporary/partial cleanup, atomic publication, and source safety
  for success, cancellation, and failure.
- Re-run ordinary non-enhanced exports and retained legacy-script tests to
  prove the new path does not silently alter protected behavior.
- Record target-workstation benchmark and visual evidence with local
  limitations.

## Explicit non-goals

- Replacing the existing legacy scripts or their command names.
- Claiming visual quality from metadata alone.
- Adding remote services, telemetry, collaboration, or non-Linux support.
- Changing unrelated timeline, composition, or audio behavior.

## Observable requirements

- Given the same project policy, GUI and CLI should report equivalent planning
  inputs, backend choice, progress stages, and final output metadata.
- Given a completed enhanced export, all required frame-count, timing, audio,
  playability, and source-safety checks should pass before publication.
- Given cancellation, a failed artifact gate, or an encoder error, no
  unverified output should be reported as complete and the last valid state
  should remain intact.
- Given enhancement disabled, the existing export route and legacy workflows
  should remain green.

## Validation intent

- Run automated policy, persistence, CLI, export, timing, and verification
  tests.
- Execute generated-media and representative real-media enhanced and ordinary
  exports.
- Perform target-workstation playback/visual checks and record measurable
  versus subjective evidence separately.
- Exercise failure, cancellation, missing-tool, and output-collision paths.

## Protected behaviors

Existing one-source and mixed-source editing, fixed 1920x1080 output,
source-level audio normalization, project compatibility, atomic export,
structured CLI errors, legacy scripts, and source preservation remain
required baselines.

## Definition of done

- GUI, CLI, project persistence, export, verification, and failure recovery
  agree on the enhancement decision.
- Enhanced and ordinary exports have terminal automated, real-media, and
  target-workstation evidence, or explicit blocked/skipped records.
- No unverified or artifact-bearing output is exposed as successful.

## Closure

FEAT-023 was closed on 2026-08-26 after its child tickets and linked evidence
were accepted as tested by the user. Remote and target-environment
limitations remain explicit in the evidence rather than being represented as
successful checks.
