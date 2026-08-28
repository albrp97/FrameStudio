# PHASE-008 Focus Controls Evidence

## Interaction contract

- **Focus hit area:** the Zoom, X, and Y `SpinButton` controls own vertical
  scroll events received over their widget bounds. The controller
  runs in GTK capture phase and returns handled, so the event cannot also move
  the timeline.
- **Scroll direction and increment:** wheel up (negative GTK delta) increases
  the focused field; wheel down decreases it. Zoom changes by `0.10x`; X and Y
  change by 10 fixed project-canvas pixels. Values are clamped to valid bounds.
- **Feedback:** every handled adjustment updates the selected segment(s),
  refreshes the preview backend, refreshes the controls, and reports the
  resulting Zoom/X/Y values in the status label.
- **Keyboard parity:** SpinButton keyboard editing remains available when a
  focus control has keyboard focus; global playhead Left/Right handling is
  bypassed for that focused widget. The key-bindings panel documents
  `Focus controls: Up / Down`.
- **Normal vs triplicate:** normal segments update their visual transform.
  Triplicate segments update the segment transform and its shared group
  transform together. Multi-selection uses the existing atomic timeline
  operation and does not share state between unrelated segment identities.
- **Timeline ownership:** scroll outside the three focus widgets retains the
  existing timeline routing: Ctrl-wheel zooms the timeline, alternate or
  horizontal wheel scrolls its viewport, and ordinary vertical wheel moves the
  playhead.

## Coordinate contract

Focus offsets are fixed 1920x1080 project-canvas pixels. For zoom `z`, valid
offsets are:

`X = ±(1920 * (z - 1) / 2)` and `Y = ±(1080 * (z - 1) / 2)`.

Therefore 2x reaches `X ±960, Y ±540`, and 4x reaches `X ±2880, Y ±1620`.
The same transform is used by normal and triplicate render branches; triplicate
X is scaled to its 640-pixel slot. Contain-scaled portrait and landscape inputs
remain letterboxed on the fixed canvas before the shared crop.

## Automated evidence

- Baseline before this work: `python3 -m unittest discover -s tests` — 260
  tests passed.
- Focused workstream: `python3 -m unittest tests.test_editor_ui_helpers
  tests.test_editor_composition tests.test_editor_cli_parity
  tests.test_editor_persistence` — 58 tests passed.
- Full regression and compile: `python3 -m unittest discover -s tests &&
  python3 -m py_compile resolve_editor.py resolve_editor/*.py tests/*.py` —
  274 tests passed; compilation passed.
- Formatting: `.venv/bin/python -m ruff format --check ...` — 10 changed focus
  files already formatted.
- Lint: `.venv/bin/python -m ruff check ...` — passed for changed focus files.
- Repository smoke: `TMPDIR="$PWD/.smoke-work" make smoke` — passed. A normal
  source smoke and a portrait triplicate CLI/reopen GTK smoke also passed using
  project-local fixtures; generated fixtures were removed.
- A generated portrait source exported with a 4x corner transform and
  triplicate enabled; FFmpeg output probe verified `1920x1080`, then the
  generated source/output were removed.
- CLI parity covers 4x out-of-range input clamping, and persistence covers 4x
  corner values plus triplicate linkage.

## Gaps and user validation

Direct physical wheel gestures and visual corner screenshots were not
automated; the GTK display was available for the repository smoke harness, but
there is no deterministic headless gesture driver in the repository. Mypy
remains blocked by a pre-existing annotation error in
`resolve_editor/ffmpeg_playback.py:82`, outside this workstream.

The later user-validation addendum records a target-workstation `PASS` for
normal and triplicate segments, direct focus scrolling, ordinary timeline
scrolling, save/reopen, and CLI/group-linkage parity. Physical wheel gestures
and visual corner screenshots were not independently automated.

## Remediation addendum — 2026-08-26

Triplicate rendering now first contain-scales and letterboxes each source onto
the project canvas, then applies the shared zoom and offset before extracting
the three columns. The X mapping accounts for the narrower 640-pixel slot, so
the configured 2x and 4x bounds can reach the corresponding canvas edges
without relying on aspect-ratio enlargement that crops portrait or landscape
inputs at 1x.

Regression coverage includes filter-graph assertions for 2x edge mapping and
the existing generated portrait triplicate export. The full 280-test suite,
30-test CLI contract suite, configured quality gates, and generated-media
smoke all passed. The later user-validation addendum records `PASS` for visual
corner placement and direct wheel interaction.

## User-validation addendum - 2026-08-26

The target-workstation handoff requested direct Zoom/X/Y adjustments at 2x and
4x, four-corner and edge placement, ordinary timeline scrolling outside the
controls, save/reopen persistence, and triplicate linkage confirmation.

**User response:** `PASS`

**Status:** passed

No separate evidence paths were supplied with the response. The human
validation gate is terminal; the historical scope and remote limitations are
unchanged.

## Superseding addendum - 2026-08-27 - TICKET-082

The earlier coordinate statement that default-zoom X and Y bounds are both
zero remains the historical contract for the normal full-canvas crop, but it
does not cover the later triplicate requirement. For an enabled triplicate
segment at `1.0x`, the shared transform now permits X offsets from `-640` to
`640` because each linked instance crops one 640-pixel output column; Y
remains `0`. Zoom `2.0x` and above retain the established fixed-canvas bounds.

Model, GTK-control, CLI-parity, persistence, filter-graph, and generated-media
regressions are recorded in
`evidence/ticket-082-triplicate-default-zoom-offset.md`. Physical preview
interaction remains a user-validation step for TICKET-082.
