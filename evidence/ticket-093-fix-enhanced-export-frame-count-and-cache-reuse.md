# Evidence - TICKET-093

**Ticket:** TICKET-093 - Fix Enhanced Export Frame Count and Retry Reuse
**Status:** verifying
**Last updated:** 2026-09-04

## Baseline

- The reported Downloads project contains 16 active enhanced segments.
- The selected 60 FPS target and timeline allocation require 45,942 video
  frames.
- The retained enhanced artifacts record frame counts summing to 45,942.
- The cached concat-demuxer route produces 45,942 frames but its container
  duration exceeds the plan tolerance, so strict verification correctly
  rejects it.
- The decoded fallback composition applies a duration limit and produces
  45,941 frames, causing the reported strict frame-count verification failure.
- A diagnostic frame-limited composition using `-frames:v 45942` produces the
  requested 45,942 frames within the existing duration tolerance.

## Implementation evidence

Pending. Add the regression before the source change, then record the focused
implementation and retry evidence here.

### Baseline - 2026-09-04

- **Requirement/flow:** Existing enhanced-export planning, cache, and
  execution behavior remains protected before the retry fix.
- **Command:** `python3 -m unittest tests.test_editor_operations
  tests.test_editor_export_cache tests.test_editor_smart_render
  tests.test_editor_export_execution`
- **Expected:** Existing operations and enhanced-export tests pass without
  changing source or cache behavior.
- **Observed:** 39 tests passed in 47.009 seconds.
- **Status:** passed.
- **Artifacts:** command output retained in the session execution record.
- **Failure/fix:** None at baseline.

### Implementation and regression - 2026-09-04

- **Requirement/flow:** A retry plan created from a resolved CLI policy must
  describe only sources still active in the edited timeline, so equivalent
  retries retain the same cache request.
- **Regression:** Added
  `EditorExportExecutionTests.test_mixed_export_resolved_policies_ignore_inactive_sources`.
  The test passes resolved frame-rate and upscale policies containing an
  inactive source, then verifies that the plan and the equivalent raw-policy
  plan have identical serialized plans, active source IDs, decisions, and
  route.
- **Observed before the source fix:** The test failed because
  `plan.rate_decisions` contained `("first", "second")` after `second` was
  deleted from the timeline.
- **Fix:** Resolved policies are now recalculated against the active mixed
  source metadata before route selection, decision persistence, and cache
  request generation. The selected policy settings are preserved while
  inactive-source decisions are excluded.
- **Focused command:** `python3 -m unittest
  tests.test_editor_export_execution.EditorExportExecutionTests.test_mixed_export_resolved_policies_ignore_inactive_sources
  tests.test_editor_export_execution tests.test_editor_operations
  tests.test_editor_export_cache tests.test_editor_smart_render`
- **Observed:** 41 tests passed in 46.817 seconds.
- **Status:** passed.
- **Artifacts:** regression source
  `tests/test_editor_export_execution.py`; implementation source
  `framestudio/export_planning.py`.

### Reported-project plan and fingerprint - 2026-09-04

- **Requirement/flow:** The reported Downloads project should produce the same
  retry request as the original active-source export rather than a request
  polluted by an inactive source.
- **Command:** `python3 framestudio.py export-plan <reported project>
  --output <reported destination> --full-paths`, followed by local request
  fingerprint inspection using the same plan, source identities, runtime
  paths, and FFmpeg identities as enhanced execution.
- **Expected:** Six active sources and six frame-rate/upscale decisions, no
  eligible upscale sources, and cache key
  `8f6e7e1047cf1494188313531ccb4675f0f260861e127bdda69569b456406434`.
- **Observed:** The corrected plan contains six active sources and six
  decisions, no eligible upscale sources, and computes the expected
  `8f6e7e1047cf1494188313531ccb4675f0f260861e127bdda69569b456406434`
  key. The retained cache currently contains
  `23e073f24ec8063f1807fecab881cc9615cd91154bec9eed08fee1cb4a16346b`
  because it was created by the interrupted pre-fix retry.
