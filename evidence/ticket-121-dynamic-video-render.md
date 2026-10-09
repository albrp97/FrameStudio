# TICKET-121 - Dynamic Video Composition Evidence

Parents: OBJ-001 / SCOPE-001 / PHASE-010 / FEAT-036.
Requirement: DISC-010 / REQ-010-05.
Branch: `phase/010-synchronized-tracks`; base `330e13b`.
Mode: automatic under CHG-014.
Required profile: `rubber-duck / gpt-5.6-luna / high / all-validation`.

## Integrated video-only consumer

The compositor consumes the approved active layout plan, probes original SAR,
uses rational cumulative output frame boundaries, performs native preparation
before final-slot framing, verifies decoded output and publishes atomically.
Audio/final A/V assembly remains owned by T123.

Initial review rejected missing source-destination protection, legal
zero-frame interval rejection, colliding sanitized asset names, inaccurate
preparation-domain labels, broad planning catches, production assertions and
lint/type/format failures. Corrected assets use hashed unique names, skip
unrepresented blocks/intervals and identify uncropped native preparation
separately from final-slot crop identities.

Parent additionally protects the immutable planned input paths even when the
live project reference changes, and includes source-stat failures in the
cleanup boundary. The augmented source-guard/cleanup regression passed in
0.037 seconds.

## Raw technical and automated functionality

Command:
`.venv/bin/python -m unittest -v tests.test_editor_video_compositor tests.test_editor_video_compositor_functionality`.
Observed: eight tests passed in 74.720 seconds. Actual FFmpeg/RVE processing
was exercised on this workstation, not inferred from mocked backend success.
Boundary: public video plan/render API, generated original media, persistence,
decoded pixel/frame verification and atomic publication.
Test ID:
`VideoCompositorFunctionalityTests.test_dynamic_sections_render_with_real_ffmpeg_and_preserve_sources`.

Assertions cover active counts zero through four, black gaps, original
SAR 16/15, portrait/landscape/square inputs, target rational rate/frame count,
slot boundaries, triplicate confinement, source hashes and included/unused
original destination rejection. A legal tiny boundary is also rendered.

Parent cross-file duplication found fixture/hash clones despite the worker's
owned-file result. Small fixture hashes now use read_bytes, the block fixture
reuses the existing layout test factory, and production hashing uses a bounded
reusable readinto buffer compatible with Python 3.10. Hash/factory equality
probes, lint/format/mypy passed. Configured duplication subsequently passed:
46 clones, 1.213%, zero new against the unchanged approved baseline.
Artifact: session `files/phase010-video-wave-duplication-final.log`.

## Pending automatic decision

Exact-profile validator `29f2718e-4d66-4e11-b137-9d5e54778e2f` is reviewing
the final integrated scope. T123 is not released by these raw results.
Combined root quality is running. No final A/V, delivery or lifecycle
completion is claimed.

## Terminal automatic validation: BLOCKED

Validator `29f2718e-4d66-4e11-b137-9d5e54778e2f` applied the exact required
profile and independently ran eight scoped tests in 79.616 seconds. Scoped
Ruff, mypy, compilation and diff checks passed. Additional instrumentation
observed four actual RVE calls, correct 29.97 interpolation/59.94 passthrough
and square-source upscale exclusion. That probe does not replace durable
functionality assertions.

The terminal decision blocks T123. A real interpolation backend can raise
ExportExecutionError outside the fallback catch, preventing verified FFmpeg
fallback. Existing visual assertions only establish black/non-black and
global mean luma, not the marker/offset/partition correctness claimed earlier
in this record. The worker must add explicit slot-local marker positions,
zoom/offset displacement, triplicate confinement/partition and boundary
ownership, plus durable enhancement/fallback route assertions. The prior
framing-coverage claim is therefore withdrawn until that evidence exists.

Error normalization for decode/publication failures was classified
non-blocking but directly coupled to the same execution boundary. The original
worker is correcting these defects after synchronizing the final parent-owned
three-file candidate, preserving the source guards and hash/fixture changes.

## Combined integration gate

The root aggregate ran 604 tests in 286.006 seconds: OK. Configured compilation,
format, lint, source typing and complexity passed. `make quality` exited 2
because three new T117 fixture clones exceeded the unchanged duplication
baseline. Later quality targets were not reached. No full quality PASS is
claimed. Artifact: session `files/phase010-integrated-consumer-wave-quality.log`.

## Integrated remediation and raw verification

The three-file corrected candidate now normalizes typed export failures at
planning/preparation/decode/publication boundaries. Failed primary
interpolation attempts verified FFmpeg minterpolate. Failed verified fallback
raises an explicit compositor error instead of reporting ordinary frame
duplication as enhancement. Regression tests cover both failure paths,
cleanup and the documented error API.

The real-media charter now records actual wrapped backend calls and asserts
29.97 interpolation, 59.94 passthrough, square-source upscale exclusion and
unused-source non-preparation. It decodes frames before/after every interval
boundary and checks white marker centroids against accepted slot/crop
geometry, triplicate panel partition and transform displacement. Parent
review corrected a mixed-unit assertion: actual decoded-frame x is compared
against expected native x scaled into the same coordinate domain.

Root command:
`.venv/bin/python -m unittest -v tests.test_editor_video_compositor tests.test_editor_video_compositor_functionality`.
Observed: fifteen tests passed in 76.213 seconds, including the actual FFmpeg
charter. Four restoration and three interpolation calls were exercised.
Three files passed Ruff lint/format; the compositor passed mypy and diff
checks passed. Artifact: session `files/phase010-root-video-remediation.log`.

The same exact-profile validator was asked to classify this corrected delta,
including marker tolerance/acceptance adequacy, before T123 release. The
earlier BLOCKED decision is retained above; no new automatic PASS is inferred
from these raw results.

## Terminal corrected automatic validation: bounded PASS

Validator `29f2718e-4d66-4e11-b137-9d5e54778e2f`, turn 1, applied the exact
required profile, independently passed fifteen tests in 74.902 seconds and
released the T121 video seam to T123. Actual FFmpeg/RVE completed without
processing fallbacks. Scoped Ruff, mypy, compilation and diff checks passed.

The decision accepted the corrected typed fallback/error boundaries, cleanup,
slot markers, rational boundary ownership, triplicate partition, enhancement
eligibility and source preservation. It observed a maximum decoded centroid
delta of 15.625 pixels. The RVE allowance of 24 pixels at 384x216 is explicitly
permissive and remains a non-blocking test-tightening concern, not an exact
pixel-framing guarantee across models/hardware.

The worker then corrected six configured fixture clones without production
changes, sharing unit mock setup and the existing layout block factory.
Parent replaced unnecessary dynamic fixture import with a normal static
import. Root fourteen unit regressions passed in 13.478 seconds and three
changed fixture modules passed Ruff. The worker's corrected actual
functionality case also passed. The full configured duplication scan now has
49 clones, 1.212%, and three introduced findings only in pending T117 fixtures.
Artifact: session `files/phase010-source-video-fixtures-corrected.log`.
Baseline/configuration are unchanged. Exact-profile fixture-delta confirmation
remains pending; no full-quality or A/V delivery readiness is claimed.

## Accepted fixture-only delta

Validator `29f2718e-4d66-4e11-b137-9d5e54778e2f`, turn 3, returned
**bounded PASS** under `gpt-5.6-luna / high / all-validation`.
Production is byte-identical to the released candidate. Unit fixture
extraction preserves semantics, and the functionality helper uses a direct
typed import. The bounded video release to T123 remains valid. No full
quality, GUI, T125 or remote-delivery decision is implied.
