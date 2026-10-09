# TICKET-125 - Integrated Editing and Delivery Evidence

Parents: OBJ-001 / SCOPE-001 / PHASE-010 / FEAT-038.
Requirements: DISC-010 / REQ-010-01 through REQ-010-06 / CHG-013.
Mode: automatic under CHG-014.
Profile: `rubber-duck / gpt-5.6-luna / high / all-validation`.
Integration branch: `phase/010-synchronized-tracks`; base `330e13b`.

## Bounded authoring readiness and ownership

All declared prerequisites have bounded exact-profile releases. T124's final
Root release is validator `8f6c24ed-e225-4166-ad3c-198dfee6bc90`, turn 6:
nine actual CLI/media/native cases, 39 protected CLI cases, 29 coordinator/
source cases, 50 protected consumers and the complete configured static
suite. The unchanged baseline has 46 clones and zero introduced.
T126's bounded local release is separate from pending actual provider CI.

Exact validator `d3c2c166-b1dc-4485-9583-e30a348b34ba`, turn 0, returned
**READY FOR BOUNDED T125 TEST AUTHORING ONLY**. An absent integrated charter
blocks final acceptance, not its approved creation. Native GTK input, public
CLI processes and decoded video/audio must exercise one continuous journey.
Calling predecessor test methods or substituting unit proxies is not valid.

The parent prepared and verified an isolated snapshot on
`ticket/125-integrated-acceptance`. Worker ownership is only
`tests/test_phase010_functionality.py`, preserving its existing T109 and
migration charters. Parent owns shared planning/evidence, documentation,
CI, integration, final quality and delivery. All GTK execution holds the
shared X11 desktop lease. No production feature changes are assigned.

## Planned executable functionality and baseline

Entry point:
`python3 -m unittest tests.test_phase010_functionality.Phase010FunctionalityTests.test_complete_edit_and_delivery_journey`.

Exercise source inspection, physical Delete/Backspace/Undo, four-track
collision-safe arrangement, silent preview with zero through four active
clips, save/reopen and public CLI delivery. Assert Track 1 A/B and Track 2 A/C
with distinct A transforms produce four compact independent full-canvas
normal-audio reels, with an optional fifth composed final. Include mixed
FPS/resolution, absent audio, copies, Triplicate and gaps, decoded pixels/PCM,
metadata/frame counts, original hashes and truthful cancellation/resume.
Source-only must never start the final compositor.

The predecessor Root functionality/static records provide the scoped
baseline. The historical 688-case failed runner remains failed evidence,
with its two old composition expectations subsequently reconciled in the
61-case passing module. Final whole-suite verification will include the new
charter, not repeatedly replay the old baseline or infer a pass.

No T125 functionality, final quality, automatic validation, remote CI,
publication or phase-closeout PASS is claimed at this authoring stage.

## Authoring baseline and provider-charter wiring

Parent ran the exact proposed entry before authoring. It failed immediately
because the method was absent, recorded at session
`phase010-root-integrated-charter-missing-entry.log`. This proves the missing
acceptance entry only, not a failing product behavior or a functionality pass.
Worker `af5f3dad-963f-4815-b6c7-00d01eb9106a` uses GPT-5.6 Luna/max and owns
the bounded isolated test implementation.

Parent added a fail-first CI contract requiring the named integrated method,
then wired it alongside the preserved selected-video charter in the provider
workflow's real GTK execution step. All three local CI configuration guards,
focused Ruff/format and diff checks passed. Artifacts:
`phase010-root-integrated-ci-charter-red.log` and
`phase010-root-integrated-ci-charter-final.log`. These string/configuration
checks are not execution of the new method or of Ubuntu/provider CI.

Read-only publication preparation verified the remote default branch is
`main` at the same `330e13b` base and that Git transport works. No open PR
exists for the unpublished phase branch. The provider CLI is unavailable.
No commit, push, PR creation, remote run or delivery closeout occurred.

## Final Root integration and raw verification

The integration owner collected the completed worker result and applied a
scoped patch to `tests/test_phase010_functionality.py` only. Byte comparison
against the worker file, pinned Ruff/format and diff checks succeeded.
Existing metadata and migration charters remain in the module.

