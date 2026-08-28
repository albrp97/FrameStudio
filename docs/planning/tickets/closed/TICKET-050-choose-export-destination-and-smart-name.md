# TICKET-050 - Choose Export Destination and Smart Name

**Ticket ID:** TICKET-050
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-007
**Feature:** FEAT-021
**Capability links:** CAP-005, CAP-012
**Status:** complete
**Closure:** user-approved on 2026-08-26 after implementation, testing,
review, and acceptance of destination safety and smart naming; unavailable
remote and target-specific checks remain recorded as accepted warnings.
**Horizon:** future
**Priority:** 3
**Owner:** repository planning; maintainer identity is not recorded
**Approval:** user-authorized on 2026-08-24 to create the PHASE-007 planning
set; implementation requires the approved parent policy and configured
ticket-execution approval
**Provider:** auto; base and target branches are not configured in
`.github/aidd-config.yml`
**Source paths:** `docs/planning/features/closed/FEAT-021-planning-export-destination-and-estimates.md`,
`docs/planning/tickets/closed/TICKET-048-define-target-fps-selection-and-enhancement-scope.md`,
`resolve_editor/app_export.py`, `resolve_editor/app_ui.py`,
`resolve_editor/operations.py`, `resolve_editor/persistence.py`,
`.github/aidd-config.yml`
**Dependencies:** TICKET-048; current destination conflict guard; GTK
file-selection support; project/source naming information
**Risks:** a collision algorithm can overwrite prior work, destination
permissions can fail late, and names can become misleading after policy
changes
**Affected surfaces:** export destination UI, filename resolution, filesystem
checks, project-file conflict protection, GUI tests, and evidence
**Evidence path:** `evidence/phase-007-export-planning.md`
**Protected behaviors:** export never replaces the project file or source
media; temporary/partial output and atomic publication remain unchanged
**Last updated:** 2026-08-26
**Path history:** created at
`tickets/open/TICKET-050-choose-export-destination-and-smart-name.md` ->
`tickets/closed/TICKET-050-choose-export-destination-and-smart-name.md`

## Outcome

The user can choose an export folder and receive a meaningful, collision-safe
video filename before processing starts.

## Scope

- Provide a destination-folder selection step in the export workflow.
- Derive a readable name from the project or source, edited state, target FPS,
  and enhancement state without exposing private path details unnecessarily.
- Detect an existing file and recommend a deterministic new name rather than
  silently replacing it.
- Reject the project file, source media, directories, invalid extensions, and
  unusable destinations with visible reasons.
- Keep the chosen destination and name separate from project persistence until
  an export is explicitly confirmed.

## Explicit non-goals

- Running FFmpeg or interpolation.
- Choosing output codecs or quality settings.
- Replacing the existing atomic publication or verification behavior.
- Uploading files or inspecting remote folders.

## Observable requirements

- Given a writable folder and project, the workflow should show a proposed
  filename before starting export.
- Given a collision, the workflow should recommend a distinct deterministic
  name and never overwrite the existing file implicitly.
- Given the project path or an input source as destination, the workflow should
  block the export before planning or execution.
- Given cancellation, no output or project setting should be changed.

## Commands and quality gates

- `python3 -m unittest discover -s tests`
- `make check`
- `make quality PYTHON=.venv/bin/python`
- Target-workstation GTK interaction with disposable media

## Functionality flows

- Export to an empty writable folder, a folder with a colliding name, and the
  project folder.
- Try the project file, source media, missing folder, and canceled chooser.
- Change target FPS and enhancement state and verify the proposed name updates.

## User validation before closure

Open Export, choose a destination folder, review the suggested name, create a
collision, and repeat the flow. Confirm the existing file and source media are
unchanged and that canceling leaves the project unchanged. Return `PASS`,
`FAIL`, or `BLOCKED`.

## Definition of done

- Destination and filename are selected before export execution.
- Collision and safety rules are deterministic and tested.
- No implicit overwrite or premature output creation occurs.

## Closure

TICKET-050 was closed on 2026-08-26 after the user confirmed the completed
ticket set was approved, accepted, and tested.
