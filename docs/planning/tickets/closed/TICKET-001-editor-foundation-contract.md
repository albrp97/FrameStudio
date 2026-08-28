# TICKET-001 - Select the Editor Foundation Runtime and Source Contract

**Ticket ID:** TICKET-001
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-001
**Feature:** FEAT-001
**Capability links:** CAP-001, CAP-012
**Status:** complete
**Horizon:** first
**Priority:** 1
**Owner:** repository planning; implementer is not assigned
**Approval:** user-approved on 2026-08-21 before execution
**Source paths:** `vision.md`, `docs/specs/project-scope.md`,
`docs/planning/phases.md`, `docs/planning/features.md`,
`AGENTS.md`, `.github/aidd-config.yml`
**Dependencies:** confirmed objective, scope, capability map, phase, and
feature; available target-workstation media tools
**Risks:** selecting a stack that cannot provide responsive seeking or
reliable packaging; defining a schema that prevents future segment and
multi-source expansion; relying on unverified workstation assumptions
**Affected surfaces:** GUI/runtime boundary, playback boundary, source/project
contract, packaging/setup, manual GUI evidence
**Evidence path:** `evidence/selecting-editor-foundation.md`

## Outcome

The project has an evidence-backed PHASE-001 foundation decision that names
the GUI/runtime and playback approach, the setup path, the initial source and
project contract, source relinking behavior, and the practical target-
workstation smoke-test method. The result is explicit about limitations and
does not claim editor behavior has been implemented.

## Scope

- Compare viable approaches against the repository's Linux-only target,
  real-time preview and seeking needs, local/offline operation, FFmpeg
  integration, Python reuse, packaging complexity, and future CLI parity.
- Select and record the GUI/runtime and playback approach, including versions,
  required system tools, setup steps, and known timing/seek limitations.
- Define the initial one-source project/source contract: identity, source
  metadata needed by the editor, version marker, and behavior when the source
  is missing or moved.
- Select a practical target-workstation manual smoke-test path for import,
  playback, and persistence without adding private media to the repository.
- Record rejected alternatives and the evidence supporting the selected
  approach.

## Explicit non-goals

- Implementing the GUI, playback backend, project serialization, or source
  import.
- Choosing future multi-source, triplicate, audio-normalization, or FPS
  architecture beyond compatibility constraints the initial contract must
  preserve.
- Adding dependencies, package manifests, CI, or installation behavior
  without the evidence and approval required by the selected approach.
- Claiming that a candidate is suitable based only on theoretical features or
  benchmark claims from another machine.

## Observable requirements

- Given the PHASE-001 constraints and repository evidence, the decision record
  should identify one selected runtime/playback approach or clearly document
  why the phase remains blocked.
- Given the selected approach, the project should have documented setup
  commands, required versions/tools, known limitations, and a manual
  validation path.
- Given a one-source project contract, the record should define source
  identity, required metadata, versioning, missing-source behavior, and
  non-destructive path handling.
- Given rejected alternatives, the record should explain the decision using
  target-workstation evidence rather than an unverified assumption.

## Validation and evidence

- Run the existing baseline command:
  `python3 -m unittest discover -s tests`.
- Exercise the selected candidate's smallest real target-workstation probe
  for source opening, playback/seek feasibility, and local setup.
- Record the selected stack, versions, setup output, limitations, and manual
  smoke-test steps in `evidence/selecting-editor-foundation.md`.
- Redact private media paths and do not retain credentials or sensitive media
  metadata in durable evidence.
- Record unavailable checks as blocked or skipped with a reason.

## Protected behavior

The existing `framestudio_media.py`, `framestudio_concat.py`, and `framestudio_fps.py`
commands, their tests, existing installation wrappers, and source-safe
output behavior remain available and unchanged.

## Definition of done

- A reviewed decision record identifies the GUI/runtime, playback approach,
  setup path, versions, limitations, and rejected alternatives.
- The initial one-source project/source contract and missing/moved-source
  behavior are explicit.
- The target-workstation smoke-test procedure is reproducible without
  repository-private media.
- Baseline and candidate evidence are attached at the configured evidence
  path, with unavailable checks clearly identified.
- The ticket is accepted as the prerequisite for TICKET-002; no editor
  implementation is implied by completion of this ticket.

## Readiness

The selected foundation, source/project contract, and validation path are
implemented and recorded at `evidence/selecting-editor-foundation.md`.
Target-workstation visual evidence remains an accepted environment concern for
the downstream user-facing tickets, not an unresolved foundation decision.
