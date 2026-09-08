# FrameStudio

FrameStudio is a fast, local video editor for Linux. It combines a GTK 4
timeline editor, FFmpeg playback and export, and a deterministic CLI for
automation.

It is built for one practical workflow: import footage, make precise
non-destructive edits, preview the result, and export a verified video without
touching the original media. The repository also preserves the media
preparation, concatenation, and frame-rate workflows that came before the
editor.

## What is delivered

The current editor supports:

- One or several source videos in a project, including mixed dimensions and
  frame rates.
- A fixed 1920x1080 project canvas with contain scaling and letterboxing.
- FFmpeg-backed video playback with play, pause, seek, and frame navigation.
- A visual timeline with selection, split, delete/restore, movement, copy, and
  paste operations.
- Multi-selection with `Ctrl`-click and range selection with `Shift`-click.
- Per-segment focus controls with zoom and X/Y offsets.
- Linked triplicate composition for portrait or center-focused footage.
- Versioned JSON projects with atomic saves and source identity validation.
- One current-project autosave with crash recovery.
- Background source-level audio analysis without blocking initial project use.
- Unlimited timeline zoom and a 30-minute viewport-fit action.
- Export planning with frame-rate and upscale counts before rendering.
- Verified stream-copy exports when safe, with an explicit fallback render path
  when decoding is required.
- Optional frame-rate enhancement and orientation-aware SuperUltraCompact
  upscale enhancement.
- Resumable ordinary and enhanced exports across cancellation, failure,
  process restart, project reopen, and time-sliced work.
- Numbered export stages on the terminal, while stdout remains valid JSON Lines.
- Explicit GTK actions for Resume, Start over, and Discard.
- Failure logs and optional sleep or shutdown actions after export.

FrameStudio is not a full DaVinci Resolve replacement. It is a focused,
single-user Linux editor with a safe, inspectable workflow.

## Requirements

FrameStudio targets a Linux workstation and requires:

- Python 3.10 or newer. Python 3.14 is validated on the development
  workstation.
- GTK 4 and PyGObject (`gi`).
- FFmpeg and FFprobe.

`ffplay` is optional and is used for audio preview. The editor remains usable
without it and reports audio-preview failures explicitly.

The optional FPS and upscale paths may use NVIDIA/CUDA/NVENC, Vulkan, and a
local REAL-Video-Enhancer installation. If the preferred RVE runtime is not
available, eligible editor exports use the validated FFmpeg interpolation
fallback. The legacy media workflows also support CPU-only operation.

## Install the command

The repository uses the system GTK/PyGObject runtime rather than packaging the
GUI as a Python wheel.

```sh
git clone <repository-url>
cd FrameStudio
./install.sh
```

`install.sh` installs one canonical command at `~/bin/framestudio` and removes
the obsolete standalone `framestudio-*` and `resolve-*` workflow aliases.
Ensure `~/bin` is on `PATH`, then verify:

```sh
framestudio --help
framestudio --version
```

You can always run the repository entrypoint directly:

```sh
python3 framestudio.py --help
```

## Start the editor

Launch an empty editor and choose media from the interface:

```sh
framestudio
```

Open a source directly:

```sh
framestudio --source ~/Videos/source.mp4
```

Reopen a saved project:

```sh
framestudio --project ~/Videos/source.framestudio.json
```

The same commands are available from the repository:

```sh
make start
make editor ARGS="--source /absolute/path/to/video.mp4"
make editor ARGS="--project /absolute/path/to/project.framestudio.json"
```

## Editor workflow

1. Select one or more local videos.
2. Wait for metadata probing to attach the project. Full-file audio analysis
   continues in the background and is shown per source.
3. Play, pause, seek, or use `Left` and `Right` for frame navigation.
4. Split at the playhead with `B`.
5. Select blocks with click, `Ctrl`-click, or `Shift`-click.
6. Toggle deletion with `Delete`, move blocks with `Shift+Left` and
   `Shift+Right`, and copy/paste with `Ctrl+C` and `Ctrl+V`.
7. Use Focus and Triplicate controls when a segment needs a different visual
   framing.
8. Save a normal project when a durable named project file is needed.
9. Use Recover autosave after an unexpected exit.
10. Export only after reviewing the plan, target frame rate, upscale count, and
    estimated work.

Useful timeline controls:

| Control | Action |
| --- | --- |
| `Space` | Play or pause |
| `B` | Split at the playhead |
| `Delete` | Toggle the selected block deleted/included |
| `Shift+Left` / `Shift+Right` | Move selected blocks |
| `Ctrl+C` / `Ctrl+V` | Copy and paste selected blocks |
| `Ctrl` + mouse wheel | Zoom the timeline without an upper limit |
| `Ctrl+0` | Fit the default timeline view |
| `30 min` | Fit a 30-minute viewport |
| Normal mouse wheel | Move the playhead |
| `Alt`/`Shift` + mouse wheel | Move the zoomed timeline viewport |

