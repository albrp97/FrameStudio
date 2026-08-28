# Delivery Evidence: TICKET-077

**Ticket:** TICKET-077 - Benchmark REAL Video Enhancer Restoration on
Degraded Media  
**Objective:** OBJ-001  
**Scope:** SCOPE-001  
**Phase:** PHASE-008  
**Feature:** FEAT-027  
**Planning chain:** `OBJ-001 -> SCOPE-001 -> CAP-005/CAP-011/CAP-012 ->
PHASE-008 -> FEAT-027 -> TICKET-077`  
**Status:** verifying  
**Branch:** `ticket/phase-008-responsive-preview-media-strategy`  
**Base revision:** `93b49e8`  
**Evidence date:** 2026-08-26

## Context and boundary

This record covers the approved personal-use benchmark of FFmpeg restoration
filters and REAL Video Enhancer (RVE) on the supplied local compressed video.
The source path and private filename are intentionally omitted. No production
code, editor route, dependency manifest, export default, or model default was
changed.

Generated media is retained outside the repository at:

`~/Documents/edit/restore-benchmark-20260826/`

The directory contains the fixture, three individual 15-second windows,
canonical candidate outputs, raw RVE outputs, logs, machine-readable reports,
and contact sheets. These files are local user data and must not be committed.

## Evidence entries

### E-077-BASELINE-001 - Source preservation and source metadata

- **Timestamp:** 2026-08-26
- **Category:** baseline
- **Requirement:** The original source remains byte-for-byte unchanged after
  fixture creation and all candidate runs.
- **Command/steps:** Hash the source before fixture creation, after fixture
  creation, and after all candidate runs; inspect source metadata with
  FFprobe.
- **Expected:** Hashes remain equal; the source is approximately 924x520,
  HEVC, 24000/1001 FPS, AAC stereo at 48 kHz, and approximately 853.644
  seconds.
- **Observed:** All three source hashes are equal. The source metadata reports
  924x520 HEVC/yuv420p video, AAC stereo at 48 kHz, and 853.643750 seconds.
- **Status:** passed
- **Artifacts:** `source-metadata.json`, `source-sha256.before`,
  `source-sha256.after-fixture`, `source-sha256.after-runs`

### E-077-FIXTURE-001 - Deterministic representative fixture

- **Timestamp:** 2026-08-26
- **Category:** functionality
- **Requirement:** The benchmark uses three distinct 15-second windows with
  recorded selection data and preserved audio.
- **Command/steps:** Select windows with seed `770`; trim and concatenate them
  into one fixture; inspect the result with FFprobe.
- **Expected:** A reproducible approximately 45-second H.264/AAC fixture
  without modifying the source.
- **Observed:** Windows were `319.657-334.657`,
  `379.221-394.221`, and `760.684-775.684`. The fixture is 45.021333
  seconds, 924x520, H.264/yuv420p, AAC stereo at 48 kHz, and contains 1077
  video frames. Three individual 15-second inspection clips were also
  generated.
- **Status:** passed
- **Artifacts:** `fixture-selection.txt`, `fixture-45s.mp4`,
  `fixture-metadata.json`, `clips/window-01.mp4`,
  `clips/window-02.mp4`, `clips/window-03.mp4`

### E-077-ENVIRONMENT-001 - RVE runtime and backend selection

- **Timestamp:** 2026-08-26
- **Category:** functionality
- **Requirement:** Record the RVE revision, model, backend, device, and
  resource observations for every runnable candidate.
- **Command/steps:** Run the pinned RVE checkout at revision `2.4.1-dev16`
  on the target workstation with the PyTorch CUDA backend and inspect each
  candidate log and machine-readable record.
- **Expected:** Each runnable candidate records its model, backend, device,
  precision, timing, resource observation, and output metadata.
- **Observed:** RVE used PyTorch 2.10.0+cu128 on CUDA with float16 on an NVIDIA
  GeForce RTX 5070 Ti with approximately 16 GB VRAM. Nine candidates ran
  successfully. TensorRT was unavailable because `libtorchtrt.so` could not
  be loaded; NCNN was unavailable. RVE raw outputs were encoded with CPU
  `libx264` CRF 18 and normalized with `h264_nvenc`.
- **Status:** passedWithConcerns
- **Accepted warning:** Backend availability is workstation-specific. The
  TensorRT and NCNN paths remain untested and are not inferred to be good or
  bad.
- **Artifacts:** `rve-restoration-benchmark.json`, `logs/rve-*.log`,
  `outputs/rve-raw/`

### E-077-FFMPEG-001 - Matched FFmpeg CUDA comparison