- **Status:** passedWithConcerns.

### User-validation closeout - 2026-09-07

- **User response:** `PASS` — the user confirmed the implemented ticket set
  is good.
- **Status:** passed; this supersedes the earlier pending user-validation
  state.
- **Artifacts:** `/tmp/framestudio-export-plan-after-fix.json`;
  reported-project retained manifest under the destination's
  `.framestudio-intermediates` directory.
- **Failure/fix:** The pre-fix retry discarded the original enhanced
  artifacts after resolving an inactive source. Those artifacts are no
  longer recoverable in the retained directory, so a warm real-media
  enhanced retry still requires regeneration.

## Verification evidence

Pending focused tests, full repository checks, target-workstation retry, and
review.

## User validation

Pending terminal maintainer validation of the fixed Downloads export and retry
behavior.

## Known limitations

- Remote checks remain unavailable until the active branch is published.
- The pre-existing complexity finding at
  `benchmarks/restoration_benchmark.py:1794` remains outside this ticket's
  scope.

### Target-workstation failure retention - 2026-09-04

- **Requirement/flow:** A failed enhanced export must leave valid prepared and
  interpolated intermediates available for a later retry, without publishing
  a partial destination.
- **Command/steps:** Started the reported Downloads project export with
  `--human-progress`, allowed all 16 enhanced segments to complete, then
  interrupted the composition step in the test harness before publication.
- **Expected:** The destination remains absent, the request cache retains its
  16 prepared and 16 enhanced artifacts, and the corrected cache key remains
  `8f6e7e1047cf1494188313531ccb4675f0f260861e127bdda69569b456406434`.
- **Observed:** The interrupted process exited with status 143; no final
  destination was published; the manifest retained 32 artifacts under the
  corrected cache key. The harness-created partial composition was removed
  before retry; normal application failures continue to use the existing
  partial-output cleanup path.
- **Status:** passed.
- **Artifacts:** Reported-project retained manifest and 32 validated
  intermediate media files beside the destination.

### Target-workstation warm retry - 2026-09-04

- **Requirement/flow:** A retry with unchanged sources, timeline, policies,
  and runtime must reuse completed enhancement work and proceed to assembly.
- **Command:** `python3 framestudio.py export <reported project>
  --output <reported destination> --human-progress`
- **Expected:** The retry validates retained artifacts, does not start RVE
  interpolation again, assembles the final output, verifies it, publishes it
  atomically, and removes the cache only after success.
- **Observed:** Cache validation advanced through all 16 interpolation segment
  slots without an RVE backend process; the retry reached final composition at
  elapsed 06:26, completed publication at 18:55, exited with status 0, and
  removed the intermediate cache. The machine-readable progress stream
  contained 2,011 valid JSON Lines with no parse failures.
- **Status:** passed.
- **Artifacts:** `/tmp/framestudio-t093-retry2.stderr`,
  `/tmp/framestudio-t093-retry2.json`, and the successfully published
  reported-project destination.

### Target-workstation output verification - 2026-09-04

- **Requirement/flow:** The reported enhanced mixed-source export must preserve
  the exact planned frame count and existing output contract.
- **Expected:** 45,942 decoded video frames, 60 FPS, 1920x1080 output,
  duration within the existing 0.05-second tolerance, stereo 48 kHz AAC
  audio, decodeability, source preservation, and no retained cache after
  verified publication.
- **Observed:** `ffprobe` reported 45,942 video frames, `60/1` average and
  nominal frame rate, 1920x1080 dimensions, duration `765.721333` seconds
  against the planned `765.6943546069225` seconds (delta approximately
  `0.026978` seconds), and AAC stereo 48 kHz audio. The application completed
  strict frame-count, artifact-gate, decoded-output, and source-preservation
  checks before publication; the cache directory and partial-output pattern
  were absent after success.
