# Synchronized Audio Contract

**Design ID:** DESIGN-010-122
**Parents:** DISC-010 / REQ-010-06 / PHASE-010 / FEAT-037 / TICKET-122
**Status:** bounded gain/channel law and audio implementation reviewed; released to T123
**Authorization:** CHG-014 autonomous technical preparation
**Dependency:** verified TICKET-119 active-interval interface

## Slots and sample boundaries

Use the same half-open active intervals and persistent track order as
DESIGN-010-119. Fixed pan vectors are0; -25/+25; -25/0/+25; and
-25/+25/-50/+50 for1/2/3/4 active visual slots. Silent and absent-audio video
blocks retain their visual slot and pan index without contributing mix signal.

At48 kHz, map every shared boundary tick with
`sample = (tick * 48000 + 500000) // 1000000`. Derive interval endpoints from
these cumulative boundaries, not independently rounded durations. Trim/pad
final audio to the sample corresponding to the last included video endpoint.
All-inactive intervals are silent. Preview remains silent.

## Proposed channel mapping

Normalize pan percentage to `p = percentage / 100`. Mono uses equal-power
mapping with `theta = (p + 1) * pi / 4`, left coefficient `cos(theta)` and
right coefficient `sin(theta)`. Measured directional amplitude ratios are
1.496606 for25% and2.414214 for50%.

Stereo uses balance without crossfeed. For negative pan, left gain is1 and
right gain is `1 + p`. For positive pan, left gain is `1 - p` and right gain
is1. Center keeps both channels unchanged. Actual PCM experiments measured
zero sample differences for the centered stereo mapping and no cross-channel
tone leakage.

The proposed supported surround layouts are `5.1` and `5.1(side)`. For
`5.1`, proposed downmix is:

```text
L = FL + 0.7071067812*FC + 0.5*LFE + 0.7071067812*BL
R = FR + 0.7071067812*FC + 0.5*LFE + 0.7071067812*BR
```

For `5.1(side)`, substitute SL/SR for BL/BR. Apply stereo balance after
downmix. Channel-marker experiments measured both layouts and the pre-gain row sum
2.9142135624. Unknown, conflicting and unsupported layouts fail explicitly
before final publication. Ordered two-channel L/R with absent layout preserves
existing stereo behavior. Absent/unknown layout for other channel counts and
explicitly conflicting channel-count/layout declarations are rejected.

Ready sources use their persisted `legacy-concat-v1` gain exactly once.
Pending/failed analysis blocks final composition. Absent/silent audio
contributes exact silence. Classify channels before stereo-forcing conversion.
Standalone track/source reels bypass final pan/mix and retain ordinary audio.

## Reviewed clipping and compatibility rules

Exact `rubber-duck / gpt-5.6-luna / high / all-validation` review identified
these contract conditions, resolved by revision2 real-media experiments:

1. Include linear source gain `g_i = 10 ** (gain_db / 20)` in the effective
   channel-mapping coefficients and clipping bound. Apply it exactly once.
   A downstream legacy audio filter must not apply the gain again.
2. Preserve the ordinary one-audible-source centered legacy route without
   unnecessary `amix` or limiter. For a sole panned audible source, apply only
   mapping unless safety requires attenuation. Silent visual slots alone
   must not trigger mix attenuation. Prove centered stereo/mono compatibility.
3. Record and measure both surround channel matrices, LFE contribution,
   post-gain row bounds and explicit unsupported-layout errors.

For composed/unsafe cases, the effective coefficient bound is the larger
sum of absolute effective coefficients for either output channel. The
candidate gain is1 for a safe bound at most1, otherwise `min(1, 0.90 / bound)`,
with `amix=normalize=0` and a bounded limiter where required. Compute coefficients
after the once-applied persisted source gain. Ordinary centered single-source
audio stays on its existing route without unnecessary mixing or limiting.

Measured coherent four-source stereo output with nominal0.90 protection had
PCM peak0.891 and decoded AAC peak0.906225. The0.90 value describes the
pre-encode safety domain, not a universal decoded-codec ceiling. Finalize a
delivered-AAC acceptance uses a fixture-specific peak below0.95, not a universal
codec guarantee. Positive20.5dB and negative36.4dB source-gain fixtures measured
once-applied gain, effective bounds and compatibility.

## Raw experiments and acceptance boundary

Artifacts are under session `files/design-ticket122/`: `contract-summary.json`,
`exp-20261009-audio-contract-01/` and
`exp-20261009-audio-contract-02-stereo-mixes/` and
`exp-20261009-audio-contract-03-gain-layout/`. Reports retain real FFmpeg
commands, stereo-preservation measurements, channel amplitudes, hashes,
headroom results and exact boundary samples.

The gap experiment produced96000 PCM frames over2s with exact zero PCM gap
samples. AAC gaps had small codec residual noise, not source tones. Source
hashes were unchanged. These are raw design measurements, not final-project
export functionality evidence.

Implementation must add an executable supported mixer/export-boundary test
covering1..4 active slots, mono/stereo/approved surround, distinct tones,
silent slots, positive/negative gain, changing active sets, sample boundaries,
ordinary centered compatibility, peak safety and unsupported-input atomic
failure. TICKET-123 owns final A/V assembly and its public export charter.
Exact `rubber-duck / gpt-5.6-luna / high / all-validation` review found no further
measurement blocker after the ordered-L/R missing-layout rule was normalized
in the session summary and this contract. No further design document is
required. The exact-profile119 implementation review released the shared interval API.
The exact-profile audio validator released the bounded T122 implementation,
including actual PCM tests and malformed persisted-peak rejection. Evidence:
[`ticket-122-fixed-stereo-mix.md`](../../evidence/ticket-122-fixed-stereo-mix.md).
Final-output readiness remains owned by TICKET-123 and TICKET-124.

## Implemented consumer boundary

`framestudio.audio_compositor.build_audio_plan(project, layout_plan)` produces
typed source/block/interval plans with cumulative 48 kHz sample positions.
`render_audio(project, layout_plan, destination)` verifies float32 stereo PCM
and publishes atomically. Legal intervals that round to zero samples are
omitted without shifting subsequent cumulative positions. Ready analysis
requires supported policy, matching source fingerprint, valid gain and a
finite representable peak measurement.

TICKET-123 consumes this audio seam only after the separate video release.
Standalone reels and preview audio must not be routed through this final mix.
Whole-PCM verification currently uses in-memory capture. Large-project bounded
memory or a measured resource limit is not established by the short fixtures.