- **Timestamp:** 2026-08-26
- **Category:** functionality
- **Requirement:** Classical candidates use a comparable 1920x1080 delivery
  profile and produce inspectable outputs or explicit failure records.
- **Command/steps:** Run each filter against the same fixture with
  `scale=1920:1080:flags=lanczos`, CFR `24000/1001`, `h264_nvenc` preset `p5`
  CQ 18, yuv420p, and AAC 192k.
- **Expected:** Every supported filter produces a playable output with
  1920x1080 video, 24000/1001 FPS, AAC stereo audio, and recorded timing and
  size.
- **Observed:** Seven candidates passed. All passing outputs contain H.264
  1920x1080/yuv420p video, 1079 frames, CFR `24000/1001`, and AAC stereo at
  48 kHz. The FFmpeg `pp=hb/vb/dr` candidate failed explicitly because this
  FFmpeg build does not provide a usable `pp` filter.
- **Status:** passedWithConcerns
- **Accepted warning:** Container duration is 45.034667 seconds for these
  outputs because the audio tail is slightly longer than the 45.003292-second
  video stream.
- **Artifacts:** `ffmpeg-restoration-benchmark-nvenc.json`,
  `outputs/ffmpeg-nvenc-*.mp4`, `logs/ffmpeg-nvenc-*.log`

#### FFmpeg results

| Candidate | Wall time | Output bytes | Output MiB |
|---|---:|---:|---:|
| Lanczos control | 4.257 s | 58,356,359 | 55.65 |
| `hqdn3d` mild | 4.161 s | 56,477,682 | 53.86 |
| `hqdn3d` strong | 4.173 s | 55,124,668 | 52.57 |
| `atadenoise` | 4.006 s | 59,565,413 | 56.81 |
| `deblock` strong | 4.088 s | 62,392,819 | 59.50 |
| cleanup (`hqdn3d` + `deblock`) | 4.326 s | 59,686,806 | 56.92 |
| cleanup + mild `unsharp` | 4.485 s | 68,243,837 | 65.08 |
| `pp=hb/vb/dr` | unavailable | no output | - |

### E-077-RVE-001 - RVE restoration and upscale candidates

- **Timestamp:** 2026-08-26
- **Category:** functionality
- **Requirement:** Every selected compatible local RVE path produces a
  playable normalized output or an explicit failure record.
- **Command/steps:** Run each selected RVE model on the same 45-second fixture
  with CUDA/PyTorch, then normalize to CFR `24000/1001`, 1920x1080 Lanczos,
  `h264_nvenc` p5 CQ 18, yuv420p, and AAC 192k.
- **Expected:** Successful candidates retain playable 1920x1080 video and
  AAC stereo audio, with model, backend, timing, resource, size, and
  metadata evidence.
- **Observed:** All nine selected RVE candidates passed playability and
  metadata checks. Each final output contains H.264 1920x1080/yuv420p video,
  CFR `24000/1001`, 1079 frames, and AAC stereo at 48 kHz. The final RVE
  container duration is 45.003292 seconds. RVE reported 1077 input frames and
  the bounded CFR normalization produced 1079 output frames; this timestamp
  and frame-count behavior is recorded as a future boundary-policy concern,
  not hidden as an exact frame-preservation result.
- **Status:** passedWithConcerns
- **Accepted warning:** RVE final sizes are not directly comparable to a
  fixed-bitrate encode. NVENC CQ responds to the restored frame complexity;
  AAC settings are the same, so the size difference is primarily video
  complexity and encoder behavior rather than a changed audio policy.
- **Artifacts:** `rve-restoration-benchmark.json`,
  `outputs/rve-*.mp4`, `outputs/rve-raw/`, `logs/rve-*.log`

#### RVE results

| Candidate | Model | Wall time | Output bytes | Output MiB | Peak GPU MB |
|---|---|---:|---:|---:|---:|
| DeH264 SuperUltraCompact | `deH264_SuperUltraCompact.safetensors` | 13.248 s | 54,554,532 | 52.03 | 1,192 |
| DeH264 RTMoSR | `1xDeH264_RTMoSR.pth` | 70.614 s | 55,977,425 | 53.38 | 2,152 |
| DeH264 SPAN | `1x_DeH264_SPAN.safetensors` | 38.777 s | 55,028,372 | 52.48 | 2,270 |
| DeH264 PLKSR | `1xDeH264_realplksr.pth` | 370.997 s | 64,016,423 | 61.05 | 1,698 |
| DnCNN | `dncnn_color_blind.pth` | 30.156 s | 58,553,463 | 55.84 | 1,324 |
| DRUNET | `drunet_color.pth` | 53.023 s | 49,305,411 | 47.02 | 1,676 |
| SCUNet | `scunet_color_real_psnr.pth` | 121.109 s | 52,136,391 | 49.72 | 1,992 |
| NAFNet deblur | `nafnet_gopro1x.pth` | 29.814 s | 75,765,961 | 72.26 | 1,502 |
| RealisticVideo upscale | `realesr-general-x4v3.pth` | 54.246 s | 64,010,391 | 61.05 | 1,414 |

