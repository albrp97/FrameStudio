# FEAT-038 - Verifying Recoverable Flexible Delivery

**Feature ID:** FEAT-038
**Parents:** OBJ-001, SCOPE-001, PHASE-010
**Capability links:** CAP-004, CAP-005, CAP-006, CAP-012, CAP-013
**Status:** complete
**Approval:** planning approved 2026-10-09; subsequent orchestration request
authorizes execution/delegation; CHG-014 supplies autonomous routine approval,
with exact-profile automatic validation and delivery gates retained
**Last updated:** 2026-10-09
**Requirements:** DISC-010 / REQ-010-01 through REQ-010-06, integrated delivery
**Dependencies:** FEAT-032 through FEAT-037 interfaces and tested behaviors;
TICKET-104 final route baseline remains a prerequisite for export integration
**Ticket links:** TICKET-124, TICKET-125, TICKET-126
**Evidence plan:** `evidence/ticket-124-flexible-export-recovery.md`,
`evidence/ticket-125-phase010-functionality.md`,
`evidence/ticket-126-local-quality-ci-parity.md`
**Affected surfaces:** output sessions/cache, GUI/CLI recovery,
publication/progress, integrated GTK/media acceptance, documentation,
existing quality/CI definitions and export-panel test deduplication
**Risks:** stale multi-output checkpoints, false complete state,
partial-result loss, resume after pan/track changes and undetected parity drift
**Path history:** created in `features/open/` on 2026-10-09
Moved unchanged-ID to `features/closed/` on 2026-10-09 (UTC) after required tickets completed.
**Completion evidence:** `evidence/ticket-125-phase010-functionality.md`,
source `981e5e2a`, CI `38004558177`, exact validator turns 18/19.

## Outcome, scope, and acceptance

Given flexible final/source outputs and track layouts, cancellation or failure
must retain valid checkpoints, report each result truthfully, and permit
explicit resume without repeating valid work. Changed tracks, cuts,
transforms, audio/layout rules, outputs, or source identity invalidate stale
artifacts. Publish only verified outputs and never overwrite original media.

Separate outputs are keyed by stable track/source pair and independent
full-canvas/normal-audio mode; never alias a source on two tracks, confuse it
with the final composition's crop/pan, or omit outputs due to track count.

Given the combined workflow, GUI, persisted projects, deterministic CLI,
preview and export satisfy all approved behaviors before phase closeout.
No universal speedup claim, new runtime, or waiver of missing gates.

## Dependencies and parallel work

124 depends on113,121,123. 125 follows all feature acceptance tickets:
109,111,114,118,120,124,126. Maintenance126 has no product dependency and
can execute alongside115 with isolated workflow/export-panel-test ownership.
Its repair does not waive any product acceptance. Session identity design must be reviewed before
implementation. No parallel integration writes to cache/delivery seams.

## Verification and closeout

Generated multi-output failure/resume tests and full GUI/CLI journey charters
cover final-only/source-only/combined modes on one to four tracks, empty-track
omission, duplicated sources across tracks, standalone versus final pixel/audio
parity, migration, Undo, source hashes, exact duration/rates/frame counts,
and truthful failures. Agent-run functionality charters, exact-profile
`automaticValidation` and review precede delivery and lifecycle closure.
The validator is Rubber Duck GPT-5.6 Luna, high reasoning, `all-validation`.
Unavailable remote CI remains a delivery gate, never inferred from local checks.
