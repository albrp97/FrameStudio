# TICKET-024 - Define Mixed-Source Output Canvas and Timing Policy

**Ticket ID:** TICKET-024
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-004
**Feature:** FEAT-012
**Capability links:** CAP-005, CAP-007, CAP-012
**Status:** complete
**Closure:** user-approved on 2026-08-22 after successful implementation,
review evidence, and target-workstation validation; remote checks remain
unavailable and are recorded as an accepted warning.
**Path history:** `tickets/open/TICKET-024-defining-mixed-source-output-canvas-and-timing-policy.md`
-> `tickets/closed/TICKET-024-defining-mixed-source-output-canvas-and-timing-policy.md`
**Horizon:** future
**Priority:** 7
**Owner:** repository implementation in the active Phase 4 worktree
**Approval:** user-authorized on 2026-08-21 to prepare and implement all
current PHASE-004 open tickets; CHG-002 fixed the project render profile;
human validation remains required before closure
**Provider:** auto; base and target branches are not configured in
`.github/aidd-config.yml`
**Source paths:** `vision.md`, `docs/specs/project-scope.md`,
`docs/specs/capability-map.md`,
`docs/planning/phases/open/PHASE-004-combining-mixed-source-footage.md`,
`docs/planning/features/open/FEAT-012-previewing-and-exporting-mixed-source-edits.md`,
`docs/planning/tickets/open/TICKET-019-implement-mixed-source-import-probing-and-persistence.md`,
`docs/planning/tickets/open/TICKET-020-defining-mixed-source-timebase-and-placement-semantics.md`,
`docs/specs/phase-002-export-policy.md`, `docs/specs/future-product-direction.md`,
`AGENTS.md`, `.github/aidd-config.yml`
**Dependencies:** TICKET-019 and TICKET-020; representative mixed dimensions,
orientations, frame rates, codecs, and audio streams; CHG-002
**Risks:** silent stretching/cropping, timing drift, fixed-canvas scaling cost,
false smart-render eligibility, and output settings that cannot be verified
**Affected surfaces:** output profile, scaling/timing policy, export planner,
preview contract, project settings, CLI, documentation, and tests
**Evidence path:** `evidence/phase-004-output-policy.md`

## Outcome

The project has an explicit fixed 1920x1080 output canvas, aspect-ratio,
current timing, established render-profile, and smart-render boundary for
one-source and mixed-source edits.

## Scope

- Define the fixed 1920x1080 output dimensions for landscape, portrait, and
  mixed inputs.
- Define contain scaling and letterbox behavior and how decisions are surfaced.
- Preserve current deterministic timebase, frame-rate, timestamp, and duration
  behavior without defining the future 60 FPS enhancement policy.
- Define that the established render profile owns container, codecs, audio, and
  pixel format.
- Define when fixed-canvas composition requires rendering and stream copy is
  unavailable.
- Define that a one-source input may use stream copy only when it already
  matches the fixed project canvas.
- Define required video/audio streams and metadata validation.
- Record source-level versus segment-level settings relevant to export.

## Explicit non-goals

- Automatic per-input audio-level normalization.
- Source-driven codec/container selection, triplicate layouts, reusable
  transforms, or 60 FPS enhancement.
- Implementing preview or export execution.

## Observable requirements

- Given different dimensions and orientations, the policy selects a fixed
  1920x1080 canvas without silently stretching or cropping.
- Given mixed frame rates or timestamps, the policy preserves deterministic
  current timing and explicitly defers 60 FPS enhancement.
- Given any source codec or container, the established render profile remains
  the output authority.
- Given mixed sources, the planner reports why fixed-canvas rendering is
  required.
- Given a one-source input that does not match 1920x1080, the planner selects
  fixed-canvas fallback rendering; a matching source may retain eligible
  stream-copy behavior.

## Commands and quality gates

- `make test`
- `make contract`
- `make check`
- `make quality PYTHON=.venv/bin/python`
- Review of output-policy examples and metadata fixtures

## Functionality flows

- Resolve policy for portrait plus landscape fixtures and confirm 1920x1080.
- Resolve policy with deliberately different source codecs and confirm the
  established render profile is unchanged.
- Inspect current mixed-frame-rate timing metadata without treating it as the
  final 60 FPS policy.
- Compare eligible and ineligible smart-render decisions.

## User validation before closure

Review sample outputs for portrait, landscape, and mixed-frame-rate sources,
confirm the fixed 1920x1080 canvas and contain/letterbox behavior, confirm that
source codec differences do not change the established render profile, and
confirm that automatic audio normalization and 60 FPS enhancement remain out
of scope.

## Protected behavior

One-source stream requirements, source-preservation rules, temporary-output
boundaries, and eligible fast-path behavior remain protected; non-1080p
one-source inputs now follow the fixed project canvas policy.

## Definition of done

- Fixed-canvas, timing, render-profile, stream, and smart-render rules are
  documented with representative fixtures.
- The policy is approved before preview/export implementation begins.