- **Status:** passed.
- **Artifacts:** Published output metadata from `ffprobe`; source
  preservation and cache-cleanup observations; `/tmp/framestudio-t093-retry2.time`
  (`1155` seconds).

### Repository verification and quality gates - 2026-09-04

- **Protected repository checks:** `make PYTHON=.venv/bin/python test`
  completed with 419 tests passed in 69.964 seconds. `make
  PYTHON=.venv/bin/python check` completed with the same 419-test result,
  compilation, and `git diff --check`. `make PYTHON=.venv/bin/python
  contract` completed with 35 tests passed in 15.399 seconds, and `make
  PYTHON=.venv/bin/python FFMPEG=/usr/bin/ffmpeg smoke` completed
  successfully.
- **Static analysis:** Formatting (89 files), Ruff lint, all configured Mypy
  targets, dependency checks, pip-audit, Bandit, jscpd, and churn completed
  successfully; the security and dependency reports contain no findings and
  no known vulnerabilities. The configured complexity check remains blocked
  only by the pre-existing `C901` finding at
  `benchmarks/restoration_benchmark.py:1794` (`16 > 15`).
- **Local/PR parity:** The local commands use the same `make quality`
  wrapper, pinned Python quality environment, `npm ci` tooling, and
  `.github/workflows/quality.yml` scopes and policies. Remote workflow
  execution remains unavailable because this branch has not been published.
- **Status:** passedWithConcerns.
- **Artifacts:** `evidence/static-analysis/` reports, command output retained
  in the session execution record.
- **Accepted warning:** The complexity finding is existing repository debt and
  is outside TICKET-093 scope; it was not suppressed or relabeled as fixed.

### User-validation handoff - 2026-09-04

- **Required flow:** Open the published output from the reported project and
  confirm that playback, duration, audio, and the edited segment sequence are
  correct. If the export is interrupted or fails before publication, rerun
  the same export command and confirm that the retry reports the numbered
  stages and completes without repeating the expensive enhancement work.
- **Expected response:** `PASS`, or `NOT APPLICABLE` with a reason if the
  target-workstation flow cannot be exercised.
- **Observed:** Automated target-workstation validation passed; maintainer
  validation has not yet been returned.
- **Status:** blocked.
- **Blocker:** `.github/aidd-config.yml` requires terminal user validation
  before review readiness and delivery.

### Review remediation - cache-root symlink safety - 2026-09-04

- **Finding:** A destination-adjacent cache path supplied as a symbolic link
  was followed by cache invalidation, allowing `_clear_directory` to remove
  files from the link target instead of rejecting the unsafe cache.
- **Regression:** Added
  `EditorExportCacheTests.test_symlinked_cache_root_is_rejected_without_clearing_target`.
  The test failed before the fix because `ExportCache.open` followed the link
  and did not raise `ExportCacheError`.
- **Fix:** Cache-root validation now uses `lstat` and rejects symbolic-link or
  non-directory roots before creation or invalidation. Child links continue to
  be removed as links rather than traversed.
- **Focused command:** `python3 -m unittest
  tests.test_editor_export_cache tests.test_editor_export_execution
  tests.test_editor_smart_render`
- **Observed:** 35 tests passed in 48.005 seconds, including the new
  symlink-safety regression and existing enhanced-export retry coverage.
- **Status:** passed.

### Post-remediation repository verification - 2026-09-04

- **Protected checks:** `make PYTHON=.venv/bin/python check` completed with
  420 tests passed, compilation, and `git diff --check`. The CLI contract
  suite completed with 35 tests passed, and the repository media smoke flow
  completed successfully.
- **Quality checks:** Formatter, Ruff lint, configured Mypy targets, Bandit,
  dependency boundary checks, pip-audit, duplication, and churn completed
  successfully. Duplication reported zero new clones; Bandit and pip-audit
  reported no findings or known vulnerabilities.
- **Known gate:** The configured complexity command still reports only the
  pre-existing `C901` finding at
  `benchmarks/restoration_benchmark.py:1794` (`16 > 15`).
- **Status:** passedWithConcerns.
