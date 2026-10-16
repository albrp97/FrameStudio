# FrameStudio

FrameStudio is a local Linux video editor for turning one or more source
videos into a precise, verified final file. It combines a GTK 4 editor, an
FFmpeg-backed playback and export engine, and a deterministic command-line
interface.

It is designed for practical editing rather than for replacing a complete
professional suite. You can import mixed source media, preview the timeline,
cut and arrange segments, reframe footage, save the project, and export the
result without overwriting the original videos.

## What you can do

### Edit video

- Load one or several local videos, including mixed dimensions and frame rates.
- Import and append videos without a fixed per-project source-count limit.
  Practical project size depends on available memory and processing resources.
- Play, pause, and seek through the editor timeline.
- Split clips at the playhead.
- Delete, restore, move, copy, and paste timeline segments.
- Select individual segments with `Ctrl`-click or ranges with `Shift`-click.
- Apply a focus transform to a segment with zoom and X/Y offsets.
- Enable linked triplicate composition for portrait or center-focused footage.
- Zoom the timeline without an artificial upper limit.
- Fit the timeline to the default view or to a 30-minute window.
- See the edited duration and the planned final output.

### Save and recover work

- Save versioned `.framestudio.json` project files atomically.
- Reopen a project with source identity validation.
- Autosave the one current project for crash recovery.
- Replace the autosave automatically when a different project or source set
  becomes current.
- Keep project state separate from the original media.

### Preview and audio

Composited timeline playback keeps an FFmpeg decoder running for each active
layout interval rather than restarting it for every frame. Seeking or changing
the active layout restarts the decoder as needed. Preview keeps the same canvas,
framing, and triplicate behavior; this is not a lower-resolution proxy or an
export-quality change.

Ordinary sequential imports now open only the source contributing at the
playhead, not every video in the project. They keep the original sequential
scale/pad/fps graph. Uncached paused seeks on this path use exact FFmpeg;
the native CPU/CUDA composition path is not substituted because its pixels
do not match the sequential renderer.

Cursor seeks run asynchronously, keeping the interface responsive while the
exact frame is decoded. Rapid cursor changes retain the latest target rather
than rendering a backlog; repeated positions reuse the bounded preview cache.
For absolute/synchronized timelines, the optional preview runtime retains
decoder state in an isolated helper instead of reopening FFmpeg for every
image. Supported H.264 footage uses NVIDIA decoding when available; other eligible footage uses
CPU decoding, with explicit FFmpeg fallback for unsupported capabilities.
Run-up frames stay on the GPU and only the selected frame is downloaded.
Nearby forward moves continue decoding instead of repeatedly seeking back to
a keyframe. Distant or backward long-GOP seeks still need that run-up. No
proxies, background indexing, or lower-quality previews are added.
Opaque full-canvas native previews also reuse bounded source-aware color/scale
pipelines, rebuilding when input metadata or framing changes. With the normal
helper RSS budget, all-CUDA working sets can retain five demand-loaded decoders
and pipelines; post-render RSS retirement still applies. CPU/mixed working sets
stay at two. Lower helper budgets
also restrict CUDA residency to two. No adjacent videos are eagerly decoded
in the background. This avoids repeated filter setup without changing the
exact color-conversion path.

The timeline reuses validated layout geometry until the model changes and uses
an indexed visible-viewport lookup rather than scanning all cached clips.
Scrolling, zooming, selection, and edits still invalidate the relevant view.
See [preview optimization guide](docs/specs/preview-optimization.md) for the
current design, measured results, and rejected alternatives. Detailed records:
[preview strategy and measurements](docs/specs/preview-responsiveness-strategy.md),
[exact-preview research](docs/specs/instant-preview-research.md), and
[large-project strategy comparisons](docs/specs/large-project-preview-research.md)
for measured gains, compared alternatives, and remaining limits.

Import, adding clips, reopening, recovery, and preview do not run audio scans.
Audio analysis starts only after **Start export** is confirmed, not while
viewing the export plan. It scans only sources used by the selected outputs
and reuses valid saved results. Sources without audio do not need a scan.
Independent scans run in CPU-parallel processes using the available CPU
affinity, with progress and cancellation during export preparation.
Playback is paused for export, and retained native and streaming preview resources are
released before export preparation. They reopen lazily on the next uncached
preview after export. The export temporarily enables the available
system performance profile and restores the previous profile afterward.
Final audio decisions are applied and validated during export.

### Export safely

