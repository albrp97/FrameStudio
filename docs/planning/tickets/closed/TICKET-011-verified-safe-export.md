# TICKET-011 - Execute, Verify, and Publish Export Safely

**Ticket ID:** TICKET-011  
**Objective:** OBJ-001  
**Scope:** SCOPE-001  
**Phase:** PHASE-002  
**Feature:** FEAT-005  
**Capability links:** CAP-005, CAP-012  
**Status:** complete  
**Horizon:** first  
**Priority:** 5  
**Owner:** repository planning; implementer is not assigned  
**Approval:** user-approved on 2026-08-21 before execution  
**Provider:** auto; base and target branches are not configured in
`.github/aidd-config.yml`  
**Source paths:** `vision.md`, `docs/specs/project-scope.md`,
`docs/specs/capability-map.md`, `docs/planning/phases.md`,
`docs/planning/features.md`,
`docs/planning/tickets/closed/TICKET-010-export-plan-selection.md`,
`AGENTS.md`, `.github/aidd-config.yml`  
**Dependencies:** TICKET-008 and TICKET-010; validated FFmpeg/ffprobe
toolchain; generated or fixture media  
**Risks:** corrupt or incomplete output, duration drift, missing streams,
  partial-file exposure, output replacement after failure  
**Affected surfaces:** export service, temporary-file lifecycle, output
validation, editor export action/status, Makefile/manual workflow, FFmpeg
integration tests  
**Evidence path:** `evidence/verified-safe-export.md`

## Outcome

The user can export a valid one-source edit through the selected fast or
fallback plan, see progress and failure reasons, and receive a final output
only after its playability, duration, streams, and source preservation have
been verified.

## Scope

- Execute the structured plan from TICKET-010.
- Write to a temporary or partial path outside the published output path.
- Validate the candidate with FFmpeg/ffprobe for playability, expected
  duration, required streams, and relevant metadata.
- Publish the verified output atomically and retain the last valid output on
  failure.
- Integrate an explicit export action and status/error presentation into the
  editor.
- Document output path, fallback reason, validation result, and elapsed time.

## Explicit non-goals

- Multiple sources, multiple tracks, composition, scaling, triplicate layouts,
  audio normalization, FPS enhancement, hardware-specific tuning, or CLI
  parity.
- Publishing unverified output or overwriting source media.

## Observable requirements

- Given an eligible edit, export executes the selected fast plan and publishes
  a playable output only after verification succeeds.
- Given an ineligible edit, export executes the selected fallback and reports
  the fallback reason.
- Given a completed export, output duration matches the edited-duration
  contract within the approved validation tolerance and required streams are
  present.
- Given a command, validation, or publication failure, the source, project,
  and last valid output remain intact and the UI reports an actionable error.
- Given a successful export, the published path is distinct from the source
  and can be reopened or probed independently.

## Validation and evidence

- Add FFmpeg integration tests for fast-path and fallback fixtures,
  verification failures, output replacement safety, and source preservation.
- Run `python3 -m unittest discover -s tests`, `make check`, and
  `git diff --check`.
- Perform the manual target-workstation split/delete/save/reopen/export flow
  with the one-minute 1080p fixture or an equivalent local fixture.
- Record output metadata, duration, playability, route, fallback reason,
  failure recovery, and elapsed-time evidence in
  `evidence/verified-safe-export.md`.

## Quality gates

- TICKET-010 terminal evidence and TICKET-008's editor integration are
  required.
- Baseline, local quality, FFmpeg integration, output validation, and
  user-facing manual evidence are required.
- Remote checks remain required by configuration but unavailable locally.

## Protected behavior

Source media, versioned project files, last-valid-project and
partial-output safety, existing scripts, command names, and PHASE-001 tests
remain unchanged.

## Definition of done

- Fast and fallback plans execute through a safe temporary-output boundary.
- Invalid output is never published as complete.
- Verified output has expected duration and required streams.
- Failed exports preserve source, project, and last valid output.
- Focused integration, baseline, and manual evidence is recorded.
- Future multi-source, composition, audio, FPS, and CLI capabilities are not
  claimed.

## Latest lifecycle state

The maintainer confirmed the documented target-workstation export flow was
completed and explicitly authorized closure. TICKET-011 is `complete` and has
been moved to the closed directory. Configured remote checks and screenshot
artifacts were not available in the current environment and remain recorded as
accepted delivery warnings rather than claimed passes.

**Closure authorization:** User-confirmed on 2026-08-21 after the documented
manual flow was checked.  
**Closure evidence:** `evidence/verified-safe-export.md` E-1109.
