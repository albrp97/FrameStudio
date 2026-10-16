# TICKET-124 - Flexible Output Recovery Evidence

Parents: OBJ-001 / SCOPE-001 / PHASE-010 / FEAT-038.
Requirements: DISC-010 / REQ-010-03 through REQ-010-06 / CHG-013.
Mode: automatic under CHG-014.
Profile: `rubber-duck / gpt-5.6-luna / high / all-validation`.
Integration branch: `phase/010-synchronized-tracks`; base `330e13b`.
Proposed worker branch: `ticket/124-flexible-export-recovery`.

## Released prerequisites and pending readiness

T113 source rendering, T121 video composition and T123 A/V assembly have
bounded exact-profile releases. The final T123 decision is validator
`29f2718e-4d66-4e11-b137-9d5e54778e2f`, turn 7. T114 output controls also
have bounded release at validator `6a2540b0-3610-444e-b264-0f42b37bbac1`,
turn 10. These are actual dependency releases, not ticket closeout.

The current root snapshot passed eighteen focused output/A/V cases and
configured typing/dependency/duplication checks with zero introduced clones.
No T124 session fingerprint, cancellation, recovery, synchronized final
GUI/CLI dispatch or per-output resume result is approved or implemented.

Parent reserves shared planning, evidence, root integration and quality
checks. Initial delegated scope, after exact readiness, is two dedicated
tests plus a response-only fingerprint/session design for approval before
production. T111 app/UI/removal and T120 playback files are excluded.

## Isolated snapshot and exact authoring readiness

Parent created and verified `worktree-ticket124` on the proposed branch.
The released compositor, source renderer, export controls and configuration
match root bytes. Eighty-nine untracked code/context files were copied,
excluding generated media/screenshots, and existing development tools were
linked. The output/A/V reports were archived at session
`phase010-output-av-verified-quality`.

Exact validator `8f6c24ed-e225-4166-ad3c-198dfee6bc90`, turn 0, returned
**readyForTestAuthoring**. The current single-destination session cleanup,
stat-only fingerprint, absent child cancellation hooks and intentional
synchronized final guards identify the approved T124 work, not failed
prerequisites. Production requires the concrete design and executable red
charter to be reviewed first.

Worker `cd9c1071-f258-479e-8560-047815998457` uses GPT-5.6 Luna/max and owns
only `test_editor_flexible_output_recovery.py` and its functionality
counterpart this turn. Its response-only design must reuse existing
session/lock/restart/resume/discard semantics, explicit per-output
fingerprints/results and bounded event-driven child cancellation. No new
backend, editable track-name field or all-or-nothing multi-file publication
is authorized. Current track IDs and sanitized labels are the naming inputs.
No T124 functionality or production PASS is claimed.

## Fail-first authoring and bounded production authorization

The worker returned nine expected missing-coordinator unit failures.
Actual FFmpeg/ffprobe fixture preflight and native recovery controls passed.
Final-only and combined CLI journeys failed at the current synchronized
guards. Source-only actually rendered, then failed the missing future
structured-results assertion. Compilation and standalone Ruff passed.
None of these intentional red cases is a current-product acceptance PASS.

Exact validator `8f6c24ed-e225-4166-ad3c-198dfee6bc90`, turn 1, returned
**READY FOR BOUNDED PRODUCTION IMPLEMENTATION**. The approved coordinator
reuses existing locks/manifests, explicit cancellation, per-output states and
full canonical source/content/settings fingerprints. It rejects duplicate
identities/destinations and incomplete fingerprint maps before rendering.
Resume requires matching fingerprints and real output re-verification.
Restart preserves published destinations until verified replacement.
Cancellation after publication retains that output as verified and prevents
starting the next sibling.

The approved adjacent receipt is an atomically written batch receipt, never
an atomic transaction across output files. It is written only after all
requested outputs have been individually verified/published, with same-
directory replacement and fsync, before successful session cleanup.
It records batch/output fingerprints, output identities/destinations,
published hash/stat and media-verification metadata, and schema/tool/
compositor versions. Resume treats it as advisory and re-verifies every
output. Incomplete work retains sibling proof in the session manifest.
Discard removes only owned session/receipt state, not published outputs.

The same Luna/max worker was authorized for the new coordinator,
export GUI/CLI dispatch, session/process helpers, source outputs and
video/audio/A/V compositors, plus its two tests. App/UI/keybindings,
core CLI/parser, model/layout and playback remain excluded. Required test
amendments include post-publication cancellation, actual track-order
reversal and explicit layout/pan-law fingerprint mutation, and real native
final-only/combined completion parity.

Production and test execution are ongoing privately. All GTK commands must
hold the shared session desktop lease. No coordinator, export-recovery,
partial-success or terminal automatic-validation PASS is claimed.

## Private implementation review and scoped remediation

The worker reported ten coordinator unit cases, 31 protected A/V cases and
nine actual CLI/native functionality cases passing privately. The native
charter took 209.976 seconds, with a separate six-case CLI rerun. These
results describe the candidate, not root integration or terminal acceptance.

Parent review found missing production fingerprint inputs: fresh legacy
timelines had no canonical track blocks in the payload, tools were identified
only by path strings, and actual layout/audio/pan policy values were absent.
Unsupported fingerprint values were silently stringified. The same worker
is adding production-builder regressions and corrections, not merely tests
of hand-authored fingerprint dictionaries.

