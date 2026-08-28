# Fast Video Concatenation Research

Date: 2026-08-19

This report evaluates the fastest ways to concatenate the videos in
`~/Documents/edit/copy` while preserving the current output policy:

- MP4 container with `+faststart`
- H.264 High, 8-bit `yuv420p`, BT.709
- Lowest input frame rate and most common resolution
- AAC-LC, 48 kHz, stereo, 192 kb/s
- Per-input audio gain targeting mean RMS `-35 dBFS` and median absolute
  sample level `-50 dBFS`, with an estimated `-1 dBFS` peak cap

This document records the research, experiments, implementation change, and
the full six-file validation run.

## Executive conclusion

LosslessCut is much faster because its merge path does not decode, filter, or
encode. It uses FFmpeg's concat demuxer with stream copy, so it mostly reads
packets and rewrites the container. That is the fastest possible method, but
only when every input already has compatible encoded stream parameters.

The current six inputs are not eligible for that path:

- Five use `30000/1001` fps and one uses `30/1`.
- Video profiles are a mixture of H.264 Main and High.
- Audio bitrates differ, including one approximately 64 kb/s track and tracks
  around 256 kb/s.
- The requested per-file gain normalization requires decoding and re-encoding
  audio regardless of video compatibility.

For the complete requested output, the fastest tested design was:

1. Normalize each input independently to identical H.264/AAC parameters.
2. Run those independent jobs concurrently.
3. Join the normalized parts with FFmpeg concat demuxer and `-c copy`.

On this machine, three concurrent NVIDIA jobs were the best point in the
sample benchmark. The full six-file run confirmed the direction: the new
parallel path took 179 seconds, versus 263 seconds for the current
single-process path with identical normalization settings.

The older retained one-pass file was created under different runtime
conditions and is byte-identical to the current single-process result, but
its historical 117-second wall time is not a controlled comparison. The
current strategy comparison is therefore the 179-second parallel run versus
the 263-second single-process rerun.

## Local benchmark results

### Test material

Short samples were created from the actual six source files. The test clips
were approximately 8-12 seconds each and were written under `/tmp`; the
original media was not modified. The normalized target was 1920x1080 at
`30000/1001` fps, H.264 High, `yuv420p`, BT.709, AAC-LC 48 kHz stereo at
192 kb/s.

### Architecture comparison

| Method | Sample | Elapsed | Result |
| --- | ---: | ---: | --- |
| Compatible stream copy through `framestudio concat` | 3 compatible parts, about 40 s | 0.26 s | Valid and lossless |
| Direct mixed-input `ffmpeg -c copy` | 2 incompatible parts, about 24 s | completed quickly | Invalid timing: reported duration about 4.3 hours |
| Current single-process GPU concat filter | 2 mixed parts, about 24 s | 4.09 s | Valid target output |
| Current single-process CPU `libx264` path | 2 mixed parts, about 24 s | 11.86 s | Valid target output |
| Per-file GPU normalization, sequential, then copy join | 2 mixed parts, about 24 s | 3.60 s | Valid target output |
| Per-file GPU normalization, parallel, then copy join | 2 mixed parts, about 24 s | 2.10 s | Valid target output |

The direct mixed-input copy result is important: the command can appear to
finish successfully while producing unusable timestamps. Speed alone is not a
valid concatenation strategy.

### Parallelism benchmark

The six short samples were normalized independently with NVIDIA H.264 and
then joined by stream copy:

| Concurrent jobs | Elapsed | Approximate speed for 48.6 s output |
| ---: | ---: | ---: |
| 1 | 7.71 s | 6.3x real time |
| 2 | 4.57 s | 10.6x |
| 3 | 4.16 s | 11.7x |
| 4 | 4.19 s | 11.6x |

Three jobs were the fastest in this run. Four did not improve the result, so
the tool should use a bounded default rather than launching one process per
file.

### Full six-file validation run

The real inputs in `/home/ghiki/Documents/edit/copy` were processed without
modifying the originals. The run used GPU NVENC `p6/CQ 19`, three workers,
per-file audio gain analysis, and the final concat-demuxer stream-copy join.