Seeking while playing preserves playback. Enabling or disabling Triplicate
preserves the current playhead and play/pause state.

## Projects and recovery

Normal project files use the `.framestudio.json` suffix. They contain versioned
editor state, source identities, timeline blocks, playback position, visual
modifications, triplicate state, and output policies. Project writes are
atomic, and a source is rejected when its stored identity no longer matches.

FrameStudio also keeps one autosave for the current project:

```text
$XDG_STATE_HOME/framestudio/autosave.framestudio.json
```

When `XDG_STATE_HOME` is not set, the default is:

```text
~/.local/state/framestudio/autosave.framestudio.json
```

Loading another project or attaching new sources replaces the previous
autosave. Autosave is separate from the normal Save project destination.

## Export

The editor and CLI use the same export planning and execution paths.

### Safety guarantees

- Original source files are never overwritten or deleted by editor export.
- The destination is written to a temporary or partial path first.
- FFmpeg and FFprobe verify the result before publication.
- The final output is published atomically only after verification.
- Failed or cancelled exports remove incomplete final output but preserve
  validated work that can be resumed.
- Empty edits and incompatible export destinations are rejected explicitly.

### Render behavior

Every editor project renders to the fixed 1920x1080 canvas. Sources with other
dimensions or orientations are contain-scaled and letterboxed. Stream copy is
used only when the source, cut boundaries, and policies make it safe.
Otherwise FrameStudio uses the validated fallback render profile.

The persisted frame-rate policy defaults to a 60 FPS target with enhancement
enabled for eligible sources. The export panel reports how many sources need
enhancement. The RVE 4.26 backend is preferred when available and
`ffmpeg-minterpolate` is the validated fallback.

Upscale enhancement is enabled by default for eligible sources. It uses the
SuperUltraCompact model and orientation-aware thresholds. The export panel
reports the eligible source count, and both the GUI and CLI support an
explicit opt-out.

Audio analysis is source-level, not segment-level. Export waits for terminal
audio decisions and fails explicitly when analysis cannot complete.

### Resumable exports

Each destination can have two adjacent working areas:

```text
.<destination-name>.framestudio-session/
.<destination-name>.framestudio-intermediates/
```

The session manifest records compatible checkpoints for cuts, preparation,
interpolation, upscale, assembly, and verification. The enhanced intermediate
cache stores validated expensive work. Both are fingerprinted against the
project, timeline, sources, destination, policies, runtime, and media tools.

The GTK export panel offers:

- **Resume export** to continue a compatible session.
- **Start over** to invalidate checkpoints and rebuild.
- **Discard** to remove a pending session without rendering.

The same controls are available from the CLI:

```sh
framestudio export PROJECT --output OUTPUT.mp4 --resume
framestudio export PROJECT --output OUTPUT.mp4 --restart
framestudio export PROJECT --output OUTPUT.mp4 --discard
```

Normal export remains fresh when no mode is supplied. A changed source,
project, destination, policy, runtime, or FFmpeg/FFprobe identity is rejected
instead of reusing unsafe artifacts. Session and intermediate directories are
removed only after verified final publication.

## Deterministic CLI

Editor commands emit versioned JSON on stdout and structured errors on stderr.
Absolute local paths are redacted by default. Use `--full-paths` only when an
automation workflow explicitly needs them.

Create and inspect projects:

```sh
framestudio import ~/Videos/landscape.mp4 ~/Videos/portrait.mp4 \
  --project ~/Videos/mixed.framestudio.json
framestudio inspect ~/Videos/mixed.framestudio.json
framestudio duration ~/Videos/mixed.framestudio.json
framestudio analyze-audio ~/Videos/mixed.framestudio.json
framestudio reopen ~/Videos/mixed.framestudio.json
```

Edit timeline blocks:

```sh
framestudio split PROJECT.framestudio.json --at 12.5
framestudio delete PROJECT.framestudio.json --segment SEGMENT_ID
framestudio restore PROJECT.framestudio.json --segment SEGMENT_ID
framestudio move PROJECT.framestudio.json --segment SEGMENT_ID \
  --direction right
framestudio copy PROJECT.framestudio.json --segment SEGMENT_ID
framestudio paste PROJECT.framestudio.json --segment SEGMENT_ID --at 0
```

Apply visual modifications:

```sh
framestudio focus PROJECT.framestudio.json --segment SEGMENT_ID \
  --zoom 2 --offset-x 120 --offset-y -80
framestudio copy-focus PROJECT.framestudio.json \
  --source-segment SOURCE_SEGMENT_ID --segment DESTINATION_SEGMENT_ID
framestudio triplicate-enable PROJECT.framestudio.json --segment SEGMENT_ID
framestudio triplicate-disable PROJECT.framestudio.json --segment SEGMENT_ID
framestudio clean-focus PROJECT.framestudio.json --segment SEGMENT_ID
```

Configure and inspect export policy:

```sh
framestudio set-fps-policy PROJECT.framestudio.json \
  --choice 60 --enhance-fps --fps-backend rve-4.26
framestudio set-upscale-policy PROJECT.framestudio.json \
  --enable-upscale --upscale-model SuperUltraCompact \
  --upscale-backend rve-restoration
framestudio export-plan PROJECT.framestudio.json
```

Export with machine-readable progress and terminal stage output:

```sh
framestudio export PROJECT.framestudio.json \
  --output ~/Videos/edited.mp4 \
  --human-progress
```

Export progress is JSON Lines on stdout. Human-readable numbered stages are
written to stderr, so scripts can parse stdout without filtering terminal
messages. The full versioned contract is documented in
[`docs/specs/cli-contract.md`](docs/specs/cli-contract.md).

## Preserved media workflows

The canonical command also exposes the original preparation workflows:

### Media preparation

```sh
framestudio media --root ~/Videos/to-edit
framestudio media --dry-run --root ~/Videos/to-edit
framestudio media --profile fast --keep-originals --root ~/Videos/to-edit
framestudio media --profile lossless --gpu auto --root ~/Videos/to-edit
```

The default `fast` profile prepares unsupported media as DNxHR/PCM editing
intermediates. The `lossless` profile uses FFV1/PCM. Conversions use partial
outputs, verification, and safe cleanup. Original files are retained when
`--keep-originals` is selected.

### Concatenation and FPS enhancement

```sh
framestudio concat ~/Videos/to-edit
framestudio concat ~/Videos/to-edit --concat-only
framestudio concat ~/Videos/to-edit --engine ffmpeg-minterpolate
framestudio fps ~/Videos/source.mp4 --target-fps 60
framestudio fps ~/Videos/source.mp4 --engine ffmpeg-minterpolate
```

`concat` is the integrated folder workflow. `fps` is the direct single-input
workflow. Both report progress and can temporarily switch to the system
performance profile, restoring the previous profile afterward when that
behavior is enabled.

The research and benchmark records remain separate from product behavior:

- [`FAST-CONCAT-RESEARCH.md`](FAST-CONCAT-RESEARCH.md)
- [`FPS-ENHANCEMENT-RESEARCH.md`](FPS-ENHANCEMENT-RESEARCH.md)
- [`FLOWFRAMES-RESEARCH.md`](FLOWFRAMES-RESEARCH.md)
- [`docs/research/video-restoration-strategies.md`](docs/research/video-restoration-strategies.md)

## Development

Create the local quality environment:

```sh
make setup
```

Run the repository checks:

```sh
make test
make compile
make check
make contract
make smoke
make quality PYTHON=.venv/bin/python
```

The full test suite uses Python `unittest`. Quality checks use the pinned
Ruff, mypy, Bandit, pip-audit, jscpd, dependency, and churn tools configured
by the repository. Generated static-analysis reports belong under
`evidence/static-analysis/`. Duplication keeps an approved baseline and gates
only newly introduced clone findings.

The GitHub Actions quality workflow is defined in
[`.github/workflows/quality.yml`](.github/workflows/quality.yml). The local
quality command is intended to match that workflow.

## Documentation map

| Document | Purpose |
| --- | --- |
| [`vision.md`](vision.md) | Product direction and durable constraints |
| [`docs/specs/project-scope.md`](docs/specs/project-scope.md) | Approved scope and acceptance outcomes |
| [`docs/specs/future-product-direction.md`](docs/specs/future-product-direction.md) | Deferred product intent beyond the delivered work |
| [`docs/specs/editor-foundation-decision.md`](docs/specs/editor-foundation-decision.md) | GTK, FFmpeg playback, and project-format decisions |
| [`docs/specs/cli-contract.md`](docs/specs/cli-contract.md) | Versioned CLI and export contract |
| [`docs/planning/repo-map.md`](docs/planning/repo-map.md) | Repository surfaces and validation commands |
| [`docs/planning/phases.md`](docs/planning/phases.md) | Delivery phase index |
| [`docs/planning/features.md`](docs/planning/features.md) | Feature index and capability coverage |
| [`docs/planning/backlog.md`](docs/planning/backlog.md) | Ticket lifecycle and delivery traceability |

## Compatibility

FrameStudio is the canonical product identity and command. Existing
`resolve_*` scripts, legacy imports, compatibility wrappers, cache locations,
and `.resolve.json` projects remain supported while users migrate.

The old standalone `resolve-*` and `framestudio-*` shell aliases are no longer
installed. Use `framestudio media`, `framestudio concat`, and `framestudio fps`
instead.

## Current boundaries

FrameStudio is local and offline. It does not provide cloud storage,
collaboration, accounts, telemetry, Windows/macOS support, multiple tracks,
advanced transitions, titles, captions, color grading, or full compositor
behavior. GPU and restoration performance depends on the local workstation,
media, drivers, and installed runtimes.

When a codec, timestamp, runtime, or export policy is unsupported, the
application reports the reason and preserves the source and last valid output.