Exact validator `8f6c24ed-e225-4166-ad3c-198dfee6bc90`, turn 2, independently
identified GUI legacy-final routing bypassing recovery, loss of per-output
partial-success results, original-source aliases at receipt write/discard,
missing batch-level resume checks and incorrect failure classification
after successful publication. Parent additionally identified missing
published-content hash comparisons on resume and insufficient GUI media
verification, including a success-shaped fallback. Validator turn 3
confirmed the content-proof gap as blocking: a different valid movie with
the same media shape must not be skipped as the original verified output.

All findings remain within the approved recovery/source-preservation
contract. The retained worker owns failing regressions and corrections for
safe receipt/temporary paths, all-mode GUI parity, structured results,
canonical fingerprints, exact published-output proof and post-publication
truthfulness. No new architecture or independent review worker was added.
T124 remains inProgress, private and not integrated into root. T125 remains
pending its bounded release. No final automatic-validation PASS is claimed.

Exact validator turn 4 inspected the updated private snapshot and confirmed
five execution findings resolved: ordinary-project GUI routing, structured
GTK results, complete batch metadata matching, verified truth after
publication errors, and published-content proof with expected-media
verification. One blocker remains: receipt/temp/discard protection includes
source aliases but not the actual project file and every planned output
alias. Parent sent this precise residual finding to the retained worker,
requiring hash-preserving project/output collision regressions and separate
input-versus-receipt safety sets so legitimate outputs remain writable.
This is a current-snapshot review, not terminal T124 acceptance.

## Private release and parent integration gates

Exact validator turn 5 returned **READY FOR PARENT INTEGRATION**, confirming
the residual receipt/project/output alias correction and all six retained
execution findings. Parent generated a Root-versus-private patch for exactly
eight production files and two dedicated tests, checked applicability and
integrated it without replacing other workers' changes.

The Root recovery/source regression runner ran 38 cases in 211.653 seconds.
The new recovery cases had no failures, including actual CLI/media, running
child cancellation and native output-mode controls. The whole runner failed
on three old source-output expectation/seam mismatches. Parent updated only
the old tests to use typed coordinator results and supported multi-track
routing. This is not a whole-run PASS.

Root caught four formatting mismatches and applied the pinned formatter.
Every configured Mypy target passed, including 68 production source files,
and dependency checks passed. The unchanged duplication gate failed with
16 introduced clones, 63 total and 1.205%. No suppression, threshold change
or baseline update is authorized. The retained worker owns scoped shared-
helper remediation in its existing production/test files.

Protected `make contract` ran 39 cases in 22.623 seconds and failed with four
failures and four errors. Parent's compatible candidate-output fixtures
isolated genuine regressions: failed batches emitted a successful terminal
command before their error, final-only planning/result fields were lost,
and resume session events/checkpoint telemetry were missing. The actual
restart test now observes owned nested cut checkpoints and excludes tool-
identity version invocations from its instrumented render counter. Its
original source-preservation, process-cleanup and checkpoint-reuse outcomes
remain required. The same production owner is fixing these regressions,
not weakening the public contract or deleting failing assertions.

Fifty protected export-planner and video/audio/A/V cases passed in
31.371 seconds. Parent-owned compatibility test lint/format/diff checks
passed. Human-facing tracks, output-mode and receipt documentation was
updated against the implemented surfaces, without claiming release readiness.

Artifacts: session `ticket124-final-integration.patch`,
`phase010-root-recovery-integration.log`,
`phase010-root-recovery-static.log`,
`phase010-root-recovery-cli-contract.log`,
`phase010-root-source-output-truth-red.log`,
`phase010-root-cli-compatibility-red.log` and
`phase010-root-recovery-protected-consumers.log`.
T124 remains open/inProgress. Root final quality and exact validation are
pending. T125 remains planned, with its acceptance matrix prepared but not
executed. No commit, push, PR, merge or delivery closeout occurred.

## Superseding Root recovery and compatibility verification

Parent integrated the retained worker's zero-clone/compatibility remediation.
The final CLI preserves concrete final-only planning, resolved FPS/upscale
policies, route/destination metadata, session events and child-checkpoint
resume. Failed batches now return their per-output details only through the
structured error contract, without a successful terminal command on stdout.
One last protected assertion caught a generic failure message hiding the
underlying reason. Parent preserved the first actual output failure message
while retaining every sibling's details.

The native completion wait now has a bounded five-minute budget for the
five-output job instead of two minutes. Completion, status, result-count,
verification, metadata and source-preservation assertions were not weakened.
The final native combined job actually completed in the full runner.

Terminal agent-owned Root results:

- Recovery functionality: **9 PASS in 213.448 seconds**, including all CLI
  output modes, four independent source reels, same-shape output replacement,
  actual running-child cancellation and native final/combined/cancel controls.
- Protected CLI contract: **39 PASS in 19.987 seconds**, including actual
  process interruption/restart, retained nested cut checkpoints, session
  telemetry, no leaked source FFmpeg process and preserved source bytes.
- Coordinator/source compatibility: **29 PASS in 0.335 seconds**.
- Protected export planners/video/audio/A/V: **50 PASS in 31.371 seconds**.
- Exact `make static-analysis PYTHON=.venv/bin/python`: exit zero. All
  configured formatting, Ruff, Mypy, complexity, dependency, pip-audit and
  Bandit checks passed. Every Mypy target passed, including 68 source files.
- Unchanged duplication baseline: **46 clones, 0.933%, zero introduced**.
  All 138 affected formatter files, compilation and diff checks passed.

Artifacts: session `phase010-root-recovery-functionality-final.log`,
`phase010-root-recovery-cli-contract-final.log`,
`phase010-root-recovery-unit-final.log`,
`phase010-root-recovery-complete-static-final.log`,
`phase010-root-recovery-duplication-final.log` and
`phase010-root-recovery-compile-final.log`.
The historical failed runners remain failed records, superseded only for
their focused scopes by these final results.

