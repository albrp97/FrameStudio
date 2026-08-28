# Future Product Direction

**Record ID:** FUTURE-001
**Parent objective:** OBJ-001
**Parent scope:** SCOPE-001
**Status:** confirmed context; deferred from the first horizon
**Last updated:** 2026-08-26

## Purpose

This document preserves the user's broader product intent so future planning
does not lose features that are intentionally deferred from the first
implementation. It is a durable context record, not an implementation
backlog, capability map, phase plan, or approval to build every item.

The first horizon remains the one-source cut workflow defined in
[`project-scope.md`](project-scope.md).

## Long-Term Product Shape

The project should grow from the current media-preparation scripts into a
focused personal video editor. It should provide a real-time view of the
edited result, a timeline containing the selected clips and segments, safe
non-destructive projects, and fast exports without trying to reproduce every
feature of DaVinci Resolve.

The interface is the primary workflow. The same project state and meaningful
editing operations should also be available through a deterministic CLI and
machine-readable project format so Copilot or another agent can inspect,
change, and render an edit.

## Future Feature Inventory

### Multi-video timeline

- Import one or several videos into a project.
- Allow source videos with different dimensions, orientations, frame rates,
  codecs, and other media parameters.
- Show all clips in a timeline with real-time playback of the composed edit.
- Pause, play, seek, and inspect the current position and final output length.
- Use a fixed 1920x1080 project canvas by default, contain-scaling and
  letterboxing inputs that do not match it.
- Move clips or segments left and right and keep the resulting duration
  visible.
- Define how source boundaries, gaps, ordering, and multiple tracks should
  behave before implementation.

### Segment editing and reusable modifications

- Split a source clip into editable segments at the playhead or a selected
  position.
- Delete segments non-destructively and update the final duration immediately.
- Copy and paste segments within a project.
- Treat each segment as an atomic timeline block. Moving a block preserves its
  source interval, source identity, deletion state, and segment-owned state;
  copying creates a new segment instance with a fresh identity and the same
  persisted block state.
- Pasting one or several copied blocks inserts them at an explicit timeline
  cursor while preserving their relative order and leaving the originals
  unchanged.
- Splitting a block creates fresh child identities and gives both children the
  parent's segment-owned state.
- Copy visual or timeline modifications from one segment to another segment or
  to several selected segments.
- Zoom into one segment or a group of selected segments for precise editing.
- Support selecting several segments for shared operations.
- Preserve the distinction between source-level settings and segment-level
  edits.

### Automatic per-input audio handling

- Analyze and automatically adjust audio level independently for each input
  video.
- Apply the input's level handling to that source across its timeline
  segments; do not recalculate a different automatic level for every segment
  by default.
- Preserve source dynamics where possible and expose the applied gain or
  normalization decision.
- Establish target loudness, peak protection, channel handling, and fallback
  behavior through measured tests before implementation.

### Triplicate portrait and focused-action mode

- Provide a mode for a portrait video inside a landscape output: one copy in
  the middle and two copies on the left and right.
- Support using the same source three times as a visual background/focus
  treatment for portrait or mostly-vertical action.
- Allow the user to activate the mode for a clip or selected segments.
- Automatically select or link the three copies so a shared edit applies to
  all of them.
- Allow shared X offset, Y offset, and zoom adjustments to search for and
  focus on the important action.
- Support a 1080p source where the useful action is concentrated in a
  vertical region, not only a physically portrait source.
- Preserve a clear relationship between the source segment and its linked
  triplicate instances.
- Decide later how background copies are scaled, cropped, blurred, colored,
  and positioned; those visual details are not yet fixed.

### Segment-level visual controls

- Apply zoom and pan to one segment or multiple selected segments.
- Treat zoom, X/Y offsets, triplicate mode, and its layout parameters as one
  segment-owned modification bundle.
- Moving a segment preserves its modification bundle. Splitting or
  copy/pasting a segment clones the bundle to the resulting segment instance
  or split children without sharing their identities.
- Provide a visible **Clean modifications** button/action that resets the
  selected segment's visual bundle to defaults without changing its source
  interval.
- When triplicate mode is active, a copied or split segment receives a new
  independent linked group whose three instances retain the cloned bundle;
  cleaning that segment resets the linked group atomically.
- Keep transforms editable after saving and reopening the project.
- Decide later whether keyframes, interpolation, and animation belong in this
  focused editor or should remain outside its scope.

### Efficient render and delivery

