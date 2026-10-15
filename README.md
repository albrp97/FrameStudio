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
- Write failure logs before an optional sleep or shutdown action.
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
| `B` | Split at the playhead |
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

### Synchronized tracks

Use **Add track** to create up to four tracks. For an existing sequential
project, confirm **Convert and add track** to preserve its clips while
switching to absolute timeline positions. The Track selector chooses where
newly imported clips go. **Remove track** removes only an empty track.

Drag clips within or between track rows. Clips cannot overlap on the same
track, including excluded clips. A colliding drop snaps forward to the first
available position. Framing, copies and Triplicate remain individual block
settings.

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

When stdout is used for automation, export progress is JSON Lines. Human
readable numbered stages are written to stderr, so terminal progress does not
corrupt machine-readable output. Human progress refreshes every five seconds
while progress samples continue, even when the displayed percentage has not
advanced, and during long FFprobe frame-count and FFmpeg decoded-output
validation scans. The versioned details are in
[`docs/specs/cli-contract.md`](docs/specs/cli-contract.md).

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
