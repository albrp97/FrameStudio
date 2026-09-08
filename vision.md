# FrameStudio Project Vision

> This document is the source of truth for project direction.
> Revisit when goals, users, or constraints change.

**Objective ID:** OBJ-001
**Status:** confirmed
**Last updated:** 2026-09-07

## Overview

FrameStudio is a local Linux video-editing tool for one user. It replaces the
basic cut-and-export workflow currently performed in a traditional editor
without attempting to become a full replacement for DaVinci Resolve.

The normal workflow is an interface with real-time video playback and a
timeline. A deterministic CLI and machine-readable project format provide an
automation surface for Copilot and other agents when the user wants edits or
exports performed without manually operating the interface.

The first delivery horizon was intentionally narrow: import one video, review
it in a timeline, split and delete unwanted segments, save and reopen the
project, and export the result while preserving the original source.

That foundation has since been extended through the approved PHASE-004 through
PHASE-008 delivery work. The current product also supports mixed-source
timelines, source-level audio decisions, reusable focus controls, linked
triplicate composition, optional 60 FPS and upscale enhancement, background
audio analysis, autosave/recovery, and resumable verified exports. The
current user-facing contract is documented in [`README.md`](README.md), while
the phase and ticket records remain the traceable delivery history.

## Goals

- Provide a responsive interface for basic non-destructive editing of one
  source video.
- Make play, pause, seek, split, segment deletion, and final-duration feedback
  direct and understandable.
- Save edits as a reopenable project rather than modifying source media.
- Export through the fastest valid path, preferring stream-copy smart rendering
  when the requested edit permits it and using a reliable fallback when it
  does not.
- Keep a deterministic, machine-readable CLI surface for agent-assisted
  project inspection and editing.
- Preserve the existing media-preparation, concatenation, and FPS scripts
  while the editor is developed.
- Keep the editor model extensible without turning it into a full
  professional NLE.

## Original Future Direction and Remaining Work

The broader product intent is preserved in
[`docs/specs/future-product-direction.md`](docs/specs/future-product-direction.md).
That record was created before the later phases and includes capabilities that
are now delivered as well as capabilities that remain future work. Consult
the closed phase and feature indexes for current implementation status.
Remaining direction includes multiple tracks, advanced audio editing,
keyframed or animated transforms, richer compositor behavior, broader
packaging, and other features beyond the focused editor contract.

## Historical First-Horizon Boundaries

The following list records what was intentionally excluded from the original
first horizon. Most of the listed editor capabilities were later delivered
through approved scope extensions; the list is retained to explain the
sequencing decision.

- Reimplementing DaVinci Resolve or becoming a general-purpose NLE.
- Cloud storage, accounts, collaboration, telemetry, or multi-user workflows.
- Replacing or removing the existing Python workflow scripts in the first
  horizon.
- Multiple source clips or multiple timeline tracks in the first horizon.
- Mixed-dimension or mixed-frame-rate normalization in the first horizon.
- Triplicate portrait/background composition in the first horizon.
- Per-input audio-level normalization in the first horizon.
- Automatic FPS enhancement to 60 FPS in the first horizon.
- Advanced effects, color grading, transitions, titles, captions, or
  compositor features in the first horizon.

## Current Non-Goals

- Multiple video or audio tracks and timeline mixing beyond the current
  composed sequence model.
- Keyframes, animated transforms, advanced transitions, titles, captions,
  color grading, and full compositor behavior.
- Cloud storage, accounts, collaboration, telemetry, and non-Linux support.
- Replacing or removing the existing compatibility workflows.

## Key Constraints

- The supported environment for the first horizon is this Linux workstation;
  broader operating-system and hardware support is deferred.
- The tool is local and offline. Source media and project files remain on the
  local filesystem.
- Original source files must be preserved. Editing and export operations must
  not overwrite them.
- Existing scripts and their current behavior remain available during the
  transition.
- FFmpeg and ffprobe remain the media-processing foundation unless a later
  evidence-based decision replaces a specific component.
