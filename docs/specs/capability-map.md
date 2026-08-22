# Capability Map

**Capability map ID:** CAP-MAP-001
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Status:** confirmed
**Planning depth:** full
**Approval:** user-approved on 2026-08-21 before phase creation
**Owner:** repository planning; maintainer identity is not recorded
**Last updated:** 2026-08-21
**Repository revision:** `150d2f7`
**Repository map:** [`../planning/repo-map.md`](../planning/repo-map.md)
**Future direction:** [`future-product-direction.md`](future-product-direction.md)

## Purpose

This map connects the approved project objective and scope to the abilities
the product must provide. It covers both the narrow first horizon and the
confirmed deferred direction so later phase planning does not lose context.
It does not create phases, features, tickets, architecture decisions, or
implementation work.

## Capability Summary

| ID | Capability | Horizon | Status | Primary evidence |
|---|---|---|---|---|
| CAP-001 | Managing projects and source media | First | draft | `project-scope.md`, `future-product-direction.md` |
| CAP-002 | Playing and navigating an edit timeline | First | draft | `project-scope.md` |
| CAP-003 | Editing segments non-destructively | First, then expanded | draft | `project-scope.md`, `future-product-direction.md` |
| CAP-004 | Persisting and reopening edit state | First | draft | `project-scope.md`, `future-product-direction.md` |
| CAP-005 | Rendering fast, valid, and safe outputs | First, then expanded | draft | `project-scope.md`, `FAST-CONCAT-RESEARCH.md` |
| CAP-006 | Automating the project through a deterministic CLI | First, then expanded | draft | `project-scope.md`, `future-product-direction.md` |
| CAP-007 | Supporting multiple mixed-media sources | Future | draft | `future-product-direction.md` |
| CAP-008 | Handling audio per source input | Future | draft | `future-product-direction.md`, `resolve_concat.py` |
| CAP-009 | Applying reusable visual modifications | Future | draft | `future-product-direction.md` |
| CAP-010 | Composing linked triplicate focused-action layouts | Future | draft | `future-product-direction.md` |
| CAP-011 | Enhancing frame rate to 60 FPS | Future | draft | `future-product-direction.md`, `FPS-ENHANCEMENT-RESEARCH.md` |
| CAP-012 | Protecting media, state, and failure recovery | Cross-cutting | draft | `vision.md`, `project-scope.md`, existing scripts |

## Capability Definitions

### CAP-001 - Managing projects and source media

**Parent links:** OBJ-001, SCOPE-001  
**Horizon:** First  
**Status:** draft  
**Outcome:** The user can start a project from one source video, inspect the
source, and keep the source reference separate from the editable project
state.

**Observable behavior:**

- Given a supported source video, the application should create or open a
  project with a clear source reference.
- Given missing or unreadable source media, the application should report the
  problem without modifying the project or source.
- Given a project with a source reference, the application should expose the
  source metadata needed for playback, timeline, and export decisions.

**Affected surfaces:** project model, media probing, interface, CLI, FFmpeg.  
**Dependencies:** `python3`, `ffprobe`, local filesystem, project schema.  
**Risks:** moved or renamed sources; unsupported codecs; variable-frame-rate
media; incomplete metadata.  
**Evidence:** `project-scope.md` current horizon and dependencies;
`resolve_media.py` and `resolve_concat.py` probing behavior.  
**Coverage:** first-horizon import and source inspection.

### CAP-002 - Playing and navigating an edit timeline

**Parent links:** OBJ-001, SCOPE-001  
**Horizon:** First  
**Status:** draft  
**Outcome:** The user can see the edit in real time and control playback
position through a timeline.

**Observable behavior:**

- Given an opened project, the interface should show a real-time view of the
  current edit.
- The user should be able to play, pause, seek, and identify the current
  position.
- The timeline should show the source duration and current edited duration.
- Playback state should remain understandable when media buffering, seeking,
  or an unavailable backend prevents immediate output.

