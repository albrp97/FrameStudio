# Preview Responsiveness Strategy

## Decision

The editor keeps the existing FFmpeg raw-frame playback contract and adds a
bounded eight-frame LRU preview cache. Preview requests still use generation
checks so a frame decoded for an obsolete cursor position is never delivered.
Cache keys use the nearest source frame index. A cache hit is presented at the
requested cursor position while `VideoFrame.decoded_position_seconds` preserves
the timestamp from which the cached pixels were decoded.

This is a deliberately small, dependency-free change in
`framestudio/preview_strategy.py` and `framestudio/ffmpeg_playback.py`.
The cache is scoped to one backend instance and is not used by export or
persistence.

## Evidence

The reproducible harness is `benchmarks/preview_responsiveness.py`. It sends
cursor, click, seek, and scroll-like requests, then records request-to-frame
latency, displayed versus requested position, timeout failures, cancellation
and coalescing observations, stale frames, and cache hits. The captured
one-source and mixed-source outputs are:

- `evidence/phase-008-preview-benchmark-one-source.json`
- `evidence/phase-008-preview-benchmark-mixed-source.json`

On the captured 10 FPS H.264 fixtures, cold cache misses were approximately
29 ms (one source) and 32 ms (mixed source). Warm cache hits were approximately
0.01 ms median in both cases. Rapid traces delivered only the newest decoded
frame with the current cache disabled; cache hits delivered several already
decoded frames immediately. The failure probe reported the missing decoder
explicitly. These are local measurements, not universal codec or hardware
claims.

## Lossless Cut research boundary

Lossless Cut revision `e1f4348637575bb21fe9bc2ba70e0f9a70cbafaf` was inspected
from its public repository on 2026-08-26. `package.json` declares
`GPL-2.0-only`, and its `LICENSE` is GPL version 2. The disposable checkout was
removed after inspection; no source, dependency, or generated file was copied.

Transferable hypotheses were:

- `src/renderer/src/hooks/useVideo.ts:35-59`: retain only the latest pending
  scrub target while a seek is in flight.
- `src/renderer/src/MediaSourcePlayer.tsx:196-231`: throttle reads when a
  bounded buffer is sufficiently ahead, and remove old buffered ranges.
- `src/renderer/src/hooks/useThumbnails.ts:20-55`: debounce viewport changes
  and abort obsolete asynchronous thumbnail work.
- `src/renderer/src/MediaSourcePlayer.tsx:252-304`: periodically resynchronize
  a slave stream to the authoritative player and adjust playback rate when
  drift is small.

Those concepts are not direct implementation matches: this editor uses GTK 4,
PyGObject, subprocess FFmpeg, and raw RGBA frames rather than Chromium
`HTMLVideoElement`/MediaSource. The adopted cache and generation checks are
repository-native implementations, not derivative code.

## Tradeoffs and limits

The cache improves repeated nearby scrubs but cannot reduce the first decode.
Nearest-frame keys can show a decoded frame slightly before or after the
requested timestamp; both the requested presentation position and decoded
position remain available for diagnostics. Eight frames bounds memory but may be insufficient for long
timelines or high-resolution canvases. No GTK/display session was available
for this run, so interactive paint latency and visual usability remain
target-workstation validation items.