Exact validator `8f6c24ed-e225-4166-ad3c-198dfee6bc90` has the terminal Root
results for the bounded decision. Root automatic validation remains pending
that response. T125's integrated charter and final whole-suite/remote
evidence remain separate required gates, not inferred from these results.

**automaticValidation:** exact validator
`8f6c24ed-e225-4166-ad3c-198dfee6bc90`, turn 6, returned bounded **Root T124
PASS** with no remaining blocker in the requested scope. This supersedes
the pending Root decision above, releasing the declared dependency for T125.
T124 remains open/verifying until configured delivery is satisfied. This
does not close the phase, turn the historical full-suite failures into passes,
or claim remote CI/publication evidence.

## 2026-10-16 - UI resume policy representation repair

Focused maintenance scope under the existing PHASE-010 / FEAT-038 recovery
contract. Given identical project, sources, destination and export settings,
the UI should accept the session produced by the CLI rather than report a
stale request. Genuine project/content/policy changes must still be rejected.
No renderer, publication policy, user project or checkpoint artifacts are
changed by this repair.

Diagnosis: the UI supplies plain FPS/upscale policy objects, while the CLI
supplies resolved policies containing per-source decisions. The fingerprint
also recorded a backend in `rve_route` for plain FPS policies but `None` for
resolved policies. Identical export choices therefore produced different
session identities. Shared fingerprint construction now resolves plain,
mapping and default policies against the same active sources, preserving
the existing resolved CLI representation.

Fail-first evidence: the new representation regression failed for UI,
mapping and default inputs. The real-media functionality test completed a
CLI export, then failed through `run_output_choice_job(..., resume_mode="resume")`
with a receipt mismatch. After normalization, both pass.

Technical evidence:
- `python3 -m unittest tests.test_editor_flexible_output_recovery
  tests.test_editor_export_session tests.test_editor_cli_policy_sources
  tests.test_editor_source_outputs
  tests.test_editor_flexible_output_recovery_functionality.FlexibleOutputRecoveryCliFunctionalityTests`:
  46 tests passed.
- Scoped Ruff lint and formatting checks using `.venv/bin/python`: passed.
  The system interpreter lacked Ruff; the existing virtual environment was
  used without installing dependencies.
- `.venv/bin/python -m mypy --config-file pyproject.toml
  framestudio/export_coordinator.py`: passed.
- `git diff --check`: passed.

Automated functionality evidence: the new CLI-to-UI resume test uses actual
FFmpeg output and persisted receipts, requires a skipped verified output,
and checks unchanged destination hash/mtime, receipt fingerprint, decoded
video/audio and original source hashes. The protected CLI functionality
class also passed in the 46-test run.

Local project diagnosis independently matched all 72 saved output
fingerprints and the exact parent session request key using the corrected
UI representation. Fresh diagnostic content hashes were reused only after
checking source stat equality. The session manifest remained byte-for-byte
unchanged. The user's render was not restarted.

This is raw technical/functionality evidence, not a new automaticValidation
decision or lifecycle closeout. The configured exact-profile validator has
not been invoked for this repair; no new commit, push or remote readiness
claim is made. Existing unrelated deleted test fixtures were left untouched.

## 2026-10-16 - UI shutdown during large multitrack composition

Focused repair under the same recovery contract, on local `main` at
`f02bd86`. Given a large synchronized export, composition should not buffer
the entire future timeline in shared decoder branches. Completed interval
work should survive interruption without a lossy intermediate or resetting
native extraction/interpolation checkpoints.

Diagnosis: the export journal stopped during video composition at frame
1239/29581. The workstation system journal identified `systemd-oomd` killing
the editor service at 11:10:54 local time, with SIGKILL / `oom-kill`,
18.2G peak RAM and 17.9G peak swap; system RAM and swap exceeded 90%.
The older export-failure text described the preceding fingerprint mismatch,
not this shutdown. A SIGKILL cannot execute a Python error handler.

Implementation: repeated-input graphs and graphs with more than four unique
input paths now render independent layout intervals to verified FFV1/AVI
checkpoints, followed by one final H.264 encode. Each interval uses the
existing atomic/checksummed preparation protocol, a single decoder thread
per input, and two filter/FFV1 threads. Simple independent graphs retain
their existing direct route. Native, interpolation, upscale and shared
triplicate-scale reuse remain intact. Final media and original-source
verification remain mandatory. Journal heartbeats now inspect children
launched from every worker thread and retain RSS, peak RSS and swap for
the editor and discovered children.

Failures retained during development:
- Matroska did not preserve exact fractional-rate metadata for the lossless
  checkpoint; NUT subsequently failed one-frame duration verification. AVI
  supersedes both candidates; verification requirements were not relaxed.
- Real-project verification exposed a one-frame interval whose first
  prepared slot had no timestamp inside its narrow trim, and whose other
  slot trimmed beyond the last prepared timestamp. Both produced empty
  inputs. A CFR one-frame interval now selects the covering available frame
  only when its ordinary time trim would be empty, including rounded EOF.
  Ordinary nonempty time trims are unchanged.
- The expanded unit fixture initially changed source duration without the
  corresponding timeline duration and correctly failed the no-speed-change
  model invariant. The fixture now starts with the required duration.

Terminal deterministic command evidence, agent-owned:

