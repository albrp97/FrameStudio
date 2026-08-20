# Flowframes research

Research snapshot: 2026-08-19

## Scope

This document covers the Flowframes application at:

- https://flowframes.app/
- https://nmkd.itch.io/flowframes
- https://github.com/n00mkrad/flowframes

The goal is to identify which implementation and settings are best for an
NVIDIA RTX 5070 Ti, while preserving useful audio and video output for
DaVinci Resolve and general playback.

## Confirmed local artifact diagnosis

A controlled 1920x1080 test on the RTX 5070 Ti reproduced the artifacts seen in
the first RIFE 4.26 output. The corruption is a regular grid of bright and
dark blocks, and it is already present in the raw VapourSynth frames before
FFmpeg or NVENC encoding:

| RIFE 4.26 path | Input format/runtime | Result |
| --- | --- | --- |
| TensorRT | `RGBH` (FP16) | **Corrupted** grid pattern |
| TensorRT with selective fallback | `RGBH` (FP16), PyTorch `aten.pixel_shuffle` | Clean |
| TensorRT | `RGBS` (FP32) | Clean |
| PyTorch eager | FP16 model | Clean |
| TensorRT FP16 with `trt_max_aux_streams=0` | `RGBH` | **Still corrupted** |

This isolates the failure to the TensorRT FP16 implementation of
`aten.pixel_shuffle` in the current engine/runtime combination, not to the
RIFE 4.26 weights, source decoding, RGB conversion, scene handling, or final
H.264 encoding. The best validated local path is selective FP16: keep the
model in TensorRT FP16 but execute `aten.pixel_shuffle` in PyTorch. TensorRT
FP32 (`RGBS`) remains the simple fallback, and the unmodified pure TensorRT
FP16 engine must not be accepted merely because its benchmark FPS is higher.

The artifact-free FP32 baseline reference used:

- RIFE 4.26, TensorRT, static 1920x1088 engine, FP32.
- BestSource input with explicit BT.709 limited-range to `RGBS` conversion.
- Scene-change protection enabled at the `vs-rife` threshold of `0.15`.
- De-duplication off, matching Flowframes' normal-video behavior.
- Direct target `60/1` FPS, trimmed explicitly to 3,600 frames.
- YUV420P10 intermediate, then NVENC H.264 High, BT.709, `yuv420p`, CQ/QP 1.
- Original AAC audio copied into the output.

The corrected full-minute output and telemetry are outside this repository:

```text
/home/ghiki/Documents/edit/copy-concatenated-29.97fps-parallel-rife-4.26-tensorrt-fp32-corrected-60fps.mp4
/home/ghiki/.cache/resolve-fps/results/60s-4.26-fp32-corrected-gpu.csv
```

Its interpolation stage produced 3,600 frames in 41.61 seconds (86.52
frames/s); end-to-end wall time was about 45 seconds. Sampled peak VRAM was
3,666 MiB and peak board power was 278 W. The previous FP16 render was faster,
but its output is not a valid quality reference because of the grid failure.

The preferred selective-FP16 outputs are:

```text
/home/ghiki/Documents/edit/copy-concatenated-29.97fps-parallel-rife-4.26-tensorrt-fp16-pixel-fallback-corrected-60fps.mp4
/home/ghiki/Documents/edit/copy-concatenated-29.97fps-parallel-rife-4.26-heavy-tensorrt-fp16-pixel-fallback-corrected-60fps.mp4
/home/ghiki/Documents/edit/copy-concatenated-29.97fps-parallel-rife-4.26-comparison-3way-fp16-pixel-fallback-corrected-60fps.mp4
```

The standard model produced 3,600 frames in 35.44 seconds (101.57
frames/s), with about 39 seconds end to end, 3,909 MiB peak VRAM, and 261 W
peak power. The heavy model produced 3,600 frames in 53.73 seconds (67.01
frames/s), with about 57 seconds end to end, 6,122 MiB peak VRAM, and 278 W
peak power. The comparison is a true horizontal three-way layout: each
640x360 panel is original, standard, or heavy, producing a 1920x360 video.

## REAL-Video-Enhancer alternative test

REAL-Video-Enhancer 2.4.1 was tested as a Linux alternative to the
Flowframes-style pipeline. Its RIFE 4.26 weights are byte-identical to the
weights used by the clean local `vs-rife` renders, so RVE is a frontend and
pipeline alternative rather than a newer model.

