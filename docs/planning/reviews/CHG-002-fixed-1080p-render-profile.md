# CHG-002 - Fixed 1080p Project Render Profile

**Change ID:** CHG-002
**Type:** Material planning change
**Status:** approved-and-applied
**Date:** 2026-08-21
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Owner:** repository planning and implementation in the active Phase 4 worktree
**Approval:** User-authorized by the 2026-08-21 requirement clarification:
“the resolution by default of the project will always be 1080p no matter the
dimensions of the input file. the rest of it like codec and stuff will not
matter because we already have it stablished in the render. and the fps will
be improved eventually for 60 using the fps improvement model so it doesn
matter right now”
**Source paths:** `docs/specs/project-scope.md`,
`docs/specs/future-product-direction.md`,
`docs/specs/capability-map.md`,
`docs/planning/phases/open/PHASE-004-combining-mixed-source-footage.md`,
`docs/planning/features/open/FEAT-012-previewing-and-exporting-mixed-source-edits.md`,
`docs/planning/tickets/open/TICKET-024-defining-mixed-source-output-canvas-and-timing-policy.md`,
`docs/planning/tickets/open/TICKET-026-implement-verified-mixed-source-export.md`,
`docs/planning/tickets/open/TICKET-027-verifying-mixed-source-round-trips-and-source-preservation.md`,
`.github/aidd-config.yml`
**Affected IDs:** PHASE-004, FEAT-012, TICKET-024, TICKET-026, TICKET-027,
CAP-005, CAP-007
**Last updated:** 2026-08-21

## Request and classification

The project output contract must use a fixed 1920x1080 render canvas regardless
of input dimensions or orientation, for both one-source and mixed-source
projects. Source codec, container, and related delivery details are already
established by the render profile and must not be inferred from source
differences. Frame-rate enhancement to 60 FPS is deferred to PHASE-007 and is
not a PHASE-004 acceptance requirement.

This is a material change because it replaces the approved mixed-source
maximum-dimension output policy and removes source-codec differences from the
current policy decision. It affects the active preview/export feature and its
verification evidence, but does not create a new capability or change stable
planning IDs.

## Decision

1. Project preview and export use a fixed 1920x1080 (1080p) output canvas.
2. Inputs are contain-scaled and letterboxed within that canvas so portrait
   and landscape sources are not silently stretched or cropped.
3. The established render profile owns the output container, codecs, audio
   handling, and pixel format. Source codec/container differences do not
   change the selected profile.
4. Current mixed-source timing remains deterministic for preview/export
   compatibility, but FPS enhancement and a final 60 FPS policy belong to
   PHASE-007.
5. Existing one-source source-safety, timing, stream-presence, and atomic
   publication guarantees remain protected. One-source inputs that already
   match 1920x1080 may retain the eligible stream-copy route; other
   one-source inputs use the established fallback profile.

## Affected-artifact inventory

| Artifact | Previous contract | Approved change | Action |
|---|---|---|---|
| PHASE-004 | Mixed output used the maximum input dimensions and considered source stream differences in normalization | Use a fixed 1080p project canvas and established render profile | Updated in place |
| FEAT-012 | Output canvas, timing, and normalization were source-policy decisions | Make canvas fixed and delivery profile-owned; defer 60 FPS | Updated in place |
| TICKET-024 | Define dimensions, source-driven stream normalization, and frame-rate policy | Define fixed 1920x1080 canvas and record current timing without planning FPS enhancement | Updated in place |
| TICKET-026 | Normalize incompatible dimensions, codecs, and timing through a mixed fallback | Render every mixed export through the fixed canvas and established profile | Updated in place |
| TICKET-027 | Verify output metadata against the prior mixed policy | Verify fixed 1920x1080 dimensions and preserve the FPS deferral boundary | Updated in place |
| CAP-005, CAP-007 | Future output policy could vary with source parameters | Establish project render profile as the output authority | Updated in place |
| One-source export path | Non-1080p source dimensions were retained by fallback validation | Force non-1080p sources through fixed-canvas fallback while preserving fast copy for matching sources | Updated in place |
| Mixed-source evidence | Prior evidence reported a 320x320 output | Preserve the historical result and add a superseding verification requirement | Appended |

## Normative behavior

- A project renders to 1920x1080 by default, regardless of input dimensions.
- Input aspect ratios are preserved through contain scaling and letterboxing.
- A one-source input that is not already 1920x1080 cannot use stream copy,
  because the fixed project canvas requires scaling and padding.
- Output codec, container, audio codec, and pixel format come from the
  established render profile rather than source codec comparison.
- Current frame-rate handling is an implementation detail for the active
  renderer; 60 FPS enhancement is deferred to PHASE-007.
- Mixed preview and export evidence must verify the fixed canvas and source
  preservation.

## Validation and remaining gates

- Output-policy and one-source planner tests expect 1920x1080 and confirm
  source codec/container changes do not alter the established render profile.
- Mixed-source export and GUI preview evidence must be rerun against the fixed
  canvas before user validation is terminal.
- TICKET-024, TICKET-026, and TICKET-027 remain `verifying`; no ticket is
  closed by this change.
- Local quality, real-media, and user-validation gates remain required.
- No commit, push, or remote-check claim is made by this planning change.
