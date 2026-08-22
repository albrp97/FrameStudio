# Resolve Media TUI

`resolve-media` is a dependency-free Python/curses browser and preparation tool
for DaVinci Resolve on Linux Free. It starts in `~/Documents/edit`, or accepts a
different root with `--root`. The default profile is optimized for speed and
editing compatibility rather than mathematical losslessness.

## Safety and codec policy

The policy is intentionally conservative for the installed Resolve Free
(`davinci-resolve 21.0.4-1`), based on the official Resolve 20 Linux codec list:

* **Ready video:** FFV1, DNxHD/DNxHR, ProRes, Huffyuv, Ut Video, v210, v410, or
  rawvideo (intra-frame formats documented here as explicitly safe).
* **Ready audio:** PCM (`pcm_*`) or FLAC.
* H.264/H.265 are treated as Studio-only on Linux. AAC is treated as unsupported
  for Linux decode.

Anything else with a video stream, or with non-PCM/FLAC audio, is prepared.
The default `fast` profile encodes unsupported video as DNxHR SQ and audio as
PCM in MXF (`.mxf`). DNxHR SQ is an intra-frame editing intermediate and is
fast enough to run several times faster than real time on this machine. A
10-bit source automatically uses DNxHR HQX so the conversion does not
unnecessarily reduce its bit depth. Audio-only preparation uses Matroska
because MXF requires a video stream.

The fast profile is intentionally CPU-encoded: the installed FFmpeg has no
GPU DNxHR encoder, and the tested GPU ProRes path is slower. `--gpu` remains
available for the explicit `lossless` profile, which can use CUDA decoding and
Vulkan FFV1.

The choice was benchmarked on this Ryzen 5 9600X/RTX 5070 Ti system with a
10-second 1920x1080 H.264/AAC sample:

| Path | Wall time | Result |
| --- | ---: | --- |
| CPU decode + DNxHR SQ | ~1.1s | MXF, ~184 MB |
| CUDA decode + CPU DNxHR SQ | ~1.6s | MXF, ~184 MB |
| GPU ProRes LT/Standard | ~3.4s | MOV, ~135/189 MB |

`--profile lossless` remains available when mathematical losslessness is
required. It writes FFV1 video and PCM audio to Matroska (`.mkv`). The legacy
`--profile dnxhr` name is accepted as an alias for `fast`.

## Usage

```sh
resolve-media
resolve-media --root ~/Videos/to-edit
resolve-media --dry-run --root ~/Documents/edit
resolve-media --profile fast --root ~/Videos/to-edit
resolve-media --profile lossless --root ~/Videos/to-edit --gpu on
resolve-media --jobs 1                 # force sequential processing
resolve-media --performance-mode off   # leave the current system profile alone
resolve-media --keep-originals    # opt out of the default Trash move
resolve-media --gpu off            # disable NVIDIA acceleration for lossless mode
resolve-media --gpu auto           # quiet GPU detection with CPU fallback
resolve-media --version
```

To open the combined concat-and-FPS selector anywhere in a terminal:

```sh
resolve-concat
```

To open the focused one-source editor:

```sh
resolve-editor
resolve-editor --source ~/Videos/source.mp4
resolve-editor --project ~/Videos/source.resolve.json
```

The same executable also provides deterministic, machine-readable editor
operations. Successful commands emit versioned JSON on stdout; errors emit
structured JSON on stderr with a non-zero status:

```sh
resolve-editor import ~/Videos/source.mp4 --project ~/Videos/source.resolve.json
resolve-editor import ~/Videos/landscape.mp4 ~/Videos/portrait.mp4 \
  --project ~/Videos/mixed.resolve.json
resolve-editor inspect ~/Videos/source.resolve.json
resolve-editor split ~/Videos/source.resolve.json --at 12.5
resolve-editor delete ~/Videos/source.resolve.json --segment SEGMENT_ID
resolve-editor restore ~/Videos/source.resolve.json --segment SEGMENT_ID
resolve-editor move ~/Videos/source.resolve.json --segment SEGMENT_ID \
  --direction left
resolve-editor copy ~/Videos/mixed.resolve.json --segment SEGMENT_ID
resolve-editor paste ~/Videos/mixed.resolve.json --segment SEGMENT_ID --at 0
resolve-editor relink ~/Videos/mixed.resolve.json --source SOURCE_ID \
  --path ~/Videos/relocated.mp4
resolve-editor duration ~/Videos/source.resolve.json
resolve-editor export ~/Videos/source.resolve.json --output ~/Videos/edited.mp4
```