- Use the fastest valid rendering path for each edit.
- Prefer stream-copy or smart-render behavior when the source codec,
  container, timestamps, and requested cuts allow it.
- Fall back to a validated encode when exact cuts, composition, scaling,
  frame-rate conversion, audio changes, or incompatible inputs require
  decoding.
- Avoid treating a command that finishes quickly as successful when it creates
  invalid timestamps, missing streams, or an unplayable file.
- Select practical container, codec, pixel-format, color, audio, and hardware
  settings from reproducible tests on the target workstation.
- Treat the established render profile as the authority for output delivery;
  input codec/container differences do not change the project canvas or
  delivery profile.
- Retain the source-safe temporary-output, verification, and cleanup policy.
- Use the existing fast-concatenation research as evidence, not as a
  universal promise for every future edit.

### Automatic frame-rate enhancement

- Offer an optional path to enhance video to 60 FPS.
- Prefer a validated motion-interpolation workflow rather than merely
  duplicating or blending frames.
- Preserve timing, audio, scene-cut behavior, and exact output frame counts.
- Keep model, precision, GPU, and fallback choices evidence-based; the
  existing RIFE/RVE research records current local findings.
- Decide whether enhancement is project-wide, per source input, or
  segment-selectable after multi-video timing semantics are defined.

### Responsive preview and evidence-based media processing

- Optimize preview feedback while the user moves the cursor, clicks, or
  scrolls along the timeline through measured experiments on the target
  workstation.
- Inspect the public Lossless Cut implementation as a research reference,
  while keeping its checkout disposable and separate from the runtime.
- Compare the current concat-first mixed-FPS enhancement route with a
  per-source smart-render, enhancement, and final-concatenation route using
  matched timing, correctness, storage, and quality measurements.
- Research classical and AI approaches for upscaling, denoising, deblocking,
  deblurring, and low-bitrate artifact recovery before selecting any future
  production model or dependency.
- Keep restoration research separate from implementation until quality,
  temporal stability, performance, licensing, runtime, and fallback gates are
  explicit.

### Project files and agent control

- Store source references, clip order, segment boundaries, deletion state,
  source-level audio decisions, transforms, triplicate links, and export
  settings in a versioned, machine-readable project file.
- Reopen projects without modifying original source media.
- Provide deterministic CLI operations for importing sources, selecting and
  moving segments, splitting, deleting, copying/pasting, applying
  modifications, configuring triplicate mode, inspecting duration, and
  exporting.
- Return structured errors for missing sources, invalid ranges, unsupported
  media, unavailable tools, and unsafe render plans.
- Define source relinking, moved-file detection, project version migration,
  and compatibility behavior before the project format becomes durable.

## Future Product Principles

- Keep the workflow substantially simpler than a full professional NLE.
- Prefer fast feedback and fast export without hiding quality or compatibility
  tradeoffs.
- Make source-level versus segment-level behavior explicit.
- Make linked operations visible and reversible.
- Keep all edits non-destructive and preserve original media.
- Let the interface and CLI express the same underlying project operations.
- Validate media behavior on the target workstation with real representative
  footage.

## Deferred Design Questions

- Which GUI/runtime and playback backend can provide responsive real-time
  playback while reusing the existing Python and FFmpeg work?
- Should multi-video editing use one timeline, multiple tracks, or a composed
  sequence model?
- What frame-accuracy and smart-render guarantees can be provided for each
  container and codec?
- Which audio measurement and target policy best matches the user's footage?
- How should triplicate instances be represented and edited as a linked group?
- How should automatic focus selection work, and when should it require manual
  adjustment?
- Which codec/container profiles are best for fast previews, intermediate
  renders, and final delivery?
- Which FPS-enhancement backend and quality gates remain reliable as local
  GPU/runtime versions change?
- What project-file schema, migration, source relinking, and CLI compatibility
  policy should be supported?

## Source References

- User-confirmed product description in the project-bootstrap conversation,
  including the one-source first horizon and the deferred feature inventory.
- [`vision.md`](../../vision.md)
- [`project-scope.md`](project-scope.md)
- [`FAST-CONCAT-RESEARCH.md`](../../FAST-CONCAT-RESEARCH.md)
- [`FLOWFRAMES-RESEARCH.md`](../../FLOWFRAMES-RESEARCH.md)
- [`FPS-ENHANCEMENT-RESEARCH.md`](../../FPS-ENHANCEMENT-RESEARCH.md)