| Strategy | Elapsed | Output size | Output duration |
| --- | ---: | ---: | ---: |
| Current single filter graph | 263 s | 3,319,908,730 bytes | 2189.787600 s |
| Parallel parts + copy join | 179 s | 3,316,313,714 bytes | 2189.307979 s |

The parallel design was 84 seconds faster, or approximately 32% lower wall
time, for this batch. Its output remained H.264 High, 1920x1080,
`30000/1001`, `yuv420p`, AAC-LC, 48 kHz stereo, and 192 kb/s. The small
duration difference is from ending each normalized part at its shortest
decoded stream before the copy join, which prevents cumulative encoder padding
between parts. The final MP4 was decoded through FFmpeg without errors.

The produced files are:

- `/home/ghiki/Documents/edit/copy-concatenated-29.97fps-parallel.mp4`
  - New parallel result.
- `/home/ghiki/Documents/edit/copy-concatenated-29.97fps-onepass.mp4`
  - Preserved one-pass baseline.
- `/home/ghiki/Documents/edit/copy-concatenated-29.97fps-single-current.mp4`
  - Controlled single-strategy comparison; byte-identical to the preserved
    baseline.

The exact worker count can be reproduced with `--jobs 3`. The default
automatic policy caps normalization at three workers on this machine.

### Hardware decode experiment

For a 12-second 1080p sample with the required frame-rate filter:

| Decode path | Elapsed |
| --- | ---: |
| Normal software decode, NVIDIA encode | 1.93 s |
| CUDA decode, download for `fps`, upload for NVIDIA encode | 2.20 s |

The CUDA path was slower because the required `fps` processing moved frames
back to system memory and then uploaded them again. The current FFmpeg build
does not provide a complete hardware-only filter path that avoids this
transfer for the required normalization. GPU decoding should not be added
automatically without another benchmark showing a benefit.

### NVENC preset experiment

One short 1080p sample was encoded with the same H.264 NVENC constant-quality
settings:

| Preset | Elapsed | Output size |
| --- | ---: | ---: |
| `p1` | 1.09 s | 18.65 MB |
| `p3` | 0.88 s | 17.14 MB |
| `p5` | 1.56 s | 13.79 MB |
| `p6` | 1.60 s | 14.02 MB |
| `p7` | 1.81 s | 14.00 MB |

These are short single-run measurements and the `p3` timing is affected by
startup variance. `p1` is the raw-speed choice, but it produced a substantially
larger file. `p6` is a reasonable default for the requested balance of speed,
quality, and size; `p1` could be exposed as an explicit maximum-speed option.

The CPU x264 sample was smaller than the NVENC sample at the tested quality
settings, which is consistent with x264's better compression efficiency. It
was also materially slower. This is the expected quality/size versus speed
tradeoff, not a concatenation-tool inefficiency.

## Why LosslessCut is so fast

LosslessCut's merge operation builds an FFmpeg concat-demuxer command and
uses stream-copy flags for the streams. It does not run a video filter,
change frame rate, scale frames, normalize colors, or adjust audio gain.
Therefore the expensive operations are absent.

FFmpeg documents the same limitation: concat-demuxer inputs must have the
same streams, codecs, and time bases. LosslessCut is the right tool when the
clips already came from the same encoding pipeline and need only joining.
It is not a substitute for the requested normalization.

## Online method comparison

| Method | No re-encode | Change fps/resolution | Per-clip gain | Fit for this tool |
| --- | --- | --- | --- | --- |
| LosslessCut merge | Yes, when compatible | No | No | Fastest compatible-only path |
| FFmpeg concat demuxer with `-c copy` | Yes, when compatible | No | No | Final join for normalized parts |
| FFmpeg concat filter | No | Yes, before the concat node | Yes | Correct, but one serial encode |
| GPAC/MP4Box `-cat` or `flist` | Usually packet/sample copy | No | No | No advantage over FFmpeg here |
| `mkvmerge` | Packet copy | No | No | Fast, but produces Matroska rather than MP4 |
| GStreamer `concat` | Only when caps already match | Yes with decode/convert/encode | Yes | Flexible, no measured speed advantage |
| Hardware decode plus CPU filters | No | Yes | Yes | Not faster in the local test |
| Per-file parallel normalize then demuxer copy | Final join is copy | Yes | Yes | Fastest complete design tested |