Use `--full-paths` only when automation needs local paths; output redacts them
by default. Export emits structured progress events followed by a verified
final result. The complete contract is documented in
[`docs/specs/cli-contract.md`](docs/specs/cli-contract.md). From the
repository, use `make cli ARGS="inspect /absolute/path/to/project.resolve.json"`.

The simplest workflow is to start the editor first and choose media inside the
interface:

```sh
make start
```

Use **Select video(s)** to choose one or several local video files. One-source
projects retain the original schema and editing behavior; selecting several
files creates a mixed-source project with stable source identities and a
sequential timeline.

The editor uses Python with PyGObject/GTK 4 and an FFmpeg raw-frame preview
pipe. The target workstation must provide GTK 4, PyGObject, FFmpeg, and
ffprobe. The editor supports one-source and mixed-source projects, real-time
composed preview, play/pause, seek, a visual clip timeline, non-destructive
split/delete-toggle editing, block movement and copy/paste, versioned project
save/reopen, and verified MP4 export. Preview audio is not included yet.
The implementation keeps the public `resolve_editor.model`, `export`, `app`,
`timeline`, and `cli` paths as compatibility facades over focused model,
export, playback, application, timeline, and CLI modules.
Every project uses a fixed 1920x1080 (1080p) canvas. Inputs with another
dimension or orientation are contain-scaled and letterboxed without stretching
or cropping.

The timeline shows every source block in order. Included blocks use colored
blocks; deleted blocks remain visible with a red hatched treatment. Click or
drag across the timeline to move the playhead precisely and select the block
under the pointer. Block colors belong to each block, so moving or
copying/pasting preserves its color; splitting creates fresh child colors and
restoring a deleted block reveals its original color. Use **Ctrl-click** to
add or remove blocks from the selection, **Shift-click** to select an
inclusive range, and a normal click to replace the selection. Use **Space**
for play/pause, **B** to split at the playhead, **Delete** to toggle the selected
block or blocks, **Shift+Left/Right** to move selected blocks, and
**Ctrl+C/Ctrl+V** to copy and paste them immediately after the selected
block. Click **Play** or **Pause**, or press **Space**, to toggle playback.
Bare
**Left/Right** moves one output frame at a time. Use **Ctrl+mouse wheel** to
zoom, **Ctrl+0** to fit, and **Alt/Shift+mouse wheel** or a horizontal
secondary wheel to move the zoomed timeline viewport. A normal wheel always
moves the playhead, even when zoomed. The timeline also displays the
calculated final output duration and export progress includes percentage,
frames, FPS, elapsed time, and ETA. The editor keeps this area compact; click
**Key bindings** to open the complete keyboard and timeline-control reference.

The `.mp4` file selected in the editor is source media. **Save project** writes
a `.resolve.json` editor project. **Export video** writes a separate edited
video only after FFmpeg/ffprobe verify its playability, duration, dimensions,
and audio-stream presence; the source is never overwritten.

Export uses stream copy when the source and cut boundaries are conservatively
eligible. Otherwise it reports the reason and uses an H.264/AAC MP4 fallback.
Both routes write to a temporary partial file and publish atomically only
after validation. Empty edits are rejected.

For a non-1080p input, fixed-canvas scaling requires the fallback render path.
The established render profile owns the output container, codecs, audio, and
pixel format; source codec/container differences do not change it. Current
frame-rate handling is deterministic and 60-FPS enhancement remains a later
capability.

### Makefile shortcuts

From the repository root:

```sh
make setup
make help
make start
make editor
make editor ARGS="--source /absolute/path/to/video.mp4"
make editor ARGS="--project /absolute/path/to/project.resolve.json"
make cli ARGS="inspect /absolute/path/to/project.resolve.json"
make smoke
make test
make check
make quality
```

The `media`, `concat`, and `fps` targets keep the existing workflow scripts
available, for example `make media ARGS="--dry-run --root ~/Videos"`.

### Quality setup

`make setup` creates `.venv` with the system GTK bindings visible, installs
the pinned Python quality tools from `requirements-dev.txt`, and installs the
pinned local npm tools from `package-lock.json`. Use the environment explicitly
when running checks:

```sh
make setup
make quality PYTHON=.venv/bin/python
```

The quality suite runs Ruff formatting/lint checks, source-only mypy checks,
scoped C901 complexity checks for the editor CLI/domain surfaces, jscpd,
the repository dependency-boundary check, pip-audit, Bandit, and the AIDD
churn report. Generated JSON reports are written to
`evidence/static-analysis/`; sensitive values and absolute paths must not be
added to those artifacts. jscpd currently reports approximately a 1.76%
duplication baseline against a configured 2% ceiling, so new duplication
remains visible without blocking on the existing helper/test overlap. The
GTK/rendering/export
adapters retain known complexity debt outside the current CLI/domain gate and
remain a review follow-up rather than being hidden. The same commands run in
[`.github/workflows/quality.yml`](.github/workflows/quality.yml).

On a Hyprland Wayland desktop, focus the editor window and capture configured
UI evidence with `make screenshot LABEL=before`, then repeat with
`make screenshot LABEL=after`. The target captures only the active window
using `grim` and `hyprctl`; screenshots are saved under
`evidence/screenshots/` and are not required for CLI-only changes. The
quality-tool setup evidence includes
[`quality-before.png`](evidence/screenshots/quality-before.png) and
[`quality-after.png`](evidence/screenshots/quality-after.png).

### Manual editor test

Use a short disposable MP4 or a copy of a local source:

1. Launch with `make start`.
2. Click **Select video(s)** and choose one local video, or choose two
   disposable videos with different dimensions or frame rates for the
   mixed-source flow.
3. Confirm the preview loads, the duration is shown, and the timeline is
   enabled.
4. Press **Space** and confirm the preview starts, the position label/playhead
   advance together, and pressing **Space** again pauses it.
5. Click inside different colored timeline blocks and confirm the selected
   block is outlined, the source details update, and the playhead seeks there.
6. Drag across the timeline and confirm the playhead and preview image update
   while the pointer moves, stale intermediate renders do not hold up the
   latest position, and the final frame matches the exact released position.
7. Press **Left** and **Right** repeatedly while paused. Confirm each press
   moves the playhead by exactly one source frame.
8. Press **B** at an interior playhead position. Confirm a new clip block
   appears at the split and both clips remain included.
9. Select a clip in the timeline and press **Delete**. Confirm it remains
   visible with the deleted styling, the **Final output** duration decreases,
   and the selected clip status changes to **Deleted**.
10. Press **Delete** again and confirm the clip returns to included styling and
    the final output duration returns.
11. Split the source into three clips, select the middle clip, and press
    **Shift+Left** or **Shift+Right**. Confirm the whole block changes
    timeline position while its source range, color, and duration remain
    attached to it.
12. Seek across the moved blocks and confirm the preview follows timeline
    order; split the selected moved block and confirm both children stay in
    that position.
13. Hold **Ctrl** and click another block. Confirm both blocks have orange
    selected outlines; click it again with **Ctrl** to remove it from the
    selection. Click a different block normally and confirm the previous
    selection clears.
14. Select a block, hold **Shift**, and click another block. Confirm every
    block between the two endpoints is selected inclusively.
15. Select a block, press **Ctrl+C**, then **Ctrl+V**. Confirm a fresh copy is
    inserted immediately after the selected block, later blocks move forward,
    the copied color/state remain attached, and the final timeline duration
    increases by the copied block duration.
