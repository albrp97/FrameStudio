# TICKET-080 Upscale render strategy benchmark

Status: **passed**

Generated 40-second fixtures: 1920x1080/24 landscape, 854x480/30 landscape, and 720x1280/30 portrait. Retained range is 10 seconds per source; the portrait range is triplicated side-by-side. Final policy is 1920x1080 at 60 FPS with AAC stereo.

The current editor supports constant-frame-rate 24->60 through a 3x integer RVE oversampling pass followed by exact 60 FPS GPU normalization. The original ticket-080 strategy rows below were measured before that fractional-rate fix and therefore retain their historical FFmpeg `minterpolate` measurements; the superseding real-media validation is recorded in TICKET-081 evidence.

| Strategy | Status | Total seconds | Final bytes | FPS/frames | Playable |
|---|---:|---:|---:|---:|---:|
| production_per_source_rve | passed | 546.6812 | 46705617 | 60/1800 | yes |
| concat_first_control | passed | 7.6967 | 43561775 | 60/1800 | yes |
| cut_first_control | passed | 6.2767 | 46787816 | 60/1800 | yes |
| full_source_before_cut_control | passed | 10.2189 | 45140474 | 60/1800 | yes |

## Bounded recommendation

For this workstation and generated fixture set, retain `production_per_source_rve` as the quality-oriented production candidate: SuperUltraCompact restoration ran per source before spatial preparation. This historical row took 546.6812 seconds and produced a 46,705,617-byte output; its 24 FPS source used the pre-fix FFmpeg `minterpolate` fallback and is not a measurement of the current fractional RVE route.

Controls are no-enhancement timing/integrity controls using non-RVE FPS conversion; they are not quality-equivalent to the RVE production row and must not be used for a visual-quality ranking. The repaired concat-first control now normalizes each spatially prepared source to 30 FPS, concatenates those normalized streams, then performs the 60 FPS control conversion; its measured result is 7.6967 seconds and 43,561,775 bytes. Control measurements are: 7.6967s/43561775 bytes, 6.2767s/46787816 bytes, 10.2189s/45140474 bytes.

The result is bounded to one cold run, synthetic `testsrc2`/sine fixtures, and this workstation. Contact sheets and fixed frames require human inspection. No numeric visual-quality claim is made. Production routing is not changed by this benchmark.

Artifacts are retained under the external user artifact directory recorded in the JSON; committed report paths are redacted. Contact sheets/fixed timestamps require human visual review. Failed or unavailable stages remain explicit in the machine-readable report.
