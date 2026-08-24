# PHASE-006 - Focusing and Composing Important Action

**Phase ID:** PHASE-006  
**Parent links:** OBJ-001, SCOPE-001  
**Capability links:** CAP-005, CAP-009, CAP-010, CAP-012  
**Sequence:** 6  
**Status:** complete
**Closure:** user-approved on 2026-08-23 after FEAT-017 through FEAT-019 and
TICKET-038 through TICKET-047 passed implementation, automated and real-media
verification, target-workstation validation, review, and local delivery gates;
remote checks remain unavailable and are recorded as an accepted warning.
**Horizon:** future  
**Owner:** repository planning; maintainer identity is not recorded  
**Approval:** user-approved on 2026-08-21 before feature generation;
implementation authorized on 2026-08-22 after ticket approval
**Feature links:** FEAT-017, FEAT-018, FEAT-019
**Evidence path:** `evidence/phase-006-focused-composition-delivery.md`
**Source paths:** `vision.md`, `docs/specs/project-scope.md`,
`docs/specs/capability-map.md`, `docs/planning/phases.md`,
`docs/planning/repo-map.md`, `.github/aidd-config.yml`  
**Migration source:** `docs/planning/phases.md`, inline section
`PHASE-006 - Focusing and Composing Important Action`; migrated on
2026-08-21 with the phase content preserved.  
**Affected surfaces:** segment transforms and modification inheritance,
selection, linked triplicate composition, preview, output canvas, project
persistence, CLI, and renderer
**Path history:** `phases/open/PHASE-006-focusing-and-composing-important-action.md`
-> `phases/closed/PHASE-006-focusing-and-composing-important-action.md`

## Outcome

The user can focus the viewer's attention through reusable
segment transforms and a linked triplicate layout for portrait or
vertically concentrated action.

### Included

- Apply zoom and X/Y position changes to one segment or selected segments.
- Treat zoom, X/Y offsets, triplicate mode, and its layout parameters as a
  segment-owned modification bundle.
- Copy and paste the modification bundle between existing segments or
  selected groups.
- Preserve the modification bundle when a segment moves; clone it when a
  segment is split or copy/pasted so the resulting segment identities remain
  independent.
- Provide a visible Clean modifications button/action that resets the
  selected segment's bundle to defaults without changing its source interval.
- Preserve transforms across save/reopen and expose shared versus overridden
  values.
- Activate a triplicate mode for portrait or mostly vertical action.
- Place one copy in the middle and two linked copies on the left and right.
- Automatically select or link the three instances when the mode is enabled.
- Apply shared X offset, Y offset, and zoom controls to the linked copies.
- Give copied or split triplicate segments new independent linked groups while
  retaining the cloned modification bundle; clean a linked group atomically.
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
- PHASE-004 block operations provide deterministic split/copy inheritance and
  fresh identities.
- The transform model defines coordinate space, aspect-ratio behavior, and
  source-versus-segment ownership.
- Triplicate linking, automatic selection, and background treatment are
  explicitly specified.
- Representative portrait and vertically focused landscape footage is
  available for manual evaluation.

### Exit conditions

- A user can apply, review, copy, paste, save, reopen, and export transforms
  on one or several segments.
- A user can split or copy/paste a modified segment and observe the same
  modification bundle on the independent resulting segment(s), then clean
  that bundle without changing source ranges.
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
  deleted, split, or reordered unless cloned group identity and reset rules
  are explicit.
- Automatic focus quality may be unreliable and must remain user-correctable.
- Composition increases render cost and removes stream-copy eligibility.

### Validation and evidence

- Transform and linked-group invariant tests.
- Project round-trip and CLI parity tests.
- Render fixtures for portrait, landscape vertical focus, crop, and
  out-of-bounds offsets.
- Manual before/after visual evidence and target-workstation playback/export.

## Planned feature decomposition

- FEAT-017 - Edit reusable visual focus controls on timeline segments.
- FEAT-018 - Create linked triplicate portrait and focused-action
  compositions.
- FEAT-019 - Preview, persist, and safely deliver focused compositions.

The feature records and ticket contracts were created on 2026-08-22 in the
configured open lifecycle directories. Their implementation, validation, and
local delivery are complete; provider-side checks remain unavailable because
no remote or upstream is configured.

## Planning readiness

- PHASE-004A and PHASE-005 are complete with terminal local evidence.
- FEAT-017 through FEAT-019 each have one phase, explicit capability links,
  observable requirements, non-goals, dependencies, risks, affected surfaces,
  and evidence paths.
- TICKET-038 through TICKET-047 have bounded scope, dependency order,
  protected behaviors, commands, evidence paths, and user-validation plans.
- The transform coordinate policy and triplicate layout policy are implemented
  and covered by automated evidence.
- TICKET-038 through TICKET-047 have terminal implementation, automated,
  real-media, user-validation, review, and local delivery evidence.

## Closure

All PHASE-006 exit conditions are satisfied by FEAT-017 through FEAT-019 and
TICKET-038 through TICKET-047. The phase is moved to the configured closed
directory after user approval; remote publication and provider-side checks
remain unavailable because no remote or upstream is configured.