### E-077-VISUAL-001 - Sampled visual comparison

- **Timestamp:** 2026-08-26
- **Category:** functionality
- **Requirement:** Separate visual observations from metadata and identify
  detail recovery, smoothing, ringing, hallucination, and stability risks.
- **Command/steps:** Inspect matched-timestamp contact sheets at 7.0, 22.0,
  and 37.0 seconds, enlarged detail sheets, a consecutive-frame sheet from
  21.0-22.0 seconds, and a boundary sheet around 15 and 30 seconds.
- **Expected:** The report identifies visible strengths and failure risks
  without treating a subjective visual result as a universal claim.
- **Observed:**
  - The Lanczos control is visibly soft but preserves the source appearance
    conservatively.
  - Mild `hqdn3d`, `atadenoise`, and `deblock` make small conservative
    changes. Strong denoise and cleanup reduce fine texture; cleanup plus
    `unsharp` restores local contrast but risks halos and amplified artifacts.
  - SuperUltraCompact is the most conservative RVE result and is close to the
    control while adding modest edge and texture definition.
  - RTMoSR gives the best balance in these samples: fine edges and repeated
    texture are more legible than the control without the visibly aggressive
    texture emphasis of PLKSR.
  - SPAN is a strong faster alternative with more local sharpness, but its
    extra edge emphasis should be checked on additional material.
  - PLKSR is the most computationally expensive and visibly emphasizes fine
    texture; it is not the safe default despite its apparent sharpness.
  - DnCNN, DRUNET, and SCUNet are useful denoise comparisons but tend toward
    smoothing rather than recovering compression detail. NAFNet deblur and
    RealisticVideo add contrast or texture but have a higher risk of changing
    content that was not present in the source.
  - No obvious geometric hallucination or catastrophic frame discontinuity
    was visible in the sampled stills and boundary sheets. Still-image
    inspection cannot prove temporal stability, so this remains a confidence
    limit.
- **Status:** passedWithConcerns
- **Accepted warning:** The source has no clean reference. These are
  three-window subjective observations, not proof that any model recovered
  ground-truth detail.
- **Artifacts:** `contact-sheets/window-01.jpg`,
  `contact-sheets/window-02.jpg`, `contact-sheets/window-03.jpg`,
  `contact-sheets/window-01-detail.jpg`,
  `contact-sheets/window-02-detail.jpg`,
  `contact-sheets/window-03-detail.jpg`,
  `contact-sheets/shortlist-window-01-large-detail.jpg`,
  `contact-sheets/shortlist-window-02-large-detail.jpg`,
  `contact-sheets/shortlist-window-03-large-detail.jpg`,
  `contact-sheets/motion-window-02-shortlist.jpg`,
  `contact-sheets/boundary-shortlist.jpg`

### E-077-TEMPORAL-001 - Frame-to-frame stability proxy

- **Timestamp:** 2026-08-26
- **Category:** functionality
- **Requirement:** Record a measurable temporal observation without
  misrepresenting it as a flicker-quality score.
- **Command/steps:** Decode each final output to 320x180 grayscale, compute
  frame-to-frame mean luminance change and its variation, and exclude frames
  around the two intentional fixture boundaries.
- **Expected:** A proxy is recorded separately from visual judgment and is not
  treated as a proof of temporal consistency.
- **Observed:** The control mean frame delta was 3.599 with standard deviation
  3.078. SuperUltraCompact was 3.548/3.116, RTMoSR 3.570/3.119, SPAN
  3.570/3.132, PLKSR 3.570/3.061, DnCNN 3.560/3.112, DRUNET 3.436/3.081,
  SCUNet 3.478/3.087, NAFNet 3.847/3.197, and RealisticVideo 3.620/3.120.
  The selected DeH264 models are close to the control on this proxy.
- **Status:** passedWithConcerns
- **Accepted warning:** Motion, camera noise, and content changes affect the
  proxy. It is not a flicker detector and does not replace longer human
  playback review.