16. Hold **Ctrl** and scroll up/down. Confirm the zoom percentage changes.
17. Press **Ctrl+0** and confirm the complete source returns to view.
18. At any zoom level, scroll normally and confirm the playhead moves by about
    one second instead of moving the horizontal scrollbar.
19. Hold **Alt** or **Shift** while scrolling, or use a horizontal secondary
    wheel, and confirm the zoomed timeline viewport moves left/right.
20. Click **Save project**, choose a path ending in `.resolve.json`, and
   confirm the status reports a saved project. Verify the source file's size
   and modification time are unchanged.
21. Click **Reopen project**, or close the app and run
   `make editor ARGS="--project /absolute/path/to/project.resolve.json"`.
   Confirm the same source, duration, and saved playhead reopen.
22. Save the project, close/reopen it, and confirm the clip deleted/included
    state is preserved.
23. Click **Export video**, choose a new `.mp4` path, and watch the export
    panel. Confirm it shows percentage, current frame/total frames, FPS,
    elapsed time, and ETA while the export runs. Confirm the output plays and
    inspect it with:

    ```sh
    ffprobe -v error -show_entries format=duration:stream=codec_type,width,height,codec_name \
      -of compact /absolute/path/to/exported-edited.mp4
    ```

    Confirm the duration matches the edited duration, required audio remains
    present, the source file is unchanged, and the output dimensions are
    exactly 1920x1080.
24. For the mixed-source flow, seek across the source boundary, use
    **Ctrl-click** to select blocks from both sources and **Shift-click** to
    select an inclusive range, move them with **Shift+Left/Right**, and use
    **Ctrl+C/Ctrl+V** to insert copies after the selected block. Confirm
    order, source coverage, fresh pasted identities, final duration, and the
    fixed 1920x1080 preview/output canvas.
25. Reopen the mixed project and confirm source order, block order, deletion
    state, and the selected output duration are preserved.
26. Check an error path safely with an invalid disposable project:
   `printf '{' > /tmp/invalid.resolve.json`, then run
   `make editor ARGS="--project /tmp/invalid.resolve.json"`. Confirm the
   status shows an actionable error and does not replace valid state.

The mixed-source editor intentionally does not yet provide triplicate layouts,
automatic per-input audio normalization, or 60-FPS enhancement. Those remain
planned future capabilities.

The TUI starts in `~/Documents/edit`. Navigate with the arrow keys or `j/k`,
use `Right/l` to enter a folder, press `Space` on each video to select it, and
press `Enter` to run the complete workflow. One selected video goes directly
to FPS enhancement with audio stream-copy; multiple selected videos are
concatenated once and then enhanced globally. `a` selects every video in the
current folder, `n` clears the selection, and `Left/h/Backspace` goes up. Use
`resolve-concat --root ~/Videos` to start in a different folder.

For a non-interactive run, pass the folder directly:

```sh
resolve-concat ~/Documents/edit/copy
```

For a multiple-video run it chooses the most common resolution and the lowest
nominal frame rate, normalizes each file independently with bounded GPU
workers when needed, joins the temporary parts, and then performs one RIFE
pass. `--concat-only` preserves the older concat-without-FPS behavior. The
single-process filter graph remains available with `--strategy single`. The
delivery output is MP4 with H.264, 8-bit `yuv420p`, BT.709 tags, `faststart`,
and the original audio stream copied at the final remux. The default NVENC
delivery profile is preset `p1` with constant QP 18, the fastest tested
quality/storage balance for the current RTX 5070 Ti pipeline. LosslessCut uses
the same FFmpeg engine, but its stream-copy merge cannot normalize a mixed
30/29.97 fps folder. The benchmark and redesign results are recorded in
[`FAST-CONCAT-RESEARCH.md`](FAST-CONCAT-RESEARCH.md).