**Affected surfaces:** editor interface, playback backend, timeline model,
manual test harness.  
**Dependencies:** GUI/runtime choice, playback backend, source media access.  
**Risks:** seek latency, frame-accurate positioning, variable-frame-rate
behavior, UI responsiveness.  
**Evidence:** `project-scope.md` acceptance outcomes and verification plan.  
**Coverage:** first-horizon real-time playback, seek, and duration display.

### CAP-003 - Editing segments non-destructively

**Parent links:** OBJ-001, SCOPE-001  
**Horizon:** First, then expanded  
**Status:** draft  
**Outcome:** The user can change which portions of the source appear in the
edit without changing the source file.

**First-horizon behavior:**

- Given a playhead position, the user should be able to split the source into
  separate editable segments.
- Given a segment marked for deletion, the final duration and export should
  exclude that segment.
- Given ordered one-source segments, the user should be able to move a complete
  segment block left or right without changing its source interval or state.
- Segment changes should remain reversible through project state.

**Deferred expansion:**

- In PHASE-004, extend atomic block movement across mixed-source timelines,
  controlling ordering and gaps while preserving source ranges and owned state.
- In PHASE-004, select multiple blocks and copy/paste one or several blocks at
  an explicit timeline cursor while preserving relative order and assigning
  fresh identities to pasted instances.
- In PHASE-004, split blocks into fresh child identities that inherit the
  parent's segment-owned state.
- In PHASE-006, zoom into one or several segments and copy/paste reusable
  visual modifications between segments.
- Keep source-level settings distinct from segment-level modifications.

**Affected surfaces:** timeline/edit-state model, interface, project storage,
CLI, export planner.  
**Dependencies:** timeline coordinate model, project schema, cut semantics.  
**Risks:** exact frame boundaries, ripple behavior, gap semantics, invalid
source ranges, stream-copy limitations.  
**Evidence:** `project-scope.md`; `future-product-direction.md` segment editing
and reusable modifications.  
**Coverage:** first-horizon split/delete; future segment operations.

### CAP-004 - Persisting and reopening edit state

**Parent links:** OBJ-001, SCOPE-001  
**Horizon:** First, with future expansion  
**Status:** draft  
**Outcome:** The user can save an edit and later reopen it with the same
source reference and decisions.

**Observable behavior:**

- Given an active edit, saving should create a versioned, machine-readable
  project file without rewriting the source media.
- Given a saved project, reopening it should restore timeline segments,
  deletion state, current project settings, and final duration.
- Given an invalid or incompatible project file, the application should report
  the reason and preserve the last valid state.
- Future project versions should be able to store clip order, source-level
  audio decisions, transforms, linked triplicate instances, and export
  settings.

**Affected surfaces:** project storage, interface, CLI, migration logic.  
**Dependencies:** schema/version policy, source relinking policy.  
**Risks:** moved files, schema migration, partial writes, incompatible future
  features.  
**Evidence:** `project-scope.md` definition of done and
`future-product-direction.md` project-file requirements.  
**Coverage:** first-horizon save/reopen; future project evolution.

### CAP-005 - Rendering fast, valid, and safe outputs

**Parent links:** OBJ-001, SCOPE-001  
**Horizon:** First, then expanded  
**Status:** draft  
**Outcome:** The application exports the edited result using the fastest
  valid route without exposing corrupt output or changing the source.

**Observable behavior:**

- Given an edit eligible for stream copy or smart rendering, the exporter
  should use or report that fast path.
- Given an edit requiring decoding or re-encoding, the exporter should use a
  validated fallback and explain the reason.
- Given an export failure, the source and last valid output should remain
  untouched.
- A completed output should be verified for playability, expected duration,
  stream presence, and relevant metadata before it is exposed as complete.
- Project output should use the fixed 1920x1080 canvas, contain-scaling inputs
  that do not match it, and use the established render profile for codec,
  container, pixel-format, color, audio, and hardware settings.

**Affected surfaces:** export planner, FFmpeg integration, output validation,
interface, CLI.  
**Dependencies:** cut semantics, codec/container support, FFmpeg.  
**Risks:** keyframe boundaries, timestamp drift, incompatible streams,
  hardware-specific behavior, false success from fast but invalid commands.  
