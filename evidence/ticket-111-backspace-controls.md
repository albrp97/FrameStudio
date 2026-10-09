# TICKET-111 - Backspace and Undo Controls Evidence

Parents: OBJ-001 / SCOPE-001 / PHASE-010 / FEAT-033.
Requirement: DISC-010 / REQ-010-02.
Mode: automatic under CHG-014.
Profile: `rubber-duck / gpt-5.6-luna / high / all-validation`.
Integration branch: `phase/010-synchronized-tracks`; base `330e13b`.
Worker branch: `ticket/111-backspace-controls`.

## Bounded implementation-readiness inspection

Validator `a7116924-d06a-4a74-8b7b-0b95e4e72509`, turn 0, returned
**readyForTestAuthoring**, not production-ready. Active ancestry, worktree,
current baseline and released T110/T117 prerequisites were accepted.
Dedicated executable tests must precede implementation.

The approved Undo contract is in-process and guarded by runtime identity,
revision and exact state. Public CLI removal persists its result. No
serialized or cross-process Undo is authorized.

T111 owns removal helpers and app/UI/keybindings/CLI-dispatch surfaces.
Playback adapters/backends and domain/history files are excluded. Parent
reserves CLI parser registration until T114 integration. That binding gap
must remain explicit, not become a claimed CLI PASS.

## Fail-first charter

Create `tests/test_editor_removal_controls.py` and
`tests/test_editor_removal_controls_functionality.py`.
Real generated-media GTK/X11 input must exercise Backspace removal/ripple,
Delete exclusion/restore, exact bounded Undo, visible selection/duration,
transforms/tracks, actual text-entry isolation and source preservation.
Public CLI removal must cover persisted/reopened results and explicit errors.
No product functionality or final readiness result is claimed.

## Executable charter and production authorization

The worker's actual generated-media preflight passed. Missing removal
modules, the unregistered public CLI command and physical Backspace leaving
the selected block present are intentional fail-first results. Protected
physical Delete/restore behavior passed.

Parent rejected an invented main-window filename-entry assertion. The worker
instead opened the existing native export planner, discovered its real
Filename/Output FPS entries, enabled the native custom-FPS choice, and routed
physical Backspace/Delete to that uniquely titled planner. Text-only edits
and unchanged main project/history passed in 3.154 seconds. Ruff,
formatting and compilation passed.

Validator `a7116924-d06a-4a74-8b7b-0b95e4e72509`, turn 1, returned **READY**
for bounded T111 production. The same worker is now implementing only its
reserved app/UI/removal/CLI-dispatch paths and two tests. Parent parser
registration remains an explicit integration prerequisite before public CLI
acceptance. No terminal T111 functionality PASS is claimed.

## Root integration and supported-boundary verification

Parent integrated the corrected helper/window candidate, reused the bounded
`RemovalHistory` for sequential Undo, and registered `remove` in the public
parser and editor command allowlist. Before registration, the public in-process
and subprocess removal selectors failed explicitly with `invalid_arguments`.
The first native invocation selected Wayland, so its XTest precondition failed.
The corrected `GDK_BACKEND=x11` invocation ran nine cases in 5.333 seconds with
no skips, including real keyboard/text-entry and persisted CLI behavior.

Root Mypy exposed invariant parser generics. The helper now preserves the
actual parser subtype with a bounded `TypeVar`. All configured Mypy targets
and the dependency analyzer passed. Duplication initially reported three
introduced test clones. Shared GTK-runtime and screen-coordinate helpers,
plus an exact unit result-shape assertion, removed all three without changing
the approved baseline. The final pre-preview scan found 46 clones, 1.027%,
zero introduced findings. Ruff check/format and diff checks passed.

The integrated removal/domain/drag runner first encountered a fixed-delay
paste observation failure. Standalone and shared replay passed. Copy, paste
and split now wait for their actual observable event completion using the
existing bounded event-pumping helper. A later native geometry failure showed
the viewport changing during concurrent worker GTK activity. All desktop
commands now share the session `phase010-desktop.lock`, including passive GTK
tests. Under that lease, the following runner passed 37 cases in 10.852 seconds,
with no skips:

