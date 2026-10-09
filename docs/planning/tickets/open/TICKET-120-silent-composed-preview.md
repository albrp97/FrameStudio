# TICKET-120 - Play and Seek a Silent Multi-Track Preview

**Ticket ID:** TICKET-120
**Parents:** OBJ-001, SCOPE-001, PHASE-010, FEAT-036
**Capability links:** CAP-002, CAP-009, CAP-010, CAP-013
**Status:** verifying
**Approval:** execution/delegation authorized by the 2026-10-09 orchestration
request and CHG-014 autonomous authorization; dependencies and exact-profile
automatic validation remain required
**Requirements:** DISC-010 / REQ-010-05, REQ-010-06 (preview)
**Dependencies:** TICKET-119, TICKET-117
**Affected surfaces:** FFmpeg raw-frame playback, GTK preview lifecycle,
shared playhead, composition and tests
**Risks:** decoder drift, stale frames, audio accidentally launched, UI stalls
**Evidence path:** `evidence/ticket-120-silent-composed-preview.md`
**Path history:** created in `tickets/open/` on 2026-10-09

## Scope and acceptance

- Given play/pause/seek across1/2/3/4 active blocks and gaps, should display
  synchronized sections from119, current transforms/triplicate and one global
  playhead without stale layouts or losing segment selection.
- Given any project in this horizon, should launch no preview audio, including
  one track. Decoder failure should surface and release resources; retain
  responsive control behavior and generation-safe updates.

This intentionally changes optional preview audio; final export audio remains.
No new playback architecture/dependency without approval.

## Automated functionality charter

Dedicated charter integrated and executed against root:
`GDK_BACKEND=x11 python3 -m unittest tests.test_editor_composed_preview_functionality`

Launch real GTK with generated four-source colored/center-marker clips.
Play/seek/pause at active-set boundaries and gaps; sample actual displayed
decoded frames against119's expected sections and clock positions.
Assert centers/transform independence, black gaps, no audio process/output,
and failure/cancellation cleanup. Record measured latency/resource use against
the protected baseline; do not claim a threshold without approved evidence.

## Automatic functionality validation and completion

Execute this charter as the agent under CHG-014. Record `automaticValidation`
using Rubber Duck GPT-5.6 Luna high `all-validation`, never `userValidation`.

Setup: staggered four-track fixture with audible sources. Play and seek, then
open a one-track fixture. Expected: correct dynamic framing and no preview
sound in either. Failure: drifting frames, frozen UI or any audio.
Cleanup: close fixture. Record agent PASS/FAIL/BLOCKED with optional window-only
evidence. Require readiness, GTK/media functionality and normal gates.

## Parallel ownership

Can overlap isolated122 audio work. Reserve shared app/compositor seams
against111/114/121; shared layout definitions belong119.
