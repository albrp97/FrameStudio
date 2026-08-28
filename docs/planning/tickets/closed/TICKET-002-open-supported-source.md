# TICKET-002 - Open and Probe a Supported Source Project

**Ticket ID:** TICKET-002
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-001
**Feature:** FEAT-001
**Capability links:** CAP-001, CAP-012
**Status:** complete
**Horizon:** first
**Priority:** 2
**Owner:** repository planning; implementer is not assigned
**Approval:** user-approved on 2026-08-21 before execution
**Source paths:** `vision.md`, `docs/specs/project-scope.md`,
`docs/planning/phases.md`, `docs/planning/features.md`,
`docs/planning/tickets/closed/TICKET-001-editor-foundation-contract.md`,
`AGENTS.md`, `.github/aidd-config.yml`
**Dependencies:** TICKET-001; selected GUI/runtime and source/project
contract; `python3`, `ffmpeg`, and `ffprobe`
**Risks:** unsupported codecs or incomplete metadata; stale source paths;
variable-frame-rate duration ambiguity; accidental source mutation
**Affected surfaces:** source/project model, media probing, editor open flow,
user-facing errors, FFmpeg integration, existing tests
**Evidence path:** `evidence/open-supported-source-project.md`

## Dependency resolution

TICKET-001 is complete and its runtime, source/project contract, relinking
policy, and validation evidence are recorded at
`evidence/selecting-editor-foundation.md`.

## Outcome

Given one supported source video and the approved PHASE-001 foundation
contract, the editor creates or opens a non-destructive project, probes and
exposes the metadata required by the editor, and reports source failures
without changing the source or replacing the last valid project state.

## Scope

- Add the source-opening flow using the selected runtime and the existing
  FFmpeg/ffprobe foundation.
- Map validated source metadata into the initial one-source project model.
- Establish a clear project/source identity and preserve the original source
  reference separately from editor state.
- Surface missing, unreadable, unsupported, and incomplete metadata errors
  with actionable reasons.
- Add focused automated coverage for successful probing, metadata mapping,
  and failure paths.

## Explicit non-goals

- Playback controls, timeline seeking, split/delete, persistence round trips,
  export, or CLI commands.
- Multiple sources, multiple tracks, mixed-media normalization, triplicate
  composition, audio normalization, or FPS enhancement.
- Replacing or removing the existing media-preparation scripts.
- Silent source relinking, overwriting, deletion, or modification.

## Observable requirements

- Given a supported source, opening it should create a project with a stable
  source reference and the metadata required by the selected foundation.
- Given a missing, unreadable, unsupported, or incomplete source, opening
  should return an actionable error and preserve the source and last valid
  project state.
- Given an opened source, the original file should remain unchanged.
- Given metadata that cannot support an unambiguous duration or position,
  the editor should report the limitation instead of silently inventing
  timing.

## Validation and evidence

- Run focused tests for source probing, metadata mapping, and explicit
  failure behavior using the repository's existing test runner.
- Run the protected baseline command:
  `python3 -m unittest discover -s tests`.
- Run a target-workstation import smoke test with representative local media
  selected through the TICKET-001 validation path.
- Record source metadata, error behavior, and source-preservation evidence at
  `evidence/open-supported-source-project.md` without private paths where
  they are not required.
- Record unavailable media/tool checks as blocked or skipped with a reason.

## Protected behavior

Existing command names, `framestudio_media.py`, `framestudio_concat.py`,
`framestudio_fps.py`, their tests, and source-safe partial-output behavior remain
available and unchanged.

## Definition of done

- The approved source-opening flow creates a non-destructive one-source
  project and exposes the required metadata.
- Missing, unsupported, unreadable, and ambiguous-source cases are explicit,
  actionable, and state-preserving.
- Focused automated coverage and the existing baseline remain green.
- Target-workstation import and source-preservation evidence is recorded.
- No playback, persistence, cutting, export, or future-phase behavior is
  claimed beyond this ticket's scope.
