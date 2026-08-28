# CHG-004 - Responsive Preview and Evidence-Based Media Strategy

**Change ID:** CHG-004
**Type:** Material planning change
**Status:** approved-and-applied
**Date:** 2026-08-26
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Owner:** repository planning; maintainer identity is not recorded
**Approval:** User-authorized by the 2026-08-26 request to create an
additional phase covering preview optimization, direct focus controls,
mixed-FPS render-strategy comparison, and restoration research.
**Source paths:** `vision.md`, `docs/specs/project-scope.md`,
`docs/specs/future-product-direction.md`, `docs/specs/capability-map.md`,
`docs/planning/phases.md`, `docs/planning/features.md`,
`docs/planning/backlog.md`, `.github/aidd-config.yml`
**Affected IDs:** PHASE-008, FEAT-024, FEAT-025, FEAT-026, FEAT-027,
TICKET-061 through TICKET-075, CAP-002, CAP-005, CAP-009, CAP-011, CAP-012
**Last updated:** 2026-08-26

## Request and classification

The user requested a new future phase to improve cursor-driven preview
responsiveness, make segment focus changes easier, compare two mixed-FPS
rendering strategies with empirical measurements, and research future
upscaling and restoration approaches.

This is a material planning change because it adds a new outcome phase and
child planning subtree after PHASE-007. It does not change the first-horizon
scope, the fixed output canvas, source-safety guarantees, current production
render defaults, or the existing restoration-free runtime.

## Decision

1. Add PHASE-008 as a confirmed future phase after PHASE-007.
2. Add FEAT-024 through FEAT-027 for responsive preview, direct focus
   controls, mixed-FPS strategy comparison, and restoration research.
3. Add TICKET-061 through TICKET-075 as planned open tickets with explicit
   dependencies, evidence paths, user-validation plans, and execution gates.
4. Inspect Lossless Cut only through a disposable, revision-pinned,
   license-aware research checkout; do not vendor or copy its code.
5. Require matched benchmark inputs before selecting a mixed-FPS rendering
   default or changing production routing.
6. Keep upscaling, denoising, deblocking, and related restoration work
   research-only in PHASE-008; any implementation requires a later approved
   planning change.
7. Preserve the existing GUI, CLI, project, playback, export, interpolation,
   audio, legacy-script, verification, and source-preservation contracts.

## Affected-artifact inventory

| Artifact | Impact | Action |
|---|---|---|
| `docs/specs/future-product-direction.md` | Add durable intent for responsive preview and media-strategy research | Updated in place |
| PHASE-008 | New future outcome and explicit entry/exit gates | Added to `phases/open/` and phase index |
| FEAT-024 through FEAT-027 | New outcome slices with capability links and evidence plans | Added to `features/open/` and feature index |
| TICKET-061 through TICKET-075 | New bounded research, implementation, benchmark, and verification units | Added to `tickets/open/` and backlog |
| Existing production routes | No approved behavior change in this planning step | Protected |
| Restoration dependencies | Not approved for runtime integration | Explicitly deferred |

## Normative boundary

- PHASE-008 remains future work and cannot expand the first-horizon product.
- Benchmark results must distinguish measured facts, subjective observations,
  assumptions, and unavailable checks.
- External research code remains outside the repository and runtime.
- A preview or render strategy is not promoted to a default without the
  configured evidence, review, and user-approval gates.
- Restoration research cannot add models, downloads, dependencies, or
  production UI in this phase.
- All future implementation must retain atomic output publication,
  verification, cancellation cleanup, and source preservation.

## Validation and remaining gates

- The phase, feature, and ticket indexes reference the new current paths.
- New records remain in the configured open directories with non-terminal
  statuses.
- TICKET-061 through TICKET-075 require the configured preimplementation,
  baseline, user approval, evidence, local-quality, applicable real-system,
  static-analysis, and review gates before execution or closure.
- Target-workstation, network, model/runtime, license, and remote limitations
  must be recorded explicitly when the relevant ticket is executed.
- No implementation, dependency installation, external clone, production
  route change, commit, push, or readiness claim is made by this planning
  change.
