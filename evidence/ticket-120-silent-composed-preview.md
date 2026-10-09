# TICKET-120 - Silent Synchronized Preview Evidence

Parents: OBJ-001 / SCOPE-001 / PHASE-010 / FEAT-036.
Requirements: DISC-010 / REQ-010-05 / REQ-010-06 (preview).
Mode: automatic under CHG-014.
Profile: `rubber-duck / gpt-5.6-luna / high / all-validation`.
Integration branch: `phase/010-synchronized-tracks`; base `330e13b`.
Worker branch: `ticket/120-silent-preview`.

## Bounded implementation-readiness inspection

Validator `a7116924-d06a-4a74-8b7b-0b95e4e72509`, turn 0, returned
**readyForTestAuthoring**, not production-ready. Active ancestry, worktree,
current baseline and released T119/T117 prerequisites were accepted.
Existing typed raw-frame lifecycle and window adapter seams are usable.

The editing-only absolute path and sequential composed backend do not yet
implement synchronized layouts/gaps. This is T120 work, not existing
functionality. Reuse the approved layout/framing plan and FFmpeg lifecycle,
without a new dependency or competing playback architecture.

T120 owns FFmpeg playback and app playback/track/project adapters plus
optional dedicated composed-playback helpers. App window/UI/keybinding,
domain, layout and export/compositor files are excluded.

## Fail-first charter

Create `tests/test_editor_composed_preview.py` and
`tests/test_editor_composed_preview_functionality.py`.
Actual generated-audible-source GTK display must verify dynamic one-through-
four active framing, black gaps, isolated transforms/triplicate, global
playhead, play/pause/seek, stale-generation suppression, decoder error and
resource cleanup. Both synchronized and single-track preview must launch no
audio process/output. Record latency observations without an invented limit.
No product functionality or final readiness result is claimed.

## Corrected executable charter and production authorization

Two actual generated-fixture preflight cases passed. Parent required all
zero-through-four active counts, source-local colors and tight raster
centroids rather than white markers alone, interval boundary sides,
triplicate panels, and silence for both synchronized four-source and legacy
one-source preview. The worker corrected RGBA/BGRA texture handling and
verified a real 1920x1080 texture fallback. Ruff, formatting, compilation and
diff checks passed.

Backend/GTK/silence selectors remain intentionally red at the unsupported
absolute-project guard or missing backend. No displayed-frame PASS was
inferred from fixture or layout preflight.

Validator `a7116924-d06a-4a74-8b7b-0b95e4e72509`, turn 2, returned **READY**
for bounded production. The same worker is implementing its reserved
playback/backend and window-adapter paths in parallel with T111. App window,
UI, shared helpers, CLI, model, layout and compositor files remain excluded.
No terminal T120 preview functionality PASS is claimed.

## Temporal defects reproduced and corrected privately

Parent review found that the candidate advanced by one frame interval after
each complete per-frame decode, rather than elapsed wall time. It also
published an in-flight frame after pause. The worker reproduced both:
unit playhead 0.25 versus elapsed 0.5004 seconds, and actual GTK playhead
1.4167 versus elapsed 2.0207 seconds. The GTK pause selector observed a
post-control frame.

The corrected candidate uses a pause-accounted monotonic global clock,
skips decode-limited intermediate frames, drops paused/stale in-flight
frames, and terminates a decode cancelled immediately after registration.
Its dedicated backend/GTK runner passed 15 cases, and protected playback
passed 27. Ruff, formatting and compilation passed. Artifact: session
`ticket120-validation.log`. This is correctness evidence, not a 60-FPS
performance claim.

## Root integration findings and remaining remediation

Parent integrated the backend, three adapters and dedicated tests.
The shared 52-case runner ran in 37.497 seconds: the dedicated preview
selectors passed, but three T117 cases still asserted the earlier
editing-only/unsupported state, and two unit fixtures lacked the new
controller or complete valid media metadata. Parent updated those protected
tests to require live silent synchronized preview, including controller-based
wheel seeking. The revised adapter unit runner passed 12 cases.

Root Mypy rejected an `object` sentinel assigned to the inherited
`Popen[bytes] | None` field at `composed_playback.py:358`. The owning worker
is moving the realtime-run token to its own properly typed field, without
casts or widening the base-process type. The actual all-block Backspace
journey also reproduces an empty-timeline attachment failure. The worker owns
empty/no-included attachment, cleared stale pictures, and actual empty-load/
restore tests. Parent owns the physical Backspace/Undo seam test.