The exact named integrated test then executed on Root under the shared X11
desktop lease: **1 test, 46.083 seconds, OK, no skips**. Raw command:
`GDK_BACKEND=x11 .venv/bin/python -m unittest tests.test_phase010_functionality.Phase010FunctionalityTests.test_complete_edit_and_delivery_journey`
with `FRAMESTUDIO_PHASE010_ARTIFACT_DIR` pointing into session
`files/phase010-root-final-artifacts`. Log:
`files/phase010-root-integrated-final.log`.

Its 21 machine-checked outcomes cover generated mixed inputs and metadata,
native GTK split/Backspace/Undo/copy/paste/drag/Triplicate/Delete, zero through
four active intervals, silent decoded preview, final decoded pixels/stereo,
save/reopen through GUI and public CLI, four independent source reels plus
optional final, a source-only final-compositor guard, live GUI/CLI cancellation,
resume/restart and same-shaped output tampering, structured missing-tool
failure, source hashes and owned-process cleanup. JSON records, window-only
images and generated media are retained in the artifact directory rather than
published as source media.

The final configured static suite also exited zero:
`make static-analysis churn PYTHON=.venv/bin/python STATIC_ANALYSIS_DIR=<session-files>/phase010-final-quality`.
All 148 formatter inputs, Ruff, Mypy, complexity, dependency boundaries,
dependency audit and Bandit completed. Duplication remains **46 existing
clones, 0.912%, zero introduced**. The copied baseline remains byte-identical,
SHA-256 `a2bd1fc526d47a69a8c24d6c9d26a5c7870c3c22e2ca512e5159939879963d55`.
Raw log: `files/phase010-root-final-static.log`; reports:
`files/phase010-final-quality/`.

These are terminal deterministic observations submitted to validator
`d3c2c166-b1dc-4485-9583-e30a348b34ba` using
`rubber-duck / gpt-5.6-luna / high / all-validation`. Its final classification
and the full shared check/contract/smoke run are still pending at this entry.
No `userValidation`, whole-phase readiness or delivery completion is inferred.

The Root journey's machine-readable record is
`files/phase010-root-final-artifacts/phase010-ticket109-run-ztsatq_1/ticket125-integrated-evidence.json`.
Comparable application-window captures are retained durably as
`evidence/screenshots/ticket-125-before.png` and
`evidence/screenshots/ticket-125-after.png`. The after image shows the edited
project reopened, rather than merely its transient pre-save state.

## Final shared-gate failure and scoped remediation

The final Root `make check contract smoke` runner stopped at its complete
unit/functionality suite: **716 cases in 841.266 seconds, 10 failures and
1 error**. Log: `files/phase010-root-final-shared-checks.log`. Consequently
compilation, CLI-contract and smoke targets in that command did not execute.
This is failed evidence, not a final-suite pass.

Failures include stale export-choice/tool/coordinator seams, the old migration
charter's expectation that synchronized export remains unsupported, and a
native geometry baseline sampled before physical selection settled the
window's allocation. Parent reconciled migration to actual supported public
planning/export with unchanged project/source hashes and decoded
1920x1080, 10 FPS, 100-frame media: **1 test, 26.072 seconds, OK**,
`files/phase010-migration-final-consumer.log`. Native geometry remediation
preserves the original width/left-shift assertions and establishes its
baseline after selecting the target block physically.

Exact validator `d3c2c166-b1dc-4485-9583-e30a348b34ba` accepted bounded
Root functionality/static observations but identified five integrated
acceptance-proof gaps: distinct A transforms, actual dynamic slot pixels,
observed silent preview, public-subprocess source-only compositor exclusion,
and decoded combined final media. The retained T125 worker owns only its
test-file refinement. An isolated bounded export-regression worker owns four
export/performance test modules and any demonstrated CLI/export seam fix.
Parent owns removal/migration reconciliation and final integration.

All remediation retains the same
`rubber-duck / gpt-5.6-luna / high / all-validation` decision profile.
No failed gate is bypassed, no baseline is updated, and no commit,
publication or closeout is authorized by these incomplete results.

