# TICKET-010 - Select Fast or Fallback Export Plans

**Ticket ID:** TICKET-010  
**Objective:** OBJ-001  
**Scope:** SCOPE-001  
**Phase:** PHASE-002  
**Feature:** FEAT-005  
**Capability links:** CAP-005, CAP-012  
**Status:** complete  
**Horizon:** first  
**Priority:** 4  
**Owner:** repository planning; implementer is not assigned  
**Approval:** user-approved on 2026-08-21 before execution  
**Provider:** auto; base and target branches are not configured in
`.github/aidd-config.yml`  
**Source paths:** `vision.md`, `docs/specs/project-scope.md`,
`docs/specs/capability-map.md`, `docs/planning/phases.md`,
`docs/planning/features.md`,
`docs/planning/tickets/closed/TICKET-007-segment-model-and-cut-semantics.md`,
`docs/planning/tickets/closed/TICKET-008-split-delete-editor-workflow.md`,
`AGENTS.md`, `.github/aidd-config.yml`  
**Dependencies:** TICKET-007; FFmpeg/ffprobe availability;
approved cut semantics  
**Risks:** false stream-copy eligibility, keyframe-bound cuts, timestamp
  discontinuities, unsupported streams, workstation-specific codec behavior  
**Affected surfaces:** export planner, FFmpeg command construction, media
  capability checks, structured status/errors, planner tests, export docs  
**Evidence path:** `evidence/export-plan-selection.md`

## Resolution

The export planner now returns deterministic stream-copy or fallback plans,
checks source/timeline consistency, verifies keyframe-aligned boundaries with
FFprobe JSON when needed, explains fallback reasons, and rejects empty or
ambiguous edits before command execution.

## Planning blocker

The stream-copy eligibility and fallback output policy must be accepted as
part of this ticket before export execution is ready. The planner must expose
the reason for a fallback or rejection rather than silently selecting a
slower or less compatible command.

## Outcome

Given a valid one-source cut project, the editor can deterministically choose
an eligible fast path or a validated fallback plan and explain that choice
before any output is written.

## Scope

- Define eligibility checks for stream copy/smart rendering under the approved
  cut semantics.
- Define the fallback container, video, audio, timing, and metadata policy
  supported by the target FFmpeg toolchain.
- Represent a structured export plan with route, inputs, outputs, and reasons.
- Reject unsupported or ambiguous plans before command execution.
- Keep the planner independent from UI and output publication.
- Document keyframe, timestamp, variable-frame-rate, and codec limitations.

## Explicit non-goals

- Running export commands or publishing outputs; covered by TICKET-011.
- Multi-source composition, scaling, triplicate layouts, audio normalization,
  FPS enhancement, hardware-specific profiles, or CLI parity.
- Destructive source replacement.

## Observable requirements

- Given an eligible edit and source, the planner returns the configured fast
  route with an inspectable reason.
- Given an ineligible edit, the planner returns the validated fallback route
  and identifies the failed eligibility conditions.
- Given unsupported streams, missing tools, or ambiguous timestamps, the
  planner returns a non-success plan error without writing output.
- Given equivalent project state, repeated planning returns the same route and
  relevant command inputs.

## Validation and evidence

- Add unit tests for eligible, ineligible, unsupported, ambiguous, and
  deterministic plan cases.
- Probe representative generated fixtures with `ffprobe`.
- Run `python3 -m unittest discover -s tests`, `make check`, and
  `git diff --check`.
- Record the accepted policy, plan examples, and known limitations in
  `evidence/export-plan-selection.md`.

## Quality gates

- TICKET-007's cut semantics must be approved and evidenced.
- Planner tests, baseline tests, and local quality checks must pass.
- Remote checks remain required by configuration but unavailable locally.

## Protected behavior

Existing source probing, partial-output safety, legacy FFmpeg scripts,
project persistence, and all PHASE-001 behavior remain available.

## Definition of done

- Fast-path eligibility and fallback policy are documented and approved.
- Planner output is deterministic, structured, and reasoned.
- Unsupported/ambiguous cases fail before output creation.
- Focused fixture tests and baseline evidence are recorded.
- Command execution and final output publication are not claimed.

## Completion evidence

- Focused planner tests: `python3 -m unittest tests.test_editor_export`
- Full local gate: `make check` (78 tests passed, compilation and diff checks
  passed).
- Real-media keyframe probe is covered by the focused test suite.
- Evidence record: `evidence/export-plan-selection.md`