- Plan the output before rendering, including frame-rate and upscale counts.
- Use stream copy when the media and edit boundaries make it safe.
- Fall back to a verified render when decoding or composition is required.
- Target the fixed 1920x1080 project canvas with contain scaling and
  letterboxing for sources with other dimensions.
- Optionally enhance eligible sources to the selected frame rate.
- Optionally upscale eligible low-resolution sources.
- Show numbered export stages in the terminal.
- Preserve validated intermediate work after cancellation or failure.
- Resume a compatible export without repeating completed stages.
- Show the previous run's overall percentage when available, not a misleading
  count of top-level stages. Historical progress is not a promise that every
  operation at that percentage was checkpointed; Resume validates saved work.
- Preserve frames in subframe composition intervals, holding the last video
  frame when a short interval reaches an audio/container tail.
- Fill cuts beyond the available audio samples with correctly timestamped
  silence, preserving exact duration through concatenation and track recovery.
- Keep every planned video frame in the final audio/video merge, even when
  audio ends a fraction of a frame earlier. Resume rebuilds an invalid merge
  without repeating the verified video and audio compositions.
- Show the underlying per-output error and write failure logs before an
  optional sleep or shutdown action.
- Publish the final file only after FFmpeg and FFprobe verification.

Original source files are never overwritten or deleted by editor operations.

## How FrameStudio works

1. **Import** - FrameStudio records source identities and metadata in a
   versioned project. It does not copy or modify the original media.
2. **Edit** - The project stores ordered timeline segments. Splits, deletion,
   movement, copies, visual transforms, and triplicate state are project
   operations rather than destructive source edits.
3. **Preview** - FFmpeg decodes raw video frames for the GTK preview. Seeking
   changes the preview position without forcing the project to render.
4. **Plan** - The export planner resolves the output canvas, frame-rate policy,
   audio decisions, enhancement eligibility, and the safest render route.
5. **Render** - Cuts, preparation, interpolation, upscale, composition, and
   verification run through temporary or cached artifacts.
6. **Publish** - The verified temporary output is atomically moved to the
   requested destination. Validated checkpoints are removed only after
   publication succeeds.

## Requirements

FrameStudio targets a Linux workstation and requires:

- Python 3.10 or newer.
- GTK 4 and PyGObject (`gi`), including the Cairo bridge for timeline drawing
  (`python3-gi-cairo` on Ubuntu/Debian).
- FFmpeg and FFprobe.

`ffplay` is optional and is used for audio preview. The editor reports audio
preview failures explicitly and remains usable without it.

The optional frame-rate and upscale paths can use NVIDIA/CUDA/NVENC, Vulkan,
and a local REAL-Video-Enhancer installation. If the preferred restoration
runtime is unavailable, eligible exports use the validated FFmpeg
interpolation fallback. The original media workflows also support CPU-only
operation.

Faster uncached exact seeking optionally uses **PyAV 19.0.1 with Python 3.12
or newer** in a separate preview worker. The editor itself still supports
Python 3.10. The worker keeps a bounded set of decoder contexts open and can
use supported NVIDIA hardware without changing export or preview resolution.
Missing optional capabilities retain the FFmpeg preview path with a diagnostic.

## Install

Clone the repository and install the single canonical command:

```sh
git clone <repository-url>
cd FrameStudio
./install.sh
```

The installer creates `~/bin/framestudio` and removes obsolete standalone
workflow aliases. It also adds **FrameStudio** to desktop application launchers
(including Noctalia) using an XDG application entry with `Terminal=false`.
Press `Super+Space`, search for `FrameStudio`, and launch it without a terminal.
Both the desktop entry and the command run this checkout directly, so restarting
FrameStudio uses the latest code present here, with no reinstall after updates.
This does not automatically download newer commits.

Ensure `~/bin` is on `PATH`, then verify the installation:

```sh
framestudio --version
framestudio --help
```

The repository entrypoint can always be used directly:

```sh
python3 framestudio.py --help
```

To install the optional faster preview runtime without changing system Python:

```sh
python3 -m venv --system-site-packages .venv
.venv/bin/python -m pip install --requirement requirements-preview.txt
```

Use Python 3.12 or newer for that environment. `make setup` includes the same
optional runtime alongside the development tools. The editor can discover the
repository's `.venv` for its preview worker even when the canonical command
uses system Python.

The default `FRAMESTUDIO_PREVIEW_BACKEND=auto` selects supported acceleration
and reports capability fallback. To compare CPU decoding or restore the
reference path:

```sh
FRAMESTUDIO_PREVIEW_BACKEND=cpu framestudio
FRAMESTUDIO_PREVIEW_BACKEND=ffmpeg framestudio
```

`cuda` requests hardware decoding where supported, with diagnostic CPU
fallback otherwise. `FRAMESTUDIO_PREVIEW_PYTHON=/absolute/path/to/python`
selects another helper interpreter with the pinned optional runtime installed.
Initial helper/device startup is separate from retained-decoder seek latency.

## Open the editor

Start with an empty project and add videos in the interface:

```sh
framestudio
```

Open one source directly:

```sh
framestudio --source ~/Videos/source.mp4
```

Reopen a saved project:

```sh
framestudio --project ~/Videos/project.framestudio.json
```

Equivalent repository commands are available:

```sh
make start
make editor ARGS="--source /absolute/path/to/video.mp4"
make editor ARGS="--project /absolute/path/to/project.framestudio.json"
```

## Edit in the GTK interface

1. Click **Add clips** and choose one or more local videos.
2. When a project is already open, **Add clips** appends the new videos to the
   existing edited timeline. It does not replace the saved cuts, deleted
   segments, focus settings, or triplicate settings.
   Selecting multiple videos in one batch randomizes their timeline order;
   adding a single video leaves it at the end.
3. Wait for metadata probing to attach or append the clips. Audio analysis
   waits until export.
4. Play, pause, seek, or use `Left` and `Right` to move by one second.
5. Press `B` to split at the playhead.
6. Select segments with click, `Ctrl`-click, or `Shift`-click.
7. Press `Delete` to toggle a selected segment between deleted and included.
   Press `Backspace` to remove selected segments instead, closing their space
   on each affected track. **Undo removal** restores up to the last 20 removals
   in the current editor session. Other timeline edits invalidate this history.
8. Move selected segments with `Shift+Left` and `Shift+Right`.
9. Copy and paste segments with `Ctrl+C` and `Ctrl+V`.
10. Use Focus and Triplicate controls when a segment needs a different framing.
11. Save a normal project when a durable named project file is needed.
12. Use Recover autosave after an unexpected exit.
13. Review the export plan, enhancement counts, and destination before
    starting the render.

Use `Ctrl+Z` or `Super+Z` to undo the latest split or removal. Up to 20
consecutive splits can be undone, including splits made with `B`. Split undo
restores the original clips and selection. Other timeline edits or loading a
project clear split history; this is not a general undo/redo stack. Text fields
keep their own keyboard shortcuts. Arrow navigation stops at the first or last
available frame rather than seeking past the video.

The information strip shows only the focused selected video's filename,
original dimensions, and original FPS. For a multi-selection, it follows the
last focused segment. Clearing the selection shows **No video selected**.
Audio analysis remains deferred until confirmed export and does not run while
editing. Export-preparation failures remain visible in the status area.

### Timeline controls

| Control | Action |
| --- | --- |
| `Space` | Play or pause |
| `Left` / `Right` | Move the playhead by one second |
| `B` | Split at the playhead |
| `Ctrl+Z` / `Super+Z` | Undo the latest split or removal |
| `Delete` | Toggle the selected segment deleted/included |
| `Backspace` | Remove selected segments and ripple later blocks on their tracks |
| **Undo removal** | Restore the latest removal in the current editor session |
| `Shift+Left` / `Shift+Right` | Move selected segments |
| `Ctrl+C` / `Ctrl+V` | Copy and paste selected segments |
| `Ctrl` + mouse wheel | Zoom the timeline |
| `Ctrl+0` | Fit the default timeline view |
| `30 min` | Fit a 30-minute timeline window |
| Normal mouse wheel | Move the playhead by 30 seconds per scroll unit |
| `Alt` or `Shift` + mouse wheel | Move the zoomed timeline viewport |

Seeking while playing keeps playback active. Enabling or disabling Triplicate
keeps the current playhead and play/pause state.

The selected clip follows playback and playhead seeks. With synchronized
tracks, it follows the included clip on the active track; empty or excluded
intervals have no playing selection. While paused, a manually selected deleted
clip can stay selected independently of the playhead for moving or restoring it.
Paused multi-selections also remain available for editing; starting playback
returns to the single playing clip.
Ctrl-click adds or removes clips without playhead-follow selection replacing the
manual selection. A normal clip click or starting playback resumes automatic
selection.

