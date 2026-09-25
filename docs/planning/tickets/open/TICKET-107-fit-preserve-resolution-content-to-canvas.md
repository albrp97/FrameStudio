# TICKET-107 - Fit Preserved-Resolution Content to the Output Canvas

**Ticket ID:** TICKET-107
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-008
**Feature:** FEAT-028
**Capability links:** CAP-005, CAP-009, CAP-010, CAP-012
**Status:** verifying
**Horizon:** future
**Priority:** 1
**Owner:** repository implementation in the active worktree
**Approval:** User-authorized as part of the complete-worktree delivery under
CHG-011.
**Last updated:** 2026-09-24
**Source paths:** `docs/planning/reviews/CHG-011-deliver-authorized-existing-worktree-changes.md`,
`docs/planning/features/open/FEAT-028-adding-optional-upscale-enhancement.md`,
`framestudio/composition_render.py`, `tests/test_editor_composition.py`,
`framestudio/export_smart_render.py`, `.github/aidd-config.yml`
**Dependencies:** fixed 1920x1080 output-canvas contract and existing
preserve-resolution composition path
**Risks:** crop/pad changes could alter portrait composition or accidentally
downscale restoration intermediates before the final composition stage
**Affected surfaces:** shared preview/export composition filters, normal
segments, triplicate segments, generated-media output, and tests
**Evidence path:** `evidence/ticket-107-preserve-resolution-canvas-fit.md`
**Protected behaviors:** the fixed output canvas, source preservation,
portrait and triplicate framing, restoration/upscale input resolution, output
frame rate/count, audio, and verified atomic publication

## Outcome

Oversized source content in preserve-resolution composition fits the fixed
output canvas without being cropped, while restoration/upscale intermediates
retain their source-resolution requirements.

## Scope

- Detect source content that exceeds the final canvas in both dimensions.
- Use the established aspect-preserving contain-and-pad route only for that
  final composition case.
- Retain preserve-resolution behavior for content that does not exceed the
  canvas and for restoration/upscale intermediates.
- Verify the resulting rendered output, not only the generated filter graph.

## Explicit non-goals

- Changing the fixed 1920x1080 output canvas or output codecs.
- Downscaling sources before restoration/upscale processing.
- Changing transform offsets, crop policy for intentionally zoomed content,
  or triplicate layout.

## Observable acceptance criteria

- Given oversized landscape content and preserve-resolution composition, the
  final video fits within the 1920x1080 canvas without losing image edges.
- Given oversized portrait content, the final video preserves aspect ratio
  and the established composition/crop behavior.
- Given content at or below the canvas size, preserve-resolution behavior
  remains unchanged.
- Given an eligible restoration/upscale source, its intermediate is not
  downscaled before the model stage.
- Given any export, frame count, duration, audio policy, source bytes, and
  atomic publication remain valid.

## Validation

- Automated functionality test that renders generated oversized media and
  probes the final dimensions and visible framing.
- Focused filter-graph coverage for landscape, portrait, and triplicate cases.
- Existing export, composition, and source-preservation tests plus repository
  quality, smoke, and contract gates.
- Target-workstation visual confirmation with window-only before/after
  evidence.

## User-validation plan

- **Setup:** use generated or approved local 3840x2160 and portrait sources
  with preserve-resolution composition enabled.
- **Steps:** render both source orientations, inspect all canvas edges and
  triplicate framing if used, probe output metadata, and compare source hashes.
- **Expected result:** output remains 1920x1080, the oversized landscape
  content is fit rather than cropped, portrait behavior remains intentional,
  and no pre-restoration downscale occurs.
- **Failure paths:** missing edges, distorted aspect ratio, wrong output
  dimensions, changed source bytes, or reduced restoration input resolution.
- **Cleanup:** remove only generated temporary fixtures and outputs after
  evidence is retained.
- **Evidence response:** return `PASS`, `FAIL`, or `BLOCKED` with output
  metadata, source-preservation observations, and screenshot paths.
- **Pass criteria:** both orientations render safely with unchanged protected
  export behavior.