**Evidence:** `project-scope.md`; `FAST-CONCAT-RESEARCH.md`; existing atomic
partial-output and verification behavior in `resolve_media.py`.  
**Coverage:** first-horizon cut export; future smart rendering and delivery
profiles.

### CAP-006 - Automating the project through a deterministic CLI

**Parent links:** OBJ-001, SCOPE-001  
**Horizon:** First, then expanded  
**Status:** draft  
**Outcome:** Copilot or another agent can inspect and modify the same project
state that the interface edits.

**Observable behavior:**

- Given a project file, the CLI should inspect source, timeline, duration, and
  export state in a machine-readable form.
- The CLI should support first-horizon import, split, delete, save, reopen,
  and export operations.
- Future commands should cover segment movement, multi-selection,
  copy/paste, reusable modifications, triplicate mode, audio decisions,
  frame-rate settings, and export profiles.
- Invalid ranges, missing sources, unsupported media, unavailable tools, and
  unsafe render plans should return structured errors and non-success status.

**Affected surfaces:** CLI, project schema, timeline model, export planner,
automation tests.  
**Dependencies:** stable project schema and command/error contract.  
**Risks:** GUI/CLI behavioral drift, ambiguous partial operations, unstable
  schema, unclear idempotency.  
**Evidence:** `project-scope.md`; `future-product-direction.md` project and
agent-control requirements.  
**Coverage:** first-horizon agentable operations; future full editing model.

### CAP-007 - Supporting multiple mixed-media sources

**Parent links:** OBJ-001, SCOPE-001  
**Horizon:** Future  
**Status:** draft  
**Outcome:** The project can combine one or several videos with different
  dimensions, orientations, frame rates, codecs, and audio characteristics
  into a composed timeline.

**Observable behavior:**

- Given compatible or normalizable sources, the project should retain each
  source's identity and place it in a defined timeline order on the fixed
  1920x1080 project canvas.
- The preview should show the composed result with clear source boundaries.
- The exporter should contain-scale to the fixed canvas, use the established
  render profile, and report material transformations.
- The final duration should reflect ordering, gaps, and deleted segments.

**Affected surfaces:** project model, timeline, media normalization, preview,
  export, CLI.  
**Dependencies:** timeline/track model, output profile, codec policy.  
**Risks:** incompatible timestamps, aspect-ratio decisions, sync drift,
  normalization cost, unclear multi-track semantics.  
**Evidence:** `future-product-direction.md` multi-video timeline.  
**Coverage:** future multi-source workflow; not part of first-horizon scope.

### CAP-008 - Handling audio per source input

**Parent links:** OBJ-001, SCOPE-001  
**Horizon:** Future  
**Status:** draft  
**Outcome:** The application can automatically handle audio level per input
  video while preserving a consistent decision across that source's
  segments.

**Observable behavior:**

- Given an input with audio, analysis should produce an explicit level
  decision for that input.
- The default automatic decision should apply per source input, not be
  recalculated independently for every segment.
- The application should protect peaks, preserve useful dynamics, and expose
  the applied gain or normalization policy.
- Unsupported audio or failed analysis should produce a clear fallback or
  error, not silent success.

**Affected surfaces:** media analysis, source model, audio pipeline, preview,
  export, CLI.  
**Dependencies:** target loudness policy, peak/channel rules, output profile.  
**Risks:** inconsistent source material, clipping, channel layouts, analysis
  cost, mismatch between preview and final output.  
**Evidence:** `future-product-direction.md`; existing per-clip analysis in
`resolve_concat.py`.  
**Coverage:** future per-input audio handling; first horizon preserves source
audio only unless separately approved.

### CAP-009 - Applying reusable visual modifications

**Parent links:** OBJ-001, SCOPE-001  
**Horizon:** Future  
**Status:** draft  
**Outcome:** The user can apply visual modifications to one or several
  segments and reuse those modifications elsewhere.

**Observable behavior:**

- Given one segment or a selected group, the user should be able to apply
  zoom and pan/position changes.
- Given a modified segment, the user should be able to copy its applicable
  modifications to another segment or selected group.
- Given a modified segment, splitting should give both child segments the same
  modification bundle, while copy/paste should clone that bundle to a fresh
  segment identity.