Each clip has a lighter start zone: the first 10% of its displayed width,
capped at 16 screen pixels. Clicking this zone snaps the playhead to the exact
clip start. Hold `Super` while clicking to bypass snapping. The zone follows
zoom and never extends beyond the clip's actual duration, including subpixel
clips when zoomed out. Clicking the ruler or scrubbing does not use start
snapping; actual drags use the track-movement rules below.
Small pointer movement during a click uses GTK's configured drag threshold,
so ordinary hand movement does not cancel snapping or accidentally move a clip.
The numbered badges are part of each clip's clickable area, including their
portion above the clip body; the same start-zone and Super-bypass rules apply.

### Synchronized tracks

Use **Add track** to create up to four tracks. For an existing sequential
project, confirm **Convert and add track** to preserve its clips while
switching to absolute timeline positions. The Track selector chooses where
newly imported clips go. **Remove track** removes only an empty track.

Drag clips within or between track rows. Clips cannot overlap on the same
track, including excluded clips. A colliding drop snaps forward to the first
available position. Framing, copies and Triplicate remain individual block
settings.
Dragging any selected clip moves the entire selection as one group, in both
the live preview and the final drop. Relative timing, gaps, and track spacing
are preserved. Collisions shift the whole group together to the first fitting
position; a group cannot move before time zero or beyond the available tracks.
Invalid drops leave every clip unchanged, and the moved group remains selected.

Preview is silent. Simultaneously included clips determine the visible
layout: one fills the canvas, two use vertical halves, three use vertical
thirds, and four use a row-major 2-by-2 grid. Sources are centered in their
cells, with their individual framing applied. Empty intervals are black.
The final video uses the same layout with fixed stereo positioning, while
independent source reels retain normal source audio.

## Projects and autosave

Normal projects use the `.framestudio.json` suffix. They contain versioned
editor state, source identities, timeline segments, playback position, visual
modifications, triplicate state, and export policies.

The current-project autosave is stored at:

```text
$XDG_STATE_HOME/framestudio/autosave.framestudio.json
```

When `XDG_STATE_HOME` is not set, FrameStudio uses:

```text
~/.local/state/framestudio/autosave.framestudio.json
```

There is one current autosave. Opening another project replaces it, while
adding clips updates the current autosave with the expanded source set.
Autosave is separate from the normal Save project destination. To render the
same edited project with different additional videos, reopen the saved base
project before each new **Add clips** operation.

## Export and resume

The export panel shows the selected output frame rate, the number of sources
that need frame-rate enhancement, the number eligible for upscale enhancement,
and the expected work before rendering begins.

Enhancement counts and FPS choices use only sources with included timeline
segments. Planning shares one AI-runtime preflight across those sources and
subsequent setting or filename changes within the same panel. Refreshes run
serially and keep only the latest pending request, rather than launching
competing CUDA/model-loading processes. Closing the panel drops pending work;
an already-running check may finish, but its result is discarded. Reopening
the panel starts a fresh validation session. Actual rendering still validates
its prerequisites, and audio analysis remains deferred until **Start export**.

Completed audio measurements are also saved atomically to
`${XDG_CACHE_HOME:-~/.cache}/framestudio/audio-analysis/` as each source finishes.
They survive cancellation and application restarts, including when the project
file still contains pending audio settings. Reuse requires the same source
identity, audio metadata, analysis policy, and FFmpeg identity. Changed sources
or configuration invalidate the cache; interrupted or failed scans are not
persisted as successful results.

After audio analysis, export reports source inspection, source preservation,
output planning, segment preparation, and video composition instead of leaving
the audio stage at 100%. Synchronized planning inspects only included video
sources and does not decode entire original videos to count frames that the
planner never uses. Source hashes persist in
`$XDG_CACHE_HOME/framestudio/source-hashes/` (default
`~/.cache/framestudio/source-hashes/`), across failed exports and application
restarts. Each completed hash is saved atomically, keyed by resolved path,
size and nanosecond mtime, plus device, inode and ctime to detect replacement
or same-size edits with a restored mtime. Changed identities are rehashed;
unchanged sources avoid another complete read during planning and preservation
checks. Cache reuse relies on filesystem metadata, not a fresh byte-for-byte
scan. Rendered outputs and checkpoint files still receive full content checks.
Cancellation is checked while hashing and is forwarded to native segment
extraction, enhancement, and composition subprocesses.

The CLI supports the same export engine:

```sh
framestudio export PROJECT.framestudio.json \
  --output ~/Videos/edited.mp4 \
  --human-progress
```

