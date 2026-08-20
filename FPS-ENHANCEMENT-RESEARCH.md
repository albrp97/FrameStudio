# Modern FPS Enhancement Research

Research snapshot: 2026-08-19

This report evaluates current ways to increase the frame rate of video for
the Resolve media workflow. It covers neural video frame interpolation (VFI),
classical motion-compensated conversion, diffusion-based frame generation,
inference runtimes, Linux support, and a practical setup for the RTX 5070 Ti.

A controlled local benchmark, one-minute render, and REAL-Video-Enhancer
evaluation are now included below.
Performance numbers are labeled as local measurements, upstream measurements,
or estimates. The local render is an experimental reference, not yet a
production `resolve-fps` command.

## Executive decision

For normal footage, the best current practical candidate remains RIFE 4.26 or
`4.26.heavy`, but the backend precision must be validated per GPU/runtime.
On this RTX 5070 Ti, the unmodified TensorRT FP16 path is **not safe**: it
produces a regular grid corruption in raw frames. Selective FP16, with only
RIFE's `aten.pixel_shuffle` operation executed by PyTorch, is clean; the
standard model is faster than the FP32 fallback, while the heavy model is a
quality-first path with similar throughput. RIFE 4.25 remains the stable
control because its upstream project still recommends it for most scenes:

1. Benchmark RIFE 4.25, 4.26, and `4.26.heavy` on representative clips.
2. Use 4.26 for the normal quality/speed profile if it wins the local test.
3. Use selective TensorRT FP16 (`RGBH`) with a PyTorch
   `aten.pixel_shuffle` fallback as the validated local fast path. Use
   TensorRT FP32 (`RGBS`) as the simple fallback; never enable the unmodified
   pure TensorRT FP16 path without a raw-frame artifact gate.
4. Use scene detection and do not synthesize frames across hard cuts.
5. Use a direct target FPS such as 60 rather than chaining unrelated passes.
6. Trim output with explicit rational frame-count math and keep interpolation
   separate from the final delivery encode.

## REAL-Video-Enhancer evaluation

REAL-Video-Enhancer (RVE) is a useful Linux-oriented wrapper, not a newer
interpolation model. The project is archived until further notice; the
investigated release checkout reported `2.4.1-dev16` and supports TensorRT,
PyTorch, and NCNN backends. Its model registry exposes RIFE 4.26 and
`4.26.heavy`, but its `ModelHandler` maps those files to the RIFE 4.25
architecture implementations. The downloaded RVE RIFE 4.26 and heavy files
were SHA-256 verified byte-for-byte against the weights already used by the
clean `vs-rife` renders.

```text
rife4.26.pkl        45c7f74156704769dc9f85cfcaf8552e1e926f9399dcfa3a553dee88fac6f53f
rife4.26.heavy.pkl  4cc518e172156ad6207b9c7a43364f518832d83a4325d484240493a9e2980537
```

The one-minute test used the same 1920x1080 source as the local RIFE benchmark:

```text
/home/ghiki/Documents/edit/copy-concatenated-29.97fps-parallel-benchmark-60s-original.mp4
```

| RVE path | Result | RVE-reported render time |
| --- | --- | ---: |
| Unmodified TensorRT FP16, RIFE 4.26, PySceneDetect | **Regular grid corruption**; 3,605 output frames at about 59.892 FPS | 120.3 s |
| TensorRT FP16 with `aten.pixel_shuffle` in PyTorch, corrected RGB input and frame pacing | Clean sampled frames; exactly 3,600 frames at 60 FPS | 66.9 s |

The unmodified RVE output is available for direct inspection at:

```text
/home/ghiki/Documents/edit/copy-concatenated-29.97fps-parallel-rve-rife4.26-pure-fp16-59.94fps.mp4
```

The regular grid is visible in the decoded output, so RVE's default TensorRT
FP16 path reproduces the same local failure as the earlier `vs-rife` path.
RVE's `TensorRTHandler` does not exclude `aten.pixel_shuffle` from TensorRT;
the RVE model and runtime therefore do not avoid the faulty operator merely by
using a different frontend.

The corrected experimental RVE output and a four-way comparison are:

```text
/home/ghiki/Documents/edit/copy-concatenated-29.97fps-parallel-rve-rife4.26-pixel-fallback-corrected-60fps.mp4
/home/ghiki/Documents/edit/copy-concatenated-29.97fps-parallel-rve-comparison-4way-original-rve-standard-heavy-60fps.mp4
```

Three pipeline issues had to be corrected for a meaningful comparison:

1. RVE's raw FFmpeg reader did not request timestamp passthrough, so FFmpeg
   duplicated three source frames during conversion; the interpolation loop
   then produced 3,605 rather than 3,600 output frames.
2. Its normal `yuv420p` path converts frames with OpenCV before inference and
   does not honor the source's BT.709 range metadata. The corrected test
   requests RGB24 directly from FFmpeg.
3. The interpolation loop emits `N * factor - (factor - 1)` frames. The
   corrected test duplicates the final source frame as required for an exact
   fixed-rate output and uses an explicit 60 FPS output rate.
4. RVE's default writer did not emit the desired SDR color tags. The final
   reference was stream-copy remuxed with limited-range BT.709 metadata.

These changes were applied only to the temporary RVE checkout for diagnosis;
they are not an upstream RVE patch or a production project dependency. The
clean result demonstrates that RVE can be made usable on this GPU, but it
does not improve the RIFE model itself and its full pipeline was slower than
the validated selective-`vs-rife` path (35.44 seconds for the comparable
interpolation stage). RVE is therefore a useful reference/fallback, not the
default backend for `resolve-fps`.

To reproduce the TensorRT part of the corrected RVE run, patch
`backend/src/pytorch/TensorRTHandler.py` inside `build_engine` and use a new
model directory for the engine cache:

```python
torch_executed_ops=(
    {torch.ops.aten.pixel_shuffle.default}
    if os.environ.get("RVE_TRT_TORCH_PIXEL") == "1"
    else None
),
```

The temporary pipeline patch also adds `-fps_mode passthrough` and
`format=rgb24` to `backend/src/FFmpegBuffers.py`, writes
`ceilInterpolateFactor - 1` copies of the final frame in
`backend/src/RenderVideo.py`, and uses `RVE_OUTPUT_FPS=60` for the output
writer. Run the corrected backend with `RVE_TRT_TORCH_PIXEL=1`; rebuild the
engine if the TensorRT/Torch-TensorRT versions change.

The best first native-Linux integration is VapourSynth with either
`vs-mlrt` or `vs-rife`:

- `vs-mlrt` is the better long-term abstraction because it exposes TensorRT,
  TensorRT-RTX, ONNX Runtime CUDA, NCNN/Vulkan, and multiple model families.
- `vs-rife` is the simpler RIFE-focused path and currently exposes the newest
  RIFE model variants with direct target-FPS support.

GMFSS Fortuna is the main specialist candidate for anime and difficult 2D
animation. It combines multiple motion components and has a current
VapourSynth/TensorRT wrapper, but it is more complicated and its upstream
training environment is older.

Diffusion and long-context models are a real research improvement for some
large-motion or long-sequence cases, but they are not a better default for
this workstation:

- EDEN is a promising high-quality large-motion experiment.
- LDF-VFI targets long-range temporal consistency, but its quick-start
  documentation requires about 20 GB of GPU memory, above the RTX 5070 Ti's
  16 GB.
- These models are much slower, less integrated, and more likely to alter
  content instead of preserving it exactly.

There is no single current model that is objectively best for every type of
video. Published PSNR/SSIM results are useful for research comparisons, but
they do not replace visual checks for occlusions, fast cuts, animation
holds, subtitles, flashes, and fine textures.

## What "increase FPS" actually means

Increasing the nominal frame rate can mean several different operations:

| Method | What it does | Motion smoothness | Typical artifacts | Use |
| --- | --- | --- | --- | --- |
| Duplicate/drop frames | Changes timestamps or count without inventing motion | None | Judder or repeated frames | Compatibility only |
| Frame blending | Mixes adjacent frames | Low | Ghosting and double edges | Emergency fallback |
| Classical motion compensation | Estimates motion and warps frames | Medium | Holes, tearing, bad occlusions | Fast fallback |
| Neural VFI | Predicts an intermediate frame from adjacent frames | High when motion is supported | Warping, hallucinated detail, flicker | Normal production choice |
| Diffusion VFI | Generates an intermediate through a learned generative process | Potentially very high on difficult motion | Content changes, temporal drift, high cost | Selective quality experiments |
| Game frame generation | Generates display frames from rendered game frames | High for games | Not designed for arbitrary video files | Not a video-processing replacement |

For ordinary video, neural VFI is the correct term and the correct default.
Frame duplication is not a quality improvement. Frame blending is faster but
usually visibly worse. NVIDIA DLSS Frame Generation, AMD AFMF, and similar
display technologies are not general-purpose offline video converters.

Diffusion VFI is newer, but "newer" does not automatically mean better for a
preservation workflow. It can produce a visually plausible frame that does
not correspond to the actual physical motion or hidden content in the
source. That tradeoff can be valuable for a badly occluded shot, but it is
undesirable for archival or editing footage.

FFmpeg's `minterpolate` is the correct non-neural reference path. Its
motion-compensated mode can be used as a CPU fallback, for example with
`mi_mode=mci`, `mc_mode=aobmc`, and `me_mode=bidir`. It is useful for
correctness and baseline comparisons, but it should not be assumed to beat a
modern GPU VFI model on quality or throughput.

## Model landscape

### Recommended model matrix

| Model family | Best use | Practical strengths | Important limitations | Recommendation |
| --- | --- | --- | --- | --- |
| RIFE 4.25 | General footage | Mature, fast, arbitrary factors, many runtimes | Can fail on occlusions and very large motion | Default baseline |
| RIFE 4.26 | General footage and newer content | Newer model family, current wrappers | No universal proof that it wins every clip | Compare with 4.25 |
| RIFE 4.25/4.26 lite | Speed or limited VRAM | Lower computational cost | May lose detail or artifact resistance | Speed profile |
| RIFE 4.25/4.26 heavy | Quality-first RIFE | More expensive quality candidate | Higher VRAM and throughput cost | Final-shot comparison |
| GMFSS Fortuna | Anime and 2D animation | Anime-focused, RIFE plus global motion components, TensorRT wrapper | Complicated install, older upstream stack | Best specialist candidate |
| FILM | Large motion | Designed for large motion and high visual quality | Official implementation is TensorFlow-oriented and less production-ready | Research fallback |
| AMT | Efficient research alternative | Lightweight, fast, and accurate design | Official code is CC BY-NC 4.0 and not a turnkey runtime | Benchmark only |
| IFRNet | Lightweight fallback | Compact, fast design and NCNN/Vulkan implementation | Older model and less current tooling | Portable fallback |
| VFIMamba | High-resolution research | NeurIPS 2024 state-space approach, arbitrary interpolation | Requires older Python/PyTorch/CUDA environment | Research comparison |
| GIMM-VFI | Perceptual quality and arbitrary factors | Perceptual variants, RAFT/FlowFormer choices | Research setup and substantial compute | Selective comparison |
| SGM-VFI | Large motion | Sparse global matching targets difficult motion | More complex, research-oriented pipeline | Difficult-shot experiment |
| MoMo | Motion modeling research | Full and 10M variants, AAAI 2025 | Not integrated into a stable production runtime | Research comparison |
| BiM-VFI | Non-uniform motion | Targets acceleration, deceleration, and direction changes | No optimized TensorRT/Vulkan/VapourSynth runtime found | Research comparison |
| HFD | Large-motion diffusion | Flow-diffusion design, reported faster than older diffusion VFI | No mature Linux production runtime found | Research only |
| InterpAny | Long slow-motion chains | Distance indexing and iterative reference estimation | Older Torch/CUDA environment and no optimized runtime | Research only |
| EDEN | Very difficult large motion | CVPR 2025 diffusion quality focus | Slow, generative, not a routine converter | Quality experiment |
| LDF-VFI | Long sequences and consistency | CVPR 2026 holistic autoregressive diffusion | About 20 GB VRAM in quick start, high complexity | Not suitable as default |
| DAIN/CAIN/FLAVR/XVFI | Legacy or special cases | Existing implementations and historical references | Usually slower, older, or less robust than current RIFE | Avoid by default |

The model numbers are not a universal quality ranking. The Practical-RIFE
upstream documentation recommends 4.25 for most scenes, while current wrappers
also expose 4.26 and heavy/lite variants. The correct policy is to benchmark
adjacent versions on the user's footage, not to assume that the highest
number always looks best.

### RIFE 4.25 and 4.26

RIFE remains the strongest practical baseline because it combines:

- Fast inference.
- Direct intermediate-frame prediction.
- Arbitrary target factors in current VapourSynth wrappers.
- Scene-change handling.
- FP16 and TensorRT support.
- Mature CUDA and Vulkan implementations.
- Simple integration into a frame-by-frame video pipeline.

The current `vs-rife` package is version 5.7.0 and lists models from 4.0
through 4.26, including:

- `4.25`
- `4.25.lite`
- `4.25.heavy`
- `4.26`
- `4.26.heavy`

Its default model is 4.25. RIFE 4.25 and 4.26 are both worth testing because
the visual difference can depend on the source domain. The lite variants
trade model cost for speed. The heavy variants are quality candidates, not
automatic recommendations; upstream does not publish a universal
quality-per-second ranking for every variant.

For this workstation, the recommended order is:

1. RIFE 4.26 with selective TensorRT FP16 for the clean fast baseline; gate
   RIFE 4.25 separately.
2. TensorRT FP32 when the selective fallback cannot be built.
3. RIFE 4.26 heavy with selective TensorRT FP16 for difficult shots.
4. RIFE 4.25 lite or 4.26 lite when throughput or VRAM is the priority.

### Local TensorRT FP16 failure and corrected profile

The one-minute source was 1920x1080, 29.97 FPS, and 1,800 frames. The
controlled comparison used the same RIFE 4.26 weights, source frames, scene
markers, and output encoder:

| Path | Result | Local measurement |
| --- | --- | --- |
| TensorRT FP16 / `RGBH` | Regular grid corruption in raw output | ~111.5 output FPS; ~2.5 GiB peak VRAM |
| TensorRT FP16 / `RGBH` + PyTorch `aten.pixel_shuffle` | Clean | 101.57 interpolation FPS; 35.44 s; 3,909 MiB peak VRAM |
| TensorRT FP32 / `RGBS` | Clean | 86.52 interpolation FPS; 41.61 s; 3,666 MiB peak VRAM |
| PyTorch eager FP16 | Clean | ~59.9 warm inference FPS in the earlier benchmark |

Disabling TensorRT auxiliary streams did not change the FP16 corruption. The
same model in PyTorch FP16 was clean, so this is not a general FP16 model
failure. Export-graph inspection identified repeated
`aten.pixel_shuffle.default` operations in the flow network. Executing only
that operation in PyTorch removed the corruption while leaving the
convolutional network in TensorRT FP16. The current preferred settings are:

```text
RGBH -> vs-rife 4.26 -> TensorRT FP16
      (PyTorch aten.pixel_shuffle fallback)
    -> explicit 60/1 target -> trim to 3600 frames
    -> YUV420P10 -> NVENC H.264 delivery encode
```

The corrected preferred outputs are:

```text
/home/ghiki/Documents/edit/copy-concatenated-29.97fps-parallel-rife-4.26-tensorrt-fp16-pixel-fallback-corrected-60fps.mp4
/home/ghiki/Documents/edit/copy-concatenated-29.97fps-parallel-rife-4.26-heavy-tensorrt-fp16-pixel-fallback-corrected-60fps.mp4
/home/ghiki/Documents/edit/copy-concatenated-29.97fps-parallel-rife-4.26-comparison-3way-fp16-pixel-fallback-corrected-60fps.mp4
```

The two interpolated outputs are exactly 60 seconds with 3,600 video frames
and copied AAC audio. The comparison is a 1920x360 three-way video with equal
640x360 original, standard, and heavy panels. The experimental harness is
`/home/ghiki/.cache/resolve-fps/benchmark.vpy`; its `INPUT_FORMAT`, explicit
limited-range handling, scene markers, and `TARGET_FRAMES` trim are the
important corrections. A production tool should render a short raw-frame
smoke test and reject any backend that shows periodic grid/block corruption
before starting a long job.

