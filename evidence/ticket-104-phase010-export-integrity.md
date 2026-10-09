# TICKET-104 Bounded PHASE-010 Prerequisite Evidence

**Context:** CHG-014 / PHASE-010, prerequisite of TICKET-113 and TICKET-121.
**Scope:** executable protected export/recovery proof, not reopening or closing
the older delivery phase and not implementing synchronized composition.
**Status:** bounded local proof accepted; repeat after canonical-v4 integration.

## Real CLI and media boundary

`tests/test_editor_export_integrity_functionality.py` generates blue, green and
red video sections with distinct left/right tones, then runs the supported CLI
import, split, delete, inspect, export-plan and export commands. FFmpeg really
encodes and interpolates the retained sections. Its wrapper records commands
but delegates to the real executable.

The test asserts one grouped preparation command, `ffmpeg-minterpolate`,
1920x1080 H.264/yuv420p at 60 FPS, 60 decoded frames over one second and stereo
48 kHz AAC. Frame29 is blue and frame30 red. Source audio windows prove the
fixture contains distinct section tones. Decoded output windows prove retained
blue then red audio, channel order and more than 100-fold power separation from
both excluded green frequencies. Source/project hashes stay unchanged. Verified
publication leaves no partial output, export session or intermediate residue.

Unique fixture directories are temporary by default. Retained artifacts require
an explicit artifact-directory environment variable. No sibling repository
directory or shared fixture directory is deleted.

## Parent integration and quality

Parent integrated only the owned test, then ran:

```sh
FRAMESTUDIO_TICKET104_ARTIFACT_DIR=<session>/files/ticket104-integrated-final \
FRAMESTUDIO_PHASE010_ARTIFACT_DIR=<session>/files/phase010-ci-repair-gtk \
make quality PYTHON=.venv/bin/python \
  STATIC_ANALYSIS_DIR=<session>/files/phase010-static-ci-repair
```

Terminal result: exit0, 503 tests in156.987s, configured local quality checks
passed and zero introduced clones. The unchanged baseline has50 clones and742
duplicated lines. The introduced audio-window self-clone was extracted rather
than suppressed or added to the baseline.

Raw log: `files/phase010-integrity-quality.log`. Integrated output:
`files/ticket104-integrated-final/verified-i55jm_it/integrity-result.json`.
Expected-tone/excluded-green power ratios exceed725,000 on every reported
retained channel, above the explicit100-fold acceptance threshold.

## Automatic validation and limits

The exact `rubber-duck / gpt-5.6-luna / high / all-validation` validator accepted
the bounded local functionality proof and local review. It also reported a
repeat real integrity test (1 pass in48.043s) and eight real cancellation,
resume and restart selectors (8 passes in22.663s).

Temporal clarification: canonical TICKET-115 files were **not integrated in the
parent repository at this checkpoint**. These results cannot establish the
post-integration migration/export contract, regardless of the validator's
report wording. Repeat the affected real flows after115 integration and have
the exact validator classify that aggregate separately.

No older104 full-delivery closure, absolute compositor pass, remote CI pass,
commit, push, PR or lifecycle closeout is claimed.

## Post115 integration

Parent combined `make quality` exited0 with520 tests in188.053s, including this
real export charter and existing cancellation/resume/restart flows. The exact
`rubber-duck / gpt-5.6-luna / high / all-validation` validator independently
confirmed the specific CLI process-restart resume flow as part of16 passing
migration/functionality/recovery tests in33.447s and accepted the bounded104
post115 prerequisite. Its earlier temporal limitation is now resolved for
that local prerequisite, not for older104 full delivery or absolute rendering.