```sh
.venv/bin/python -m ruff check framestudio/video_compositor.py framestudio/export_journal.py framestudio/export_coordinator.py tests/test_editor_video_compositor.py tests/test_editor_video_compositor_functionality.py tests/test_editor_export_recovery.py tests/test_editor_flexible_output_recovery.py tests/test_editor_flexible_output_recovery_functionality.py
.venv/bin/python -m ruff format --check framestudio/video_compositor.py framestudio/export_journal.py framestudio/export_coordinator.py tests/test_editor_video_compositor.py tests/test_editor_video_compositor_functionality.py tests/test_editor_export_recovery.py tests/test_editor_flexible_output_recovery.py tests/test_editor_flexible_output_recovery_functionality.py
.venv/bin/python -m mypy --config-file pyproject.toml framestudio/video_compositor.py framestudio/export_journal.py framestudio/export_coordinator.py
python3 -m unittest tests.test_editor_video_compositor tests.test_editor_export_recovery tests.test_editor_video_compositor_functionality tests.test_multitrack_render_benchmark tests.test_editor_av_compositor tests.test_editor_av_compositor_functionality tests.test_editor_flexible_output_recovery tests.test_editor_export_session tests.test_editor_flexible_output_recovery_functionality.FlexibleOutputRecoveryCliFunctionalityTests
git diff --check
```

Observed: scoped lint/format/type/diff commands exited zero; 92 tests
completed with `OK` in 105.263 seconds. These are raw tool results, not an
exact-profile automatic validation decision or a whole-repository-suite claim.

Executable automated functionality requirements:
- `VideoCompositorFunctionalityTests.test_bounded_composition_resumes_lossless_intervals_without_changing_frames`:
  actual FFmpeg render interrupted after two interval encodes; resume must
  avoid encoding those intervals again, publish all planned frames, match
  decoded monolithic-reference frame hashes at fractional FPS, and preserve
  original source bytes.
- `VideoCompositorFunctionalityTests.test_prepared_subframe_and_tail_slots_produce_a_real_composite_frame`:
  actual extraction, FFmpeg interpolation, three-track interval composition,
  lossless checkpoints and final encoding. The planned one-frame interval
  includes an early subframe slot and a rounded-tail slot; its final decoded
  frame must contain visible content in all three columns, with exact total
  frame count and unchanged source hash.
- `ExportRecoveryTests` worker-thread subprocess coverage records actual
  descendant process identity and memory. Existing hard-interruption,
  export-session, CLI/UI recovery and A/V functionality controls are included
  in the terminal runner above.

Real-project verification: original one-frame layout interval 37 and the
following interval 38 rendered through the final FFV1/AVI path, reusing
four native/interpolation preparations and checkpointing two new composition
intervals. The final sample verified 733 frames / 12.216667 seconds, unchanged
original source hashes, and peak summed child RSS of 1258.2 MiB. The charter
cancelled if child RSS exceeded 2 GiB; it did not trigger. Elapsed time was
137.1 seconds including verification. The private temporary sample was
removed after verification; reusable checkpoints were retained. The earlier
six-interval NUT experiment verified 2153 frames with peak child RSS
1346.9 MiB, but is not evidence for the final checkpoint container.
These sample child-RSS measurements are not a full-service or full-project
memory guarantee.

Private session artifacts: `real-bounded-avi-verification.json`,
`real-bounded-composition-verification.json`, and
`bounded-benchmark-regression.json` (retained failed NUT experiment).
Original user media, completed enhancement checkpoints, and unrelated fixture
deletions were not altered. No full final video/source-reel batch was run,
no commit/push occurred, and no ticket was closed. Configured
`rubber-duck / gpt-5.6-luna / high / all-validation` remains a separate
unfulfilled gate; no substitute validation or user-validation claim is made.

## 2026-10-16 - Persistent source hashes and audio-track checkpoints

User-authorized continuation of the recovery repair. Given an unchanged
source, subsequent exports and application processes should reuse its
completed hash rather than reread the entire file. Given completed audible
timeline tracks, interruption in another track or final mixing should reuse
those tracks, without applying headroom/limiting twice.

Source hashing is now shared through `source_hash_cache.py`, with the
existing video `_sha256` import retained for compatibility. Source identity
calls in fingerprinting, video planning/preservation and AV
planning/preservation explicitly opt into the on-disk cache. Its identity
includes resolved path, size and nanosecond mtime, strengthened with device,
inode and ctime. Entries are independently atomically replaced after stable
pre/post hash stats, fsync and cancellation checks. Corrupt/unreadable cache
records are explicit errors. Published output, tool and preparation-content
hashes do not opt in and still read actual content. Reuse depends on
filesystem stat identity; it is not a fresh content scan.

Audible timeline tracks now materialize independently through the existing
owned `RenderPreparations` protocol, keyed by track identity, source hashes,
exact command and FFmpeg/ffprobe runtime identity. Verified float32 PCM tracks
retain placement, gap silence, original-context pan and gain. The final mix
uses the original complete audio plan for shared attenuation/limiting; raw
track contributions may exceed unity but must have exact sample count and
finite samples. Final mixed PCM still enforces the existing unity ceiling.
Silent/excluded sources do not acquire unnecessary track renders. Existing
completed final-audio checkpoints remain usable without invalidating video
or enhancement preparations.

Fail-first evidence: four source-cache cases and the interrupted-track
functionality case failed before implementation, including a second fresh
export-planning process attempting to reread the original source. During
implementation, PCM parity exposed FFmpeg format negotiation rounding mono
contributions to 16-bit before the final mix. Contribution graphs now match
the original mix's floating-format requirements; the safe single-mono case
retains its original conversion semantics. The sample-difference assertion
remains below `1e-6`, not weakened to accept quantization drift.

Terminal raw technical/functionality command:

```sh
python3 -m unittest tests.test_editor_source_hash_cache tests.test_editor_audio_compositor tests.test_editor_audio_compositor_functionality tests.test_editor_av_compositor tests.test_editor_av_compositor_functionality tests.test_editor_video_compositor tests.test_editor_video_compositor_functionality tests.test_editor_flexible_output_recovery tests.test_editor_export_session tests.test_editor_export_recovery tests.test_editor_cli_contract tests.test_editor_flexible_output_recovery_functionality.FlexibleOutputRecoveryCliFunctionalityTests
```

Observed: **106 tests, OK, 105.054 seconds**.

Acceptance-level executable evidence:
- `SourceHashCacheFunctionalityTests.test_export_planning_reuses_hashes_across_fresh_processes`
  creates real FFmpeg media and a persisted project, runs `plan_project_av`
  in two independent Python processes, and forbids source-content reads in
  the second process. Hashes match the original bytes.
- Source-cache regressions require invalidation of a same-size modification
  with restored mtime, rejection of corrupt cache records, cancellation
  without persistence, and rejection of a source modified mid-hash. The
  default uncached output/content-hash path must still open actual bytes.
- `AudioCompositorFunctionalityTests.test_audio_track_checkpoints_resume_without_repeating_completed_tracks`
  performs real PCM rendering, interrupts the second audible track, and
  resumes with a fresh cache object. The first track's hash and mtime remain
  unchanged and its render command cannot run again. An interruption in final
  mixing preserves the previously published output and then resumes without
  rendering either completed track. Changing only the first track's gain
  rebuilds only that track. Decoded PCM matches the direct reference within
  `1e-6`, with exact 48 kHz stereo sample count.
- `AudioCompositorFunctionalityTests.test_checkpointed_audio_preserves_safe_unsafe_and_silent_track_behavior`
  compares actual cached/direct decoded PCM for centered mono/stereo,
  no-audio silence and an over-unity raw contribution requiring final
  attenuation. All final peaks remain within the existing bound.

Scoped Ruff lint and formatting checks passed for the five changed production
modules and two affected test modules. Whole-package Mypy passed for 78 source
files after correcting a progress-duration annotation. The repository-native
dependency check exited zero; `git diff --check` exited zero. No dependencies,
thresholds or validation policies were changed. README now documents cache
location/invalidation, stat-trust boundary, per-track reuse, and the need to
repeat only an unfinished track.

No user render was started, source files changed, checkpoints deleted, or
commit/push performed. This records raw deterministic results only. The
previous exact-profile automaticValidation blocker remains unresolved;
no new formal readiness decision or lifecycle closure is claimed.

## 2026-10-16 - FFmpeg version gate for shared audio inputs

CI installs FFmpeg 6.1 and failed the quality suite. On FFmpeg 6.1.3, the
shared-input audio graph (one input fanned out with `asplit` to many track
branches) drops a branch with a later offset and pans the mix to the other
branch's ratio. The legacy one-input-per-clip graph is correct there. On
FFmpeg 9.0.2 both graphs match. The 6.1 root cause was not isolated.

Decision (user-approved): input reuse is enabled only when the detected
FFmpeg major version is at least 9. Unknown or unparseable builds, and
versions 7 and 8 (untested), use the legacy graph. The gate is
`_shared_input_reuse_supported` in `framestudio/audio_compositor.py`.

Tradeoff: on FFmpeg below 9, each clip is decoded once per use instead of
shared, so multitrack audio export does more decode work. The user's 9.0.2
machine keeps reuse.

Tests gated to FFmpeg 9 or newer, with skip reasons naming FFmpeg 6.1:
- shared-vs-legacy PCM comparison and the mapping tests in
  `tests/test_editor_audio_input_reuse_functionality.py`. A new test asserts
  reuse is off on FFmpeg 6.
- VFR seek case in `tests/test_editor_multitrack_render_optimization.py`
  (raw 14 vs decoded 17 frames on 6.1; this exercises FFmpeg's own
  `-ss -noaccurate_seek -copyts` behavior, not FrameStudio code).
- two real-multisource cases in `tests/test_multitrack_render_benchmark.py`.
  On 6.1 the AAC decoder returns 29696 PCM samples for a 0.6 s file, where
  9.0.2 returns 28800. The benchmark's decoded-length gate therefore cannot
  pass on 6.1. This is a decoder difference, not an export defect.

Verified raw results:
- `tests.test_editor_audio_input_reuse_functionality`,
  `tests.test_editor_multitrack_render_optimization`,
  `tests.test_multitrack_render_benchmark` on FFmpeg 6.1.3:
  28 tests, OK, 6 skipped.
- Same modules on FFmpeg 9.0.2: 28 tests, OK.
- Full suite on FFmpeg 6.1.3 with `make quality`: 1042 tests, 733 s. Two
  failures remain, both X11-only and environmental here (session is
  Wayland): `NativeRemovalControlsFunctionalityTests` setUpClass and
  `test_complete_edit_and_delivery_journey`. CI runs them under `xvfb-run`
  with `GDK_BACKEND=x11`.
- Static analysis (`make compile diff-check static-analysis`) passed: ruff
  format and lint, mypy, complexity, duplication, dependency check and audit,
  and security.

## 2026-10-16: CI follow-up (heartbeat milestone replay and X11 pointer tests)

CI for `f08bfbc` failed with one interpolation-restart failure and two X11
pointer errors.

Interpolation restart (`test_twenty_of_forty_interpolations_survive_process_restart`):
- Cause: `ExportJournal` heartbeat (`framestudio/export_journal.py`) called
  `ExportProgressTracker.heartbeat()`, which re-sent the last progress event.
  When that event was `Checkpointed interpolated segment`, the duplicate was
  counted as a 20th checkpoint and the first run cancelled after 19 real
  interpolations. The 19-versus-20 count matches this exactly; the trace was
  inferred, not captured.