Parent's native geometry regression now passes with every original
left-shift/width/Undo assertion intact: **1 test, 1.196 seconds, OK**,
`files/phase010-removal-final-geometry.log`. Focused formatting/lint/diff
checks pass and duplication still has 46 existing clones with zero new.
The separately executed `make compile contract smoke PYTHON=.venv/bin/python`
also exits zero under the X11 lease, including **39 protected CLI cases in
21.176 seconds** and both generated-media GTK smoke flows. Log:
`files/phase010-parent-protected-final-consumers.log`.
These results do not supersede the failed 716-case suite or the pending
integrated-proof refinements; final shared verification is still required.

## Integrated-proof remediation execution

The retained T125 worker supplied a scoped 581-line refinement of the same
test file, without production edits. Parent applied it and confirmed exact
byte equality, pinned Ruff/format and diff checks. It adds direct comparisons
for distinct A framing, actual rendered slot positions, owned preview
process/audio-route observations, independent public source-only process
tracing, and decoded combined-final pixels/frames/PCM.

The strengthened exact Root entry now passes: **1 test, 50.325 seconds, OK,
no skips**, `files/phase010-root-integrated-proof-remediation.log`.
Duplication is **46 existing clones, 0.908%, zero new**, with the same
unchanged baseline, `files/phase010-root-proof-remediation-duplication.log`.
The exact Luna/high validator is reviewing the five corrections against
this executable proof. The remaining export-regression worker and final
whole-suite rerun are still pending; this entry is not phase delivery.

Exact validator `d3c2c166-b1dc-4485-9583-e30a348b34ba`, turn 5, returned
**focused five-gap proof PASS** under
`rubber-duck / gpt-5.6-luna / high / all-validation`, accepting all five
corrections against the stronger Root execution. Direct preview-frame/render
comparison and a standalone source-audio PCM baseline comparison remain
explicit non-blocking evidence improvements, not silently claimed coverage.
The validator explicitly withheld overall T125, local commit, phase and
delivery readiness because nine shared export/performance cases and the
final complete-suite result remain unresolved.

## Shared export regression integration

Worker `75d9d4e1-88bb-449f-ad99-3c1af4a56fb4` completed its six owned
paths: `framestudio/cli_export.py`, `framestudio/app_export.py`,
`tests/test_editor_performance.py`, `tests/test_editor_export_choices.py`,
`tests/test_editor_export_choices_functionality.py`, and
`tests/test_editor_source_outputs_functionality.py`.
Its four-module runner passed **27 cases in 128.724 seconds**, retained at
`files/phase010-final-export-regressions/final-owned-modules-terminal.log`.

The production correction prepares required source audio analysis before
synchronized A/V planning, using the existing cancellable analysis lock in
GTK. Test corrections preserve immutable worker snapshots and partial-result
truth, use real media for concrete planning, wait for observable plan readiness,
test supported multi-track publication instead of obsolete rejection, and
match failure injection to the coordinator's actual candidate destination.
Portable fixture-only 24 FPS FFmpeg interpolation replaces reliance on the
optional default RVE runtime; user defaults and eligibility rules are unchanged.

Parent reviewed the 84-line production patch, integrated only the six scoped
files, and ran all configured Mypy targets successfully. The full Root clone
scan caught one fixture policy duplication missed by the worker's bounded
scan. Parent extracted the shared fixture constructor without changing
assertions or baseline: **46 existing clones, 0.906%, zero new**,
`files/phase010-root-regression-duplication-fixed.log`.
The early final runner was explicitly stopped before this correction and
is not passed evidence.

The final unchanged-source canonical runner is now
`make quality contract smoke PYTHON=.venv/bin/python STATIC_ANALYSIS_DIR=<session-files>/phase010-final-quality`
under the shared X11 lease, with its full raw output at
`files/phase010-root-final-complete-quality.log`. The retained exact
`rubber-duck / gpt-5.6-luna / high / all-validation` validator owns the
production-remediation review and eventual whole-phase local decision.
No commit, push, remote check or closeout is inferred from the private result.

## Audio-planning cancellation remediation