The export planner defaults to the final video only. Enable edited source
reels to also export a compact video for each included `(track, source)`
pair. The same source on two tracks produces two independent reels. Each
reel preserves retained cuts, copies, framing and smart enhancement policies,
but has no timeline gaps, split-screen layout or other tracks' audio.
Empty and excluded-only tracks produce no reels.

The synchronized final video uses one shared timeline: overlapping included
blocks occupy their layout slots at the same time. Each enhanced block is
extracted at its native resolution, optionally upscaled, then frame-rate
enhanced before final cropping and placement. Copies of the same exact source
range now share that native preparation, including across tracks, reimported
copies of the same file content, and different final crop/zoom/Triplicate
settings. Each block still receives its own final framing and timeline
placement. Different source ranges, processing domains, models or rate policies
are not treated as interchangeable. Adjacent cuts are not joined into one AI
stream, avoiding interpolation across edit boundaries.

The final compositor avoids opening an entire large timeline as one filter
graph. Graphs with repeated input paths or more than four input paths render
one layout interval at a time to verified lossless FFV1/AVI checkpoints, then
perform one final H.264 encode. This bounds simultaneous decoders and prevents
shared-input branches from buffering future intervals until memory is exhausted.
Simple independent graphs retain the direct path. Blocks that need no enhancement
still use their original source directly; caching adds no lossy intermediate.
Single-frame intervals between prepared-frame timestamps, or at a rounded clip
tail, retain the covering available frame instead of creating an empty layout.

Within a resumable batch, completed native extraction, upscale, FPS conversion,
video composition intervals, final video composition, individual audible audio
tracks, final audio composition and
verified AV mux are separate durable checkpoints. Each is recorded only after
successful verification, with a content
hash and a recipe/tool/runtime identity. Custom restoration models are
content-fingerprinted too. Resume checks checkpoint integrity and reuses matching
completed work even in a new application process. Each unique segment is saved
individually, not only at the end of an entire interpolation batch: stopping
after 20 of 40 completed segments preserves those 20. A completed verified
fallback is reused before retrying an AI backend that failed on the same range.
Audio tracks retain their timeline placement, gain and pan in floating-point
PCM checkpoints. Shared headroom and limiting are applied only in the final
mix. If another track or the final mix fails, completed matching tracks are
reused; an unfinished track must still restart. Silent and excluded tracks do
not trigger source-audio rendering.
An operation that finished writing but was interrupted before validation retains
its pending file for validation on resume. Incomplete or invalid files are
rebuilt; they are never accepted as completed work. An interruption inside an
unfinished encoder/inference operation may still require repeating that item;
arbitrary in-memory AI/encoder state is not a frame-level checkpoint.
Checkpoint/storage errors are explicit failures, not reasons to silently
downgrade the AI backend. Any permitted enhancement fallback is retained in the
video checkpoint metadata and reported again on reuse.

These preparation checkpoints live under the parent session's
`render-preparations/` directory. Successful batch delivery, **Start over**, or
**Discard** removes them through the existing session lifecycle. They are not
a permanent cross-project library. The separate source-hash cache survives
session cleanup. Source identity checks and final output-publication
verification still run on resume.

This reuse applies to the synchronized final video. Edited source reels still
use their separate full-canvas processing route and its existing checkpoints;
they do not share native AI preparations with the final compositor or with
other reels. Sharing them blindly could change crop, scaling or audio semantics.

#### Repeated-render measurements

Controlled local trials used three tracks, six blocks containing two unique
half-second ranges, a generated moving 320x180/30 FPS source with stereo audio,
and a 1920x1080/60 FPS final video. Upscale was disabled to isolate FPS work.
Each row is the median of three runs on an RTX 5070 Ti, with existing RVE
TensorRT engines, FFmpeg n9.0.2 and Python 3.14.8. Each cold render used a new
preparation store. The baseline used preserved pre-optimization renderers.

| Strategy | FFmpeg interpolation | RVE 4.26 | Extraction / FPS jobs | Decoder inputs |
| --- | ---: | ---: | ---: | ---: |
| Before content reuse | 2.831 s | 40.155 s | 6 / 6 | 6 |
| Content reuse only | 1.665 s | 14.204 s | 2 / 2 | 6 |
| Content reuse + shared inputs | 1.644 s | 13.998 s | 2 / 2 | 2 |
| Selected: reuse + shared inputs + checkpoints | 1.864 s | 14.444 s | 2 / 2 | 2 |
| Resume after video composition: remaining work | 0.434 s | 0.461 s | 0 / 0 | 0 |

