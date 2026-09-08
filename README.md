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
- Play, pause, seek, and step through frames in the editor.
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

The editor attaches media from metadata first, so a project becomes usable
without waiting for a full audio scan. Source-level audio analysis continues
in the background and is used when the export is prepared. Playback is
optimized for responsive video seeking; final audio decisions are applied and
validated during export.

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
- GTK 4 and PyGObject (`gi`).
- FFmpeg and FFprobe.

`ffplay` is optional and is used for audio preview. The editor reports audio
preview failures explicitly and remains usable without it.

The optional frame-rate and upscale paths can use NVIDIA/CUDA/NVENC, Vulkan,
and a local REAL-Video-Enhancer installation. If the preferred restoration
runtime is unavailable, eligible exports use the validated FFmpeg
interpolation fallback. The original media workflows also support CPU-only
operation.

## Install

Clone the repository and install the single canonical command:

```sh
git clone <repository-url>
cd FrameStudio
./install.sh
```

The installer creates `~/bin/framestudio` and removes obsolete standalone
workflow aliases. Ensure `~/bin` is on `PATH`, then verify the installation:

```sh
framestudio --version
framestudio --help
```

The repository entrypoint can always be used directly:

```sh
python3 framestudio.py --help
```

## Open the editor

Start with an empty project and choose videos in the interface:

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

1. Select one or more local videos.
2. Wait for metadata probing to attach the project. Audio analysis continues
   in the background.
3. Play, pause, seek, or use `Left` and `Right` for frame navigation.
4. Press `B` to split at the playhead.
5. Select segments with click, `Ctrl`-click, or `Shift`-click.
6. Press `Delete` to toggle a selected segment between deleted and included.
7. Move selected segments with `Shift+Left` and `Shift+Right`.
8. Copy and paste segments with `Ctrl+C` and `Ctrl+V`.
9. Use Focus and Triplicate controls when a segment needs a different framing.
10. Save a normal project when a durable named project file is needed.
11. Use Recover autosave after an unexpected exit.
12. Review the export plan, enhancement counts, and destination before
    starting the render.

### Timeline controls

| Control | Action |
| --- | --- |
| `Space` | Play or pause |
| `B` | Split at the playhead |
| `Delete` | Toggle the selected segment deleted/included |
| `Shift+Left` / `Shift+Right` | Move selected segments |
| `Ctrl+C` / `Ctrl+V` | Copy and paste selected segments |
| `Ctrl` + mouse wheel | Zoom the timeline |
| `Ctrl+0` | Fit the default timeline view |
| `30 min` | Fit a 30-minute timeline window |
| Normal mouse wheel | Move the playhead |
| `Alt` or `Shift` + mouse wheel | Move the zoomed timeline viewport |

Seeking while playing keeps playback active. Enabling or disabling Triplicate
keeps the current playhead and play/pause state.

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

There is one current autosave. Loading another project or attaching a new
source set replaces it. Autosave is separate from the normal Save project
destination.

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

When stdout is used for automation, export progress is JSON Lines. Human
readable numbered stages are written to stderr, so terminal progress does not
corrupt machine-readable output. The versioned details are in
[`docs/specs/cli-contract.md`](docs/specs/cli-contract.md).

## Use the command-line editor

The CLI and GTK editor operate on the same project format and domain model.
Commands return JSON on stdout and structured errors on stderr.

### Create and inspect projects

```sh
framestudio import ~/Videos/landscape.mp4 ~/Videos/portrait.mp4 \
  --project ~/Videos/mixed.framestudio.json
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
