# Video Restoration Strategies Survey

**Research phase:** PHASE-008 / FEAT-027
**Tickets:** TICKET-073, TICKET-074, TICKET-075
**Evidence:** `evidence/phase-008-restoration-research.md`
**Status:** research-complete; no production code added
**Last updated:** 2026-08-26

## Purpose and boundary

This report surveys spatial upscaling, denoising, deblocking, deblurring, and
low-bitrate artifact recovery for future planning. Quality and performance
figures are marked as paper or vendor claims unless explicitly identified as
locally measured. No model, weight, dependency, download, or production route
was added in PHASE-008.

## Artifact classes

| Artifact | Typical cause |
|---|---|
| Blocking and ringing | Low-bitrate H.264/H.265 or older MPEG encodes |
| Chroma bleed | Lossy 4:2:0 subsampling and aggressive compression |
| Sensor or Gaussian noise | High ISO, analog capture, or additive noise |
| Temporal noise and flicker | Independent frame noise or unstable processing |
| Motion blur | Exposure, subject motion, or rolling shutter |
| Spatial softness | Downscale/upscale transcodes or optical limitations |
| Combined low-bitrate damage | Multiple compression, noise, and blur stages |

## Candidate matrix

| ID | Candidate | Target | Temporal behavior | Hallucination risk | License | Runtime/resources | Fit |
|---|---|---|---|---|---|---|---|
| C01 | FFmpeg `hqdn3d` | Spatial and temporal noise | Tunable temporal averaging; can trail fast motion | None; can erase detail | LGPL-2.1+ | FFmpeg CPU, no model | Immediate conservative baseline |
| C02 | FFmpeg `nlmeans` | Gaussian and mild noise | Frame-independent | None; can over-smooth | LGPL-2.1+ | CPU and very slow at 1080p | Short clips only; deprioritized |
| C03 | FFmpeg `atadenoise` | Temporal noise and flicker | Adaptive temporal thresholds | None | LGPL-2.1+ | FFmpeg CPU | Immediate comparison candidate |
| C04 | FFmpeg `deblock` | DCT block boundaries | Frame-independent | None; can soften edges | LGPL-2.1+ | FFmpeg CPU | Immediate blocking candidate |
| C05 | FFmpeg `pp=hb/vb/dr` | Blocking and ringing | Frame-independent | None | LGPL-2.1+ | FFmpeg/libpostproc CPU | Useful legacy/low-bitrate candidate |
| C06 | FFmpeg `unsharp` | Mild softness after cleanup | Frame-independent; can amplify noise | None; amplifies existing artifacts | LGPL-2.1+ | FFmpeg CPU | Final-stage comparison only |
| C07 | FFmpeg `scale=lanczos` | Classical spatial resize | Deterministic | None | LGPL-2.1+ | FFmpeg CPU | Upscaling control |
| C08 | Real-ESRGAN x4plus | Combined real-world degradation | Per-frame flicker risk | High; GAN texture is invented | BSD-3-Clause | PyTorch/NCNN; about 63 MB weights; 4-8 GB VRAM claimed | Not a video default without temporal wrapper |
| C09 | Real-ESRGAN animevideov3 | Anime restoration | Per-frame flicker risk | Moderate | BSD-3-Clause | PyTorch/NCNN; about 4 MB weights claimed | Anime-only; exclude natural footage |
| C10 | RealBasicVSR | Real-world video degradation | Recurrent temporal propagation | Moderate; GAN-trained | Apache-2.0 | PyTorch plus mmcv/mmagic; about 5.3 MB weights claimed | Best open-license temporal AI candidate; install blocked |
| C11 | BasicVSR++ | SR, deblur, denoise, compression | Bidirectional propagation | Lower on pixel-loss tasks; not zero | Apache-2.0 | PyTorch plus mmcv/mmagic; about 14 MB per task claimed | Strong x1 restoration candidate; install blocked |
| C12 | VRT | SR, deblur, denoise, interpolation | Multi-frame attention | Moderate | CC-BY-NC-4.0 | Large checkpoints; high VRAM claimed | Exclude: non-commercial license |
| C13 | RVRT | SR, deblur, denoise | Recurrent attention | Moderate | CC-BY-NC-4.0 | Large checkpoints; GPU required | Exclude: non-commercial license |
| C14 | Real-CUGAN | Anime blur and compression | Per-frame flicker risk | Moderate on live action | MIT | PyTorch/NCNN; about 5-30 MB claimed | Exclude natural live action; wrong domain |
| C15 | FastDVDnet | Known Gaussian noise | Five-frame temporal fusion | Low; may over-smooth | MIT | PyTorch/CUDA; about 5 MB claimed | Narrow case; codec artifacts do not match AWGN |

### Interpretation

- Classical filters are immediately available, deterministic, and the safe
  fallback. `hqdn3d`, `atadenoise`, `deblock`, `pp`, and Lanczos are the
  primary no-install candidates.
