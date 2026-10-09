# Synchronized Layout and Framing Contract

**Design ID:** DESIGN-010-119
**Parents:** DISC-010 / REQ-010-05 / PHASE-010 / FEAT-036 / TICKET-119
**Status:** approved bounded mathematical/media contract; not implementation
**Owner:** orchestrator; bounded GPT-5.6 Luna max read-only design
**Authorization:** CHG-014; bootstrap-authorized exact-profile automatic review
**Dependency:** verified DESIGN-010-115 implementation before model binding

## Projection and active slots

Use the existing integer microsecond timebase and stable track order. Legacy
one-track projection concatenates included blocks in established order.
Absolute projection preserves included placements; exclusions/empty tracks
never create active slots. Partition at included starts/ends plus zero and the
last included endpoint. Membership is half-open: `start <= tick < end`.
Coincident end/start is one boundary. All-inactive intervals are black/silent.

Compact active tracks in persistent order, not configured row number:

| Active count | Canvas rectangles (x, y, width, height) |
|---|---|
| 1 | (0, 0, 1920, 1080) |
| 2 | (0, 0, 960, 1080), (960, 0, 960, 1080) |
| 3 | (0, 0, 640, 1080), (640, 0, 640, 1080), (1280, 0, 640, 1080) |
| 4 | (0, 0, 960, 540), (960, 0, 960, 540), (0, 540, 960, 540), (960, 540, 960, 540) |

Source tick equals source start plus elapsed placement time. No speed change.
Reuse cumulative half-up frame boundaries at the chosen rational output FPS,
not independently rounded section durations. Exact tick lookup and decoded
frame transitions have distinct, explicit quantization assertions.

## Framing domains and source preservation

Final slots require native/aspect-preserving source preparation before
center-crop-to-fill. Existing full-canvas standalone normalization must never
be treated as native input: current contain/pad or preserve-resolution crop
can miscenter a later slot or discard portrait content before it is composed.

Keep three explicit domains: native source preparation, standalone full-canvas
reel, final slot. Reuse FPS/upscale policies, but do not alias prepared/cache
artifacts across incompatible framing domains. If only a preframed artifact
exists, regenerate from original source or fail explicitly.

For source W/H and target w/h, cover scale is `max(w/W, h/H)`, multiplied by
the segment zoom. Choose sufficient integer scaled dimensions, then clamp
rounded center-plus-offset crop origins to source bounds. Existing offsets
are canvas pixels: map X by `w/1920` and Y by `h/1080`. Positive crop offsets
move content left/up as existing FFmpeg behavior does.

Preview and FFmpeg must consume the same resolved integer geometry rather
than independently recalculating floats. Normalize non-square sample aspect
before geometry, or explicitly account for display aspect without stretching.

Triplicate remains inside its segment's assigned slot. Cumulative half-up
partitions of a 640-pixel slot are 213/214/213. Keep intermediate branches in
a format permitting odd widths (experiment: yuv444p), compose them, and only
then convert the even final output to yuv420p. Existing divisibility-by-three
checks cannot reject approved triplicate-in-third behavior.

Standalone reels retain existing full-canvas framing and normal audio.
They bypass final-slot crop and fixed pan, independently on every track.

## Small shared surface and ownership

Prefer one pure geometry module reusing existing rectangle/transform helpers.
Define only needed active-section, slot and crop results; avoid a parallel
project model or speculative abstraction hierarchy. A small adapter binds the
verified v4 track/range/legacy projection API when115 is stable.

119 owns shared geometry. 120 consumes it for silent preview;121 consumes it
for video composition;122/123 map the same active order to audio. 113 keeps
the independent standalone route. Shared preparation changes113/121 require
reserved ownership and framing-domain identity;124 owns final checkpoint wiring.

## Raw design experiments and required functionality

Session artifacts: `files/design-ticket119/exp-crop-sample/experiment.py` and
`report.json`. Read-only worker used actual FFmpeg marker sources and decoding.
Observed native portrait1080x1920 into a960x1080 half scales to960x1707 and
crops at(0,314), keeping the center marker centered. Landscape and ultrawide
half-slot centers also matched. Zoom3/2 and offsets120/200 moved the marker to
(420,340), away from center. Original source hash stayed unchanged.

Existing portrait preserve-resolution preparation lost top/bottom markers;
contain preparation then half cropping misplaced the marker. Odd triplicate
branches negotiated to212 pixels without yuv444p, yielding638 rather than640;
explicit intermediate yuv444p preserved213/214/213 and all three markers.
These are raw design observations, not an automatic implementation pass.

Required executable acceptance uses persisted generated landscape/portrait/
ultrawide/square sources, active counts0..4, boundary ticks and decoded frames,
track-order compaction, centered markers, independent zoom/offset/triplicate,
native/preframed rejection, source hashes, dimensions/duration/FPS/frame counts
and identical preview/export plans. Unit geometry alone is insufficient.

## Automatic technical-contract review

The exact `rubber-duck / gpt-5.6-luna / high / all-validation` validator
approved the bounded geometry and framing contract against the real FFmpeg
experiment report. This is `automaticValidation` of a design contract, not
validation of implementation, migration, preview, final composition or delivery.

Implementation must keep framing domain and geometry in cache identity,
regenerate from original source when only incompatible preframed artifacts
exist, and share resolved integer geometry between preview and render. The verified115/116 foundation is now bound by `framestudio.layout_plan`:
`plan_project_layout`, `source_geometries_from_project`, `plan_crop` and
`plan_triplicate`. The exact-profile119 implementation review released121/122
to consume it. Original SAR must be probed by video consumers because the
current source metadata fallback is not proof of square pixels. Preparation
and final consumer verification remain separately owned; no phase readiness
is claimed.