```sh
GDK_BACKEND=x11 PYTHONWARNINGS=ignore::DeprecationWarning \
  flock SESSION/files/phase010-desktop.lock python3 -m unittest \
  tests.test_editor_removal_controls \
  tests.test_editor_removal_controls_functionality \
  tests.test_editor_ripple_removal \
  tests.test_editor_ripple_removal_functionality \
  tests.test_editor_track_drag tests.test_editor_track_drag_functionality
```

Artifacts: session `phase010-root-removal-controls-red.log`,
`phase010-root-removal-controls.log`, `phase010-root-removal-static.log`,
`phase010-root-removal-static-final.log`,
`phase010-root-removal-serialized.log`, and
`phase010-removal-preview-quality/`.

## Newly reproduced empty-timeline preview integration defect

After T120 root integration, parent authored
`NativeRemovalControlsFunctionalityTests.test_real_gtk_remove_all_clears_preview_and_undo_restores_playback`.
Physical Ctrl-click selects all four blocks, including the excluded block.
Physical Backspace removes them, but the new preview adapter raises
`Project segment timeline must contain a segment` before clearing the old
backend or recording the Undo receipt. The actual selector failed in
1.680 seconds. This is a tightly coupled T111/T120 defect, not an accepted
limitation or a product PASS. The owning T120 worker is correcting empty
attachment and stale picture state. The charter additionally requires
disabled empty playback, retained sources, and actual Undo restoration of
both blocks and playback. Artifact: session `phase010-root-empty-removal-red.log`.

All above commands are raw agent-owned technical/functionality results.
Final `automaticValidation` remains pending the exact header profile,
validator `a7116924-d06a-4a74-8b7b-0b95e4e72509`, and integrated remediation.
T111 remains open/inProgress, with no delivery or closeout claim.

## Superseding final GUI wave and bounded automatic validation

The empty adapter fix clears the stale backend/controller/picture and permits
the actual remove-all/Undo journey. That test captures its before-state after
physical multi-selection, including the resulting active track. An earlier
capture before selection incorrectly expected a different active track.

A separate actual fresh-source journey exposed a gap hidden by save/reopen
normalization: a newly imported schema-1/2 project had no canonical runtime
tracks, so Backspace rejected it. The new physical two-split/middle-removal
selector failed in 6.668 seconds. Three additional unit cases reproduced
single/multi-source and empty-result failures, while invalid input already
left the original representation unchanged.

Exact validator `a7116924-d06a-4a74-8b7b-0b95e4e72509`, turn 4, approved the
existing `_migrate_legacy_to_v4()` seam after selection/focus validation.
This preserves legacy-ripple timing, original source references and settings,
and creates the receipt in the original project's normalized runtime context.
No absolute conversion or receipt-guard bypass was introduced. Root window
selection now reads the normalized `project.timeline`, not its old timeline
reference. Unit checks cover source cuts, transforms/offsets, same-live-project
Undo, invalid-input/no-mutation, empty duration and reopen-stale receipts.
The physical fresh-source removal/Undo selector passed in 1.764 seconds.

Final executable runner: the eight-module command in session
`phase010-root-gui-wave-final.log`, comprising composed preview, removal
controls, domain ripple removal and protected track-drag modules.
Observed: **59 PASS in 43.477 seconds, zero skips**. Boundaries include actual
GTK/XTest events, raw-frame display, public CLI subprocesses and saved projects.
Full editor/test Ruff check and format passed for 135 files. All configured
Mypy targets, dependency checks, compilation and diff checks passed.
The unchanged duplication baseline contains 46 clones, 0.993%, zero introduced.
Artifacts: session `phase010-root-gui-wave-static-final.log`,
`phase010-removal-preview-quality/`,
`phase010-root-legacy-removal-unit-red.log`,
`phase010-root-fresh-legacy-removal-red.log` and
`phase010-root-fresh-legacy-removal-final.log`.

**automaticValidation:** exact header-profile validator
`a7116924-d06a-4a74-8b7b-0b95e4e72509`, turn 5, returned bounded **T111 PASS**,
with no current blocker or high-confidence introduced flaw. This supersedes
the preceding pending-validation entry. The result does not establish
T124/T125, remote CI, delivery or phase closeout. T111 is open/verifying.