- Fix: `framestudio/export_progress.py` no longer records milestone stages
  (`Checkpointed `, `Starting output`, `Verified output`, `Reusing verified`,
  `complete`) as the replayable last stage. Heartbeats only refresh in-progress
  stages.
- Regression: `test_heartbeat_never_replays_a_checkpoint_milestone` in
  `tests/test_editor_export_recovery.py`.
- Verified: the restart test passes twice on FFmpeg 6.1.3 (28.7 s and 31.3 s).

X11 pointer errors (`test_real_pointer_click_with_small_hand_movement_still_snaps_at_extreme_zoom`):
- Cause: `xdotool mousemove --sync` blocks until the server sends a motion
  event. It never returns when the pointer is already at the target under Xvfb.
- Fix: `tests/test_editor_keyboard_functionality.py` drops `--sync` and pumps
  GTK events (5 iterations) after the move. Assertions are unchanged.
- Not verified locally: Xvfb is not installed and sudo needs a password. CI is
  the only X11 verification.

Full suite on FFmpeg 9.0.2 (`discover -s tests`): 1043 tests, 789 s, 13 skipped.
The two failures are Wayland-only and environmental: `NativeRemovalControlsFunctionalityTests`
setUpClass requires X11, and `test_complete_edit_and_delivery_journey` fails on
the same `xdotool search` call.

## 2026-10-16: Empty raw-source interval and hidden UI error

Corrective scope linked to TICKET-121/TICKET-124, PHASE-010, FEAT-036/FEAT-038.
This is follow-up implementation evidence, not a reopening or closeout claim
for the historical completed records. The current request authorizes fixing
the render failure; the pre-existing uncommitted focus-control edits remain
separate. No source media or user checkpoint was changed.

Requirement: given a positive planned frame count for a raw-source subframe
interval or a short container tail after video EOF, should produce the planned
visible frames, verify them, and retain compatible checkpoints across failure.
Given another output failure, should preserve its underlying message through
the UI worker exception and saved failure log. Non-goals include changing
source duration metadata, bypassing output verification, or restarting the
entire user render during diagnosis.

Diagnosis from the saved journal: interval 22/88, duration 0.012208 seconds,
expected one frame. FFmpeg returned zero but wrote a header-only 5,806-byte
FFV1 AVI. FFprobe found no decoded frames and no container duration.
One source's container/audio duration exceeded its available normalized video
frames. The UI discarded the per-output error and showed only a generic batch
failure. The failure was not an out-of-memory termination.

Fail-first results:
- The generated raw-source functionality regression reproduced empty intervals
  between timestamps and at fractional-rate EOF before the fix.
- The detailed-error regression failed because `ExportBatchExecutionError`
  contained only the generic message.
- An initial target-grid sampling fix passed generated fixtures but still
  failed on the actual two-source interval. A new fixture with nonzero video
  start time and audio longer than video reproduced this remaining failure.

Fix: for raw branches with one output frame or less than one source-frame
duration, convert to the target grid before selecting frames. Extend the final
valid video frame before selection so short audio/container tails cannot empty
an xstack input. Prepared FPS branches and ordinary longer raw interval graphs
keep their existing behavior. Frame-count, decode, dimensions, FPS, duration,
source protection, and atomic publication checks remain enabled. Changed
commands invalidate only their own preparation keys; unchanged verified
interval commands retain their cache identities.

Raw technical results, not an automatic-readiness decision:
- `.venv/bin/python -m unittest tests.test_editor_video_compositor
  tests.test_editor_video_compositor_functionality tests.test_editor_post_export
  tests.test_editor_flexible_output_recovery tests.test_editor_render_preparations`
  ran 55 tests successfully after the final fix.
- `GDK_BACKEND=x11 DISPLAY=:0 .venv/bin/python -m unittest
  tests.test_editor_flexible_output_recovery_functionality
  tests.test_editor_av_compositor tests.test_editor_av_compositor_functionality`
  ran 21 tests successfully. This protected-flow run preceded the final
  raw-tail padding addition.
- Focused Ruff lint/format checks succeeded on the four changed Python files.
  `.venv/bin/python -m mypy --config-file pyproject.toml framestudio`
  found no issues in 79 source files. `git diff --check` succeeded.

Executable automated functionality:
- Test ID
  `tests.test_editor_video_compositor_functionality.VideoCompositorFunctionalityTests.test_unprepared_subframe_intervals_export_visible_frames_and_resume`.
  Run `.venv/bin/python -m unittest <test ID>` with system FFmpeg 9.0.2 or
  with FFmpeg 6.1.3 on PATH. Both completed successfully after the final fix.
  The real public video-render boundary exports two-track generated media at
  60 FPS, including 60/29.97/24 FPS sources, a between-frame trim, a video EOF
  tail with later audio and nonzero video start, and a two-frame interval.
  It interrupts after the first verified interval, resumes using a new
  preparation instance, rejects rerendering that completed command, and
  asserts exact frame count, duration, visible red pixels in both slots,
  no premature publication, and unchanged source hashes.
- `test_batch_failure_preserves_the_output_error_for_ui_and_failure_log` in
  `tests.test_editor_post_export` verifies the structured error and actual
  persisted failure-log contents. All seven post-export tests succeeded.
