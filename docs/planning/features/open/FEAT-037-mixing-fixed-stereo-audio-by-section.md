# FEAT-037 - Mixing Fixed Stereo Audio by Section

**Feature ID:** FEAT-037
**Parents:** OBJ-001, SCOPE-001, PHASE-010
**Capability links:** CAP-008, CAP-012, CAP-013
**Status:** active
**Approval:** planning approved 2026-10-09; subsequent orchestration request
authorizes execution/delegation; CHG-014 supplies autonomous routine approval,
with exact-profile automatic validation and delivery gates retained
**Last updated:** 2026-10-09
**Requirements:** DISC-010 / REQ-010-06
**Dependencies:** FEAT-036 interval/layout TICKET-119;
final integration after video render TICKET-121
**Ticket links:** TICKET-122, TICKET-123
**Evidence plan:** `evidence/ticket-122-fixed-stereo-mix.md`,
`evidence/ticket-123-layout-audio-integration.md` (future)
**Affected surfaces:** source audio normalization, pan/mix routing, final
video/audio assembly, verification and tests
**Risks:** reversed channels, clipping, drift, double source gain,
unexpected loudness changes and absent-audio handling
**Path history:** created in `features/open/` on 2026-10-09

## Outcome, scope, and acceptance

Export mixes all active clips' audio using their current visual slot: one 0%;
two -25/+25%; three -25/0/+25%; four top -25/+25%, bottom -50/+50%.
Pan is fixed stereo sound, never an image offset or adjustable setting.
Apply established per-source audio handling before a tested pan/mix law,
align starts/cuts/gaps, and prevent clipping. Silent clips add silence.

Preview audio is prohibited and owned by TICKET-120. No independent audio
tracks, audio-editor controls, or new loudness target. Define and approve
mono/stereo/multichannel mapping within the existing delivery policy.

## Dependencies and parallel work

TICKET-122 depends on TICKET-119 and can proceed alongside preview/render
with isolated audio ownership. TICKET-123 depends on TICKET-121 and
TICKET-122; it must not race other delivery
assembler writes.

## Verification and closeout

Generated distinct-tone fixtures and decoded PCM measure channel direction,
fixed pan law, active-slot reassignment, silence, clipping/peaks, and alignment.
Probe final audio/video duration and execute the listening charter through
measured decoded PCM and exact-profile automatic validation after technical
audio functionality checks have terminal results. Human listening is optional,
not a wait or a fabricated result in automatic mode.