Frame-rate enhancement research is recorded in
[`FPS-ENHANCEMENT-RESEARCH.md`](FPS-ENHANCEMENT-RESEARCH.md). It compares
current RIFE, TensorRT/TensorRT-RTX, NCNN/Vulkan, anime-focused GMFSS, newer
diffusion methods, and a reproducible RTX 5070 Ti benchmark plan. The
Flowframes-specific investigation is in
[`FLOWFRAMES-RESEARCH.md`](FLOWFRAMES-RESEARCH.md).

The local RIFE test found that pure TensorRT FP16 produced a regular grid
artifact on this RTX 5070 Ti. Executing only RIFE's
`aten.pixel_shuffle` operation in PyTorch fixes it while retaining the rest of
the TensorRT FP16 path; TensorRT FP32 remains the fallback. The validated
experimental reference uses explicit scene-cut protection and an exact
output-frame trim, with reproduction details recorded in the two research
documents above.

REAL-Video-Enhancer is now the default FPS backend for the unified workflow.
Its RIFE 4.26 weights are the same as the validated local weights, and its
unmodified TensorRT FP16 path reproduces the same grid artifact. The installed
RVE checkout includes the PixelShuffle fallback, RGB/frame-pacing corrections,
and exact output-FPS support validated on this RTX 5070 Ti. The older
VapourSynth implementation remains available with `--engine vs-rife`.

Audio is analyzed per source before encoding. The default gain is chosen to
balance mean RMS `-35 dBFS` and median absolute sample level `-50 dBFS`, with a
`-1 dBFS` peak cap. A single gain cannot make both statistics exact for every
recording, so the result is an intentionally conservative compromise that
preserves each source's dynamics. Use `--audio-normalization off` to retain
source gain; this is also required for an eligible stream-copy run.

Keys: arrows or `j/k` move, `Right/l` enters a folder, `Left/h/Backspace` goes
up, `Enter` converts, `Space` toggles selection, `a` selects all current
contents, `n` clears selection, `g` cycles GPU mode, `D` toggles deletion,
`p` cycles performance mode, `r` rescans, `?` opens help, and `q` quits.
Folders process recursively. If nothing is selected, `Enter` processes the
current folder recursively.

Only files needing preparation are converted. Output is deterministic:
`<stem>.resolve-ready.mxf` for video conversion, or
`<stem>.resolve-ready.mkv` for audio-only preparation. The explicit lossless
profile writes `<stem>.resolve-lossless.mkv`. Existing generated outputs,
including outputs from the older lossless default, are recognized and skipped;
when deletion is enabled, their source can be removed after verification.
Conversion writes a unique `.partial-*` file, uses FFmpeg progress output,
verifies duration and stream presence with ffprobe, then atomically renames it.
Failures leave the source untouched.

Deletion is ON by default. The TUI always requires an explicit confirmation
before processing when deletion is enabled. After successful verification it
uses `gio trash`, never an irreversible unlink. Each source is moved only
after its own output is verified, before the next source starts. If `gio` is
unavailable or fails, the original is retained and a warning is shown. Use
`--keep-originals` or press `D` to disable it.

Performance mode is AUTO by default. When a batch starts, the TUI temporarily
selects the system `performance` profile through `powerprofilesctl`, then
restores the profile that was active before the batch. Use
`--performance-mode off` or press `p` to cycle to OFF. Fast mode also uses
bounded parallel conversion automatically; use `--jobs 1` for sequential
processing or `--jobs N` to choose a specific worker count. On the benchmark
sample, `performance` reduced one conversion from about 1.08s to 0.89s.

The integrated workflow cleans normalized parts after the final join, preserves
source files, and retries with CPU H.264 if automatic GPU encoding fails.
Use `--concat-only` to reproduce the older one-process concat behavior.

### FPS enhancement: concatenate first, then interpolate once

The single-tool production workflow is `resolve-concat`; the installed
`resolve-fps` command remains available for direct FPS-only use:

```sh
resolve-concat
```

Select one video and it goes directly to RIFE: no concatenation and no audio
transformation are performed; the original audio stream is copied into the
final MP4. When multiple videos are selected, they are concatenated once with
audio normalization disabled, then one global RIFE pass runs over the
temporary master. Use `resolve-fps /path/to/video.mp4 --force` only when a
separate FPS-only command is desired. Run `./install.sh` once to install both
commands into `~/bin`.