- Moving a modified segment should preserve its bundle, and a visible Clean
  modifications button/action should reset the bundle to defaults without
  changing the source interval.
- Modifications should remain editable after save/reopen and should not alter
  the source.
- The system should distinguish shared changes from per-segment overrides.

**Affected surfaces:** transform model, timeline selection, interface,
  project storage, preview, export, CLI.  
**Dependencies:** segment identity, selection model, transform schema, and
  PHASE-004 block-clone semantics.
**Risks:** conflicting pasted settings, source-versus-segment scope, reset
  behavior for linked groups, preview performance, and future keyframe
  behavior.
**Evidence:** `future-product-direction.md` segment-level visual controls.  
**Coverage:** future reusable segment modifications.

### CAP-010 - Composing linked triplicate focused-action layouts

**Parent links:** OBJ-001, SCOPE-001  
**Horizon:** Future  
**Status:** draft  
**Outcome:** The user can activate a three-copy composition that presents
  portrait or vertically focused action in a landscape output.

**Observable behavior:**

- Given a portrait source, the mode should place one copy in the middle and
  two linked copies on the left and right.
- Given a landscape source whose useful action is concentrated in a vertical
  region, the user should be able to activate the same mode.
- Activating the mode should automatically create/select/link the three
  instances for shared editing.
- Shared X offset, Y offset, and zoom controls should update the linked
  copies so the user can focus on the desired action.
- Triplicate state copied or inherited through a split should create an
  independent linked group for the new segment while preserving the visual
  bundle; cleaning a triplicate segment should reset its linked group
  atomically.
- The relationship between the original segment and its three instances
  should remain visible, editable, and restorable after reopening.
- Background scaling, crop, blur, color, and exact placement should be
  configurable after their behavior is designed and tested.

**Affected surfaces:** composition model, transform/selection model, preview,
  timeline, project storage, export, CLI.  
**Dependencies:** multi-source composition, reusable modifications, output
  canvas policy.  
**Risks:** linked-state conflicts, aspect-ratio/crop choices, preview cost,
  automatic focus quality, render complexity.  
**Evidence:** `future-product-direction.md` triplicate portrait and
focused-action mode.  
**Coverage:** future triplicate feature; no first-horizon implementation.

### CAP-011 - Enhancing frame rate to 60 FPS

**Parent links:** OBJ-001, SCOPE-001  
**Horizon:** Future  
**Status:** draft  
**Outcome:** The application can optionally produce a validated 60 FPS result
  using motion interpolation rather than simple frame duplication.

**Observable behavior:**

- Given a source and an enabled 60 FPS setting, the pipeline should preserve
  timing, audio, scene-cut behavior, and the expected output frame count.
- The application should use a tested interpolation backend and report the
  selected model, precision, and hardware path.
- Artifact detection or failed backend validation should block unsafe output
  or use an explicit validated fallback.
- The user should be able to understand whether enhancement applies to the
  whole project, an input, or selected segments once timing semantics are
  defined.

**Affected surfaces:** timing model, interpolation pipeline, preview, export,
  CLI, GPU/runtime integration.  
**Dependencies:** multi-source timing semantics, interpolation backend,
  output profile, local GPU/runtime versions.  
**Risks:** hallucinated motion, scene-cut artifacts, frame-count drift,
  hardware-specific failures, high render cost.  
**Evidence:** `FPS-ENHANCEMENT-RESEARCH.md`, `FLOWFRAMES-RESEARCH.md`,
  `future-product-direction.md`.  
**Coverage:** future optional FPS enhancement.

### CAP-012 - Protecting media, state, and failure recovery

**Parent links:** OBJ-001, SCOPE-001  
**Horizon:** Cross-cutting  
**Status:** draft  
**Outcome:** Every editing and rendering operation is safe, observable, and
  recoverable.

**Observable behavior:**

- Original source media should never be silently overwritten, deleted, or
  moved by editor operations.
- Project and output writes should use temporary/partial files and atomic
  replacement where applicable.
- A failed operation should preserve the last valid project and output.
- Unsupported formats, missing tools, ambiguous timestamps, and failed
  validation should be visible to the user and CLI.