- **Artifacts:** `temporal-motion-proxy.json`,
  `contact-sheets/motion-window-02-shortlist.jpg`

### E-077-METRICS-001 - Diagnostic similarity metrics

- **Timestamp:** 2026-08-26
- **Category:** functionality
- **Requirement:** Keep objective measurements available while distinguishing
  them from subjective quality.
- **Command/steps:** Compute full-sequence SSIM and PSNR between each final
  output and the matched Lanczos control.
- **Expected:** The report states that control-relative metrics measure change
  from the control, not restoration quality against a clean reference.
- **Observed:** Selected control-relative values were:

| Candidate | SSIM All | PSNR average |
|---|---:|---:|
| FFmpeg `atadenoise` | 0.992909 | 48.965123 dB |
| FFmpeg `deblock` strong | 0.992716 | 49.214678 dB |
| RVE SuperUltraCompact | 0.925733 | 26.657179 dB |
| RVE RTMoSR | 0.926335 | 26.787550 dB |
| RVE SPAN | 0.923120 | 26.626422 dB |
| RVE PLKSR | 0.918235 | 26.496764 dB |
| RVE DnCNN | 0.926460 | 26.724761 dB |

The lower RVE similarity is expected because the neural models alter the
upscaled image more substantially. It is not evidence that the RVE result is
worse. Full values are retained in `quality-metrics-vs-control.json`.
- **Status:** passedWithConcerns
- **Accepted warning:** No clean or high-quality reference was available, so
  PSNR/SSIM cannot rank restoration quality for this sample.
- **Artifacts:** `quality-metrics-vs-control.json`,
  `quality-metrics-vs-fixture.json`

### E-077-VERIFICATION-001 - Output integrity and playability

- **Timestamp:** 2026-08-26
- **Category:** gate
- **Requirement:** Every successful candidate is playable and has the
  declared output shape, frame rate, audio, and size evidence.
- **Command/steps:** FFprobe each successful output and run an FFmpeg decode
  check; retain failure records and avoid publishing failed output paths.
- **Expected:** Successful outputs decode and report H.264 1920x1080,
  yuv420p, CFR `24000/1001`, AAC stereo at 48 kHz, and recorded sizes.
- **Observed:** All seven NVENC FFmpeg outputs and all nine RVE outputs passed
  the output checks. The `pp=hb/vb/dr` candidate has an explicit filter
  failure and no successful output. No original source bytes changed.
- **Status:** passed
- **Artifacts:** `ffmpeg-restoration-benchmark-nvenc.json`,
  `rve-restoration-benchmark.json`, `outputs/`

### E-077-QUALITY-001 - Repository protected behavior

- **Timestamp:** 2026-08-26
- **Category:** regression
- **Requirement:** The research benchmark must not change existing editor,
  export, FPS, or legacy-script behavior.
- **Command/steps:** Run the repository contract suite and the existing
  baseline suite after the benchmark work.
- **Expected:** `make contract` passes; the existing suite is recorded
  without attributing unrelated failures to this research-only benchmark.
- **Observed:** `make contract` passed 31 tests. The full unit baseline ran
  312 tests with one pre-existing failure in
  `tests/test_editor_export_execution.py:250` for mixed enhanced export
  preparation. No production route was changed to address that unrelated
  active render-strategy failure.
- **Status:** passedWithConcerns
- **Accepted warning:** The full baseline is not fully green because of the
  pre-existing mixed enhanced export failure; this ticket did not modify the
  affected production or test code.
- **Artifacts:** `docs/planning/tickets/open/TICKET-077-benchmark-real-video-enhancer-restoration.md`,
  `make contract` output, existing test records

## Recommendation

**Quality-first recommendation: RVE DeH264 RTMoSR.** It produced the best
overall balance in the three sampled windows: more legible fine structure than
the Lanczos control, no obvious geometric hallucination in the inspected
frames, a control-near temporal proxy, 70.614 seconds for 45 seconds of
content, 55,977,425 bytes, and approximately 2.15 GB peak GPU memory.

**Practical fast fallback: RVE DeH264 SuperUltraCompact.** It completed in
13.248 seconds, used approximately 1.19 GB peak GPU memory, produced a
54,554,532-byte output, and stayed visually conservative. It is the better
candidate when throughput and low risk matter more than maximum visible
detail.

**Runner-up:** SPAN completed in 38.777 seconds and produced 55,028,372 bytes
with strong local detail, but its sharper edge treatment needs more
representative footage before selection. PLKSR is not recommended as a
default: its 370.997-second runtime is about 8.24 times the output duration
and its aggressive texture emphasis increases artifact risk. Classical
`hqdn3d`/`deblock`/`atadenoise` remain the safest no-hallucination fallback,
but they do not provide the same restoration effect.