The selected resumable RVE path took **64.03% less time (2.78x speedup)** than
the baseline; the FFmpeg path took **34.15% less time (1.52x speedup)**.
Without durable checkpoints the cold run was slightly faster, so checkpoint
integrity/persistence is an explicit tradeoff, not a free optimization.
Resuming an already verified RVE AV mux took a median **0.056 s** in this
fixture, without extraction, interpolation, video/audio recomposition or muxing.
These resume values measure remaining work, not a complete render from scratch.

Decoded output frames were identical within each backend across strategies,
with 60 output frames and unchanged source content. Timings cover the core
synchronized AV renderer, not planning, audio analysis, optional source reels
or the batch coordinator's final publication verification. This small fixture
does not predict the exact speedup of an arbitrary long project, nor prove
large-project memory bounds.

Expanding the fixture to **24 blocks**, with repeated ranges both within and
across tracks, reduced FFmpeg-render median time from **10.168 s to 3.902 s**
(**61.62% less time, 2.61x speedup**, three trials). Extraction/FPS jobs and
decoder inputs fell from 24 to 2, with identical 240-frame decoded output.
Separate real-RVE cancellation checks confirmed reuse across fresh application
processes at FPS, video, audio and mux checkpoints. A restoration-plus-FPS run
also preserved a completed upscale checkpoint: only the other unique range was
restored after resume, and its final frames matched the uninterrupted render.
Exact trial data is recorded in
[`benchmarks/repeated_render_results.json`](benchmarks/repeated_render_results.json).
CPU/RVE absolute times are not a quality comparison: they use different
interpolation algorithms, and model startup dominates this short RVE fixture.

Reproduce the experiment without private media:

```sh
python3 benchmarks/repeated_render_benchmark.py \
  --strategy baseline --backend rve-4.26 --trials 3 --report /tmp/repeat-before.json
python3 benchmarks/repeated_render_benchmark.py \
  --strategy optimized --backend rve-4.26 --trials 3 --report /tmp/repeat-after.json
python3 benchmarks/repeated_render_benchmark.py \
  --strategy resume --backend rve-4.26 --trials 3 --report /tmp/repeat-resume.json
```

The standalone `baseline` mode disables content reuse; optional paired
`--baseline-video` / `--baseline-av` paths load preserved renderer snapshots.
`deduplicated` and `shared-inputs` isolate the other candidates.
`--resume-after "verified AV composition"` measures a completed mux checkpoint,
`--repeats-per-track 4` adds within-track copies, and `--upscale` includes the
restoration stage. Reports include trial times, job counts, decoded-frame hashes,
source-preservation checks, and completed interpolation backends.

#### Additional multitrack optimization

The final compositor bounds decoder/filter concurrency when it consumes at
least three distinct video inputs, rather than creating an automatic decoder
thread pool for every input. One/two-input renders and the final encoder keep
their existing settings. Identical triplicate scale/format work runs once
before the three crops, and repeated audio uses one input decoder with separate
trim, resample, pan and limiter branches.

Three sequential local trials compared this combination against the already
deduplicated renderer above, with the same encoded profile and identical
decoded video/PCM. These are additional results, not cumulative percentages:

| Generated workload | Before, median | Selected, median | Less elapsed time |
| --- | ---: | ---: | ---: |
| 3 tracks, 35 sources, 114 blocks, 116 layout intervals | 11.468 s | 8.027 s | 30.0% (1.43x) |
| 3 tracks with triplicate composition | 2.525 s | 1.776 s | 29.7% (1.42x) |
| Repeated ranges with FFmpeg FPS enhancement | 3.628 s | 3.552 s | 2.1% (approximately neutral) |

Inputs were generated 320x180 media; output remained 1920x1080. These
workstation-specific results do not predict the full duration of a real
high-resolution/RVE export. Lossless per-track/chunk intermediates were also
tested, but added overhead rather than winning on the tested static workload.
These timings describe the earlier monolithic graph, not the bounded interval
path. A subsequent real-project run exhausted RAM/swap during composition, so
risky graphs now use the lossless interval path described above even when the
small synthetic graph was faster. The interval path does not rerender preceding
timeline prefixes or encode each interval lossily. No GPU scaler/encoder
substitution or reduced-quality intermediate was adopted.

Completed native, upscale, FPS and audio checkpoints remain reusable. A
composition-clock correction invalidates only old video/mux preparation
recipes, preventing one-frame layout intervals from losing frames during
concatenation. It does not discard completed segment enhancement or audio work.
The same limitation on resuming inside an unfinished operation still applies.
Protocol, limitations and exact trial data are in
[`evidence/efficient-export-pipeline-benchmark.md`](evidence/efficient-export-pipeline-benchmark.md)
and [`evidence/multitrack-render-results.json`](evidence/multitrack-render-results.json).

