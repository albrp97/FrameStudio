# TICKET-015 - Integrate Safe Deterministic CLI Export

**Ticket ID:** TICKET-015  
**Objective:** OBJ-001  
**Scope:** SCOPE-001  
**Phase:** PHASE-003  
**Feature:** FEAT-008  
**Capability links:** CAP-004, CAP-006, CAP-012  
**Status:** complete  
**Closure:** user-authorized on 2026-08-21 after export, source-preservation,
and local quality evidence; remote checks remain unavailable and are recorded
as an accepted warning.  
**Path history:** `tickets/open/TICKET-015-integrate-safe-deterministic-cli-export.md`
-> `tickets/closed/TICKET-015-integrate-safe-deterministic-cli-export.md`  
**Horizon:** first  
**Priority:** 4  
**Owner:** repository planning; implementer is not assigned  
**Approval:** user-approved on 2026-08-21 for implementation and testing;
configured remote checks remain unavailable  
**Provider:** auto; base and target branches are not configured in
`.github/aidd-config.yml`  
**Source paths:** `vision.md`, `docs/specs/project-scope.md`,
`docs/specs/capability-map.md`,
`docs/planning/phases/open/PHASE-003-repeating-the-basic-edit-through-agents.md`,
`docs/planning/features/open/FEAT-008-applying-one-source-edits-through-cli.md`,
`docs/planning/tickets/closed/TICKET-011-verified-safe-export.md`,
`docs/planning/tickets/open/TICKET-014-implement-one-source-edit-commands.md`,
`AGENTS.md`, `.github/aidd-config.yml`  
**Dependencies:** TICKET-011; TICKET-014; existing export planner, validator,
  progress reporting, and source-preservation boundary  
**Risks:** CLI export diverging from the GUI route, unverified publication,
  incomplete progress output, and failures that replace valid outputs  
**Affected surfaces:** CLI export adapter, export planner/executor, progress
  reporting, output validation, structured errors, docs, and tests  
**Evidence path:** `evidence/phase-003-cli-export.md`

## Outcome

An agent can export a one-source project through the same verified fast or
fallback path as the editor and receive deterministic progress, validation,
publication, and failure information.

## Scope

- Add the deterministic CLI export command and contract-compliant progress
  output.
- Reuse TICKET-011's temporary-output, validation, and atomic publication
  behavior.
- Report selected route, fallback reason, output metadata, duration, and
  actionable failure causes.
- Preserve the source, project, and last valid output on failure.

## Explicit non-goals

- New codecs, hardware-specific tuning, multi-source rendering, composition,
  audio normalization, FPS enhancement, or remote export.
- Weakening the existing GUI export checks or exposing partial output.

## Observable requirements

- Given an eligible edit, the CLI selects and reports the same fast route as
  the editor and publishes only a verified output.
- Given an ineligible edit, the CLI reports the fallback reason and validates
  the resulting output before publication.
- Given a failed command, validation, or publication, valid source/project/
  output state remains intact and the CLI returns non-zero status.
- Given a successful export, progress and final metadata conform to the
  documented machine-readable contract.

## Definition of done

- CLI export is documented and covered by fast-path, fallback, validation
  failure, and source-preservation tests.
- Progress and final output results are deterministic and structured.
- FEAT-008 export evidence is recorded without claiming new media capabilities.

## Validation and evidence

- FFmpeg integration tests reusing the existing safe export fixtures.
- Disposable-media CLI export smoke test with ffprobe and source-preservation
  evidence.
