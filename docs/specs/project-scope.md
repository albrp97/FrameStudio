# Project Scope Handoff

**Scope ID:** SCOPE-001
**Objective ID:** OBJ-001
**Status:** confirmed
**Planning depth:** full
**Last updated:** 2026-08-21
**Approval:** user-approved
**Repository map:** `docs/planning/repo-map.md`

## Objective

Create a fast, local Linux editor that replaces the user's basic DaVinci
Resolve cut workflow without attempting to reproduce Resolve's full feature
set.

## Problem

The current repository contains useful media-preparation, concatenation, and
FPS scripts, but it does not yet provide an interactive editor with a
real-time preview, timeline state, non-destructive project persistence, or a
simple cut/export workflow.

## Desired Outcome

The user can work through a focused interface to import one video, review it,
split and delete unwanted segments, save and reopen the edit, and export a
playable result quickly and safely. The same edit state is available through
a deterministic machine-readable CLI surface for Copilot-assisted operations.

## Current Horizon

Included:

- One source video per project.
- Import and source-media inspection.
- Real-time playback view with play, pause, and seek.
- A timeline representing the source and its edited segments.
- Split at a selected position.
- Delete one or more segments.
- Move selected segment blocks left or right.
- Visible edited duration/final output length.
- Non-destructive project save and reopen.
- Export of the edited result.
- A fixed 1920x1080 (1080p) project canvas for preview and export, regardless
  of input dimensions; mismatched inputs are contain-scaled and letterboxed.
- Fast-path export using stream-copy/smart rendering when valid.
- Explicit reliable fallback behavior when stream copy cannot satisfy the
  requested edit.
- Preservation of original media.
- Deterministic CLI/project operations suitable for agent automation.
- Automated tests and a real-media playback/export smoke test.

## Deferred / Out of Scope

- Multiple source videos in one timeline.
- Multiple video or audio tracks.
- Multiple mixed-source timelines with different dimensions, frame rates,
  codecs, or source normalization.
- Per-input audio-level analysis or normalization.
- Portrait triplicate/background composition and linked transforms.
- Zoom/pan/keyframing or segment-level visual modifications beyond cutting.
- Automatic FPS enhancement to 60 FPS.
- Advanced effects, transitions, titles, captions, color grading, and full
  Resolve parity.
- Cloud, collaboration, accounts, telemetry, and non-Linux support.
- Destructive deletion or replacement of source files.

## Future Direction (Captured, Deferred)

The broader feature intent is recorded in
[`future-product-direction.md`](future-product-direction.md) so it remains
available for later capability and phase planning without expanding the first
horizon.

The deferred direction includes:

- A multi-video timeline with clips that may have different dimensions,
  orientations, frame rates, codecs, and audio characteristics.
- A fixed 1920x1080 project canvas is used for every project; source aspect
  ratios are preserved with contain scaling and letterboxing.
- Segment split, delete, copy/paste, movement left or right, and multi-selection
  using atomic timeline blocks.
- Block moves preserve source ranges and segment state; block copy/paste
  creates fresh segment identities, preserves relative order, and inserts at
  an explicit timeline cursor without changing the original blocks.
- Splitting a segment clones its segment-owned state to both resulting
  segments.
- Zoom, reusable segment modifications, and a visible Clean modifications
  button/action that resets a segment's visual state without changing its
  source range.
- Automatic audio level handling per input video, not independently per
  segment.
- A triplicate portrait/focused-action mode with one centered copy and two
  side copies, automatic linking/selection, and shared X/Y/zoom controls.
- Triplicate state is part of the segment modification bundle; copied or split
  segments receive independent linked groups, and cleaning a triplicate
  segment resets that group atomically.
- Efficient smart rendering, stream copy when valid, and evidence-based
  codec/container/export profiles.
- Optional validated FPS enhancement to 60 FPS.
- Versioned project files and deterministic CLI operations covering the same
  future editing model.

This is confirmed product context, not an approved capability map, phase plan,
feature list, or implementation backlog.

## Candidate Outcome Abilities

These are discovery-level abilities, not yet capability artifacts:

- Project lifecycle and source reference management.
- Timeline playback and navigation.
- Non-destructive segment editing.
- Fast validated export.
- Deterministic project/CLI automation.
- Safe failure recovery and output verification.

A capability map must be approved before these are decomposed into delivery
children.

## Affected Surfaces

