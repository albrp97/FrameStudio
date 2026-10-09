# TICKET-123 - Align Final Stereo Audio with Dynamic Layouts

**Ticket ID:** TICKET-123
**Parents:** OBJ-001, SCOPE-001, PHASE-010, FEAT-037
**Capability links:** CAP-008, CAP-012, CAP-013
**Status:** complete
**Approval:** execution/delegation authorized by the 2026-10-09 orchestration
request and CHG-014 autonomous authorization; dependencies and exact-profile
automatic validation remain required
**Requirements:** DISC-010 / REQ-010-05, REQ-010-06
**Dependencies:** TICKET-121, TICKET-122
**Affected surfaces:** final audio/video assembly, interval synchronization,
output stream validation and tests
**Risks:** stereo position assigned by track rather than slot, A/V drift
**Evidence path:** `evidence/ticket-123-layout-audio-integration.md`
**Path history:** created in `tickets/open/` on 2026-10-09
Moved unchanged-ID to `tickets/closed/` on 2026-10-09 (UTC) after source provider PASS.
**Completion evidence:** `evidence/ticket-125-phase010-functionality.md`,
source `981e5e2a`, CI `38004558177`, exact validator turns 18/19.

## Scope and acceptance

- Given slots changing as tracks start/end, final audio pan should follow
  current visual slot at the same boundary, not permanent track number.
- Given gaps, differing durations or silent sources, should retain correctly
  aligned video/audio duration and export mix with silence where needed.
  Report mux/verification failures explicitly and publish no unsafe partial.

Integrate121/122 without redefining gain or layout. Protect exact frame
counts, source bytes, source audio decisions and atomic output validation.
No preview sound or new UI controls.

## Automated functionality charter

Dedicated executable selectors authored in the isolated worktree:
`python3 -m unittest tests.test_editor_av_compositor tests.test_editor_av_compositor_functionality`

Test authoring is active. Seven explicit missing-module assertion failures
establish the red boundary. Fixture execution, decoded slot ownership and
rational boundary alignment assertions are being strengthened before the
exact-profile production-readiness decision.

Render a generated changing1/2/3/4-active-track fixture with visible markers
and distinct synchronized tones via final export. Probe duration/streams,
decode video frames and PCM around each boundary, and compare slot-to-channel
assignments, silence and peak protection. Assert source hashes and explicit
failure handling for a rejected mux.

## Automatic functionality validation and completion

Execute this charter as the agent under CHG-014. Record `automaticValidation`
using Rubber Duck GPT-5.6 Luna high `all-validation`, never `userValidation`.

Setup: staggered marker/tone clips. Play exported final video with headphones.
Expected: audio direction matches visual sections throughout; no drift or
audio during all-empty gaps. Failure: fixed track pan or missing active audio.
Cleanup: remove generated outputs. Record agent PASS/FAIL/BLOCKED.
Require readiness/baseline, automated alignment checks and normal gates.

## Parallel ownership

Single final-assembly owner after121/122; reserve delivery seams against113/
114.124 consumes the integrated result; no circular dependency.
