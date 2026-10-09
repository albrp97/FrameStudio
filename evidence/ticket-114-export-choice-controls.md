# TICKET-114 - Output Choice Controls Evidence

Parents: OBJ-001 / SCOPE-001 / PHASE-010 / FEAT-034.
Requirement: DISC-010 / REQ-010-03 / CHG-013.
Mode: automatic under CHG-014.
Required profile: `rubber-duck / gpt-5.6-luna / high / all-validation`.
Integration branch: `phase/010-synchronized-tracks`.
Worker branch: `ticket/114-export-choices`.

## Exact-profile preimplementation decision

Validator `6a2540b0-3610-444e-b264-0f42b37bbac1`, turn 4, verified active
open phase/feature/ticket records, ancestry/index consistency, CHG-014
authorization, exact profile, disjoint ownership and the released T113
interface. It accepted supplied current focused and protected baseline
results without rerunning T113.

Decision: **readyForTestAuthoring**, not production-ready. The ticket's
future Phase010FunctionalityTests.test_export_choice_ui_cli selector does
not exist. Dedicated executable GTK/CLI tests must map defaults, all modes,
save/reopen, one through four tracks, repeated sources, empty/excluded rows,
invalid neither/empty requests, structured failures, source-only actual
rendering and combined planning before production edits are authorized.

## Isolated test-authoring scope

Worker `0cb1e118-25b8-4bc9-a303-0b2ca2aed80f` uses GPT-5.6 Luna/max in
the snapshotted `worktree-ticket114`. Only
tests/test_editor_export_choices.py and
tests/test_editor_export_choices_functionality.py are writable in this turn.
The worker must establish focused export-panel/CLI baselines, author and run
the expected failing supported-boundary charter, then return for exact-profile
readiness recheck. No production implementation or functionality PASS is
claimed.

After readiness, proposed exclusive ownership is app_export.py,
export_panel.py, cli_parser.py, cli_export.py and optionally a dedicated
app_export_choices.py helper. Application/timeline wiring, models, planners,
sessions, shared planning/evidence and other workers' tests remain excluded.
No new dependency, architecture, contract round or delivery operation is
authorized by this test-authoring dispatch.

## Narrow readiness correction

Exact validator turn 5 withheld production for native control accessibility
and enhancement eligibility visibility. Worker corrected only the two owned
test files. The main native export button opens the planner and stays
available to repair invalid choices. The native Render button is enabled
for source-only and disabled for neither. Actual FPS/upscale controls and
eligibility rows are asserted across mode changes.

The focused selector now has five passes and six expected assertion failures,
with no errors or hangs. Scoped Ruff and compilation pass. Raw log:
`files/ticket114-export-choice-red-tests-expanded.log` in session artifacts.
Exact-profile readiness reassessment is pending. Production remains withheld.

## Terminal implementation readiness and production dispatch

Validator turn 7 accepted the GTK corrections but withheld production for a
missing populated-track/empty-same-source-extra-track CLI assertion.
The corrected public `export-plan` case retains four valid pair requests,
physically removes the other track's blocks with a validated removal receipt,
omits empty identities/destinations, publishes nothing and preserves hashes.
It passed independently in 11.186 seconds. Ruff and compilation passed.
Artifact: session `files/ticket114-empty-track-correction.log`.

Validator `6a2540b0-3610-444e-b264-0f42b37bbac1`, turn 8, returned **READY**
under the exact configured profile. The same isolated worker is now
implementing only the four reserved export-control/CLI modules and its two
tests. No product functionality PASS or final delivery readiness is claimed.

## Initial integration and completion finding

Parent integrated only four owned sources and two tests. Actual native
planner controls passed two tests in 4.096 seconds. Dedicated unit/public
CLI media and protected export regressions passed 37 tests in 111.120 seconds.
Artifacts: session `files/phase010-root-export-choice-gtk.log` and
`files/phase010-root-export-choice-cli.log`.

Exact validator turn 9 identified a blocking worker-completion defect:
non-final GUI jobs compute `message`, but the success callback references
`plan`, assigned only in final-only mode. Successful source output can
therefore leave the UI stuck exporting. The same worker is fixing this and
adding actual GUI render-completion evidence, not merely planner assertions.

The configured cross-file scan also found three introduced clones: internal
export planning, a unit fixture, and the existing GTK event pump. The
unchanged baseline is retained. Artifact:
session `files/phase010-root-export-choice-static.log`.
No T114 bounded release or current whole-quality PASS is claimed.

## Corrected native completion and bounded release

The worker corrected the success callback to pass the branch-computed
message, consolidated planning and fixtures, and added an actual native
source-only six-reel render. Parent retained precise typed planning inputs.
Its first typing refinement omitted forwarded FFmpeg/ffprobe keywords and
caused an actual GUI worker failure plus Mypy errors. Those failed results
remain in `phase010-root-output-av-remediation.log` and
`phase010-root-output-av-types.log`; they are not passing evidence.

Parent corrected the explicit tool parameters and removed the heterogeneous
keyword dictionary. The remaining duplicated wait loop now delegates to the
existing Phase 010 helper, retaining this charter's 500-round default.
Final integrated runner: **18 passed in 43.952 seconds**, zero skips,
including four T114 units, three native GTK cases and eleven T123 A/V cases.
The native source-only case verifies actual six-reel completion, success
status, reset export/cancel state, enabled controls, no final video and
unchanged sources. Artifact: session
`phase010-root-output-av-remediation-final.log`.

Final configured duplication: **46 clones, 1.047%, zero new**, unchanged
baseline. All configured Mypy targets and dependency checks passed; Ruff
format/lint passed. Artifact:
session `phase010-root-output-av-static-final.log`.
The public CLI contract now documents transient `--output-mode` selection.

Exact validator `6a2540b0-3610-444e-b264-0f42b37bbac1`, turn 10, returned
**bounded PASS** under the configured profile. T114 stays open in
`verifying`. T124 recovery/cancellation and synchronized final dispatch,
whole-phase validation, remote CI and delivery are not covered by this
release. The earlier 633-test core gate remains a different snapshot.
