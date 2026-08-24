# TICKET-031 - Define Source-Level Audio Policy

**Ticket ID:** TICKET-031
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-005
**Feature:** FEAT-014
**Capability links:** CAP-008, CAP-012
**Status:** complete
**Closure:** user-approved on 2026-08-22 after implementation, automated and
real-media verification, review, user validation, and local delivery evidence;
remote checks remain unavailable and are recorded as an accepted warning.
**Path history:** `tickets/open/TICKET-031-define-source-level-audio-policy.md`
-> `tickets/closed/TICKET-031-define-source-level-audio-policy.md`
**Horizon:** future
**Priority:** 1
**Owner:** repository planning and implementation in the active worktree
**Approval:** user-authorized on 2026-08-22 to implement all approved
PHASE-005 tickets, including source-level audio balancing, with the legacy
`resolve_concat.py` mean/median policy applied once per input source
**Provider:** auto; base and target branches are not configured in
`.github/aidd-config.yml`
**Source paths:** `vision.md`, `docs/specs/project-scope.md`,
`docs/specs/capability-map.md`,
`docs/specs/future-product-direction.md`,
`docs/planning/phases/open/PHASE-005-balancing-sources-and-delivering-consistent-media.md`,
`docs/planning/features/open/FEAT-014-balancing-each-source-consistently.md`,
`docs/specs/phase-002-export-policy.md`, `.github/aidd-config.yml`
**Dependencies:** PHASE-004A complete; PHASE-004 mixed-source model and
fixed-output policy; representative local audio fixtures; installed
`ffmpeg` and `ffprobe`
**Risks:** the wrong loudness target can make footage sound inconsistent,
peak protection can reduce useful dynamics, and undocumented edge cases can
become silent unsafe defaults
**Affected surfaces:** audio measurement contract, normalization policy,
fixture matrix, project settings, analysis results, evidence, and tests
**Evidence path:** `evidence/phase-005-audio-policy.md`
**Protected behaviors:** source media remains untouched; segment block
identity, ordering, deletion, split inheritance, fixed 1920x1080 output, and
structured failure handling remain unchanged
**Last updated:** 2026-08-22

## Outcome

The project has an approved, deterministic source-level audio policy that
defines what is measured, how a decision is made, and how exceptional input
media is handled.

## Scope

- Select the loudness and peak measurements used for an automatic decision.
- Define target loudness, maximum true peak, gain limits, and dynamic-range
  protections appropriate for the supported workstation.
- Define channel layout, sample-rate, silence, unsupported-audio, malformed
  metadata, and analysis-failure behavior.
- Define how one decision is associated with a source and reused by every
  segment from that source.
- Define the boundary between automatic decisions and future manual overrides.
- Create a fixture and evidence matrix with expected measurements, decisions,
  and safe fallback outcomes.

## Explicit non-goals

- Implementing preview and export consumers beyond defining their shared
  policy contract.
- Applying a different automatic gain to each segment.
- Replacing source audio, denoising, equalization, mastering, or voice
  isolation.
- Triplicate composition, visual transforms, or 60 FPS enhancement.

## Observable requirements

- Given representative quiet, loud, clipped, silent, mono, stereo, and
  multi-channel sources, the policy should define deterministic measurements
  and an expected decision for each case.
- Given a source split into multiple segments, the policy should require one
  source-level decision rather than independent per-segment analysis.
- Given unsupported audio or failed analysis, the policy should require an
  explicit safe fallback and structured diagnostic.
- Given a proposed target or peak policy, the evidence should distinguish
  measured correctness from subjective listening quality.

## Commands and quality gates

- `python3 -m unittest discover -s tests`
- `make check`
- `make quality PYTHON=.venv/bin/python`
- Review generated fixture measurements with the installed `ffmpeg` and
  `ffprobe` tools.

## Functionality flows

- Generate or select disposable fixtures covering the policy matrix.
- Record measurements, expected decisions, failure states, and rationale.
- Review the policy against the fixed output and source-preservation rules.

## User validation before closure

Review the policy matrix and approve the target loudness, peak ceiling,
channel/sample-rate handling, silence behavior, unsupported-audio fallback,
analysis-failure behavior, and source-level inheritance rule.

## Definition of done

- The policy and fixture matrix are documented in the configured evidence
  path.
- Every PHASE-005 audio entry condition has an explicit decision or is marked
  blocked with its reason.
- The policy implementation and fixture matrix match the legacy
  `resolve_concat.py` mean/median gain calculation.
- The policy is available as a shared source-level contract for analysis,
  preview, and export work.

## Preimplementation checklist

**Reviewed:** 2026-08-22
**Decision:** ready for implementation
**Result:** verifying; implementation and automated evidence are complete,
user validation is pending

### Passed checks

- The objective, scope, capability map, PHASE-005, FEAT-014, and TICKET-031
  links are present and resolve to the configured planning records.
- PHASE-005, FEAT-014, and TICKET-031 are in the open lifecycle directories;
  no closed ancestor is being used for active work.
- Scope, non-goals, dependencies, risks, affected surfaces, protected
  behaviors, commands, evidence path, and user-validation flow are defined.
- The protected baseline is available in
  `evidence/editor-architecture-refactor.md`, including a passing `make
  check` result.
- No overlapping active or in-progress ticket was found.

### Resolved blockers

- Dedicated branch `ticket/phase-005-source-audio-delivery` is active.
- The user explicitly approved implementation of all current PHASE-005
  tickets, including the legacy per-input mean/median audio policy.

### Warnings

- Remote checks are required by `.github/aidd-config.yml`, but no remote or
  upstream is configured, so no provider-side check can be claimed.

TICKET-031 has completed implementation and automated verification. User
validation, review, and local delivery are terminal; remote checks remain
unavailable because no remote or upstream is configured.

## Closure

The source-level policy is complete and matches the approved legacy
mean/median behavior. Local delivery checkpoint:
`6aebb26121eb7e4088b4c3678b670038116be2be`.