The unmodified RVE TensorRT FP16 run reproduced the same bright/dark grid
artifact. It also decoded three duplicate source frames because its FFmpeg
reader did not request timestamp passthrough, and its default loop emitted
3,605 frames instead of the required 3,600. A temporary diagnostic patch that
kept `aten.pixel_shuffle` in PyTorch, requested RGB24 directly from FFmpeg,
duplicated the final frame, and forced 60 FPS produced a clean 3,600-frame
output. The final reference was stream-copy remuxed with limited-range BT.709
metadata:

```text
/home/ghiki/Documents/edit/copy-concatenated-29.97fps-parallel-rve-rife4.26-pixel-fallback-corrected-60fps.mp4
/home/ghiki/Documents/edit/copy-concatenated-29.97fps-parallel-rve-comparison-4way-original-rve-standard-heavy-60fps.mp4
```

The corrected RVE render took 66.9 seconds in RVE's render loop, versus 35.44
seconds for the comparable selective-FP16 `vs-rife` interpolation stage. RVE
therefore confirms the pipeline fixes needed to avoid artifacts, but it does
not currently beat the validated local backend in model quality, timing, or
feature completeness. The full investigation and exact failure analysis are
recorded in [`FPS-ENHANCEMENT-RESEARCH.md`](FPS-ENHANCEMENT-RESEARCH.md).

## What was recreated from Flowframes

The public Flowframes source was inspected rather than copied. The relevant
implementation details are:

- `Pkgs/rife-cuda/rife.py` extracts RGB frames, pads the input to a model-safe
  multiple, uses queued reader/writer workers, and makes FP16 an explicit
  optional flag.
- `Flowframes/Os/VapourSynthUtils.cs` uses VapourSynth's RIFE-NCNN path with
  RGBS/FP32 input, scene detection, UHD scaling policy, TTA disabled by
  default, and YUV444P16 output before FFmpeg.
- `Flowframes/Media/FfmpegExtract.cs` normally extracts RGB24 PNG or
  high-quality JPEG frames for the CUDA path.
- `Flowframes/Main/FrameOrder.cs` protects scene cuts and controls whether the
  cut is duplicated or blended; normal camera footage does not use
  de-duplication.
- `Flowframes/Media/FfmpegAudioAndMetadata.cs` remuxes compatible audio,
  subtitles, and metadata from the source after video encoding.

Flowframes' README explicitly warns that CUDA FP16 can be unstable, and the
public configuration leaves CUDA FP16 disabled by default. The local artifact
therefore came from assuming that a TensorRT FP16 path was equivalent to
Flowframes' default CUDA/NCNN behavior. It was not. The independent
reimplementation keeps the useful behavior—explicit color conversion,
scene-cut protection, no normal-video de-duplication, exact frame count, and
audio remuxing—without copying GPL-3.0 source code.

The selective workaround is independent of Flowframes and is specific to the
current `vs-rife`/Torch-TensorRT stack. In the `torch_tensorrt.dynamo.compile`
call for the RIFE flow network, pass this fallback when building a new engine:

```python
torch_executed_ops=(
    {torch.ops.aten.pixel_shuffle.default}
    if os.environ.get("TRT_TORCH_PIXEL") == "1"
    else None
),
```

Use a separate TensorRT cache directory because the normal engine filename
does not encode the PyTorch fallback set. Run the corrected harness with
`INPUT_FORMAT=RGBH`, `TRT_TORCH_PIXEL=1`, and a new cache such as
`/home/ghiki/.cache/resolve-fps/engines-pixel-fallback`. If this patch stops
working after a TensorRT or Torch-TensorRT upgrade, rebuild the engine and
repeat the raw-frame smoke test before using it for a long render. If it
fails, use the documented FP32/RGBS path.

## What Flowframes is

Flowframes is a Windows GUI for AI video frame interpolation. It estimates
motion between existing frames and creates intermediate frames. It changes
temporal resolution, not spatial resolution: a 1920x1080 source remains
1920x1080 unless it is separately scaled.

Typical uses are:

- 24/30 FPS to 48/60 FPS conversion.
- Slow motion.
- Smoother gameplay or camera footage.
- 2D animation and anime interpolation.
- Interpolation of image sequences and some AI-generated video.

It is not a video upscaler and it cannot reliably invent motion across every
scene cut, occlusion, flash, or heavily corrupted frame.

