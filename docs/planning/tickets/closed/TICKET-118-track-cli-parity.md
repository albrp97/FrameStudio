# TICKET-118 - Expose Deterministic Track Editing to the CLI

**Ticket ID:** TICKET-118
**Parents:** OBJ-001, SCOPE-001, PHASE-010, FEAT-035
**Capability links:** CAP-003, CAP-004, CAP-006, CAP-013
**Status:** complete
**Approval:** execution/delegation authorized by the 2026-10-09 orchestration
request and CHG-014 autonomous authorization; dependencies and exact-profile
automatic validation remain required
**Requirements:** DISC-010 / REQ-010-04
**Dependencies:** TICKET-116
**Affected surfaces:** CLI parser/handlers/payload, track inspection/edit
commands, CLI-contract documentation and tests
**Risks:** incompatible JSON payload, duplicate business logic, nondeterminism
**Evidence path:** `evidence/ticket-118-track-cli-parity.md`
**Path history:** created in `tickets/open/` on 2026-10-09
Moved unchanged-ID to `tickets/closed/` on 2026-10-09 (UTC) after source provider PASS.
**Completion evidence:** `evidence/ticket-125-phase010-functionality.md`,
source `981e5e2a`, CI `38004558177`, exact validator turns 18/19.

## Scope and acceptance

- Given inspection/edit requests, should expose stable track IDs/order, block
  placements, active track, gaps and duration and edit through the shared
  collision-safe operations with explicit structured errors.
- Given existing commands/projects, should preserve compatibility and produce
  GUI-equivalent saved state for add/remove/select/move/split/copy/paste.

Document new command syntax during implementation before acceptance; do not
invent a new CLI now. Backspace/Undo CLI ownership is111; export choices are114.
No change to stdout JSON/error or legacy command compatibility without approval.

## Automated functionality charter

Implemented functionality selector:
`python3 -m unittest tests.test_editor_track_cli_functionality`

The exact-profile validator released the bounded CLI gate, including legacy
seconds-based timeline splitting without conversion. Aggregate quality,
delivery and lifecycle closeout remain pending.

Run the public `framestudio.py` entrypoint as subprocesses against fixtures;
inspect/create/move/save/reopen and compare persisted state with GUI/domain
operations. Assert stable JSON identities, collision placement, source hashes,
legacy commands and nonzero structured failures for fifth/invalid tracks.

## Automatic functionality validation and completion

Execute this charter as the agent under CHG-014. Record `automaticValidation`
using Rubber Duck GPT-5.6 Luna high `all-validation`, never `userValidation`.

Setup: same fixture as117. Inspect/edit using newly documented commands and
reopen it in the editor. Expected: matching rows/timing/modifications, explicit
errors. Cleanup: remove fixture project copies only.
Record agent PASS/FAIL/BLOCKED. Agent owns CLI contract/technical checks; require
readiness, functionality, exact-profile automatic validation, review and delivery gates.

## Parallel ownership

After116, parallel with117 if no shared-file changes; reserve CLI parser
seams against111/114 and serialize merged-payload verification.