Disable the final-video option to export only the reels. These choices also
work with synchronized tracks:

```sh
framestudio export PROJECT.framestudio.json \
  --output ~/Videos/edited.mp4 --output-mode combined
framestudio export PROJECT.framestudio.json \
  --output ~/Videos/edited.mp4 --output-mode source-only
```

In these examples, the reels are written under `~/Videos/edited-sources/`.
Source-only mode does not render `edited.mp4` or start the final compositor.
If the optional RVE restoration runtime or model is unavailable, source reels
use normal full-canvas scaling and report AI upscale enhancement as disabled.
An available RVE runtime retains the configured enhancement policy.

The UI and CLI use the same resolved enhancement settings when identifying an
export session, so the same project and export options can resume across both.

Export sessions are scoped to the destination and keep compatible checkpoints
in adjacent working directories:

```text
.<destination-name>.framestudio-session/
.<destination-name>.framestudio-intermediates/
```

Use the explicit session modes when needed:

```sh
# Continue a compatible cancelled or failed export.
framestudio export PROJECT.framestudio.json \
  --output ~/Videos/edited.mp4 --resume

# Discard checkpoints and build the export again.
framestudio export PROJECT.framestudio.json \
  --output ~/Videos/edited.mp4 --restart

# Remove the pending session without rendering.
framestudio export PROJECT.framestudio.json \
  --output ~/Videos/edited.mp4 --discard
```

Resume rejects changes to the project, source files, destination, export
policies, runtime, or FFmpeg/FFprobe identity. A normal export without a
session option starts fresh.

Each output is verified before its own atomic publication. A failure or
cancellation can leave verified siblings available without making the whole
batch complete. Resume checks both the request fingerprint and the published
file's content proof before skipping it. A changed output is rendered again.
Successful batches have an adjacent hidden
`.<destination-name>.framestudio-batch-receipt.json` receipt. It is advisory
recovery state, not an atomic transaction across all output files.
Discard removes recovery state, never original media or published outputs.

During an actual export, an adjacent hidden diagnostic journal is kept at
`.<destination-name>.framestudio-export.log`. It records operations, output
position, percentages, subprocess PIDs and exit diagnostics, chained errors,
and a heartbeat every five seconds even when no frames advance. Memory snapshots
include the editor and children launched by its worker threads, with resident,
peak resident, and swap usage. It survives
cancellation, failure, or a killed application and appends new attempts. A
subsequent attempt identifies an unfinished previous run. It is removed only
after the entire requested output set has been verified and delivered.
An abrupt kill or power loss cannot write a final explanation; the retained
last heartbeat and operation show where execution stopped, not an invented
crash cause. The log is private to the local user and is not a substitute for
the media checkpoints.

When stdout is used for automation, export progress is JSON Lines. Human
readable numbered stages are written to stderr, so terminal progress does not
corrupt machine-readable output. Human progress refreshes every five seconds
while progress samples continue, even when the displayed percentage has not
advanced, and during long FFprobe frame-count and FFmpeg decoded-output
validation scans. The versioned details are in
[`docs/specs/cli-contract.md`](docs/specs/cli-contract.md).

The editor shows separate **Overall** and **Current operation** progress bars.
The Overall bar includes whole-export elapsed time and an estimated remaining
time; the current-operation timing remains separate. ETA is unknown until there
is measurable progress, excludes jumps from verified reused work when estimating
the processing rate, and reaches zero only on whole-batch completion.
CLI progress reports both percentages and the current output number. Overall
progress weights all requested outputs by duration, reserves preparation and
verification/publication work, and nests segment preparation, composition,
audio and mux progress. It never resets for the next segment or output and
reaches 100% only when the whole batch succeeds. Verified reused outputs count
toward completed work; reused substeps advance as their integrity is checked.
These weights measure planned work, not an exact share of wall-clock time.

## Use the command-line editor

The CLI and GTK editor operate on the same project format and domain model.
Commands return JSON on stdout and structured errors on stderr.
When an import or add command receives multiple videos, their timeline order
is randomized; a single video is appended without reordering existing clips.

### Create and inspect projects