## Important build/version distinction

The official public itch page currently identifies its free web installer as
Flowframes 1.36.0 and says that newer builds are temporarily released through
Patreon. The public source repository and changelog describe newer development
code up to 1.42.0.

This matters because the model list and features are not identical between
1.36 and 1.42:

- 1.36 added RIFE 4.0.
- 1.37 added RIFE 4.1 and newer NCNN behavior.
- 1.38 added VapourSynth-RIFE-NCNN-Vulkan.
- 1.40 added RIFE 4.6 and NVENC AV1 support.
- 1.41 added RIFE models up to 4.26, VFR preservation, AMD/Intel hardware
  encoding, and CLI improvements.
- 1.42 added HDR interpolation, alpha support in the NCNN-VapourSynth path,
  experimental sub-2x interpolation, and more CLI improvements.

Therefore, do not assume that the public 1.36 installer exposes RIFE 4.26 or
the current VapourSynth path. Check the exact installed version before
following a model-specific recommendation.

## Processing implementations

| Flowframes implementation | Runtime | Current model list | Main behavior | Recommendation |
| --- | --- | --- | --- | --- |
| RIFE CUDA | PyTorch/CUDA, NVIDIA only | RIFE 1.8 through 4.13.2; 4.13.2 is marked default | Extracts frames, runs the Python RIFE implementation, then encodes | Fastest starting point on a working NVIDIA installation |
| RIFE NCNN | NCNN/Vulkan | RIFE 2.3, 4.9, 4.13, 4.18, 4.22, 4.24, 4.25, 4.26; 4.26 is marked default | Extracts frames and uses a portable Vulkan executable | Compatibility fallback or fractional-factor path |
| RIFE NCNN VS | NCNN/Vulkan through VapourSynth | Same current RIFE 4.26-oriented list | Piped processing for video; avoids the normal extracted-frame workflow and preserves VFR timing in current releases | Best Flowframes quality/feature starting point when using a current build |
| DAIN NCNN | NCNN/Vulkan | One official `best` model | Depth-aware older alternative | Use only when RIFE produces a bad result on a specific clip |
| FLAVR CUDA | PyTorch/CUDA | Official 2x, 4x, and 8x models | Fixed interpolation factors | Experimental comparison only |
| XVFI CUDA | PyTorch/CUDA | Legacy/experimental implementation | Integer factors | Not the default choice |
| IFRNet NCNN | NCNN/Vulkan | Present in source but not in the current default network list | Fixed 2x factor | Not a normal current UI choice |

Flowframes' own documentation says RIFE CUDA is generally faster on NVIDIA
hardware. Its published historical benchmark supports that direction: at
1080p/2x, an RTX 3070 was listed at 19.5 output FPS with RIFE CUDA versus
6.4 output FPS with RIFE NCNN. These numbers are old and are not a benchmark
for the RTX 5070 Ti, but they are useful evidence that CUDA should be tested
first for speed.

The NCNN-VapourSynth path can still win in total wall-clock time for some
inputs because it avoids writing and rereading a complete extracted frame
sequence. That is an implementation tradeoff, not a guaranteed speed result.

## Models

### Current RIFE CUDA models

The current source lists:

- 1.8: old 2D animation model.
- 2.3 and 2.4: older general models.
- 3.0 through 3.9: older general models.
- 4.0 through 4.12.2: general models.
- 4.13.2: current CUDA default.

### Current RIFE NCNN and NCNN-VS models

The current source lists:

- 2.3: old model, fixed 2x.
- 4.9, 4.13, 4.18, 4.22, 4.24, 4.25, and 4.26.
- 4.26 is marked as the Flowframes default for these implementations.

The upstream Practical-RIFE project says 4.25 is a good default for most
scenes and says 4.24 and newer can be useful for some diffusion-generated
videos. It also reports that the 4.7-4.10 family was optimized toward anime
content. Those statements are upstream guidance, not a guarantee for every
clip, and the exact anime-specific models are not all exposed by the current
Flowframes NCNN model list.

Recommended model order:

1. General camera, gameplay, or CGI: RIFE 4.26 in NCNN-VS, then compare 4.25
   if artifacts appear.
2. AI-generated or diffusion-style video: compare RIFE 4.25 and 4.26.
3. Anime or 2D animation: compare the best exposed current model against an
   anime-oriented 4.7-4.10 model in a current native RIFE tool if Flowframes
   does not expose the desired model.