The selective fallback is enabled in the flow-network
`torch_tensorrt.dynamo.compile` call with:

```python
torch_executed_ops=(
    {torch.ops.aten.pixel_shuffle.default}
    if os.environ.get("TRT_TORCH_PIXEL") == "1"
    else None
),
```

Set `INPUT_FORMAT=RGBH`, `TRT_TORCH_PIXEL=1`, and use a new engine cache such
as `/home/ghiki/.cache/resolve-fps/engines-pixel-fallback`. The cache must be
separate because its normal key does not include the PyTorch-executed
operator set. If a TensorRT or Torch-TensorRT upgrade breaks this path,
rebuild it and repeat the raw-frame gate; use the documented `RGBS`/FP32
profile if it fails.

The current `vs-rife` implementation does not support ensemble mode for RIFE
4.26 and `4.26.heavy`. Do not enable that option for those models; use a
different model or a separate comparison if ensemble smoothing is needed.

### GMFSS Fortuna

GMFSS Fortuna is explicitly dedicated to anime video frame interpolation. Its
VapourSynth wrapper supports:

- Base and union models.
- TensorRT.
- FP16 through RGBH input.
- Arbitrary factors and target FPS.
- Scene detection.
- Optional ensemble processing.
- Resolution scaling for the optical-flow component.
- Cached, GPU-specific TensorRT engines.

This makes it a serious candidate for anime, line art, and 2D animation.
It should not replace RIFE as the general default because the setup is more
specialized and the upstream training code uses an older PyTorch 1.13/CUDA
11.8 environment. Published TensorRT bundles for the wrapper also target
older CUDA/cuDNN/TensorRT combinations than the current RTX 5070 Ti stack.
Use a current wrapper, isolate its dependencies, and validate the runtime
before treating it as a production mode.

For anime:

1. Test GMFSS Fortuna base and union.
2. Compare against RIFE 4.25/4.26.
3. Use scene detection.
4. Consider held-frame analysis before interpolation.
5. Inspect line edges, mouths, hands, and camera pans at 100 percent.

### FILM

Google's FILM is designed for large motion and was published at ECCV 2022.
Its multi-scale feature extractor and large-motion objective remain useful
ideas. The official implementation is TensorFlow 2 and its setup is less
convenient than current RIFE/TensorRT paths.

FILM is worth testing when RIFE produces obvious failures on:

- Large camera movement.
- Long displacements.
- Wide gaps between visible positions.
- Slow-motion material with large changes between source frames.

It should be evaluated as a selective shot-level fallback rather than a
whole-library default.

### AMT and IFRNet

AMT, published at CVPR 2023, is designed to be lightweight, fast, and
accurate. Its official demo accepts videos and arbitrary interpolation depth.
However, its official repository is licensed CC BY-NC 4.0, so it should not
be embedded in a generally distributable tool without checking the license.

IFRNet is an efficient CVPR 2022 model with an NCNN/Vulkan implementation.
It is useful where a portable, low-dependency fallback matters more than the
last increment of quality. It is not the first model to benchmark on an RTX
5070 Ti if TensorRT RIFE is available.

### VFIMamba, GIMM-VFI, SGM-VFI, MoMo, and newer motion models

These newer research projects are important because they test alternatives to
the classic flow-and-warp design:

- VFIMamba uses state-space blocks and reports strong high-resolution
  results. It provides an efficient model and a stronger model, plus
  arbitrary-N demo code. The official setup uses Python 3.10, PyTorch 1.13.1,
  CUDA 11.7, and custom Mamba dependencies.
- GIMM-VFI uses generalizable implicit motion modeling. It provides
  RAFT-based and FlowFormer-based variants and perceptual versions trained
  with LPIPS-related objectives. The repository reports approximately 7.9 GB
  for 2K and 10.9 GB for 4K tests on V100 hardware with downsampling.
- SGM-VFI adds sparse global matching for difficult large motion. It is
  promising for hard benchmarks but requires a larger research pipeline with
  global flow components and special datasets.
- MoMo separates motion modeling components and provides a full model and a
  10M-parameter model. It is a useful research comparison, not yet a simple
  production backend.
- BiM-VFI targets non-uniform motion such as acceleration, deceleration, and
  direction changes with a bidirectional motion field. Its reported gains are
  interesting for real camera motion, but its official code does not provide
  a current optimized TensorRT, NCNN, or VapourSynth deployment path.
- HFD uses a hierarchical flow-diffusion design and reports a large speed
  improvement over earlier diffusion VFI methods. That does not make it a
  practical default: a mature Linux runtime and end-to-end audio/video
  pipeline are still missing.
- InterpAny focuses on long interpolation chains through distance indexing and
  iterative reference estimation. It is relevant to 8x or longer slow motion,
  but its documented environment is based on older PyTorch/CUDA versions.

These projects may beat RIFE on selected benchmark categories, but their
older dependency stacks and lack of optimized deployment paths make them
poor first choices for a daily Resolve utility.

### EDEN and LDF-VFI

EDEN is a CVPR 2025 diffusion-based method for high-quality large-motion
interpolation. It uses compact latent tokens, pyramid feature fusion, and a
diffusion transformer. It is a good candidate for:

- A few hero shots where RIFE fails.
- Large occlusions or ambiguous motion.
- A quality comparison against a conventional VFI model.

Its published inference path is a 2x adjacent-frame video workflow rather
than a complete arbitrary-FPS, VFR-aware Resolve pipeline. Audio preservation,
scene-cut handling, and high-bit-depth output must be added around it. It is
not yet the right default for hours of footage because it requires a large
research environment and generative inference.

LDF-VFI is a CVPR 2026 autoregressive diffusion-transformer method that models
longer temporal context. Its stated goals are long-range coherence,
large-motion quality, and arbitrary spatial resolution. The quick-start
documentation requires approximately 20 GB of GPU memory for 8x
interpolation, and distributed inference is documented for larger workloads.
That exceeds the RTX 5070 Ti's 16 GB in the simple single-GPU configuration.

LDF-VFI is therefore a future research target, not a practical first
implementation on this system.

### What the newer methods change

The newer methods are not all solving the same problem:

- BiM-VFI models non-uniform motion better than methods that assume a simple
  constant-velocity interval.
- HFD and EDEN use diffusion to improve difficult or ambiguous motion.
- InterpAny reduces ambiguity when generated frames are repeatedly reused in
  long slow-motion chains.
- LDF-VFI models longer temporal context instead of treating every pair as an
  isolated interpolation problem.

These are meaningful research advances, but deployment quality also requires
stable arbitrary-FPS handling, scene detection, color preservation, audio
remuxing, crash recovery, and an optimized runtime. RIFE currently wins that
complete-system comparison even when a newer model can win a selected paper
benchmark.

## Runtime and backend comparison

| Runtime | NVIDIA performance potential | Portability | Setup cost | Role |
| --- | --- | --- | --- | --- |
| TensorRT | Highest or near-highest for supported models | GPU and engine specific | Engine build and cache | First RTX 5070 Ti test |
| TensorRT-RTX | Optimized for RTX deployment and fast engine builds | RTX-focused, version-sensitive | Newer runtime integration | Test alongside TensorRT |
| Torch-TensorRT | High, with a PyTorch model path | NVIDIA only | PyTorch plus TensorRT | Simple `vs-rife` path |
| ONNX Runtime CUDA | Good compatibility | NVIDIA CUDA | Moderate | Fallback when TRT fails |
| NCNN/Vulkan | Good portability and small footprint | NVIDIA, AMD, Intel, macOS | Low | Portable fallback |
| PyTorch eager | Useful correctness baseline | NVIDIA CUDA | High package footprint | Debugging and reference |
| ComfyUI native PyTorch | Official FILM/RIFE models with adaptive memory handling | Linux, Windows, macOS through ComfyUI | ComfyUI dependency; image-only output | Correctness and memory baseline |
| Video2X C++/Vulkan | User-friendly and efficient wrapper | Linux and Windows | Low to moderate | External fallback application |

