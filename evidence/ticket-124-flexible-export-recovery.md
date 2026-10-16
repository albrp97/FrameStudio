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
