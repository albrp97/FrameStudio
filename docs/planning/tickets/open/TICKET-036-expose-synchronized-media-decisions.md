# TICKET-036 - Expose Synchronized Media Decisions

**Ticket ID:** TICKET-036
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-005
**Feature:** FEAT-016
**Capability links:** CAP-005, CAP-008, CAP-012
**Status:** verifying
**Horizon:** future
**Priority:** 6
**Owner:** repository planning and implementation in the active worktree
**Approval:** user-authorized on 2026-08-22 to implement all approved
PHASE-005 tickets, including source-level audio balancing, with the legacy
`resolve_concat.py` mean/median policy applied once per input source
**Provider:** auto; base and target branches are not configured in
`.github/aidd-config.yml`
**Source paths:** `docs/planning/features/open/FEAT-016-synchronizing-media-decisions-and-verification.md`,
`docs/planning/tickets/open/TICKET-032-analyze-and-persist-source-audio-decisions.md`,
`docs/planning/tickets/open/TICKET-034-benchmark-and-document-delivery-profiles.md`,
`docs/planning/tickets/open/TICKET-035-route-audio-aware-and-mixed-source-exports-safely.md`,
`docs/specs/cli-contract.md`, `resolve_editor/app.py`,
`resolve_editor/cli.py`, `resolve_editor/model.py`,
`resolve_editor/export.py`, `.github/aidd-config.yml`
**Dependencies:** TICKET-032, TICKET-034, and TICKET-035; PHASE-004 GUI/CLI
parity and persistence contracts
**Risks:** UI, CLI, project state, and exporter can drift; status labels may
hide a failed analysis if they are not derived from shared state
**Affected surfaces:** project serialization, GUI source controls, CLI
inspection/payloads, preview/export status, structured errors, tests, and
documentation
**Evidence path:** `evidence/phase-005-media-decision-surfaces.md`
**Protected behaviors:** existing CLI JSON contracts, project compatibility,
source identity, structured errors, fixed output canvas, and GUI/CLI shared
domain operations remain unchanged
**Last updated:** 2026-08-22

## Outcome

The GUI, CLI, and reopened project expose the same source-level audio
decision, diagnostics, override state, delivery route, and verification
status.

## Scope

- Show source-level audio measurement and decision state without presenting it
  as a per-segment setting.
- Expose selected delivery profile, route, reason, and verification status.
- Preserve structured errors and explicit pending/failed/fallback states.
- Keep GUI and CLI inspection backed by the same persisted domain behavior.
- Document how a user distinguishes automatic decisions from future manual
  overrides.

## Explicit non-goals

- Adding a second audio or rendering algorithm.
- Arbitrary mixing/mastering controls.
- Triplicate composition, visual transforms, or 60 FPS enhancement.
- Hiding unsupported or failed analysis behind a successful-looking label.

## Observable requirements

- Given a source-level decision, GUI, CLI, and save/reopen should expose the
  same source identity, policy version, decision, and status.
- Given an export route, GUI and CLI should report the same route and reason.
- Given a failed analysis or export, both surfaces should show the explicit
  failure or fallback state.
- Given a source with multiple segments, the UI should not imply that each
  segment has an independent automatic level.

## Commands and quality gates

- `python3 -m unittest discover -s tests`
- `make contract`
- `make check`
- `make quality PYTHON=.venv/bin/python`
- `make smoke`

## Functionality flows

- Analyze a mixed-source project and compare GUI and CLI inspection payloads.
- Save/reopen the project and compare decision, route, and diagnostic state.
- Trigger a supported failure and verify consistent structured reporting.

## User validation before closure

Inspect the same disposable project in the GUI and CLI, save/reopen it, and
confirm that source-level audio decisions, route explanations, failures, and
verification status match without segment-level ambiguity.

## Definition of done

- GUI, CLI, and project state expose one shared source-level decision model.
- Success, pending, fallback, and failure states are explicit and tested.
- CLI and GUI evidence demonstrates parity.
- No source media or established project compatibility is broken.