The exact validator's narrow production review found that the new CLI
audio-analysis preparation ran before the old SIGINT handler was installed.
Parent stopped the running full suite before source edits and reproduced
real SIGINT during synchronized audio analysis: an unstructured
`KeyboardInterrupt`, **1 failure in 0.256 seconds**,
`files/phase010-cli-analysis-cancellation-red.log`.

A restoring cancellation context now spans planning and coordinated execution,
passing its event to synchronized audio preparation. Two additional real
regressions exposed the coupled legacy/source-only planning paths: **2 timeout
errors in 4.454 seconds** when cancellation was not yet forwarded,
`files/phase010-cli-other-analysis-cancellation-red.log`.
The shared event is now forwarded through those planners too. Batch source
planning delegates typed keyword options to the single-output planner, avoiding
duplicated defaults without adding a runtime dependency.

Three public-process regressions now require cancellation within two seconds,
structured `export_cancelled`/exit 5, no success stdout or destination,
unchanged source/project bytes and no surviving owned analysis child.
The complete CLI contract passes **42 cases in 23.717 seconds**, and
coordinator/source coverage passes **29 cases in 0.201 seconds**,
`files/phase010-cli-planning-cancellation-final-green.log`.
Pinned formatting/lint, all Mypy targets and unchanged-baseline duplication
pass: **46 existing clones, 0.905%, zero new**,
`files/phase010-cli-planning-cancellation-final-quality.log`.

The retained exact Luna/high validator is reviewing this scoped correction.
The final canonical runner now uses
`files/phase010-root-final-cancellation-complete-quality.log` and is expected
to discover the original 716 cases plus these three regressions. Previous
stopped runners remain nonterminal evidence; no pass, publication or closeout
is inferred from them.

## Terminal final Root technical and functionality evidence

The canonical `make quality contract smoke` runner completed with exit zero:
**719 discovered cases in 650.592 seconds, OK, no skips**, followed by
**42 CLI contract cases in 23.741 seconds, OK**, compilation, diff checks,
all configured static analysis, churn and both generated-media GTK smoke
flows. Raw complete log:
`files/phase010-root-final-cancellation-complete-quality.log`.
This is the first passing final shared suite and supersedes the historical
failed/stopped runners without erasing them.

All 148 formatter inputs, Ruff, Mypy, complexity, dependency boundaries,
pip-audit and Bandit completed successfully. The unchanged duplication
baseline still distinguishes **46 existing clones, 0.905%, zero new**.
All approved requirement groups now have executable native/public-process/
decoded-media evidence in the complete suite, including the stronger
integrated journey and the three responsive planning-cancellation cases.

Before publication, configuration-only inspection identified the missing
Ubuntu Cairo bridge required by the GTK timeline drawing callback.
The official PyGObject Ubuntu/Debian instructions explicitly install
`python3-gi-cairo`:
`https://pygobject.gnome.org/getting_started.html`.
The CI guard first failed, then the workflow added this package and verifies
`gi.require_foreign("cairo")` in both runtime environments. The strengthened
three CI guards pass and the actual local GTK/Cairo initialization succeeds.
The complete static suite reran successfully against this final diff:
`files/phase010-root-final-ci-static.log`. No production source changed
after the passing 719-case runner.

These raw terminal results are submitted to the retained validator
`d3c2c166-b1dc-4485-9583-e30a348b34ba` using
`rubber-duck / gpt-5.6-luna / high / all-validation` for the final local
decision. Actual Ubuntu/provider execution, PR creation, approvals and
delivery closeout remain distinct and unproven at this entry.

## Final automaticValidation and local review decision

Retained validator `d3c2c166-b1dc-4485-9583-e30a348b34ba`, turn 8,
returned **GO for bounded local commit and push**, with no introduced local
blocker or nonblocking finding. Profile:
`rubber-duck / gpt-5.6-luna / high / all-validation`.
Technical verification, executable functionality, automaticValidation and
final local review are terminal PASS for this phase checkpoint.

The review explicitly preserves actual provider CI, remote checks, PR,
approval, merge and lifecycle closeout as outstanding external gates.
Routine scoped staging/commit/publication is integration-owner execution
authorized by CHG-014, not a userDirectiveOverride or invented human result.
The final three Cairo CI guards and real local GTK initialization are
persisted in `files/phase010-ci-cairo-bridge-final.log`.