Artifacts: session `phase010-root-removal-preview.log`,
`phase010-root-removal-preview-static.log`,
`phase010-root-empty-removal-red.log`. Native and passive GTK runners must
hold the shared session desktop lease to prevent concurrent tiled windows
from changing fixture geometry.

No final T120 functionality, shared quality or `automaticValidation` result
is claimed. Exact header-profile validator
`a7116924-d06a-4a74-8b7b-0b95e4e72509` must decide after integrated remediation.

## Superseding typed/empty remediation and bounded automatic validation

The worker introduced a properly typed independent realtime-run token and
extracted the existing seek preparation into a shared base helper. The base
process type remains `Popen[bytes] | None`; no casts or widening were used.
Empty and excluded-only attachment now clears generation/frame/paintable,
backend/controller and selection state, disables controls and supports later
restoration. Its dedicated eight-unit/nine-native cases passed privately.
Parent integrated the production/tests and independently exercised physical
remove-all followed by Undo restoration.

Six introduced preview clones were removed through actual shared primitives
and fixtures. Root caught one remaining centroid-result clone that the private
focused scan missed. RGB export and RGBA preview now reuse the same point
centroid reduction, without changing stride, thresholds or crop bounds.
The actual T121 decoded-frame/export-pixel charter passed one test in
66.737 seconds. Protected playback passed 27 cases in 4.370 seconds.
An obsolete successful-drag status claiming preview was unavailable was
removed after an actual GTK regression exposed it.

Final combined GUI/functionality runner:
session `phase010-root-gui-wave-final.log`, **59 PASS in 43.477 seconds,
zero skips**. It includes actual active counts 0–4, interval boundaries,
colors/centroids, transforms/triplicate, black gaps, normal wall-clock
progression, paused/stale frame suppression, empty restore, audible source
silence, errors/resource cleanup and protected physical arrangement.
Agent-owned raw static results passed: Ruff/format for 135 files, every
configured Mypy target, dependencies, compilation, diff checks, and unchanged
duplication baseline 46 clones, 0.993%, zero introduced. Artifacts:
session `phase010-root-gui-wave-static-final.log`,
`phase010-root-preview-playback-protected.log`,
`phase010-root-centroid-protected.log`, and
`phase010-removal-preview-quality/`.

**automaticValidation:** exact header-profile validator
`a7116924-d06a-4a74-8b7b-0b95e4e72509`, turn 5, returned bounded **T120 PASS**,
with no current blocker or high-confidence introduced flaw. This supersedes
the preceding pending-validation entry. It is not a playback FPS/performance,
T124/T125, remote CI, delivery or phase-completion claim. T120 is open/verifying.

## Whole-suite compatibility reconciliation

The parent subsequently ran the complete repository suite under the shared
X11 desktop lease. It ran 688 cases in 500.008 seconds and failed with two
errors in old composition tests. One still expected synchronized playback
to be unsupported and tried to decode a placeholder fixture. The other
omitted the window status callback now exercised by empty-preview cleanup.
This whole-suite run is not a pass.

Updated only those test expectations and fixtures. Absolute attachment now
asserts the synchronized backend, source mapping, duration and unchanged
global playhead. Empty attachment uses the shared window fixture and asserts
the visible empty-state status. No production behavior changed.
`python3 -m unittest tests.test_editor_composition` passed 61 cases in
1.947 seconds. Focused Ruff, formatting and diff checks passed.
Artifacts: session `phase010-root-gui-wave-full-suite.log` and
`phase010-root-composition-parity.log`. A complete final-suite rerun remains
required after recovery integration; these focused results do not replace it.

Exact validator `a7116924-d06a-4a74-8b7b-0b95e4e72509`, turn 6, accepted
this test-only reconciliation with no new T120 defect and no weakening of
the preceding real native evidence. The unchanged duplication baseline
again passed with 46 total clones and zero introduced. The isolated
generated-media import/reopen command `make smoke` exited zero under the
shared X11 desktop lease, recorded at session
`phase010-root-gui-wave-make-smoke.log`. Broader final-suite, recovery,
integrated acceptance and remote delivery gates remain pending.