- RealBasicVSR and BasicVSR++ are the strongest open-license temporal AI
  candidates, but their mmcv/mmagic environment and weight installation need a
  separate approved decision.
- Frame-independent GAN models can invent plausible texture and flicker across
  frames. They must not become a video default without a measured temporal
  consistency strategy.
- VRT and RVRT are excluded because CC-BY-NC-4.0 is incompatible with the
  project's distribution boundary. Real-CUGAN is anime-focused, and
  FastDVDnet expects known Gaussian noise rather than structured codec damage.

## Bounded TICKET-074 benchmark set

The immediately runnable set uses only the existing FFmpeg binary:

1. no-filter re-encode control;
2. conservative and aggressive `hqdn3d`;
3. `atadenoise`;
4. strong `deblock`;
5. `pp=hb/vb/dr`;
6. `deblock` followed by mild `unsharp`;
7. Lanczos 2x;
8. combined denoise, deblock, and mild sharpening.

Use the same source, duration, encode profile, and audio handling for each
candidate. Report wall time, output size, playability, duration, frame count,
resolution, audio, and resource observations. Keep visual observations
separate from metadata and runtime results. A representative degraded clip
was not selected or approved during this phase, so these commands remain
available benchmark procedures rather than completed quality measurements.

The conditional AI set is Real-ESRGAN x4plus, RealBasicVSR, and BasicVSR++
task checkpoints. All are explicitly **unavailable** in this phase because
weights and runtimes were not installed. No model benchmark result is inferred
from paper or upstream claims.

Suggested degradation classes for a future approved run:

| Class | Controlled input |
|---|---|
| Heavy compression | Re-encode at high CRF and low bitrate |
| Gaussian noise | FFmpeg `noise` filter with documented seed/settings |
| Blur plus noise | Mild blur followed by controlled noise |
| Natural footage | Unmodified representative source |

Where a clean reference exists, compare PSNR/SSIM separately from a visual
rubric. For every video candidate inspect motion continuity, temporal flicker,
ringing, hallucinated detail, faces/text, and boundary behavior.

## Future pipeline recommendation

This is a non-binding research recommendation, not production approval:

```text
read-only source
  -> source-safety gate
  -> optional classical pre-restoration
  -> smart render / stream-copy decision
  -> optional gated AI restoration
  -> FPS enhancement
  -> delivery encode
  -> output verification
  -> atomic publish and cleanup
```

Any restoration stage must write to a new partial path, preserve the source,
verify duration/frame count/resolution/playability, clean up on failure or
cancellation, and fall back to the last verified unrestored input. A future AI
stage additionally needs a pinned runtime and weights, an approved license for
both code and weights, VRAM headroom with FPS enhancement, explicit opt-in,
and a measured temporal-stability gate.

The smallest safe future implementation unit is an optional FFmpeg
classical pre-restoration batch step using conservative `hqdn3d` and
`deblock`, isolated from the editor until its quality and cost are measured.
AI integration remains deferred until representative footage, installation,
VRAM, temporal, licensing, and architecture decisions are separately approved.

## Explicit non-recommendations

- Do not make frame-independent Real-ESRGAN or Real-CUGAN the natural-video
  default.
- Do not use VRT or RVRT under their current non-commercial license.
- Do not use FastDVDnet as a general codec-artifact denoiser.
- Do not use aggressive `nlmeans` for ordinary 1080p video without evidence of
  acceptable throughput.
- Do not apply sharpening before denoising/deblocking.
- Do not describe AI-created texture as recovered ground truth.

## Sources

| Reference | URL |
|---|---|
| FFmpeg filters | https://ffmpeg.org/ffmpeg-filters.html |
| Real-ESRGAN paper | https://arxiv.org/abs/2107.10833 |
| Real-ESRGAN project/license | https://github.com/xinntao/Real-ESRGAN |
| RealBasicVSR paper/project | https://arxiv.org/abs/2111.12704 and https://github.com/ckkelvinchan/RealBasicVSR |
| BasicVSR++ paper/project | https://arxiv.org/abs/2104.13371 and https://github.com/ckkelvinchan/BasicVSR_PlusPlus |
| VRT paper/project/license | https://arxiv.org/abs/2201.12288 and https://github.com/JingyunLiang/VRT |
| RVRT paper/project/license | https://arxiv.org/abs/2206.02146 and https://github.com/JingyunLiang/RVRT |
| Real-CUGAN project/license | https://github.com/bilibili/ailab/tree/main/Real-CUGAN |
| NCNN Real-CUGAN port | https://github.com/nihui/realcugan-ncnn-vulkan |
| FastDVDnet project/license | https://github.com/m-tassano/fastdvdnet |
| Existing FPS evidence | `FPS-ENHANCEMENT-RESEARCH.md` |