The fastest tools do not have a secret faster renderer. They avoid rendering.
Once frame-rate conversion, scaling, audio gain, and a common codec profile
are required, decoding and encoding work is unavoidable.

## Implemented design

The implemented performance change is architectural rather than another
filter tweak:

1. Keep the existing probe and audio-analysis stage.
2. Create one temporary normalized MP4 per input.
3. Run a bounded number of independent normalization jobs. Use three as the
   default on this six-core/12-thread system, with an override for testing.
4. Use the existing universal output settings for every part:
   H.264 High/yuv420p/BT.709, target fps and resolution, AAC-LC 48 kHz stereo
   192 kb/s, and the calculated per-clip gain.
5. After every part succeeds, run one concat-demuxer `-c copy` pass to create
   the final MP4.
6. Atomically rename the final file only after the copy join succeeds.
7. Remove temporary parts on both success and failure.

This keeps the final join nearly free while allowing the expensive work to
use multiple GPU encode sessions. It also gives clearer per-file failure
reporting and makes retries cheaper. The older single-process graph remains
selectable with `--strategy single` and is retained as a fallback.

A strict compatible-input stream-copy mode remains available for users who
explicitly do not want normalization.

## Methods not recommended

- Do not use direct `-c copy` on mixed inputs just because it finishes quickly;
  the local test produced invalid duration/timestamps.
- Do not switch to MP4Box or `mkvmerge` expecting a faster normalized output.
  They are remux/join tools and cannot perform the required transforms.
- Do not add CUDA decode by default to the current graph. The local
  download/filter/upload path was slower.
- Do not launch six or more concurrent GPU encoders by default. Four was
  already slightly slower than three.
- Do not use `libx264` when minimum elapsed time is the priority. Keep it as an
  explicit quality/size mode.

## Reproduction commands

The core fast join used for compatible parts is:

```sh
ffmpeg -hide_banner -loglevel error -y \
  -f concat -safe 0 -i normalized-parts.txt \
  -map 0:v:0 -map 0:a:0 \
  -c copy -movflags +faststart output.mp4
```

The important distinction is that every file in `normalized-parts.txt` must
already have identical target stream parameters. The command is a join, not a
normalizer.

The implemented automated path is:

```sh
framestudio concat ~/Documents/edit/copy \
  --output ~/Documents/edit/copy-concatenated-29.97fps-parallel.mp4 \
  --force --jobs 3
```

For a controlled single-process comparison:

```sh
framestudio concat ~/Documents/edit/copy \
  --output ~/Documents/edit/copy-concatenated-29.97fps-single-current.mp4 \
  --force --strategy single
```

## Sources

- FFmpeg Concatenate guide:
  <https://trac.ffmpeg.org/wiki/Concatenate>
- FFmpeg concat demuxer documentation:
  <https://ffmpeg.org/ffmpeg-formats.html#concat-1>
- FFmpeg concat filter documentation:
  <https://ffmpeg.org/ffmpeg-filters.html#concat>
- LosslessCut merge implementation:
  <https://github.com/mifi/lossless-cut/blob/master/src/renderer/src/hooks/useFfmpegOperations.ts>
- LosslessCut project:
  <https://github.com/mifi/lossless-cut>
- GPAC MP4Box import and concatenation:
  <https://wiki.gpac.io/MP4Box/mp4box-import-opts/>
- GPAC MP4Box workflow:
  <https://wiki.gpac.io/Howtos/gpac-mp4box/>
- GPAC `flist` filter:
  <https://wiki.gpac.io/Filters/flist/>
- MKVToolNix `mkvmerge` documentation:
  <https://mkvtoolnix.download/doc/mkvmerge.html>
- GStreamer `concat` element:
  <https://gstreamer.freedesktop.org/documentation/coreelements/concat.html>
- FFmpeg hardware acceleration overview:
  <https://trac.ffmpeg.org/wiki/HWAccelIntro>
- FFmpeg audio volume and normalization:
  <https://trac.ffmpeg.org/wiki/AudioVolume>
- `ffmpeg-normalize`:
  <https://github.com/slhck/ffmpeg-normalize>