The `vs-mlrt` documentation states that TensorRT is typically much faster
than its ONNX Runtime CUDA backend. It also exposes TensorRT-RTX and
NCNN/Vulkan backends through the same VapourSynth-oriented interface. This is
why `vs-mlrt` is the most useful long-term integration point even if the first
production profile uses only RIFE.
The current `vs-mlrt` release is v15.16; its build workflows track modern
CUDA, TensorRT, and TensorRT-RTX versions. Version-lock the release with the
model environment rather than installing it globally.

### ComfyUI native Frame Interpolate

Current ComfyUI has a native frame-interpolation path in its core rather than
requiring a custom node. The official model package currently provides:

- `film_net_fp16.safetensors`
- `rife_v4.25.safetensors`
- `rife_v4.25_heavy.safetensors`
- `rife_v4.25_lite.safetensors`
- `rife_v4.26.safetensors`
- `rife_v4.26_heavy.safetensors`

The files belong in `ComfyUI/models/frame_interpolation/`. The native
`FrameInterpolationModelLoader` detects FILM or RIFE checkpoints, loads them
through ComfyUI's model patcher, and selects FP16 when the device supports it.
The `FrameInterpolate` node accepts an image sequence and an integer
`multiplier` from 2 through 16. Its current implementation caches features
between adjacent pairs and reduces the interpolation batch after an out of
memory event. These details explain why the native path may use RAM and VRAM
more predictably than older custom nodes.

