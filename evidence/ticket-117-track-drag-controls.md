# TICKET-117 - Track Drag Controls Evidence

Parents: OBJ-001 / SCOPE-001 / PHASE-010 / FEAT-035.
Requirement: DISC-010 / REQ-010-04.
Branch: `phase/010-synchronized-tracks`; base `330e13b`.
Mode: automatic under CHG-014.
Required profile: `rubber-duck / gpt-5.6-luna / high / all-validation`.

## Integrated implementation and corrections

The GTK timeline shows stable ordered track rows, a shared playhead and
collision-safe drag placement through the existing domain operations.
Track conversion uses an explicit confirmation dialog. Absolute attachment
is editing-only until T120, with no legacy decoder/controller/audio fallback.

Parent review found endpoint-clamped drag mapping, unused row activation,
stale active-track selector presentation, invented invalid-metadata FPS
fallback and invalid-duration handling. Corrections separate unbounded drag
mapping from clamped seeking, preserve the pointer grab offset, synchronize
active rows/selector, validate metadata before attachment mutation and allow
only finite nonnegative timeline durations.

## Raw technical and automated functionality

Command:
`.venv/bin/python -m unittest -v tests.test_editor_track_drag tests.test_editor_track_drag_functionality`.
Observed: ten tests passed in 1.986 seconds, no errors or skips.
Artifact: session `files/phase010-root-track-drag.log`.
Nine owned files passed Ruff lint/format; three changed helper sources passed
mypy. Diff checks passed.

Supported boundary: production GTK window/controllers, generated FFmpeg
media and versioned project persistence. Tests include actual track lifecycle
confirmation and drag gestures, collision placement, invalid/cancelled drops,
source hashes, independent state and active-track persistence. Beyond-endpoint
drags at multiple zoom levels assert exact ticks and extended duration.
The actual functionality selector is `tests.test_editor_track_drag_functionality`.

An older worker GTK test execution remained running after its later successful
charters. The owning worker stopped only shell 1392 and its process tree,
then cleaned its specifically resolved fixture. The root aggregate quality
process was not interrupted. No production changes were made during cleanup.

## Pending automatic decision

Exact-profile validator `c15ca413-4e1d-4a85-b995-5f7d558d2505` is reviewing
the integrated scope. T111 and T120 are not released by these raw results.
The combined root quality gate is running. No full-suite, synchronized preview,
delivery or lifecycle completion is claimed.

## Terminal automatic validation: BLOCKED

Validator `c15ca413-4e1d-4a85-b995-5f7d558d2505` applied the exact required
profile and independently ran ten focused tests in 2.168 seconds, then three
GTK functionality tests in 2.099 seconds. Scoped Ruff, mypy, Bandit and diff
checks passed. It did not release T111/T120.

Introduced findings require invalid-FPS conversion atomicity, non-mutating
collision-resolved drag preview, preserved multi-selection/focus and normal
wheel seeking for editing-only absolute projects. The current gesture-signal
charter also lacks true pointer-event routing and complete acceptance
assertions for exclusion, collision chains, copy/split/transforms, unaffected
rows and the shared playhead. Direct test-module typing is outside the
configured source-only mypy scope and was classified non-blocking.

The original GTK implementation worker is remediating only its owned scope,
with fail-first regressions and expanded real functionality. Existing local
input tools were discovered, but no usable pointer-injection capability is
claimed until verified against a uniquely identified fixture window.

## Combined integration gate

`make quality` ran 604 tests in 286.006 seconds: OK.
Compilation, format (130 files), Ruff, configured source mypy and complexity
checks passed. The gate exited 2 at duplication, before later quality targets:
49 total clones, 1.279%, three introduced fixture clones. They duplicate
FakeDrawingArea/FakeGesture from the existing timeline tests and the existing
GTK event-pump helper. The same worker owns fixture reuse corrections.
Artifact: session `files/phase010-integrated-consumer-wave-quality.log`.
The approved duplication baseline remains unchanged. This is not a full
quality PASS, and subsequent remediation requires rerunning affected checks.

## Integrated remediation and native failure diagnosis

The isolated candidate corrected FPS-conversion atomicity, first-fit ghost
placement, selection/focus preservation and controller-free wheel seeking.
Root initially ran seventeen tests in 2.711 seconds with one genuine
Wayland/X11 capability skip. Three fixture clones were resolved, but the
configured cross-file scan found two new production scroll-handler clones.

The original worker then failed with a provider HTTP 400 internal-server
error. Parent continued the remaining narrow correction directly, without
launching a replacement worker or copying frozen model/playback files.