This recommendation is bounded to this source, this three-window fixture, and
this RTX 5070 Ti/PyTorch CUDA environment. It does not authorize production
integration or a change to the editor's export defaults. A future
implementation should remain opt-in, write a new partial output, verify it,
fall back to the last verified input on failure, and add longer motion and
boundary review on representative sources.

## Readiness and open blockers

- **Passed:** source preservation, fixture creation, all 16 successful output
  integrity/playability checks, nine RVE CUDA/PyTorch runs, seven FFmpeg
  NVENC runs, contact-sheet generation, and contract tests.
- **Passed with concerns:** subjective quality review, temporal proxy, RVE
  timestamp/frame-count normalization, and the full repository baseline.
- **Blocked or unavailable:** FFmpeg `pp=hb/vb/dr`, RVE TensorRT,
  RVE NCNN, and universal quality claims without a clean reference.
- **Production readiness:** not ready. This is research evidence only; no
  restoration route or default has been enabled.
- **User validation:** pending. TICKET-077 remains `verifying` until the user
  inspects the generated media and returns a terminal response.

## User-validation handoff

**Setup:** Open
`~/Documents/edit/restore-benchmark-20260826/`. Start with
`fixture-45s.mp4`, the three files under `clips/`, the three full contact
sheets, the enlarged detail sheets, and the canonical outputs under
`outputs/`.

**Steps:**

1. Compare the Lanczos control with RTMoSR, SPAN, SuperUltraCompact, PLKSR,
   DnCNN, DRUNET, SCUNet, NAFNet, RealisticVideo, and the FFmpeg candidates at
   matching timestamps.
2. Play the control, RTMoSR, SPAN, and SuperUltraCompact through the three
   15-second windows and across the 15-second and 30-second boundaries.
3. Check fine detail, oversmoothing, ringing/halos, invented texture,
   temporal flicker, motion continuity, audio continuity, and output
   duration.
4. Confirm that the recommendation matches the visible result rather than
   only runtime or file size.

**Expected visible and external results:** Every successful output should play
at 1920x1080 with the recorded CFR/audio profile. The preferred model should
improve perceived detail without unacceptable hallucination, flicker, or
boundary artifacts. The original source must remain unchanged.

**Cleanup:** Keep the artifact directory while reviewing; afterward remove
only the generated benchmark directory if it is no longer needed. Do not
delete or modify the original source.

**Required response:**

```text
PASS: every required check succeeded; evidence: <paths or notes>
FAIL: <failed check and observed result>
BLOCKED: <missing service, data, permission, or capability>
NOT APPLICABLE: <reason and approval>
```

The ticket remains `verifying` until that response is recorded. 

### E-077-USER-VALIDATION-001 - User-confirmed manual validation

- **Timestamp:** 2026-08-28T08:06:41+02:00
- **Category:** userValidation
- **Requirement:** The generated restoration outputs, comparison artifacts,
  recommendation, and source-preservation result are manually validated.
- **Steps:** The user stated, "you can close all the tickets i manually
  validated everything and you can then /aidd-commit".
- **Observed:** The user reports that the ticket outputs and behavior were
  manually validated. This response did not identify individual artifacts or
  provide separate visual observations.
- **Status:** passed
- **Accepted warning:** The statement records user validation only; it does
  not change the documented unavailable candidates, bounded research scope,
  or delivery-policy requirements.

### E-077-READINESS-002 - User-validation response recorded

- **Timestamp:** 2026-08-28T08:06:41+02:00
- **Category:** gate
- **Requirement:** Keep the benchmark ticket open until its required
  validation and delivery gates are represented by terminal evidence.
- **Observed:** User validation is now recorded as passed from the user's
  explicit manual-validation statement. The research-only boundary and
  unavailable candidate limitations remain unchanged.
- **Status:** passedWithConcerns
- **Accepted warning:** This local evidence update does not itself create a
  commit, remote check, or pull request.

### E-077-READINESS-003 - Current delivery state after user validation

- **Timestamp:** 2026-08-28T08:06:41+02:00
- **Category:** gate
- **Requirement:** Do not close or deliver the ticket without a scoped,
  reviewed commit and the applicable delivery lifecycle.
- **Observed:** User validation is recorded as passed and the research
  artifacts remain available. The current worktree has no staged paths, the
  branch is shared across Phase 8, and no commit or remote delivery exists.
- **Status:** blocked
- **Blocker:** Commit-scope and branch prerequisites are unresolved.
