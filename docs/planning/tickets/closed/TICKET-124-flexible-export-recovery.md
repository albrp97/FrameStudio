# TICKET-124 - Resume and Publish Flexible Output Jobs Safely

**Ticket ID:** TICKET-124
**Parents:** OBJ-001, SCOPE-001, PHASE-010, FEAT-038
**Capability links:** CAP-004, CAP-005, CAP-006, CAP-012, CAP-013
**Status:** complete
**Approval:** execution/delegation authorized by the 2026-10-09 orchestration
request and CHG-014 autonomous authorization; session/fingerprint contract
review and exact-profile automatic validation remain required
**Requirements:** DISC-010 / REQ-010-03 through REQ-010-06, CHG-013, delivery recovery
**Dependencies:** TICKET-113, TICKET-121, TICKET-123
**Affected surfaces:** session/cache identity, per-output checkpoints,
GUI/CLI resume/progress, atomic publication and tests
**Risks:** stale pan/track artifacts, false complete status, output overwrite
**Evidence path:** `evidence/ticket-124-flexible-export-recovery.md`
**Path history:** created in `tickets/open/` on 2026-10-09
Moved unchanged-ID to `tickets/closed/` on 2026-10-09 (UTC) after source provider PASS.
**Completion evidence:** `evidence/ticket-125-phase010-functionality.md`,
source `981e5e2a`, CI `38004558177`, exact validator turns 18/19.

## Scope and acceptance

- Given cancellation/failure in final/source jobs, should identify verified
  published outputs, failed/pending work and reusable checkpoints explicitly;
  resume skips valid outputs without falsely declaring the whole job complete.
- Given changed source, tracks, timeline, transforms, layout/pan law,
  enhancement policy, output selection or destination, should reject stale
  artifacts. Every final file is verified before atomic publication.
- Given the same source on multiple tracks, should preserve independent
  output/checkpoint identities by stable track/source pair and standalone
  full-canvas/normal-audio mode. Track renaming/reordering and final
  composition settings must not alias or apply final slot pan to source files.

Approve output/session fingerprint design before code. Reuse existing
resume/restart/discard semantics and safe naming, never overwrite originals.
No new cache backend or all-or-nothing multi-file promise unsupported by
the approved per-output partial-success contract.

## Automated functionality charter

Implemented executable charter:
`python3 -m unittest tests.test_editor_flexible_output_recovery_functionality`

Its CLI class exercises actual final-only/source-only/combined output,
same-shape content replacement, error details and running-child cancellation.
Its GTK class exercises actual final-only/combined completion and native
cancel/recovery controls. Run under the shared X11 desktop lease locally.
The protected CLI contract additionally verifies real process-restart
checkpoint reuse. Unit tests are separate, not charter replacements.

Via GUI/CLI export boundaries, run generated final-only/source-only/combined
jobs; inject cancellation, second-output failure and verification failure.
Include Track 1 A/B and Track 2 A/C plus empty/excluded-only tracks, verifying
four independently modified full-canvas/normal-audio source reels with an
optional dynamic split-screen/stereo-mixed final file.
Close/reopen/resume and assert retained verified outputs, exact result states,
skipped completed rendering, distinct pair/mode identities, invalidation for
each relevant fingerprint input including track rename/reorder, safe
cleanup/naming, source hashes and valid output metadata/PCM/pixels.

## Automatic functionality validation and completion

Execute this charter as the agent under CHG-014. Record `automaticValidation`
using Rubber Duck GPT-5.6 Luna high `all-validation`, never `userValidation`.

Setup: combined and source-only multi-track jobs with repeated A on two
tracks, plus a final-only job. Cancel,
reopen, resume, then change one placement/policy and inspect stale-session notice.
Expected: explicit resume, truthful per-output results and no stale reuse.
Independent source files retain normal audio/full-canvas framing while the
final file alone uses dynamic layouts and fixed stereo mix.
Cleanup: discard generated sessions through supported controls.
Record agent PASS/FAIL/BLOCKED. Require readiness/design approval and all normal
automated/technical/automatic-validation/review/delivery gates before completion.

## Parallel ownership

Integrates stable render/audio/source-result interfaces after prerequisites.
Serialize all cache/session/delivery changes;125 owns final whole-phase checks.
