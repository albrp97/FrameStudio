# TICKET-049 - Persist and Expose Frame-Rate Policy

**Ticket ID:** TICKET-049
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-007
**Feature:** FEAT-020
**Capability links:** CAP-005, CAP-011, CAP-012
**Status:** complete
**Closure:** user-approved on 2026-08-26 after implementation, testing,
review, and acceptance of project and CLI frame-rate policy persistence;
unavailable remote and target-specific checks remain recorded as accepted
warnings.
**Horizon:** future
**Priority:** 2
**Owner:** repository planning; maintainer identity is not recorded
**Approval:** user-authorized on 2026-08-24 to create the PHASE-007 planning
set; implementation requires the approved TICKET-048 policy and configured
ticket-execution approval
**Provider:** auto; base and target branches are not configured in
`.github/aidd-config.yml`
**Source paths:** `docs/planning/tickets/closed/TICKET-048-define-target-fps-selection-and-enhancement-scope.md`,
`docs/planning/features/closed/FEAT-020-choosing-target-frame-rate-delivery.md`,
`resolve_editor/model_project.py`, `resolve_editor/persistence.py`,
`resolve_editor/cli_parser.py`, `resolve_editor/cli.py`,
`docs/specs/cli-contract.md`, `.github/aidd-config.yml`
**Dependencies:** TICKET-048; existing versioned project schema and atomic
save/reopen behavior
**Risks:** old project files can be invalidated, GUI and CLI fields can drift,
or absent settings can accidentally enable enhancement
**Affected surfaces:** project JSON, schema compatibility, CLI parser and
payloads, GUI state, persistence tests, contract tests, and documentation
**Evidence path:** `evidence/phase-007-target-fps-policy.md`
**Protected behaviors:** projects without FPS settings remain non-enhanced;
existing schema versions, atomic saves, structured CLI errors, and source
preservation remain unchanged
**Last updated:** 2026-08-26
**Path history:** created at
`tickets/open/TICKET-049-persist-and-expose-frame-rate-policy.md` ->
`tickets/closed/TICKET-049-persist-and-expose-frame-rate-policy.md`

## Outcome

The approved target-FPS and enhancement policy survives save/reopen and is
reported consistently by the GUI, project file, and deterministic CLI.

## Scope

- Add the approved policy to versioned output settings without invalidating
  existing projects.
- Persist the selected policy, resolved target rate, enhancement toggle,
  enhancement scope, and any explicit backend-policy identifier required by
  the contract.
- Expose the same values through inspection and export-planning payloads.
- Validate unknown, malformed, stale, or unsupported policy values with
  structured errors.
- Preserve default non-enhanced behavior when settings are absent.

## Explicit non-goals

- Running interpolation or changing output codecs.
- Implementing the GTK export page.
- Adding unrelated project-schema migrations.
- Persisting machine-specific credentials, absolute cache secrets, or private
  runtime details.

## Observable requirements

- Given a saved policy, reopening the project should restore equivalent values.
- Given an old project without FPS settings, loading and exporting it should
  preserve the current non-enhanced route.
- Given invalid policy data, loading or inspection should fail explicitly
  without partially rewriting the project.
- Given equivalent GUI and CLI operations, policy fields and resolved rates
  should match byte-for-byte where the contract requires deterministic JSON.

## Commands and quality gates

- `python3 -m unittest discover -s tests`
- `make contract`
- `make check`
- `make quality PYTHON=.venv/bin/python`

## Functionality flows

- Create one-source and mixed-source projects, set every rate choice, save,
  reopen, and inspect.
- Load legacy project fixtures with no FPS settings and confirm enhancement is
  disabled.
- Submit malformed policy payloads and verify structured errors and unchanged
  project bytes.

## User validation before closure

Save projects with each target-rate choice and enhancement state, reopen them,
and compare the visible values with CLI inspection. Confirm legacy projects
remain ordinary non-enhanced exports. Return `PASS`, `FAIL`, or `BLOCKED`.

## Definition of done

- Policy persistence is backward compatible and atomic.
- GUI, project JSON, and CLI representations agree.
- Invalid settings fail without a success-shaped fallback or partial write.

## Closure

TICKET-049 was closed on 2026-08-26 after the user confirmed the completed
ticket set was approved, accepted, and tested.