- A local real-media smoke reconstructed the exact failed interval from its
  retained request, passed its two original inputs through the production
  planner/command builder and FFmpeg, and ran the normal compositor verifier.
  Result: one decoded 1920x1080 frame at 60 FPS, duration 0.016667 seconds.
  Source stat identities were unchanged, the failed session remained untouched,
  and the temporary output was removed.

Latest regression log is in the session workspace as
`files/render-subframe-regression.log`. Private source paths/content are not
copied into this evidence. Full-project export and new remote CI were not run.
The running editor needs a restart to load changed Python code; choose Resume,
not Restart, to retain compatible completed work.

Delivery gate remains blocked: no configured
`rubber-duck / gpt-5.6-luna / high / all-validation` decision was obtained.
The user's no-delegation preference remains in force. Raw tool results above
are not `automaticValidation`, user confirmation, or lifecycle closeout.
No commit or push was performed.

## 2026-10-16: Audio EOF silence timestamps and late export recovery

Corrective follow-up under PHASE-010 / TICKET-122 / TICKET-123 / TICKET-124.
Given an interval whose source audio trim is empty, should produce correctly
timestamped silence of the planned sample count, continue subsequent intervals,
and support per-track recovery without touching completed video artifacts.
Non-goals are skipping verification, modifying sources, deleting the failed
session, or rerendering the user's video as part of diagnosis.

The latest real failure occurred in audio track 2/2 after video composition
was completely checkpointed. The second track's interval 21 requested 586
samples beyond available source audio. FFmpeg's `apad` generated silence
without a starting PTS, and subtracting `STARTPTS` preserved that undefined
timestamp. Verbose reproduction showed concat finishing a segment with a
large negative/undefined PTS immediately before error 183 (`Invalid data found
when processing input`). This was not a failed video render or source decode.

Fail-first evidence: the new public-boundary functionality test reproduced
error 183 for both centered/legacy and composed/panned empty-tail branches.
The unmodified saved 38-input audio-track command also reproduced error 183.
Replacing padded-source timestamp expressions in a diagnostic temporary copy
made that command complete, isolating the timestamp cause.

Fix: both source branches assign timestamps after padding and trimming using
`asetpts=N/SR/TB`. This anchors even initially empty audio at zero using the
actual emitted sample count. Gain, pan, mixing, decoded PCM verification,
exact sample count, source protection and publication behavior are unchanged.
Only audio preparation commands change; video preparation identities do not.
Previously verified audio tracks built with the old command can be rebuilt,
but the completed video composition remains compatible.

Raw technical results:
- `.venv/bin/python -m unittest tests.test_editor_audio_compositor
  tests.test_editor_audio_compositor_functionality
  tests.test_editor_audio_input_reuse_functionality
  tests.test_editor_av_compositor tests.test_editor_av_compositor_functionality`
  ran 34 tests successfully. Raw log:
  session `files/audio-tail-regression.log`.
- Ruff lint/format checks and Python compilation succeeded for
  `framestudio/audio_compositor.py` and
  `tests/test_editor_audio_compositor_functionality.py`.
  `.venv/bin/python -m mypy --config-file pyproject.toml framestudio`
  found no issues in 79 source files; `git diff --check` succeeded.

Executable automated functionality:
- Test ID
  `tests.test_editor_audio_compositor_functionality.AudioCompositorFunctionalityTests.test_empty_audio_tail_keeps_silence_timestamps_and_resumes_tracks`.
  Its public `render_audio` boundary generates actual stereo tone media,
  declares a container tail after audio EOF, exports centered and panned cases,
  checks exact 48 kHz stereo sample count, silent tail/gap, and audible content
  before and after the tail. It interrupts the second track, verifies there is
  no published incomplete output, resumes with a new preparation instance,
  rejects any rerender of completed track 1, compares decoded PCM with the
  uncached render, and checks unchanged source/checkpoint hashes and mtime.
  Run `.venv/bin/python -m unittest <test ID>`.
- With FFmpeg 6.1.3 on PATH, that new test plus
  `test_audio_track_checkpoints_resume_without_repeating_completed_tracks`
  completed successfully (2 tests).
- Real-media smoke rebuilt the exact failed command through production
  `_render_command`, using the retained serialized audio plan, source paths
  and track selection. An assertion verified that only the intended
  post-padding timestamp expressions differed from the original failed graph.
  The corrected track rendered and passed `_verify_pcm_output` with the exact
  planned sample count/duration. Original source stat identities and the
  user's existing checkpoint manifests/artifacts were untouched. Diagnostic
  temporary audio outputs were removed.

Read-only session discovery confirmed the user's latest destination session
exists, is valid and resumable, and contains a complete video composition
artifact. GUI recovery requires the same project, destination and export
settings. Restart the editor to load the changed module, keep the failed
output filename, and choose **Resume export**, not **Restart** or discard.
Revalidate/reuse the composed video, render audio, then mix/mux/verify/publish
the remainder. No full-project export or remote CI was run in this repair.

Configured `rubber-duck / gpt-5.6-luna / high / all-validation` approval
remains unavailable under the user's no-delegation preference. These are raw
technical/functionality observations, not terminal `automaticValidation` or
lifecycle closeout. Changes remain local; no commit or push was performed.

## 2026-10-16 - Final mux frame preservation and truthful recovery history

Context: local repairs to the delivered recovery behavior, linked to
TICKET-124 / FEAT-038 / PHASE-010. This entry does not reopen or close historical
planning records or claim delivery approval. Existing unrelated focus-control
changes remain intact and unstaged.

Requirements:
- Given audio ends just before the frame-quantized video endpoint, the final
  mux should retain every planned video frame and exact verification.
- Given an invalid completed-but-unverified mux checkpoint, Resume should
  rebuild only that mux and reuse the verified video/audio compositions.
