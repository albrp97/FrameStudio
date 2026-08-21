# PHASE-006 - Focusing and Composing Important Action

**Phase ID:** PHASE-006  
**Parent links:** OBJ-001, SCOPE-001  
**Capability links:** CAP-005, CAP-009, CAP-010, CAP-012  
**Sequence:** 6  
**Status:** confirmed  
**Horizon:** future  
**Owner:** repository planning; maintainer identity is not recorded  
**Approval:** user-approved on 2026-08-21 before feature generation  
**Source paths:** `vision.md`, `docs/specs/project-scope.md`,
`docs/specs/capability-map.md`, `docs/planning/phases.md`,
`docs/planning/repo-map.md`, `.github/aidd-config.yml`  
**Migration source:** `docs/planning/phases.md`, inline section
`PHASE-006 - Focusing and Composing Important Action`; migrated on
2026-08-21 with the phase content preserved.  
**Affected surfaces:** segment transforms, selection, linked triplicate
composition, preview, output canvas, project persistence, CLI, and renderer  

## Outcome

The user can focus the viewer's attention through reusable
segment transforms and a linked triplicate layout for portrait or
vertically concentrated action.

### Included

- Apply zoom and X/Y position changes to one segment or selected segments.
- Copy and paste applicable visual modifications between segments.
- Preserve transforms across save/reopen and expose shared versus overridden
  values.
- Activate a triplicate mode for portrait or mostly vertical action.
- Place one copy in the middle and two linked copies on the left and right.
- Automatically select or link the three instances when the mode is enabled.
- Apply shared X offset, Y offset, and zoom controls to the linked copies.
- Support a 1080p source whose important action is concentrated in a vertical
  region, not only a physically portrait source.
- Preview and export the composition, including a defined output canvas.
- Expose the linked state through the project file and CLI.

### Explicit non-goals

- Full compositing, arbitrary effects, color grading, or professional
  keyframing unless separately approved.
- An automatic focus decision that silently replaces user control.
- Unvalidated background scaling, crop, blur, color, or placement behavior.

### Entry conditions

- PHASE-004 provides multi-source/segment identity and selection semantics.
- PHASE-005 provides the output and delivery profile required by composition.
- The transform model defines coordinate space, aspect-ratio behavior, and
  source-versus-segment ownership.
- Triplicate linking, automatic selection, and background treatment are
  explicitly specified.
- Representative portrait and vertically focused landscape footage is
  available for manual evaluation.

### Exit conditions

- A user can apply, review, copy, paste, save, reopen, and export transforms
  on one or several segments.
- Triplicate mode creates three visibly linked instances, selects them
  automatically, and updates all three through shared X/Y/zoom changes.
- Portrait and vertical-action examples preserve intended focus without
  unexpected crop or aspect-ratio behavior.
- Project and CLI round trips preserve linkage and transforms.
- Preview and final render agree within the approved output tolerance.
- UI, render, persistence, and manual visual evidence is recorded.

### Dependencies and risks

- Depends on stable segment identity, selection, output canvas, and project
  schema.
- Linked-instance state can become ambiguous when segments are copied,
  deleted, or reordered.
- Automatic focus quality may be unreliable and must remain user-correctable.
- Composition increases render cost and removes stream-copy eligibility.

### Validation and evidence

- Transform and linked-group invariant tests.
- Project round-trip and CLI parity tests.
- Render fixtures for portrait, landscape vertical focus, crop, and
  out-of-bounds offsets.
- Manual before/after visual evidence and target-workstation playback/export.