- Evidence should distinguish automated checks, real-media checks, and
  environment-dependent limitations.

**Affected surfaces:** all editor layers, existing scripts, project storage,
  export, CLI, tests, evidence.  
**Dependencies:** error contract, output validation, persistence strategy.  
**Risks:** partial writes, silent subprocess failures, stale project state,
  unsafe fallback behavior.  
**Evidence:** `vision.md`, `project-scope.md`, `AGENTS.md`, and existing
  partial-output/verification behavior in the Python scripts.  
**Coverage:** all first-horizon and future capabilities.

## Coverage Against Approved Scope

| Scope outcome | Capability coverage | Evidence expectation |
|---|---|---|
| Import and inspect one source | CAP-001 | Automated media/project tests |
| Real-time playback and seek | CAP-002 | Target-workstation manual smoke test |
| Split and delete segments | CAP-003 | Timeline unit tests plus manual smoke test |
| Show edited duration | CAP-002, CAP-003 | Timeline invariant tests and UI evidence |
| Save and reopen | CAP-004 | Persistence round-trip tests and manual reopen test |
| Fast verified export | CAP-005, CAP-012 | FFmpeg integration/output verification evidence |
| Deterministic agent operations | CAP-006 | CLI contract and smoke-test evidence |
| Preserve existing scripts | CAP-012 | Existing test suite and compatibility evidence |
| Multi-video future direction | CAP-007 | Future phase-specific media evidence |
| Per-input audio future direction | CAP-008 | Audio analysis and listening/metadata evidence |
| Reusable transforms and triplicate mode | CAP-009, CAP-010 | UI, render, and project round-trip evidence |
| 60 FPS future direction | CAP-011 | Frame-count, timing, artifact, and playback evidence |

## Cross-Capability Dependencies

- CAP-001 and CAP-004 establish the source and project identity used by every
  other capability.
- CAP-002 and CAP-003 require a stable timeline coordinate and timebase model.
- CAP-005 depends on explicit cut semantics and media compatibility rules.
- CAP-006 depends on stable project and timeline identifiers and structured
  errors.
- CAP-007 is a prerequisite for the future multi-source versions of CAP-008,
  CAP-010, and CAP-011.
- CAP-009 is a prerequisite for shared transforms in CAP-010.
- CAP-012 constrains every capability and must be verified alongside each
  implementation.

## Coverage Gaps and Decisions Required Before Phase Planning

The following decisions are still unresolved and must be addressed in phase
entry conditions or an explicit architecture/discovery decision:

- GUI/runtime and packaging approach.
- Playback backend and real-time seek behavior.
- Versioned project schema and source relinking policy.
- Frame-accurate versus keyframe-bound split semantics.
- Smart-render eligibility and fallback behavior.
- First-horizon audio preservation behavior.
- Multi-source track/order/gap model.
- Audio targets, peak protection, and channel policy.
- Triplicate background treatment and automatic focus behavior.
- Codec/container profiles for previews, intermediates, and final delivery.
- FPS backend, model, precision, artifact gate, and scope of enhancement.
- CLI command grammar, identifiers, structured errors, and idempotency.
- Practical target-workstation GUI/manual-test harness.

## Approval and Handoff

This capability map is confirmed for phase planning. Phase planning may create
`PHASE-*` entries that map to these capabilities. No features or tickets are
created by this artifact.

## Source References

- [`vision.md`](../../vision.md)
- [`project-scope.md`](project-scope.md)
- [`future-product-direction.md`](future-product-direction.md)
- [`../planning/repo-map.md`](../planning/repo-map.md)
- [`FAST-CONCAT-RESEARCH.md`](../../FAST-CONCAT-RESEARCH.md)
- [`FLOWFRAMES-RESEARCH.md`](../../FLOWFRAMES-RESEARCH.md)
- [`FPS-ENHANCEMENT-RESEARCH.md`](../../FPS-ENHANCEMENT-RESEARCH.md)
- Existing implementation surfaces: `resolve_media.py`, `resolve_concat.py`,
  `resolve_fps.py`, and `tests/`.
