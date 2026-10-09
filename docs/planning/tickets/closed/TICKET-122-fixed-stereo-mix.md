# TICKET-122 - Mix Active Audio with Fixed Section Pan

**Ticket ID:** TICKET-122
**Parents:** OBJ-001, SCOPE-001, PHASE-010, FEAT-037
**Capability links:** CAP-008, CAP-012, CAP-013
**Status:** complete
**Approval:** execution/delegation authorized by the 2026-10-09 orchestration
request and CHG-014 autonomous authorization; gain/channel contract review
and exact-profile automatic validation remain required
**Requirements:** DISC-010 / REQ-010-06 (export pan)
**Dependencies:** TICKET-119
**Affected surfaces:** source audio policy, interval mixer/channel handling,
FFmpeg audio rendering and tests
**Risks:** reversed pan, clipping, wrong gain law, stereo channel loss
**Evidence path:** `evidence/ticket-122-fixed-stereo-mix.md`
**Path history:** created in `tickets/open/` on 2026-10-09
Moved unchanged-ID to `tickets/closed/` on 2026-10-09 (UTC) after source provider PASS.
**Completion evidence:** `evidence/ticket-125-phase010-functionality.md`,
source `981e5e2a`, CI `38004558177`, exact validator turns 18/19.

## Scope and acceptance

- Given active visual slots, should apply fixed normalized pan0; -25/+25;
  -25/0/+25; or -25/+25/-50/+50 in row-major four-slot order. Values are not
  configurable and never alter image offsets.
- Given mixed mono/stereo/supported multichannel/silent sources, should
  preserve source-level audio handling, align to cuts/start/gaps, mix all
  active sources and protect clipping without dropping an active source.

Approve precise gain law, supported channel mapping and sample-boundary/
peak assertions before code. This resolves technical meaning of fixed pan
percentages within existing delivery policy, not new loudness targets.
No preview audio, standalone audio tracks, or adjustable pan UI.

Technical preparation: [DESIGN-010-122](../../../specs/synchronized-audio-contract.md).
Exact-profile review requires source gain in the clipping bound, ordinary
centered-route equivalence and measured surround/LFE mapping before approval.
The bounded channel/gain review and exact-profile119 shared-interface review
are terminal. Isolated audio implementation is active without changing the
reviewed law;123 still owns final audio/video assembly.

## Automated functionality charter

Implemented functionality selector:
`python3 -m unittest tests.test_editor_audio_compositor_functionality`

The exact-profile validator released the bounded audio seam to TICKET-123,
including malformed peak-measurement remediation. TICKET-123 still requires
the separate TICKET-121 video release. Final aggregate quality, assembly,
delivery and lifecycle closeout remain pending.

Render audio via the supported mixer/export boundary using distinguishable
generated tones, mono/stereo fixtures, silent sources and changing active
counts. Decode PCM; assert per-tone channel gain ratios against the approved
law for every slot, direction/bottom-strength, all-source presence, silent
gaps, sample alignment and peak protection. Include equal0% stereo behavior
and explicit unsupported-layout errors.

## Automatic functionality validation and completion

Execute this charter as the agent under CHG-014. Record `automaticValidation`
using Rubber Duck GPT-5.6 Luna high `all-validation`, never `userValidation`.

Setup: generated tone clips in1/2/3/4 sections, listen to exported stereo
with headphones. Expected: center/left/right and stronger bottom positions,
all active audio, no clipping; preview remains silent.
Cleanup: remove test outputs. Record agent PASS/FAIL/BLOCKED.
Require readiness/gain-law approval, executable PCM checks and normal gates.

## Parallel ownership

After119, isolated audio work can overlap120/121. Shared layout is read-only;
123 owns final assembly, so do not edit its delivery seam concurrently.