- New editor interface and playback layer.
- New project persistence layer.
- New timeline/edit-state model.
- New export planning and FFmpeg integration.
- New CLI/agent automation surface.
- Existing `resolve_media.py`, `resolve_concat.py`, and `resolve_fps.py` as
  retained compatibility surfaces.
- Existing tests and documentation.

## Stakeholders

- Primary user and repository maintainer: the project owner.
- No additional stakeholders are currently identified.

## Dependencies

- Linux filesystem access.
- `python3`.
- `ffmpeg` and `ffprobe`.
- A playback/runtime stack to be selected.
- A GUI/runtime packaging approach to be selected.
- Existing scripts and their tested media-processing behavior.

## Durable Constraints

- Local, offline, single-user operation.
- Linux/current-workstation target only for the first horizon.
- Original media preservation.
- Existing scripts remain available.
- Fast export is preferred, but invalid or unsafe output is unacceptable.
- GUI is primary; CLI is deterministic and agentable.
- No credentials, cloud services, or sensitive data in project artifacts.

## Risks

- Stream copy may not support exact frame-accurate cuts for every
  codec/container.
- Real-time playback and precise timeline interaction may require a different
  runtime or media backend than the existing Python/curses tools.
- Project files may become invalid if source files move or are renamed unless
  relinking behavior is defined.
- FFmpeg failures, unsupported codecs, timestamps, and variable-frame-rate
  sources can make duration and cut semantics ambiguous.
- Introducing a GUI stack could increase packaging complexity or duplicate
  media logic if boundaries are not established.
- Existing GPU-specific research may not generalize beyond the current
  machine.

## Protected Existing Behaviors

- Existing scripts remain callable by their current command names.
- Existing tests and safe partial-output/verification behavior remain intact.
- Original inputs are not deleted or overwritten by the editor.
- Existing CLI workflows remain usable while the editor is introduced.

## Acceptance Outcomes

- Given one supported source video, the interface should import it and show a
  playable timeline.
- Given a selected timeline position, the editor should split the source into
  separate editable segments.
- Given a segment marked for deletion, the editor should exclude it from the
  final duration and export.
- Given a saved project, reopening it should restore its source reference and
  edit decisions.
- Given an export request, the tool should choose or report a valid fast path,
  create a verified playable output, and leave the source unchanged.
- Given a CLI edit request, the tool should make the same project changes as
  the interface or return a clear structured error.
- Given an unsupported or failed operation, the tool should surface the reason
  and preserve the last valid project/output.

## Verification Plan

- Unit tests for project serialization, timeline invariants, split/delete
  transformations, duration calculations, and export-plan decisions.
- Integration tests around FFmpeg command construction and output verification
  using small generated fixtures where practical.
- Manual real-media smoke test on the target workstation covering import,
  playback, seek, split, delete, save, reopen, and export.
- Manual check that the original source remains byte-for-byte or operationally
  unchanged after the workflow.
- CLI smoke test using a machine-readable project and deterministic commands.
- Existing baseline test suite must remain green.

## Evidence Plan

- Record the baseline test result before editor implementation.
- Attach automated test output to the active ticket evidence.
- Record target-workstation playback/export observations, source preservation,
  output metadata, and elapsed export time.
- Capture unresolved codec/backend limitations rather than treating them as
  passes.
- Keep project files and sample media paths free of credentials and private
  data.

## Definition of Done for This Horizon

- One source can be imported, played, edited through split/delete, saved,
  reopened, and exported through the primary interface.
- The final duration and timeline state are correct after reopening.
- The original source is preserved.
- The export is verified and playable.
- Deterministic CLI/project operations cover the same basic edit.
- Automated and manual evidence exists.
- Existing scripts and baseline tests remain functional.

## Open Questions Before Child Planning

1. Which GUI/runtime stack best meets real-time playback, timeline control,
   Linux packaging, and reuse of the current Python/FFmpeg code?
2. Which playback backend should provide reliable seeking and frame timing?
3. What versioned project-file schema and source relinking policy are needed?
4. Are splits frame-accurate, keyframe-bound, or both with an explicit tradeoff?
5. What should happen when smart rendering cannot preserve an exact cut?
6. Is source audio simply preserved in the first horizon, or are any audio
   operations required before the later normalization feature?
7. What structured CLI command and error format should agents use?
8. What local GUI/manual-test harness is practical on this workstation?
