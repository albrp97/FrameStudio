# TICKET-125 - Verify the Combined Editing and Delivery Journey

**Ticket ID:** TICKET-125
**Parents:** OBJ-001, SCOPE-001, PHASE-010, FEAT-038
**Capability links:** CAP-001 through CAP-013
**Status:** complete
**Approval:** execution/delegation authorized by the 2026-10-09 orchestration
request and CHG-014 autonomous authorization; dependencies and exact-profile
automatic validation remain required
**Requirements:** DISC-010 / REQ-010-01 through REQ-010-06, refined by CHG-013
**Dependencies:** TICKET-109, TICKET-111, TICKET-114, TICKET-118,
TICKET-120, TICKET-124, TICKET-126
**Affected surfaces:** integrated GTK/CLI/persistence/playback/export acceptance,
user guide, compatibility and target-workstation evidence
**Risks:** unit-green but unusable workflow, stale integration tests or missing AI evidence
**Evidence path:** `evidence/ticket-125-phase010-functionality.md`
**Path history:** created in `tickets/open/` on 2026-10-09
Moved unchanged-ID to `tickets/closed/` on 2026-10-09 (UTC) after source provider PASS.
**Completion evidence:** `evidence/ticket-125-phase010-functionality.md`,
source `981e5e2a`, CI `38004558177`, exact validator turns 18/19.

## Scope and acceptance

- Given a legacy project and a new four-track edit, should complete source
  inspection, Delete versus Backspace/Undo, collision-safe arrangement,
  save/reopen/recovery, silent preview, dynamic framing and fixed stereo export.
- Given one to four populated tracks, should render combined/source-only
  outputs grouped by track/source with all smart policies intact. Preserve
  independent duplicated sources, full-canvas segment edits and normal source
  audio without layout pan; omit empty/excluded-only tracks. Failure/resume
  must remain truthful/source-safe.

Verify integrated behavior and update the human-facing README/CLI docs only
when implementation exists. No new feature scope or fake target-workstation
pass. Preserve original media, old scripts/imports and output quality gates.

## Automated functionality charter

Implemented executable test:
`python3 -m unittest tests.test_phase010_functionality.Phase010FunctionalityTests.test_complete_edit_and_delivery_journey`

Use actual GTK events and public CLI subprocesses on generated marker/tone
fixtures. Exercise both acceptance outcomes end-to-end and compare reopened
projects, displayed frames, final decoded pixel/audio positions, output
selection/order/counts, dimensions/duration/FPS/frame counts, source hashes,
invalid actions and cancelled/resumed results. Matrix includes0/1/2/3/4
active clips, mixed FPS/resolutions, absent audio, triplicate, copies and gaps.
Specifically include Track 1 A/B and Track 2 A/C with different A transforms:
assert four source files with independent full-canvas framing, no placement
gaps or layout-based pan, and an optional fifth simultaneous composed final
file. Verify source-only across multiple tracks never starts final composition.

All named charters in109..124 are prerequisites/evidence, not replacements
for this integrated test. Run current discovered repository checks against
final diff and record local/remote parity and unavailable runtimes explicitly.

## Functionality validation and completion

Setup: approved workstation fixtures or local media, updated editor.
Steps: select source details; compare Delete/Backspace/Undo; drag across
four tracks; seek dynamic layouts; save/reopen; render/listen; validate
per-track A/B/A/C outputs and empty-track omission in source-only/combined
modes; compare normal source audio with final stereo mixing; cancel/resume.
Expected: every approved result, independent modifications and intact sources.
Failure: any contract mismatch or false completed export.
Cleanup: close fixtures and remove generated outputs via safe controls.
Execute this charter as the agent and record `automaticValidation` with
visible/persisted results and window-only evidence. Rubber Duck GPT-5.6 Luna,
high reasoning, `all-validation`, owns the terminal decision. No human
PASS/FAIL response is awaited. Agent owns all technical scripts. Require
review/remediation and configured commit/push/PR/local-delivery policy before
phase closeout; maintenance126 and actual remote evidence remain prerequisites.

## Parallel ownership

Final integration ticket, not independently executable before its
predecessors. CHG-014 authorizes execution after actual prerequisites and
exact-profile readiness checks, not before them.