During interpolation the console shows a live Pacman-style bar with percent,
frame count, end-to-end pipeline FPS, elapsed time, and ETA. The displayed
pipeline FPS includes decoding, RIFE, and delivery encoding; it is not the
model-only inference FPS from the benchmark. The default backend is corrected
REAL-Video-Enhancer RIFE 4.26; use `--engine vs-rife` for the VapourSynth
fallback.

The RVE backend expects the validated local setup at these paths:

```text
/tmp/REAL-Video-Enhancer
/tmp/rve-models-pixel-fallback/rife4.26.pkl
/tmp/rve-shims
```

Override them with `--rve-root`, `--rve-model`, and `--rve-shims`, or set
`RESOLVE_RVE_ROOT`, `RESOLVE_RVE_MODEL`, and `RESOLVE_RVE_SHIMS`. RVE's factor
two output is padded or trimmed to the existing rational target-frame policy,
so a 29.97-to-60 conversion preserves the timeline (for example, 900 input
frames become 1,802 output frames). The adapter rejects unsupported
non-near-integer factors instead of silently changing cadence.

Press `Ctrl+C` to cancel safely. The active FFmpeg/RIFE processes are stopped,
the hidden `.partial` output is deleted, and any temporary multi-input master
and normalized parts are removed. The source files and any previously completed
output remain unchanged. Frames are streamed through a pipe rather than stored
as an intermediate image sequence. The RVE backend uses a temporary encoded
video inside its private temporary directory so it can remux the original
audio exactly; that file is removed after success or cancellation. The
TensorRT engine cache is intentionally kept for faster future runs. A forced
`SIGKILL` or power loss can prevent cleanup, so inspect `/tmp/resolve-fps-*`,
the RVE temporary directories, and hidden `.partial` files if the machine is
forcibly stopped.

The validated strategy is a two-stage run. First create one compatible
stream-copy master; then run one global RIFE 4.26 pass over that master. Do
not run RIFE separately on each input clip, because resetting the 29.97-to-60
cadence at every clip boundary is slower and can introduce timing drift.
The integrated RVE path was 2.3x to 2.5x faster than the fallback on the
one-clip/three-clip benchmark; exact measurements and caveats are recorded in
[`FPS-ENHANCEMENT-RESEARCH.md`](FPS-ENHANCEMENT-RESEARCH.md).

From the project directory:

```sh
INPUT_DIR="$HOME/Documents/edit/copy"
MASTER="$HOME/Documents/edit/copy-concatenated-29.97fps.mp4"
OUTPUT="$HOME/Documents/edit/copy-concatenated-rife4.26-60fps.mp4"

resolve-concat "$INPUT_DIR" --concat-only --output "$MASTER" --mode auto \
  --audio-normalization off --performance-mode off --force

# This is the normal integrated command; it concatenates once and uses RVE.
resolve-concat "$INPUT_DIR" --engine rve --output "$OUTPUT" \
  --performance-mode auto --force
```

For a manual reproduction of the older VapourSynth fallback, first create the
master with `--concat-only`, then run:

```sh
INPUT_FRAMES=$(ffprobe -v error -select_streams v:0 \
  -show_entries stream=nb_frames -of csv=p=0 "$MASTER")
TARGET_FRAMES=$((INPUT_FRAMES * 2))
FPS_PYTHON="$HOME/.cache/resolve-fps/trt/bin/python"
FPS_SITE="$HOME/.cache/resolve-fps/trt/lib/python3.13/site-packages"
FPS_SCRIPT="$HOME/.cache/resolve-fps/benchmark.vpy"
TRT_CACHE="$HOME/.cache/resolve-fps/engines-pixel-fallback"
BESTSOURCE="$HOME/.cache/resolve-fps/plugins/usr/lib/python3.14/site-packages/vapoursynth/plugins/libbestsource.so"
PARTIAL="$OUTPUT.partial.mp4"

SOURCE="$MASTER" MODEL=4.26 TRT_CACHE="$TRT_CACHE" INPUT_FORMAT=RGBH \
TRT_TORCH_PIXEL=1 BESTSOURCE_PLUGIN="$BESTSOURCE" LIMIT_SECONDS=999999 \
TARGET_FRAMES="$TARGET_FRAMES" PYTHONPATH="$FPS_SITE" \
"$FPS_PYTHON" benchmarks/vsrawpipe.py "$FPS_SCRIPT" | \
ffmpeg -hide_banner -y -f yuv4mpegpipe -i - -i "$MASTER" \
  -map 0:v:0 -map 1:a:0? -c:v h264_nvenc -preset p1 -rc constqp -qp 18 \
  -profile:v high -pix_fmt yuv420p -color_range tv -colorspace bt709 \
  -color_primaries bt709 -color_trc bt709 -c:a copy \
  -movflags +faststart "$PARTIAL" && mv "$PARTIAL" "$OUTPUT"
```

`TARGET_FRAMES=$((INPUT_FRAMES * 2))` matches the validated 29.97-to-60
legacy benchmark policy. The integrated adapter uses rational frame-count
math and may pad the factor-two RVE output (900 input frames become 1,802
frames). Keep `TRT_TORCH_PIXEL=1` and the separate
`engines-pixel-fallback` cache; pure TensorRT FP16 is known to produce grid
artifacts on this RTX 5070 Ti. The specialized Python 3.13 environment is
required because the system VSPipe/Python 3.14 installation has an incompatible
NumPy/VapourSynth ABI. The runner writes progress to stderr and leaves the
source and concatenated master untouched.

## GPU behavior

`--gpu on` is the default setting, but it affects only the explicit `lossless`
profile. The fast profile deliberately uses the CPU DNxHR encoder because that
is the fastest Resolve-compatible path on this system.

For `--profile lossless`, GPU mode attempts CUDA decoding plus the experimental
Vulkan FFV1 encoder for every supported video codec. The conversion preserves
decoded pixels exactly; GPU mode changes the processing path, not the lossless
policy. Audio remains PCM/stream-copy as appropriate.

GPU FFV1 is experimental in FFmpeg. Every GPU conversion is verified, and any
GPU command failure, missing GPU, or unsupported GPU decoder automatically
falls back to the CPU FFV1 encoder. Use `--gpu auto` for quiet detection or
`--gpu off` if a particular source needs the CPU path.

## Replicating or repairing the setup

From the project directory, reinstall the global command with:

```sh
./install.sh
```

Check the installed capabilities with:

```sh
nvidia-smi
ffmpeg -hide_banner -decoders | grep cuvid
ffmpeg -hide_banner -encoders | grep -E 'dnxhd|ffv1_vulkan'
powerprofilesctl get
resolve-media --dry-run --root ~/Documents/edit
```

The implementation keeps the source safe by using atomic partial outputs,
ffprobe verification, automatic GPU-to-CPU fallback for lossless mode, and
`gio trash` only after successful verification. Performance mode restoration is
also guarded so a profile changed externally is not overwritten. If the TUI or
conversion path misbehaves, rerun with
`resolve-media --profile fast --gpu off --keep-originals`; this gives a
non-destructive recovery path. Use `--profile lossless --gpu off` to force the
CPU lossless encoder.

## Install

From this directory:

```sh
./install.sh
```

This creates `~/bin/resolve-media` and `~/bin/resolve-concat`; the requested
environment already has `~/bin` on `PATH`. It also installs
`~/bin/resolve-editor`. FFmpeg (`ffmpeg` and `ffprobe`) and the GTK 4/PyGObject
runtime must be installed for the editor.

## Checks

```sh
python3 -m py_compile resolve_media.py tests/test_classification.py
python3 -m unittest discover -s tests
./resolve_media.py --help
./resolve_media.py --dry-run --root ~/Documents/edit
resolve-concat --dry-run ~/Documents/edit/copy
```