4. CUDA speed profile: RIFE CUDA 4.13.2.

Use a short representative clip to choose between adjacent models. Newer
model numbers are not a universal guarantee of fewer artifacts.

## Recommended settings

### General settings

| Setting | Recommendation | Reason |
| --- | --- | --- |
| Processing implementation | RIFE CUDA for speed; RIFE NCNN-VS for the current model/VFR path | CUDA is NVIDIA-specific and generally faster; NCNN-VS has the newer exposed models and avoids normal frame extraction |
| Interpolation factor | 2x for normal 24/30 FPS to 48/60 FPS work | Larger factors increase compute and artifact risk |
| Exact 24 to 60 FPS | Use RIFE NCNN or NCNN-VS with a 2.5x factor/target if the installed build exposes it | CUDA's current implementation advertises integer factors, while NCNN supports arbitrary float factors |
| Scene detection | On | Prevents the model from morphing across hard cuts |
| Frame de-duplication | Off for camera footage, gameplay, CGI, and normal video | It can delete real low-motion frames and create choppy output |
| Frame de-duplication for 2D animation | Use accurate after-extraction mode first; use extraction-time `mpdecimate` only for speed | Animation often contains intentional held frames, but the faster detector is less flexible |
| Maximum video size | Keep the source size unless processing is too slow or VRAM is insufficient | Downscaling changes detail; Flowframes defaults to a 2160-pixel maximum height |
| UHD mode | Auto/default for 4K; normally off for 1080p | The source uses a 1600-pixel height threshold by default |
| Temporary directory | Local NVMe/SSD | Extracted-frame implementations are strongly affected by storage I/O |
| Auto-encode | On for long jobs | It reduces temporary disk usage by encoding while interpolation proceeds |
| Audio/subtitles/metadata | Preserve unless a deliberate clean export is wanted | Flowframes copies compatible tracks and re-encodes incompatible tracks when needed |

### NVIDIA CUDA settings

- Use the best discrete GPU ID, normally GPU `0` on a single-GPU system.
- Enable CUDA Fast Mode/FP16 only after a short visual and stability test. It
  reduces VRAM use and can improve speed, but the project warns that it may be
  unstable on some systems. This warning is material: the separate local
  pure TensorRT FP16 path fails the visual test. The corrected local fast path
  selectively executes `aten.pixel_shuffle` in PyTorch; TensorRT FP32 remains
  the unmodified fallback.
- RIFE CUDA's current source passes a worker count based on the interpolation
  factor. Do not launch multiple independent full-resolution jobs on the same
  GPU unless a benchmark proves that it helps.

### NCNN/Vulkan settings

- Start with GPU ID `0`.
- Start with 2-4 NCNN processing threads. The current Flowframes default is
  4, and the code clamps the value to the Vulkan device's available compute
  queues.
- Increase threads only while GPU utilization is low and VRAM remains
  comfortable. Larger values can increase memory use and may reduce
  performance.
- Keep TTA disabled for normal speed/quality work. Enable spatial TTA only for
  a quality-first test because it costs additional processing time.
- Use NCNN-VS rather than the older extracted-frame NCNN path when the current
  build handles the input correctly, especially for VFR footage.

## Output recommendations

### General playback and Resolve import

Use:

- MP4 container.
- H.264 High profile.
- 8-bit `yuv420p`.
- BT.709 color metadata for SDR material.
- AAC-LC audio, usually 48 kHz stereo.
- NVENC H.264 on the RTX 5070 Ti if the installed Flowframes build detects it.

Flowframes' current NVENC implementation uses `h264_nvenc`, preset `p7`, and
constant-quality mode. Its quality mapping is approximately:

- Very High: CQ 18.
- High: CQ 22.
- Medium: CQ 29.

Use Very High/CQ 18 for a quality-first delivery file and High/CQ 22 for a
smaller file. H.264 is the safest choice across Windows, Linux, VLC, Android,
Google TV, and Meta Quest. H.265 or AV1 can reduce size but have less universal
playback and Resolve compatibility.

### Resolve editing master

Do not use a low-quality delivery encode as an editing master if another
generation will be added in Resolve. Prefer:

- ProRes 422 HQ in MOV for a practical editing master.
- FFV1 or an image sequence only when very large lossless intermediates are
  acceptable.

Flowframes does not expose DNxHR as one of its main output encoder choices.

## Three practical profiles

