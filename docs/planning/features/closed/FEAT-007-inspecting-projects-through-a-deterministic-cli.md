# FEAT-007 - Inspect Projects Through a Deterministic CLI

**Feature ID:** FEAT-007
**Parent links:** OBJ-001, SCOPE-001, PHASE-003
**Capability links:** CAP-004, CAP-006, CAP-012
**Status:** complete
**Closure:** user-approved on 2026-08-22 after successful implementation,
review evidence, and target-workstation validation; remote checks remain
unavailable and are recorded as an accepted warning.
**Path history:** `features/open/FEAT-007-inspecting-projects-through-a-deterministic-cli.md`
-> `features/closed/FEAT-007-inspecting-projects-through-a-deterministic-cli.md`
**Horizon:** first
**Priority:** 1
**Owner:** repository planning; maintainer identity is not recorded
**Approval:** user-approved on 2026-08-21 to continue PHASE-003 planning
**Source paths:** `vision.md`, `docs/specs/project-scope.md`,
`docs/specs/capability-map.md`, `docs/planning/phases/open/PHASE-003-repeating-the-basic-edit-through-agents.md`,
`docs/specs/future-product-direction.md`, `.github/aidd-config.yml`
**Dependencies:** PHASE-003 entry conditions; stable versioned project schema;
local Python, FFmpeg, and ffprobe availability
**Risks:** unstable output shape, private path leakage, ambiguous schema
versions, and errors that look like successful inspection
**Affected surfaces:** CLI entry point, project persistence, media probing,
structured output/errors, documentation, and automation tests
**Evidence path:** `evidence/phase-003-cli-inspection.md`

## Outcome

Given a valid first-horizon project, Copilot or another agent can inspect its
source, timeline, segment state, edited duration, and export-relevant metadata
through a deterministic machine-readable CLI contract.

## Included

- Select and document the inspection command grammar and machine-readable
  output contract.
- Report project schema version, source identity, source metadata, ordered
  segment boundaries, deletion state, playhead, edited duration, and relevant
  export state.
- Return deterministic structured errors and non-success exit status for
  missing projects, invalid project versions, missing sources, unsupported
  media, unavailable tools, and malformed arguments.
- Define path and metadata redaction behavior for automation output.

## Explicit non-goals

- Mutating project state or publishing exports; those belong to FEAT-008.
- Natural-language agent orchestration, cloud APIs, collaboration, or accounts.
- Multiple sources, multiple tracks, composition, audio normalization, or FPS
  enhancement.

## Acceptance outcomes

- Given the same valid project and tool versions, repeated inspection produces
  equivalent machine-readable output.
- Given a valid project, inspection exposes enough stable identifiers and
  timing data for later edit commands without relying only on list positions.
- Given an invalid input or unavailable dependency, the CLI returns a
  structured error, a non-zero status, and no success-shaped result.
- Given private local paths, output follows the documented redaction policy.

## Evidence plan

- CLI contract and serialization tests.
- Golden machine-readable output and structured-error fixtures.
- Project inspection smoke test using the disposable one-source fixture.
- Documentation of command grammar, schema versioning, exit statuses, and
  redaction behavior.