```sh
framestudio import ~/Videos/landscape.mp4 ~/Videos/portrait.mp4 \
  --project ~/Videos/mixed.framestudio.json
framestudio add ~/Videos/edit.framestudio.json ~/Videos/next-source.mp4
framestudio inspect ~/Videos/mixed.framestudio.json
framestudio duration ~/Videos/mixed.framestudio.json
framestudio analyze-audio ~/Videos/mixed.framestudio.json
framestudio reopen ~/Videos/mixed.framestudio.json
```

### Edit timeline segments

```sh
framestudio split PROJECT.framestudio.json --at 12.5
framestudio delete PROJECT.framestudio.json --segment SEGMENT_ID
framestudio restore PROJECT.framestudio.json --segment SEGMENT_ID
framestudio move PROJECT.framestudio.json --segment SEGMENT_ID \
  --direction right
framestudio copy PROJECT.framestudio.json --segment SEGMENT_ID
framestudio paste PROJECT.framestudio.json --segment SEGMENT_ID --at 0
```

### Apply visual changes

```sh
framestudio focus PROJECT.framestudio.json --segment SEGMENT_ID \
  --zoom 2 --offset-x 120 --offset-y -80
framestudio copy-focus PROJECT.framestudio.json \
  --source-segment SOURCE_SEGMENT_ID --segment DESTINATION_SEGMENT_ID
framestudio triplicate-enable PROJECT.framestudio.json --segment SEGMENT_ID
framestudio triplicate-disable PROJECT.framestudio.json --segment SEGMENT_ID
framestudio clean-focus PROJECT.framestudio.json --segment SEGMENT_ID
```

### Configure export policy

```sh
framestudio set-fps-policy PROJECT.framestudio.json \
  --choice 60 --enhance-fps --fps-backend rve-4.26
framestudio set-upscale-policy PROJECT.framestudio.json \
  --enable-upscale --upscale-model SuperUltraCompact \
  --upscale-backend rve-restoration
framestudio export-plan PROJECT.framestudio.json
```

The complete command and JSON contract is documented in
[`docs/specs/cli-contract.md`](docs/specs/cli-contract.md).

## Preserved media commands

FrameStudio keeps the original media tools available under one command:

### Prepare media

```sh
framestudio media --root ~/Videos/to-edit
framestudio media --dry-run --root ~/Videos/to-edit
framestudio media --profile fast --keep-originals --root ~/Videos/to-edit
framestudio media --profile lossless --gpu auto --root ~/Videos/to-edit
```

The `fast` profile prepares unsupported media as DNxHR/PCM editing
intermediates. The `lossless` profile uses FFV1/PCM. Operations use partial
outputs, verification, and safe cleanup.

### Concatenate and enhance FPS

```sh
framestudio concat ~/Videos/to-edit
framestudio concat ~/Videos/to-edit --concat-only
framestudio concat ~/Videos/to-edit --engine ffmpeg-minterpolate
framestudio fps ~/Videos/source.mp4 --target-fps 60
framestudio fps ~/Videos/source.mp4 --engine ffmpeg-minterpolate
```

These commands preserve the original preparation, concatenation, audio, and
frame-rate workflows. Performance mode can be enabled temporarily for media
processing and is restored afterward when the system integration is
available.

## Boundaries

FrameStudio is local and offline. It does not provide cloud storage,
collaboration, accounts, telemetry, Windows or macOS support, multiple
independent tracks, advanced transitions, titles, captions, color grading, or
full compositor behavior.

GPU and restoration performance depends on the workstation, drivers, media,
and installed runtimes. Unsupported codecs, timestamp ambiguity, and FFmpeg
failures are reported explicitly. The source media and last verified output
remain protected.

Future product direction is recorded in
[`docs/specs/future-product-direction.md`](docs/specs/future-product-direction.md).
It is context for later decisions, not an automatic requirement for the
current editor.

## Project documentation

| Document | Purpose |
| --- | --- |
| [`vision.md`](vision.md) | Product direction and durable constraints |
| [`docs/specs/project-scope.md`](docs/specs/project-scope.md) | Approved product scope |
| [`docs/specs/editor-foundation-decision.md`](docs/specs/editor-foundation-decision.md) | GTK, FFmpeg playback, and project-format decisions |
| [`docs/specs/cli-contract.md`](docs/specs/cli-contract.md) | Versioned CLI and export contract |
| [`docs/specs/future-product-direction.md`](docs/specs/future-product-direction.md) | Deferred product direction |

## Run the tests

For local development, the repository uses Python `unittest` and repository
quality commands:

```sh
make test
make check
make smoke
make quality PYTHON=.venv/bin/python
```

The product documentation above is the starting point for using FrameStudio.
