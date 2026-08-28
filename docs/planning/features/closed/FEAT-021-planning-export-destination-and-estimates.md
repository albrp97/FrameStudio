# FEAT-021 - Planning Export Destination and Estimates

**Feature ID:** FEAT-021
**Parent links:** OBJ-001, SCOPE-001, PHASE-007
**Capability links:** CAP-005, CAP-011, CAP-012
**Status:** complete
**Closure:** user-approved on 2026-08-26 after TICKET-050, TICKET-051,
TICKET-052, and TICKET-060 passed implementation, automated validation,
review, and user acceptance; unavailable remote and target-specific checks
remain recorded as accepted warnings.
**Horizon:** future
**Priority:** 2
**Owner:** repository planning; maintainer identity is not recorded
**Approval:** user-authorized on 2026-08-24 to break down PHASE-007; ticket
execution remains separately gated by the configured approval policy
**Source paths:** `vision.md`, `docs/specs/project-scope.md`,
`docs/specs/capability-map.md`,
`docs/planning/phases/closed/PHASE-007-producing-validated-60-fps-edits.md`,
`resolve_editor/app_export.py`, `resolve_editor/export_process.py`,
`resolve_concat.py`, `resolve_fps.py`, `FPS-ENHANCEMENT-RESEARCH.md`,
`.github/aidd-config.yml`
**Dependencies:** FEAT-020 target-rate policy; current export destination
guard; source probing; existing progress metrics; local benchmark evidence
**Risks:** estimates can create false confidence, destination permissions can
fail late, and filename collisions can overwrite or confuse prior work
**Affected surfaces:** GTK export page/dialog, destination selection, naming
policy, estimate calculation, CLI planning payloads, tests, and evidence
**Evidence path:** `evidence/phase-007-export-planning.md`
**Planned tickets:** TICKET-050, TICKET-051, TICKET-052, TICKET-060
**Last updated:** 2026-08-26
**Path history:** created at
`features/open/FEAT-021-planning-export-destination-and-estimates.md` ->
`features/closed/FEAT-021-planning-export-destination-and-estimates.md`

## Outcome

Before an export starts, the user can choose where it will be saved, review a
collision-safe filename, and understand the expected workload for the chosen
frame-rate and enhancement policy.

## Scope

- Open a dedicated export page or dialog instead of starting immediately from
  the header button.
- Let the user choose a destination folder and edit the proposed filename.
- Suggest a meaningful filename derived from the project/source and selected
  delivery policy, then choose a new non-conflicting name when needed.
- Show input-file count, edited duration, target FPS, enhancement state, and
  separate estimates for interpolation, rendering/encoding, verification, and
  total processing time.
- Base estimates on measured local throughput and transparent duration/frame
  calculations, with an explicit uncertainty or confidence indication.
- Recalculate the plan when destination, target FPS, enhancement, or relevant
  source information changes.

## Explicit non-goals

- Promising a universal runtime across hardware or media types.
- Uploading media or using cloud estimation services.
- Changing output codecs, audio policy, or interpolation quality decisions.
- Publishing a destination file before the existing verification boundary.

## Observable requirements

- Given a project and export request, the panel should show the number of
  inputs, edited duration, target/enhancement FPS, and a total estimate before
  the export is started.
- Given an existing suggested filename, the panel should recommend a distinct
  filename without overwriting the existing output.
- Given a destination that is the project file or an unusable location, the
  panel should block export and explain the reason.
- Given changed policy inputs, the displayed estimate should update
  deterministically and identify its assumptions.

## Validation intent

- Use generated short and representative local media to compare predicted and
  observed stage durations.
- Exercise empty, writable, non-writable, colliding, and project-file
  destinations without modifying source media.
- Compare GUI planning information with a machine-readable CLI plan.
- Record estimate error and confidence rather than presenting a single
  unqualified promise.

## Protected behaviors

Existing destination conflict checks, atomic partial outputs, verification
before publication, source preservation, current progress reporting, and
non-enhanced export behavior remain required.

## Definition of done

- The export planning surface exposes destination, naming, policy summary, and
  component estimates before processing.
- Filename collision and destination safety rules are deterministic and tested.
- The estimate formula is calibrated against local evidence and reports its
  assumptions and limitations.

## Closure

FEAT-021 was closed on 2026-08-26 after its child tickets and linked evidence
were accepted as tested by the user.