Parent verified existing user-writable uinput and started a private attached
input helper without installation, elevated access or permission changes.
Actual fixture-only GTK events observed Control mask 4, yet multi-selection
was lost. This supersedes the claimed modifier-tooling blocker: drag-begin
and click-press both mutated selection, toggling the newly selected clip
twice. The exact validator's turn 1 retained BLOCKED and also identified
zero-motion drop dispatch.

## Native gesture and shared-scroll corrections

Regression selector:
`tests.test_editor_track_drag.EditorTrackDragTests.test_native_drag_begin_before_ctrl_press_does_not_toggle_selection_twice`.
It first failed because the newly selected clip was missing. Absolute
drag-begin now handles geometry only, leaving selection to click-press;
modifier resampling remains confined to legacy seek behavior.

The extended regression then failed because a zero-motion click dispatched
`('occupied', 3000000, 'track-2')`. Segment drop now requires the committed
movement threshold, preserving the deferred normal-click selection route
without move/status/history effects.

The native charter now checks received modifier state separately from
selection assertions. It no longer skips a product selection failure after
Control is delivered. Plain-click collapse and split-target selection also
assert behavior instead of presenting failure as unavailable input.

Shared modifier/zoom/viewport handling is extracted into
`app_helpers.route_timeline_scroll`, consumed by legacy and absolute
adapters. Legacy controller requirements and absolute project-playhead/
zero-duration handling remain unchanged.

## Raw corrected functionality and technical evidence

Command:
`GDK_BACKEND=x11 .venv/bin/python -m unittest -v tests.test_editor_track_drag tests.test_editor_timeline tests.test_editor_ui_helpers tests.test_editor_composition tests.test_editor_track_drag_functionality`.
Observed: **116 passed in 8.280 seconds, zero skips/errors**.
Artifact: session `files/phase010-root-track-remediation-final.log`.

The complete physical-pointer selector exercises collision chains including
exclusions, resolved ghost geometry, native Ctrl multi-selection, preserved
drop selection, copy/paste/split, invalid drops, unaffected rows, transforms,
shared playhead, save/reopen and original hashes. Pure XTest passed without
the private input helper. Parent stopped its helper and removed only the
owned socket. No new runtime dependency is required by the corrected charter.

Ruff format/lint and diff checks passed. Command:
`make PYTHON=.venv/bin/python STATIC_ANALYSIS_DIR=<session>/files/phase010-track-remediation-quality duplication dependency-check type-check`.
Observed: **46 clones, 1.103%, zero introduced findings**, no dependency
cycles and configured typing success for all 63 implementation sources plus
entrypoints, benchmarks and tools.
Artifact: session `files/phase010-root-track-shared-checks.log`.
Baseline SHA-256 remains
`a2bd1fc526d47a69a8c24d6c9d26a5c7870c3c22e2ca512e5159939879963d55`.

Exact `rubber-duck / gpt-5.6-luna / high / all-validation` classification of
this final corrected delta is pending. T111/T120 remain held until that
decision. No full-quality, remote or lifecycle completion is claimed.

## Terminal corrected bounded automatic validation: PASS

Validator `c15ca413-4e1d-4a85-b995-5f7d558d2505`, turn 2, classified the final
corrected scope **PASS** under the exact configured profile and released the
T117 prerequisite to T111/T120. No remaining scoped blocker was identified.
The authoritative raw 116-test command includes all five modules listed
above, not only the two T117 modules abbreviated in the validator response.
The actual raw log has zero skips/errors.

This is a consumer-interface release, not completion of either dependent
ticket, the phase, full quality or remote delivery. T117 remains open and
verifying.

## Terminal core prerequisite-wave gate

Before T114 integration, parent ran:
`GDK_BACKEND=x11 make PYTHON=.venv/bin/python STATIC_ANALYSIS_DIR=<session>/files/phase010-track-remediation-quality quality`.
Observed: **exit 0**, **633 tests passed in 336.365 seconds**, zero skips.
Formatting/lint, compilation, configured typing, complexity, unchanged-
baseline duplication (46 clones, 1.103%, zero new), dependencies, audit,
Bandit and churn completed successfully.

Artifact: session `files/phase010-core-wave-final-quality.log`.
Reports were archived under `files/core-wave-verified-quality` before later
consumer checks overwrote their working report directory.

Validator `c15ca413-4e1d-4a85-b995-5f7d558d2505`, turn 3, returned
**bounded core-wave PASS** under the exact profile. The snapshot includes
T110/T112/T113/T115/T116/T117/T118/T119/T121/T122/T126. It does not cover
subsequently integrated T114 or private T111/T120/T123, remote checks or
phase completion.