### Fastest sensible NVIDIA profile

- RIFE CUDA.
- RIFE CUDA 4.13.2.
- 2x interpolation.
- FP16/Fast Mode on only if Flowframes' own CUDA path passes a short visual
  test; do not transfer that setting to the failing TensorRT FP16 path.
- Scene detection on.
- De-duplication off.
- Auto-encode on.
- NVENC H.264, High quality.
- Temp folder on NVMe.

This is the profile to try first when throughput matters most.

### Best current Flowframes quality/feature balance

- A current Flowframes build with RIFE NCNN-VS.
- RIFE 4.26, with a comparison run using 4.25.
- 2x or an exact fractional factor when needed.
- Scene detection on.
- De-duplication off unless the source is 2D animation.
- NCNN threads starting at 4.
- TTA off initially; enable it only for a final quality comparison.
- Export to ProRes 422 HQ for Resolve or NVENC H.264 Very High for delivery.

This profile favors the newest model path and VFR handling over the shortest
possible inference time.

### Quality-first animation profile

- RIFE NCNN-VS or NCNN.
- De-duplication enabled only after inspecting the source.
- Accurate after-extraction de-duplication.
- Scene detection on.
- Compare RIFE 4.25/4.26 and an exposed anime-oriented model if available.
- TTA enabled only if the extra runtime is acceptable.
- Preserve an intermediate before making a delivery encode.

Held-frame animation needs different treatment from camera footage. Enabling
de-duplication on ordinary live-action material is a common cause of choppy
results.

## Platform status for this workstation

The workstation has an RTX 5070 Ti with 16 GB VRAM and a working NVIDIA
driver/NVENC stack, so the hardware is suitable for Flowframes' CUDA or
Vulkan backends. However:

- Flowframes is a Windows application.
- Its GUI and normal process control are Windows-specific.
- The official public download is a Windows installer.
- Wine is not installed on this Linux system.
- No Flowframes installation or full-video test has been performed locally.

Installing Flowframes through Wine should not be treated as equivalent to an
official Windows run without a controlled test. The safer native Linux
alternatives are:

- `rife-ncnn-vulkan` for a portable Vulkan implementation.
- VapourSynth-RIFE with CUDA/TensorRT through `vs-rife`.
- VapourSynth plus `vs-mlrt` when a runtime-specific TensorRT or NCNN setup is
  desired.

These alternatives use related RIFE models but are not the Flowframes GUI and
do not guarantee byte-identical output.

## Empirical limits of this report

The published Flowframes benchmark table is based on older versions and GPUs,
including RTX 3070/3080 hardware. It is not a valid performance claim for an
RTX 5070 Ti. The correct local comparison would be a short, representative
clip tested with:

1. RIFE CUDA 4.13.2.
2. RIFE NCNN-VS 4.26.
3. RIFE NCNN-VS 4.25.
4. The same factor, resolution, output encoder, and storage location.

Compare output FPS, total wall time, VRAM use, and visible artifacts. Do not
compare only AI inference FPS because frame extraction, VapourSynth piping,
encoding, and disk I/O can dominate total runtime.

## Sources

- Flowframes application page: https://flowframes.app/
- Official download page: https://nmkd.itch.io/flowframes
- Official source repository: https://github.com/n00mkrad/flowframes
- Official changelog:
  https://raw.githubusercontent.com/n00mkrad/flowframes/main/changelog.txt
- Official benchmark table:
  https://raw.githubusercontent.com/n00mkrad/flowframes/main/Benchmarks.md
- Current Flowframes model lists:
  https://raw.githubusercontent.com/n00mkrad/flowframes/main/Pkgs/rife-cuda/models.json
  https://raw.githubusercontent.com/n00mkrad/flowframes/main/Pkgs/rife-ncnn-vs/models.json
- Practical-RIFE model guidance:
  https://github.com/hzwer/Practical-RIFE
- RIFE NCNN-Vulkan:
  https://github.com/nihui/rife-ncnn-vulkan
- VapourSynth-RIFE:
  https://github.com/HolyWu/vs-rife
- VapourSynth-RIFE-NCNN-Vulkan:
  https://github.com/styler00dollar/VapourSynth-RIFE-ncnn-Vulkan
- vs-mlrt:
  https://github.com/AmusementClub/vs-mlrt
- REAL-Video-Enhancer:
  https://github.com/TNTwise/REAL-Video-Enhancer
