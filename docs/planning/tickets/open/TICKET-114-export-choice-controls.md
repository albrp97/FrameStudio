# TICKET-114 - Expose Safe Final and Source Export Choices

**Ticket ID:** TICKET-114
**Parents:** OBJ-001, SCOPE-001, PHASE-010, FEAT-034
**Capability links:** CAP-004, CAP-005, CAP-006, CAP-012
**Status:** verifying
**Approval:** execution/delegation authorized by the 2026-10-09 orchestration
request and CHG-014 autonomous authorization; dependencies and exact-profile
automatic validation remain required
**Requirements:** DISC-010 / REQ-010-03, refined by CHG-013
**Dependencies:** TICKET-113
**Affected surfaces:** export panel, GTK controls, CLI options/payload,
output-choice persistence and tests
**Risks:** obsolete track-count restriction, silent omissions, inconsistent CLI errors
**Evidence path:** `evidence/ticket-114-export-choice-controls.md`
**Path history:** created in `tickets/open/` on 2026-10-09

## Scope and acceptance

- Given normal settings, should show source export off and final export on.
  Enable source export to choose combined or source-only and display folder/
  requested track/source output count without hiding enhancement eligibility.
- Given one to four populated tracks, should allow source exports in GUI/CLI
  and enumerate independent pairs. Empty/excluded-only tracks produce no
  files. Neither-output/entirely empty requests should visibly block rendering,
  not switch modes silently.

Preserve responsive export planning and existing error/progress reporting.
No silent auto-selection of a different output mode.

## Automated functionality charter

Dedicated executable selectors authored in the isolated worktree:
`python3 -m unittest tests.test_editor_export_choices tests.test_editor_export_choices_functionality`

Exact-profile readiness permits test authoring only. Eleven tests execute
with four passes and seven expected assertion failures. Production edits
remain withheld pending native export-control accessibility and enhancement
eligibility visibility assertions.

Drive real GTK toggles, save/reopen, and CLI requests across final-only,
combined, source-only, neither-output, empty extras, and two populated tracks.
Include four populated tracks and repeated sources with different edits.
Assert source export stays enabled, persisted settings, track/source paths
and full-canvas/normal-audio intent; source-only requests do not launch the
final compositor. Invalid requests publish nothing. Test planned combined
multi-track dispatch here; actual integrated output acceptance belongs124/125.

## Automatic functionality validation and completion

Execute this charter as the agent under CHG-014. Record `automaticValidation`
using Rubber Duck GPT-5.6 Luna high `all-validation`, never `userValidation`.

Setup: single populated track plus empty extras. Toggle outputs, populate a
second track using the same source, then remove its last included block.
Expected: source export stays available, two independent versions are planned
when both tracks contain it, modes persist and source-only omits final video.
Cleanup: close planner/delete generated outputs. Record agent PASS/FAIL/BLOCKED.
Require readiness/baseline, charter and normal technical/automatic-validation/review/delivery
gates; no current execution readiness.

## Parallel ownership

Can overlap isolated audio tests. Reserve `app_export.py`/CLI payload writes
against111/118/120/123; consume112/113 contracts without duplicated checks.