- Fast export is preferred, but speed must not silently produce invalid timing,
  missing streams, or corrupted output.
- Project files must be non-destructive, machine-readable, versionable, and
  safe to reopen after the application exits.
- The interface is the primary user experience; CLI behavior must remain
  deterministic and suitable for automation.
- Architecture choices must be validated on the target workstation rather than
  selected only from theoretical benchmarks.

## Delivery / Operational Readiness

- Existing Python validation is `python3 -m unittest discover -s tests` and
  Python compilation with `python3 -m py_compile`.
- The first editor must have automated coverage for project and timeline
  transformations, segment operations, export-plan decisions, and failure
  handling.
- Each meaningful editor change must include a real-media smoke test covering
  playback, a basic edit, project persistence, and export.
- Export should use temporary/partial output and verification before exposing
  the final file.
- Failures must leave source media and the last valid project/output untouched.
- The application should surface unavailable media tools and unsupported
  operations explicitly rather than silently falling back to an unsafe result.
- Release or merge evidence must distinguish automated checks from manual
  playback/export evidence.
- The GUI runtime, project schema, and playback backend are confirmed in
  [`docs/specs/editor-foundation-decision.md`](docs/specs/editor-foundation-decision.md).
  Packaging beyond the local Linux setup remains future work.

## Architectural Decisions

| Decision | Rationale |
|---|---|
| Retain the existing Python media scripts as a compatibility surface. | They already implement tested FFmpeg probing, conversion, concatenation, FPS processing, progress reporting, and safe partial-output behavior. |
| Treat the editor project as non-destructive state separate from source media. | The user requires original preservation and reopenable edits. |
| Prefer smart rendering/stream copy when valid, with an explicit fallback encode. | The user's priority is the fastest export, while mixed codecs and frame-accurate cuts may require decoding or re-encoding. |
| Keep the GUI primary and the CLI deterministic and machine-readable. | The user edits interactively but wants Copilot/agents to be able to inspect and modify projects. |
| Use Python/PyGObject with GTK 4, FFmpeg raw-frame playback, and versioned JSON projects. | The target workstation has a working GTK 4/PyGObject runtime and FFmpeg/ffprobe. GStreamer cannot decode the generated MP4 probe fixture because the required demuxer plugins are unavailable, so the initial preview uses a managed FFmpeg pipe. |

## Product identity and compatibility

FrameStudio is the canonical product, Python package, command-line identity,
application ID, and project-file naming convention. Existing `resolve_*`
scripts, `resolve-*` commands, imports, cache locations, and `.resolve.json`
projects remain supported as compatibility surfaces while users migrate.

## User Experience Principles

- Fast to understand: the basic cut workflow should be visible without
  Resolve-style feature overload.
- Responsive: playback, seeking, and timeline manipulation should provide
  immediate feedback or clearly expose processing state.
- Safe by default: source files are never silently changed or deleted.
- Reversible: edits are project state and can be changed without damaging the
  source.
- Honest: unsupported formats, failed exports, and unavailable acceleration
  are visible and actionable.
- Agentable: the same meaningful operations exposed by the interface should
  have deterministic project/CLI representations.
- Extensible without bloat: future capabilities should fit the model without
  forcing the first workflow to become a full NLE.

## Success Criteria

- The user can complete the focused editing workflow without opening DaVinci
  Resolve: import sources, play/seek them, edit segments, save/reopen, and
  export safely.
- Reopening a saved project restores the same source reference and edit
  decisions without altering the original media.
- Eligible edits use a validated stream-copy/smart-render path and report when
  a fallback encode is required.
- Exported media is playable, has the expected duration and streams, and is
  not exposed as complete until validation succeeds.
- A CLI or agent can inspect and apply the same basic edit operations through
  the project representation.
- A cancelled or failed export can resume validated work without repeating
  completed stages.
- Existing scripts and their baseline tests continue to work while the editor
  is introduced.
- The resulting workflow is measurably faster and simpler for the user's
  normal basic edits than opening Resolve for the same task.