As of the inspected ComfyUI source revision
[`c67885b`](https://github.com/Comfy-Org/ComfyUI/tree/c67885b14556cf3e4e061862925282d403d09862),
the native node is a PyTorch/ComfyUI model path: it does not call TensorRT,
ONNX Runtime, or NCNN/Vulkan. It returns `IMAGE` frames rather than a video
file, so demuxing, audio, VFR timing, color metadata, and scene-cut policy
still belong outside the node. The integer multiplier also means that native
ComfyUI does not directly provide fractional factors such as 1.5x or 2.5x;
those require a target-FPS wrapper or a different runtime.

This makes native ComfyUI useful as a low-friction correctness and memory
baseline, not an assumed throughput winner. A tuned TensorRT implementation
should still be expected to win on the RTX 5070 Ti until the same clips,
resolution, multiplier, warm-up policy, and output path prove otherwise.

#### ComfyUI TensorRT custom nodes

The separate
[`ComfyUI-Rife-Tensorrt`](https://github.com/yuvraj108c/ComfyUI-Rife-Tensorrt)
node automatically downloads and builds FP16 TensorRT engines on first use.
Its documented model names are `rife47`, `rife48`, and `rife49`, with
`rife49` described as the most accurate and `rife47` as the fastest. Its
documented resolution range is 256 to 3840 pixels per side. The README's
microbenchmark used 2,000 alternating similar frames on an H100:

| Resolution | Multiplier | Reported warm FPS |
| --- | ---: | ---: |
| 512x512 | 2x | 45 |
| 512x512 | 4x | 57 |
| 1280x1280 | 2x | 21 |

Those figures are inference-only measurements on an H100 with synthetic
alternating frames, not RTX 5070 Ti or end-to-end video results. The names
`rife47`/`rife48`/`rife49` must not be treated as aliases for the official
native `rife_v4.25`/`rife_v4.26` files without comparing the actual weights.
The related
[`ComfyUI_RIFE_TensorRT_Auto`](https://github.com/silveroxides/ComfyUI_RIFE_TensorRT_Auto)
README documents CUDA 13 as the default for RTX 50-series cards, small and
medium resolution profiles, and an RTX 5070 Ti test environment, but it does
not provide a controlled RTX 5070 Ti throughput result.

Both TensorRT node repositories state
[CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/).
Using them as an external local benchmark is different from embedding their
code or redistributing a modified node; any future integration must preserve
the applicable attribution, non-commercial, and share-alike obligations.

#### Community evidence about ComfyUI VFI

The Reddit evidence is useful for selecting experiments, but it does not
replace a local benchmark:

| Community report | What it supports | Confidence |
| --- | --- | --- |
| [Native Frame Interpolate thread](https://www.reddit.com/r/comfyui/comments/1tpn7i9/fyi_theres_now_native_frame_interpolation_in/) | The author confirmed FILM and RIFE, including 4.26, and reported that native memory handling felt faster than older custom nodes. Comments suggested TensorRT RIFE, GMFSS, GIMM, and TLB VFI. | **Medium for availability; low for performance.** |
| [30 FPS to 60 FPS question](https://www.reddit.com/r/comfyui/comments/1r84aes/what_do_you_use_for_frame_interpolation/) | One commenter preferred GIMM over FILM/RIFE and claimed fewer artifacts or faster results. No controlled hardware, resolution, model version, or timing comparison was supplied. | **Low.** Subjective lead only. |
| Comments in the native-node thread | One user claimed a TensorRT RIFE run fell from about 15 minutes to 10 seconds; another reported GMFSS smoother than GIMM on extreme motion but only after one test, while a separate comment reported GMFSS taking about 4.5 minutes longer than GIMM on an 846x1152 clip using a professional GPU. | **Low.** Anecdotal and internally non-comparable. |

The practical conclusion is to benchmark three separate paths rather than
combine their claims: native ComfyUI RIFE/FILM for correctness and memory,
ComfyUI TensorRT RIFE for engine throughput, and `vs-rife`/`vs-mlrt` for the
production-style video pipeline.

### TensorRT considerations

TensorRT builds an engine for the actual model, precision, shape, GPU, and
runtime configuration. The first run is therefore not representative:

- Engine construction can take seconds or minutes.
- Engines are not generally portable between GPUs.
- Changing resolution, precision, model, or workspace can trigger a rebuild.
- Engine files must be cached and invalidated when versions change.

For a fixed Resolve workflow, static shapes are preferable when possible:

- They allow more aggressive optimization.
- They avoid dynamic-shape overhead.
- They make results reproducible.
- They simplify cache management.

Dynamic shapes are useful when one engine must process many resolutions, but
they can reduce peak performance. Build separate engines for common sizes
such as 1920x1080, 2560x1440, and 3840x2160 if the storage and warm-up time
are acceptable.

### NCNN/Vulkan considerations

NCNN/Vulkan is the safest portability fallback:

- It does not require PyTorch or CUDA libraries.
- It runs on NVIDIA, AMD, and Intel GPUs with Vulkan.
- It has a smaller deployment footprint.
- It is normally slower than a tuned TensorRT path on the same NVIDIA GPU.

The standalone `rife-ncnn-vulkan` project is portable and easy to recover, but
its latest upstream release is old and its documented model list ends at
RIFE 4.6. The VapourSynth-RIFE-NCNN-Vulkan wrapper documents newer models,
including 4.26 variants, and is a better current Vulkan comparison. Treat the
standalone binary as a compatibility fallback, not the primary quality
benchmark.

## RTX 5070 Ti recommendation

The workstation at the time of this research is:

- CachyOS/Arch Linux.
- AMD Ryzen 5 9600X.
- NVIDIA RTX 5070 Ti with 16 GB VRAM.
- NVIDIA driver 610.57.04.
- FFmpeg 9.0.1.
- DaVinci Resolve Free 21.0.4.
- No Wine installation.

The recommended first configuration is:

| Setting | 1080p recommendation | 4K recommendation |
| --- | --- | --- |
| Model | RIFE 4.26, with 4.25 as control | RIFE 4.25/4.26 |
| Backend | TensorRT or TensorRT-RTX | TensorRT or TensorRT-RTX |
| Precision | Selective FP16/RGBH with pixel-shuffle fallback; FP32/RGBS fallback | FP32/RGBS or selective FP16 after a 4K artifact test |
| Scale | 1.0 | Start at 0.5 |
| Scene detection | On | On |
| Ensemble | Off initially | Off initially |
| TTA | Off initially | Off initially |
| Shape | Static 1920x1080 | Static 3840x2160 or scaled internal path |
| Streams | 1, then benchmark 2 | 1, then benchmark 2 |
| Output | Preserve source during tests | Preserve source during tests |

The exact best combination must be measured locally because driver, TensorRT,
PyTorch, model implementation, memory clocks, thermals, and encoder choices
all affect throughput. Do not assume that two inference streams are faster:
the extra concurrency can increase VRAM use and reduce clock stability.

Current `vs-rife` documents PyTorch 2.10+, VapourSynth R69+, TensorRT 10.14.1+,
and Torch-TensorRT 2.10+ for its TensorRT path. Its installation example uses
the CUDA 13 PyTorch wheels. This is a modern stack and should be installed in
an isolated virtual environment only after the benchmark plan is approved.

## Recommended profiles

### Profile A: fastest sensible general conversion

Use this for routine 30 FPS to 60 FPS or 24 FPS to 48 FPS work:

- RIFE 4.26; keep RIFE 4.25 as a separately gated control.
- TensorRT or TensorRT-RTX.
- The fastest **validated** precision for the target GPU. On this machine use
  selective TensorRT FP16 with the PyTorch pixel-shuffle fallback. Pure
  TensorRT FP16 remains disabled because of the confirmed artifact.
- Internal scale 1.0 at 1080p.
- Scene detection on.
- Ensemble off.
- TTA off.
- One GPU worker or one/two internal streams after benchmarking.
- Direct target FPS.
- NVENC H.264 for a delivery file.

This is the profile most likely to maximize useful output per hour.

### Profile B: best speed/quality balance

- A/B test RIFE 4.25 and 4.26.
- Keep the faster model only if the visual difference is negligible.
- Use selective TensorRT FP16 with a cached static engine on this workstation.
  Keep the fallback operator set in a separate cache. TensorRT FP32 remains
  the simple recovery path, and any different TensorRT/Torch-TensorRT build
  must pass a raw-frame artifact check before acceptance.
- For RIFE 4.25, ensemble can be tested on difficult shots. RIFE 4.26 and
  `4.26.heavy` do not support ensemble in the current wrapper.
- Keep scene detection on.
- Inspect a short preview before starting the full file.

This should be the default profile exposed by the future TUI.

### Profile C: quality-first RIFE

- RIFE 4.26 heavy and RIFE 4.25 heavy comparison.
- Selective TensorRT FP16 with the PyTorch pixel-shuffle fallback.
- Scene detection on.
- Do not enable ensemble for the 4.26 models; use a compatible model if an
  ensemble comparison is required.
- One stream to avoid memory pressure.
- ProRes 422 HQ or DNxHR HQX plus PCM for Resolve.

Do not use this profile for an entire library without checking throughput and
artifact rates first.

### Profile D: 24 FPS to 60 FPS

Use a direct 2.5x target:

- `fps_num=60`, `fps_den=1`, or an equivalent `factor_num=5`,
  `factor_den=2`.
- For 23.976 FPS, use the exact source and target time bases rather than
  rounding to 24/60 when synchronization matters.
- Keep audio at its original duration; normal frame-rate conversion does not
  require audio time stretching.
- Verify the final duration and audio/video synchronization.

Avoid converting 24 to 48 and then 48 to 60 unless a specific model or
workflow requires it. Multiple passes compound inference cost and can
compound artifacts.

### Profile E: 30 FPS to 60 FPS

- RIFE 4.25 or 4.26.
- Direct factor 2.
- Selective TensorRT FP16 with the PyTorch pixel-shuffle fallback; use FP32
  if the exact GPU/runtime/model does not pass the raw-frame artifact check.
- Scene detection on.
- No de-duplication for live action.

This is the easiest target and should be the first local benchmark.

### Profile F: 60 FPS to 120 FPS

- Use RIFE 4.25 lite or 4.26.
- Compare 4.26 standard if the source has enough motion detail.
- Keep TTA and ensemble off.
- Test at 1.0 scale first.
- Expect more visible artifacts because each source interval contains less
  motion but the output exposes more model decisions.

120 FPS is not automatically more cinematic or more realistic. It is useful
for high-refresh playback and slow motion, but it can expose shutter,
compression, and interpolation errors.

### Profile G: slow motion

For 2x slow motion, generate one intermediate frame per source interval and
play the result at the original nominal FPS. For 4x or more, prefer a model
with native multi-factor support or direct target-factor support. Repeatedly
feeding generated frames back through a 2x model can accumulate artifacts;
for 8x, compare a native 8x model such as IFRNet/FLAVR or a continuous-time
research model before choosing recursive RIFE.

Audio needs a separate policy:

- Mute it for a silent slow-motion master.
- Time-stretch it with a high-quality audio tool if it must remain synchronized.
- Do not simply copy normal-speed audio into a slowed video.

Keep the original source frames in the output. Interpolation should add
frames, not replace the originals.

### Profile H: anime and 2D animation

- Test GMFSS Fortuna base and union.
- Compare RIFE 4.25/4.26.
- Enable scene detection.
- Analyze held frames and duplicate cadence before interpolation.
- Use de-duplication only for known held-frame animation.
- Inspect line art, faces, text, and camera pans.
- Keep TTA or compatible-model ensemble as a final comparison, not the first
  run. RIFE 4.26 does not support ensemble in the current wrapper.

Animation often contains intentional repeated frames. Removing all duplicates
can change timing and make the result feel unnaturally fast. The tool should
make cadence analysis explicit instead of silently applying it to every file.

### Profile I: large-motion or difficult shots

Use a shot-level fallback order:

1. RIFE 4.25/4.26 with scene detection.
2. GMFSS Fortuna for animation-like footage.
3. FILM, SGM-VFI, GIMM-VFI, or EDEN for a selected difficult shot.
4. Manual editing or original-frame retiming if every neural result changes
   the content.

Do not run a whole feature through a diffusion model just because it wins a
paper benchmark on a large-motion subset.

### Profile J: Resolve editing master

Inference output should not be treated as a final editing master when it will
be encoded again. Prefer:

- ProRes 422 HQ plus PCM for a practical master.
- DNxHR HQX plus PCM when a Resolve-friendly MXF workflow is preferred.
- FFV1 plus PCM only when large lossless files are acceptable.

Use H.264/AAC only for previews and delivery. The interpolation step already
creates a new generation, so avoiding another lossy generation is valuable.

### Profile K: universal delivery

For Windows, Linux, VLC, Google TV, Android phones, and Meta Quest:

- MP4.
- H.264 High profile.
- 8-bit `yuv420p`.
- BT.709 tags for SDR.
- AAC-LC, 48 kHz, stereo, about 192 kb/s.
- `+faststart`.

Use NVENC H.264 for speed. Use CPU x264 when compression efficiency and file
size matter more than render time. H.265 or AV1 can be smaller, but H.264 is
the safer universal compatibility choice.

## Source and timing policy

### Constant frame rate versus variable frame rate

Do not silently turn VFR footage into CFR. First determine whether the user
wants:

- A fixed target FPS for editing or delivery.
- Original timestamps preserved with only additional frames.
- A slow-motion result with changed duration.

For a fixed target FPS, rewrite PTS deliberately and document the target.
For VFR archival material, preserve timestamps where the selected runtime
supports it. A source with variable timestamps can otherwise acquire drift,
duplicate frames, or audio desynchronization.

### Scene changes

Never interpolate across a hard scene cut. The model sees unrelated frames and
will create a blended or hallucinated transition. The recommended pipeline
must:

1. Run a scene detector.
2. Mark the final frame before each cut.
3. Pass the original boundary frames through unchanged.
4. Interpolate only within each shot.

Thresholds are content-dependent. Start with the runtime default, then lower
the threshold if flashes or rapid cuts are being missed. Fades and dissolves
may need manual segmentation because they are not hard cuts.

### Color and bit depth

Most public VFI models are primarily tested on SDR RGB inputs. The future tool
must not assume that an 8-bit SDR model is safe for every HDR source:

- Preserve the input transfer function and primaries.
- Convert to the model's expected RGB range explicitly.
- Use float16 or float32 processing.
- Convert back with an explicit color transform.
- Preserve HDR metadata only when the path has been tested.
- Keep 10-bit output for a 10-bit/HDR editing master.

RIFE 4.26 clamps its input tensor to the nominal `[0, 1]` range. RGBH means
FP16 processing; it does not mean that the model is HDR-aware. PQ/HLG values
outside the model's training range can be clipped or altered. Treat HDR
interpolation as an explicit experiment and validate the color pipeline with
scopes and highlight crops.

An incorrect RGB/YUV or transfer-function conversion can create more visible
damage than the interpolation model itself.

## Proposed implementation architecture

The existing Resolve media TUI should not embed model code directly into its
main Python process. Use a separate, versioned interpolation environment and
a narrow command boundary:

1. Probe the source with `ffprobe`.
2. Detect source FPS, time base, resolution, color metadata, audio, and VFR.
3. Split or mark scene boundaries.
4. Convert frames to the runtime's required RGBH/RGBS format.
5. Run `vs-rife` or `vs-mlrt` with a cached engine.
6. Convert back to the requested editing or delivery format.
7. Copy or time-stretch audio according to the chosen duration policy.
8. Preserve or explicitly regenerate subtitles and metadata.
9. Verify frame count, FPS, duration, stream presence, color tags, and
   audio/video synchronization.
10. Write atomically and retain logs, model, runtime, and engine identifiers.

The first implementation should support only RIFE. Add GMFSS Fortuna after
the RIFE path has stable error handling and benchmark output. Research models
should be optional plugins rather than hard-coded branches.

### Suggested runtime modes

| Mode | Runtime | Model | Purpose |
| --- | --- | --- | --- |
| `fast` | `vs-mlrt` TRT/TRT-RTX | RIFE 4.25 | Default throughput |
| `quality` | `vs-mlrt` TRT/TRT-RTX | RIFE 4.26 or heavy | Final-shot quality |
| `anime` | `vs-gmfss_fortuna` TRT | GMFSS Fortuna | Animation specialist |
| `portable` | NCNN/Vulkan or Video2X | RIFE | No PyTorch/TensorRT fallback |
| `research` | Isolated project environment | FILM, EDEN, LDF, etc. | Explicit experiments only |

### Engine cache policy

Cache keys must include at least:

- Model and model checksum.
- Runtime name and version.
- TensorRT/TensorRT-RTX version.
- GPU name and compute capability.
- Precision.
- Input dimensions or dynamic-shape profile.
- Scale.
- Ensemble setting.
- Relevant optimization flags.

If any of these change, rebuild the engine rather than reusing an unknown
binary. Keep the cache outside the source media directory and provide a
clear cleanup command.

## Benchmark plan for the RTX 5070 Ti

The benchmark must separate model quality, inference speed, and encoding
speed. A single end-to-end time is not enough.

### Test clips

Use short clips from the user's actual library, plus public benchmark clips:

- Normal live action with camera movement.
- Fast motion and occlusion.
- Anime or 2D line art.
- Low-motion held-frame animation.
- Screen capture or gameplay.
- 4K material.
- VFR material.
- A hard-cut sequence and a fade/dissolve sequence.

For objective scoring, use a high-frame-rate source as ground truth:

1. Keep the original 60 FPS source.
2. Downsample it to 30 FPS by selecting frames.
3. Interpolate back to 60 FPS.
4. Compare the generated frames with the held-out original frames.

Use PSNR/SSIM for reconstruction, LPIPS for perceptual difference, and VMAF
only as an additional signal. Also record manual artifact scores because
numeric scores do not reliably detect temporal warping or hallucinated
objects.

### Runtime matrix

At minimum, compare:

- RIFE 4.25, PyTorch eager.
- RIFE 4.25, ONNX Runtime CUDA if available.
- RIFE 4.25, TensorRT FP32 and selective FP16 where the raw-frame artifact
  gate passes.
- RIFE 4.25, TensorRT-RTX FP32/FP16 if available and validated.
- RIFE 4.26, TensorRT FP32 and selective FP16 with the pixel-shuffle fallback.
- RIFE 4.26 heavy, TensorRT FP32 and selective FP16 with the pixel-shuffle
  fallback.
- NCNN/Vulkan RIFE as the portable fallback.

For anime, add GMFSS Fortuna base and union. For research-only difficult-shot
comparisons, add FILM, BiM-VFI, GIMM-VFI, and EDEN. Do not compare models with
different output resolution, target FPS, color conversion, or encoder
settings.

No credible public benchmark located for this report provides RTX 5070 Ti
throughput for the complete decode/inference/encode pipeline. Existing
figures use older GPUs, different resolutions, or partial pipelines and must
not be extrapolated. The local benchmark is required before selecting worker
counts or promising a render-time improvement.

### Measurements

Record:

- Engine build time.
- Warm-up time.
- Steady-state inference FPS.
- Input FPS and output FPS.
- End-to-end wall time.
- Peak VRAM.
- GPU utilization and power.
- CPU utilization.
- Decode time.
- Encode time.
- Temporary disk usage.
- Output duration and frame count.
- Audio/video synchronization.
- Manual artifact score.

Report engine-build time separately from warm steady-state throughput. Run
each case at least three times after one warm-up pass. Use the same GPU,
power profile, resolution, source frames, and output encoder.

### Suggested benchmark procedure

1. Reboot or stop unrelated GPU workloads.
2. Record driver, kernel, FFmpeg, VapourSynth, Python, PyTorch, TensorRT,
   and model versions.
3. Set the system to the same performance policy for every run.
4. Run a short correctness test.
5. Build and cache the engine.
6. Run one warm-up.
7. Run three timed steady-state passes.
8. Repeat at 1080p and 4K.
9. Inspect frame pairs around motion, cuts, and occlusions.
10. Save JSON/CSV results beside the report, not in the media folder.

A useful first target is not "maximum FPS" in isolation. It is the highest
quality score that completes faster than the current Resolve export workflow
and remains stable for a multi-minute clip.

## Reddit evidence and community practice

Reddit is useful for finding practical failure modes and real playback
configurations, but it is not a substitute for a controlled benchmark. The
normal Reddit web/API/JSON/RSS endpoints were blocked or rate-limited during
this research. Publicly indexed post text was therefore read through the
Redlib mirror at `safereddit.com`; the table cites the original Reddit
permalinks, not the mirror URLs. Search-result snippets were not treated as
evidence when the directly retrieved thread said something different.

### Evidence grading

- **Medium-high:** The author gives hardware, runtime, resolution, model, and
  a concrete configuration or observable failure. It is still an anecdote,
  not an independent benchmark.
- **Medium:** A detailed workflow or deployment report without enough timing
  or comparison data to reproduce performance.
- **Low:** Subjective image-quality claims, unanswered setup requests,
  historical reports, or unverified assumptions.

### Verified Reddit findings

| Source | Evidence type | Claims actually supported | Confidence and use |
| --- | --- | --- | --- |
| [r/comfyui, May 28 2026: native Frame Interpolate](https://www.reddit.com/r/comfyui/comments/1tpn7i9/fyi_theres_now_native_frame_interpolation_in/) | Current ComfyUI availability report | The author identifies the native `Frame Interpolate` node, FILM, RIFE including 4.26, and better RAM/VRAM handling than older custom nodes. Comments add unverified TensorRT speed claims and subjective GMFSS/GIMM comparisons. | **Medium for availability; low for performance.** Official source inspection confirms the native node and model files, but not the community timing claims. |
| [r/comfyui, Feb 18 2026: 30 FPS to 60 FPS](https://www.reddit.com/r/comfyui/comments/1r84aes/what_do_you_use_for_frame_interpolation/) | Advice request and subjective replies | The thread asks for a fast, low-artifact 30-to-60 workflow. One commenter prefers GIMM over FILM and RIFE, but gives no controlled hardware, resolution, model, or timing comparison. | **Low.** Use only to motivate a GIMM comparison. |
| [r/htpc, Aug 06 2025](https://www.reddit.com/r/htpc/comments/1mixcc3/entry_point_to_interpolate_videos_in_mpchc_using/) | Detailed VapourSynth configuration and hardware report | RIFE ncnn/TensorRT, monitor-refresh targeting, MVTools scene detection, and a reported RTX 2060 setup. The author says 1080p to 120 FPS required a 1280x640 internal downscale and that RIFE produced "swooping" at cuts without scene detection. | **Medium-high.** Strong practical evidence for scene detection and the cost of downscaling; not full-resolution RTX 5070 Ti performance. |
| [r/mpv, Nov 27 2025](https://www.reddit.com/r/mpv/comments/1p7p4bf/how_to_set_up_rife_interpolation_to_work_with_mpv/) | Troubleshooting report | CPU MVTools worked, while the author's Vulkan RIFE setup was difficult, scattered across dependencies and scripts, and produced flickering or no output. | **Medium.** Supports a self-contained Vulkan fallback and explicit correctness tests, not a claim that Vulkan is intrinsically poor. |
| [r/LGOLED, Jan 18 2026](https://www.reddit.com/r/LGOLED/comments/1qgjjss/finally_solved_the_24p_movies_stutterjudder_on_my/) | Playback anecdote with conflicting comments | The author used TensorRT RIFE for 24 to 30 FPS (1.25x) and 24 to 60 FPS (2.5x) on a 120 Hz OLED. The author reported no visible artifacts, while a commenter reported visible artifacts and recommended filmmaker mode or black-frame insertion. | **Medium for display cadence, low for quality.** It supports testing display-matched targets, but not "artifact-free" claims. |
| [r/StremioAddons, Jul 16 2025](https://www.reddit.com/r/StremioAddons/comments/1m143ve/does_anyone_have_a_guide_for_using_vapoursynth/) | Unanswered integration request | A user wanted VapourSynth-RIFE-NCNN-Vulkan integrated with Stremio; there was no benchmark or validated solution in the thread. | **Low.** Useful evidence that deployment remains fragmented, not evidence about quality or speed. |
| [r/LocalLLaMA, Oct 05 2025](https://www.reddit.com/r/LocalLLaMA/comments/1nykzv3/video2x_6x_opensource_upscaler_frame/) | Community release signal | Video2X 6.x was described as a C++ rewrite with Windows/Linux support, Vulkan ncnn engines, RIFE, packages/AppImage, and Docker/Podman images. No timing or quality measurements were provided. | **Medium for availability, low for performance.** Keep Video2X as a practical portable fallback, not as a benchmark winner. |
| [r/EnhancerAI, Apr 10 2024](https://www.reddit.com/r/EnhancerAI/comments/1c0eehk/gmfss_model_training_for_anime/) | Specialist-user request | An anime user wanted GMFSS Fortuna/Union at 120 FPS or 5x and reported an RTX 3080 Ti 12 GB. The claim that 32 GB VRAM is required for training was not verified. | **Low.** Motivates an anime comparison, but does not establish GMFSS quality, factor support, or VRAM requirements. |
| [r/davinciresolve, May 03 2025](https://www.reddit.com/r/davinciresolve/comments/1kdh2ya/interpolating_transparent_video_image_sequences/) | Detailed alpha-channel workflow | The author used Resolve, ProRes, Topaz Apollo, and a separate luminance render to reconstruct transparency. They reported black-edge problems when trying simpler paths. | **Medium for workflow risk.** Alpha handling needs a separate test path; this is not evidence for Flowframes. |
| [r/davinciresolve, Dec 09 2025](https://www.reddit.com/r/davinciresolve/comments/1phz6bv/solved_transparent_video_interpolation_flowframes/) | Follow-up subjective comparison | The author claimed Flowframes RIFE 4.0 Transparency handled alpha well and was fast, but also said some grid patterns distorted and some animation worked better in Topaz. | **Low-medium.** Useful case-study evidence only; no controlled comparison or universal Flowframes advantage. |
| [r/MachineLearning, Nov 15 2020](https://www.reddit.com/r/MachineLearning/comments/juv419/r_rife_15fps_to_60fps_video_frame_interpolation/) | Historical developer announcement | The RIFE author reported more than 30 FPS for 2x 720p interpolation on an RTX 2080 Ti. Comments also identified visible motion artifacts and questioned the demo construction. | **Medium for provenance, low for current speed.** Do not extrapolate this result to RIFE 4.26 or the RTX 5070 Ti. |

The later Flowframes post is the source of the transparency claim. The
earlier direct DaVinci Resolve thread does not contain that claim; it documents
a Topaz workaround instead. A search snippet that appears to merge the two
threads must therefore not be cited as proof that Flowframes solved the
earlier workflow.

### Practical conclusions from the community evidence

1. **Scene detection is essential.** Community users repeatedly report
   swooping or blended transitions when RIFE is allowed to process across a
   hard cut. The tool should detect cuts before inference, pass boundary
   frames through unchanged, and expose the detector threshold.
2. **Match the display for real-time playback, not automatically for masters.**
   24 to 30 and 24 to 60 can reduce cadence problems on 60/120 Hz displays,
   but an offline Resolve master should follow the project's delivery frame
   rate. Playback optimization and production conversion are separate goals.
3. **A downscaled 120 FPS result is not proof of full-resolution throughput.**
   The RTX 2060 report is valuable because it gives a reproducible-looking
   configuration, but its 1280x640 internal path cannot be used to promise
   1080p or 4K 120 FPS on the RTX 5070 Ti.
4. **Vulkan is a portability fallback with integration risk.** It reduces
   CUDA/TensorRT dependencies, but scattered packages, scripts, model files,
   flickering, and player-specific behavior are recurring practical issues.
   The project should ship one tested wrapper or use Video2X, not require users
   to assemble arbitrary files from several repositories.
5. **"No artifacts" is a subjective claim.** The conflicting OLED discussion
   shows why every profile needs local A/B inspection around cuts, occlusions,
   hands, text, thin lines, and animation holds. Community upvotes and
   confident wording are not visual validation.
6. **HDR remains unverified by this evidence.** The collected posts ask about
   HDR or mention tone mapping without documenting transfer functions,
   metadata preservation, scopes, or output validation. Keep HDR interpolation
   behind an explicit experimental profile.
7. **Anime deserves a specialist comparison, not an assumption.** GMFSS
   Fortuna/Union is repeatedly requested for anime, but the Reddit evidence
   does not prove that it beats RIFE 4.26 on the user's material. Benchmark
   it on line art, held frames, mouths, hands, and pans before selecting it.

These findings do not change the main recommendation: start with RIFE through
TensorRT on the RTX 5070 Ti, add scene detection, and compare the result
locally. They do change the acceptance tests. The first prototype should
include 24 to 30 and 24 to 60 playback targets, a hard-cut clip, a
downscaled-versus-full-resolution comparison, a Vulkan fallback check, and
an HDR rejection or pass/fail test.

## Why the pipeline should stay separate from concatenation

Frame interpolation and concatenation have different correctness rules:

- Concatenation can often use stream copy.
- Interpolation must decode and synthesize frames.
- Audio may be copied for FPS conversion but must be time-stretched for slow
  motion.
- Scene detection and color conversion belong to the interpolation stage.
- The final output encoder should be chosen separately.

The existing fast concatenation tool should not silently interpolate while
joining files. A future command should make the operation explicit, for
example:

```text
resolve-fps --input source.mp4 --target-fps 60 --profile fast
resolve-fps --input source.mp4 --target-fps 60 --profile quality
resolve-fps --input source.mp4 --target-fps 60 --profile anime
```

The command should preserve the original by default, use a unique partial
output, verify the result, and record the exact model/runtime configuration.

## Failure modes and recovery

### TensorRT engine failures

Symptoms include engine-build errors, unsupported operators, CUDA launch
errors, or crashes after a driver update.

Recovery order:

1. Rebuild the engine after deleting only the affected cache entry.
2. Retry with standard TensorRT instead of TensorRT-RTX.
3. Retry with ONNX Runtime CUDA.
4. Retry with NCNN/Vulkan.
5. Fall back to CPU only for a short correctness test; it is not expected to
   be practical for long high-resolution jobs.

### Out-of-memory

Reduce, in order:

1. Number of streams.
2. Ensemble and TTA.
3. Internal scale.
4. Tile size or dynamic-shape maximum.
5. Model size, using a lite variant.

Do not start multiple independent full-resolution jobs on one 16 GB GPU
unless the benchmark proves that the combined memory and scheduling are
safe.

### Visual artifacts

Check:

- Scene detection.
- Duplicate-frame policy.
- Internal scale.
- Model variant.
- TTA/ensemble.
- Source color conversion.
- Input frame ordering.
- VFR-to-CFR conversion.

If a shot remains wrong, keep the original timing or use a shot-level
fallback. A lower frame rate with correct content is better than a smoother
file with invented objects.

## Current recommendation for this project

The isolated prototype and one-minute RIFE 4.26 comparison are complete. The
next engineering step is to turn the validated path into a production tool
outside the TUI:

1. Keep the isolated Python/VapourSynth environment version-locked.
2. Use selective `RGBH` plus TensorRT FP16 with the PyTorch pixel-shuffle
   fallback as the local fast path; retain `RGBS`/FP32 as the recovery path.
3. Add a short raw-frame artifact gate before accepting any backend/precision.
4. Compare the clean RIFE 4.26 standard and heavy profiles on representative
   clips.
5. Compare one portable NCNN/Vulkan path and TensorRT-RTX if available.
6. Test 4K with scale 0.5 and explicit frame-count/duration policy.
7. Add GMFSS Fortuna only if the anime clips justify it.
8. Store benchmark results before wiring the production tool into the TUI.

The native ComfyUI node is a reasonable first correctness and memory
experiment because its official model files and adaptive batching are
available without a custom node. It should remain a benchmark harness,
however: the production architecture should still be selected from a
controlled comparison against TensorRT and `vs-rife`/`vs-mlrt`.

The likely final design is:

- `fast`: RIFE 4.26 with TensorRT FP16 and the PyTorch pixel-shuffle fallback.
- `quality`: RIFE 4.26 or heavy with the same selective FP16 path.
- `anime`: GMFSS Fortuna with the precision/backend validated separately on
  animation clips.
- `portable`: RIFE 4.26 through NCNN/Vulkan when available.
- `research`: external scripts for EDEN/LDF/other models.

This gives the user a fast everyday path, a quality path, and a recoverable
fallback without making the main tool depend on every research project.

## Sources

### Core RIFE and runtimes

- [Practical-RIFE](https://github.com/hzwer/Practical-RIFE)
- [VapourSynth-RIFE](https://github.com/HolyWu/vs-rife)
- [VapourSynth-RIFE source and model list](https://raw.githubusercontent.com/HolyWu/vs-rife/master/vsrife/__init__.py)
- [vs-mlrt](https://github.com/AmusementClub/vs-mlrt)
- [vs-mlrt runtime wrapper](https://raw.githubusercontent.com/AmusementClub/vs-mlrt/master/scripts/vsmlrt.py)
- [RIFE NCNN Vulkan](https://github.com/nihui/rife-ncnn-vulkan)
- [VapourSynth-RIFE-NCNN-Vulkan](https://github.com/styler00dollar/VapourSynth-RIFE-ncnn-Vulkan)
- [Video2X 6.x](https://github.com/k4yt3x/video2x)
- [Video2X command-line documentation](https://docs.video2x.org/running/command-line.html)
- [Torch-TensorRT documentation](https://docs.pytorch.org/TensorRT/)
- [NVIDIA TensorRT](https://developer.nvidia.com/tensorrt)
- [REAL-Video-Enhancer](https://github.com/TNTwise/REAL-Video-Enhancer)
- [REAL-Video-Enhancer backend](https://github.com/TNTwise/REAL-Video-Enhancer/tree/2.4.1/backend)

### Alternative models

- [FILM official implementation](https://github.com/google-research/frame-interpolation)
- [AMT official implementation](https://github.com/MCG-NKU/AMT)
- [IFRNet official implementation](https://github.com/ltkong218/IFRNet)
- [VFIMamba](https://github.com/MCG-NJU/VFIMamba)
- [GIMM-VFI](https://github.com/GSeanCDAT/GIMM-VFI)
- [SGM-VFI](https://github.com/MCG-NJU/SGM-VFI)
- [MoMo](https://github.com/JHLew/MoMo)
- [EDEN](https://github.com/bbldCVer/EDEN)
- [LDF-VFI](https://github.com/xypeng9903/LDF-VFI)
- [BiM-VFI](https://github.com/KAIST-VICLab/BiM-VFI)
- [HFD paper](https://openaccess.thecvf.com/content/CVPR2025/html/Hai_Hierarchical_Flow_Diffusion_for_Efficient_Frame_Interpolation_CVPR_2025_paper.html)
- [InterpAny-Clearer](https://github.com/zzh-tech/InterpAny-Clearer)
- [ComfyUI Frame Interpolation nodes](https://github.com/Fannovel16/ComfyUI-Frame-Interpolation)
- [ComfyUI core](https://github.com/Comfy-Org/ComfyUI)
- [ComfyUI native interpolation node](https://github.com/Comfy-Org/ComfyUI/blob/master/comfy_extras/nodes_frame_interpolation.py)
- [ComfyUI native interpolation model code](https://github.com/Comfy-Org/ComfyUI/tree/master/comfy_extras/frame_interpolation_models)
- [Comfy-Org frame-interpolation model package](https://huggingface.co/Comfy-Org/frame_interpolation)
- [ComfyUI RIFE TensorRT node](https://github.com/yuvraj108c/ComfyUI-Rife-Tensorrt)
- [ComfyUI RIFE TensorRT automatic setup](https://github.com/silveroxides/ComfyUI_RIFE_TensorRT_Auto)
- [GMFSS Fortuna](https://github.com/98mxr/GMFSS_Fortuna)
- [VapourSynth GMFSS Fortuna](https://github.com/HolyWu/vs-gmfss_fortuna)
- [FFmpeg `minterpolate` documentation](https://ffmpeg.org/ffmpeg-filters.html#minterpolate)
- [VFI rankings and difficult-motion benchmarks](https://github.com/AIVFI/Video-Frame-Interpolation-Rankings-and-Video-Deblurring-Rankings)

### Existing project research

- [Flowframes research](FLOWFRAMES-RESEARCH.md)
- [Fast concatenation research](FAST-CONCAT-RESEARCH.md)

### Reddit evidence

- [r/htpc: Entry point to interpolate videos in MPC-HC using RIFE](https://www.reddit.com/r/htpc/comments/1mixcc3/entry_point_to_interpolate_videos_in_mpchc_using/)
- [r/mpv: How to set up RIFE interpolation to work with MPV](https://www.reddit.com/r/mpv/comments/1p7p4bf/how_to_set_up_rife_interpolation_to_work_with_mpv/)
- [r/LGOLED: 24p playback with mpv and RIFE](https://www.reddit.com/r/LGOLED/comments/1qgjjss/finally_solved_the_24p_movies_stutterjudder_on_my/)
- [r/StremioAddons: VapourSynth-RIFE-NCNN-Vulkan setup](https://www.reddit.com/r/StremioAddons/comments/1m143ve/does_anyone_have_a_guide_for_using_vapoursynth/)
- [r/LocalLLaMA: Video2X 6.x](https://www.reddit.com/r/LocalLLaMA/comments/1nykzv3/video2x_6x_opensource_upscaler_frame/)
- [r/EnhancerAI: GMFSS model training for anime](https://www.reddit.com/r/EnhancerAI/comments/1c0eehk/gmfss_model_training_for_anime/)
- [r/davinciresolve: Transparent video and image-sequence interpolation](https://www.reddit.com/r/davinciresolve/comments/1kdh2ya/interpolating_transparent_video_image_sequences/)
- [r/davinciresolve: Flowframes and RIFE transparency follow-up](https://www.reddit.com/r/davinciresolve/comments/1phz6bv/solved_transparent_video_interpolation_flowframes/)
- [r/MachineLearning: Original RIFE 15 FPS to 60 FPS announcement](https://www.reddit.com/r/MachineLearning/comments/juv419/r_rife_15fps_to_60fps_video_frame_interpolation/)
- [r/comfyui: Native Frame Interpolate](https://www.reddit.com/r/comfyui/comments/1tpn7i9/fyi_theres_now_native_frame_interpolation_in/)
- [r/comfyui: 30 FPS to 60 FPS recommendations](https://www.reddit.com/r/comfyui/comments/1r84aes/what_do_you_use_for_frame_interpolation/)
