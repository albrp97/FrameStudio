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
environment already has `~/bin` on `PATH`. FFmpeg (`ffmpeg` and `ffprobe`) must
be installed.

## Checks

```sh
python3 -m py_compile resolve_media.py tests/test_classification.py
python3 -m unittest discover -s tests
./resolve_media.py --help
./resolve_media.py --dry-run --root ~/Documents/edit
resolve-concat --dry-run ~/Documents/edit/copy
```