- Given nested saved render work but zero completed top-level batch stages,
  the GTK recovery panel should show historical overall progress when
  available, never imply that no internal work was saved, and preserve the
  existing resume/fingerprint safeguards.

Observed real failure: the retained video checkpoint contained 49,716 frames
at 60 FPS, duration 828.600000 seconds. The audio checkpoint contained
39,772,522 samples at 48 kHz, duration 828.594208 seconds. The failed final mux
contained only 49,715 frames. A generated-media reproduction demonstrated that
`-shortest` dropped the final video frame even when PCM audio was only one
sample shorter than video. The public-boundary regression first failed on
Resume with `59 frames; expected 60`.

Fix: final muxing no longer uses `-shortest`; both child compositions already
have verified finite planned lengths. Exact frame count, stream/container
duration, decoded audio sample count and full decode checks remain unchanged.
The mux-checkpoint validator now translates `AVCompositorExecutionError` to
the `ExportExecutionError` contract used by pending checkpoint recovery.
This lets Resume reject and rebuild the existing invalid pending mux instead
of failing repeatedly on that file. Video/audio cache keys are unchanged.

Recovery UI: read at most the last 64 KiB of the existing export journal and
use only a finite numeric `overall_percent` from the latest run. Stop at its
`started` event, tolerate partial/malformed records, reject nonregular files
without blocking, and surface read errors explicitly. The label says
`Previous run reached 89.3%. Resume checks and reuses saved checkpoints.`
When history is unavailable, it says `Pending export` rather than claiming
zero reusable work. Reading does not modify journals or checkpoint manifests.

Raw technical observations:
- `.venv/bin/python -m unittest tests.test_editor_audio_compositor
  tests.test_editor_audio_compositor_functionality
  tests.test_editor_audio_input_reuse_functionality
  tests.test_editor_video_compositor
  tests.test_editor_video_compositor_functionality
  tests.test_editor_av_compositor
  tests.test_editor_av_compositor_functionality
  tests.test_editor_export_recovery tests.test_editor_post_export`
  completed 80 tests without failure. Artifact:
  session `files/final-render-repairs-regression.log`.
- With FFmpeg 6.1.3 first on PATH, `.venv/bin/python -m unittest
  tests.test_editor_av_compositor_functionality.AVCompositorFunctionalityTests.test_resume_rebuilds_shortened_mux_without_repeating_video_or_audio
  tests.test_editor_export_recovery` completed 16 tests without failure.
  Artifact: session `files/final-mux-ff61.log`.
- Focused Ruff lint and format checks completed for the six changed mux,
  journal, panel and test files. `.venv/bin/python -m mypy --config-file
  pyproject.toml framestudio` reported no issues in 79 source files.
  `make compile PYTHON=.venv/bin/python` and `git diff --check` completed.
  This is focused local coverage, not full static-analysis/PR parity.

Executable automated functionality:
- `tests.test_editor_av_compositor_functionality.AVCompositorFunctionalityTests.test_resume_rebuilds_shortened_mux_without_repeating_video_or_audio`
  exercises public `plan_project_av` / `render_project_av` with actual generated
  media and persistent `RenderPreparations`. It creates the legacy truncated
  mux, asserts no invalid destination is published, resumes with a new cache
  instance, rejects any repeated video/audio rendering, checks all 60 decoded
  frames including visible last-frame pixels, and verifies unchanged source
  hashes and child checkpoint hashes/mtime. Run with
  `.venv/bin/python -m unittest <test ID>`.
- `GDK_BACKEND=x11 DISPLAY=:0 GSK_RENDERER=cairo .venv/bin/python -m unittest
  tests.test_editor_flexible_output_recovery_functionality.FlexibleOutputRecoveryGtkFunctionalityTests`
  completed five real GTK functionality cases, including final/combined
  export, running cancellation/recovery, persisted previous-percentage label,
  missing history and visible history read errors. The two new label tests are
  `test_recovery_label_shows_previous_overall_progress_not_zero_completed_stages`
  and `test_recovery_label_without_history_or_with_read_error_preserves_resume`.
  They verify visible historical-versus-checkpoint wording, available Resume,
  absent zero-stage claims, and unchanged saved manifest/journal on discovery.
  Artifact: session `files/recovery-label-gtk-suite.log`. The installed
  PyGObject emitted existing Python 3.14 deprecation warnings.
- Target-workstation real-media smoke used the user's retained completed
  video and audio as read-only inputs to production `_mux_stages`, writing
  only a temporary diagnostic output. Unchanged `_verify_muxed_output` fully
  decoded it and confirmed 49,716 video frames, 39,772,522 decoded audio
  samples, 48 kHz stereo, correct stream/container durations and valid peak.
  Input checkpoint size/mtime identities were preserved. Elapsed time was
  86.88 seconds; the diagnostic output was removed automatically.
  Artifact: session `files/final-mux-real-media.json`.

UI continuation: restart FrameStudio to load the repaired modules, reopen the
same project and retain the failed destination filename/settings, then choose
**Resume export**, not Restart or Discard. The invalid pending mux is rebuilt;
compatible completed video/audio compositions stay reusable. No original
media, user checkpoint or existing final output was modified by diagnostics.

Configured automatic validation remains blocked on the exact
`rubber-duck / gpt-5.6-luna / high / all-validation` capability under the user's
no-delegation preference. The results above are raw agent-owned technical and
automated-functionality observations, not terminal `automaticValidation`,
`userValidation`, formal review readiness or lifecycle closeout. No full-suite,
full-static-analysis, remote CI, commit or push was performed for this repair.
