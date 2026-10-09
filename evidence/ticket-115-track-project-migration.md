# TICKET-115 - Track Project Migration Evidence

## Context

- Chain: OBJ-001 / SCOPE-001 / PHASE-010 / FEAT-035 / TICKET-115.
- Requirement: DISC-010 / REQ-010-04.
- Base: `330e13bbb451e041118304bc7f32fcf6e19b3387`.
- Mode: guided; implementation/delegation authorized 2026-10-09.
- Integration owner: orchestrator; bounded agent: GPT-5.6 Luna max.
- Protected flows: source and segment identities, legacy retained timing,
  source bytes, exclusions/modifications, saves/autosave/recovery and facades.

## Entries

### 2026-10-09 - Design discovery and user approval

- Category: planning; owner: agent; status: passedWithConcerns.
- Read-only design agent inspected existing model/persistence/operations and
  reported a conflict between excluded-block visible occupancy, legacy
  compact output and new synchronized absolute time.
- Artifact: `docs/specs/track-project-migration-contract.md`, DESIGN-010-115.
- No model code or migration functionality pass resulted from this analysis.
- Category: gate; owner: user; status: passed (design approval only).
- Clarification response: synchronized Delete keeps time fixed, filled by
  other active tracks or black/silence; legacy conversion requires explicit
  confirmation and preserves visible positions; proposed v4 contract approved.
- This response is not `userValidation` of an implemented feature.

### 2026-10-09 - Protected baseline reference

- Category: baseline; owner: agent; status: passed.
- Command: `python3 -m unittest discover -s tests`.
- Observed: 496 tests passed before first-wave changes.
- Agent-run compilation, 39 CLI contracts and generated-media GTK smoke also
  passed; raw artifacts are session `files/phase010-baseline-tests.log` and
  `files/phase010-baseline-boundaries.log`.
- Existing duplication/CI-parity blockers are recorded in TICKET-109 evidence
  and remain applicable; no quality or delivery waiver is inferred.

## Current gates

Model implementation, migration functionality, final technical review and
guided validation are pending. TICKET-115 remains open and is not ready for
dependent implementation or closeout until its shared interface is verified
and applicable gates are satisfied.

### 2026-10-09 - Approved isolated implementation dispatch

- Category: implementation; owner: agent; status: passedWithConcerns
  (dispatch only, implementation results pending).
- Same retained GPT-5.6 Luna max agent continues TICKET-115 on isolated
  `phase/010-ticket-115`; parent copied the approved contract to its snapshot.
- Ownership is model/persistence and minimum inspection compatibility, not
  metadata UI, placement, Undo, composition/audio or export/session code.
- Required acceptance command is now
  `python3 -m unittest tests.test_editor_track_migration_functionality.TrackMigrationFunctionalityTests.test_track_project_migration`.
  This separate module avoids TICKET-109's GTK fixture state and requires
  actual CLI/JSON/persistence/autosave assertions. It is not yet implemented
  or passed in the integration worktree.
- Delegate must report unsupported interim GUI/export boundaries explicitly;
  no multi-track renderer capability is inferred from schema support.

### 2026-10-09 - Automatic authorization and blocking scoped review

- Category: gate/review; owner: agent; status: failed for the initial
  migration/persistence implementation; retained-worker remediation active.
- Validation profile: `rubber-duck`, `gpt-5.6-luna`, reasoning `high`,
  scope `all-validation`; exact runtime invocation confirmed capability.
- CHG-014 supersedes historical guided waits. Routine authorization is
  autonomous; no human functionality result is required or fabricated.
- Initial raw results: 44 focused/affected tests and 504 full-suite tests
  passed, plus one CLI/persistence functionality test. These are not a
  migration gate pass because public-boundary reproductions failed.
- Reproduction: `Project.create`/`create_synchronized`, `timeline.set_deleted`,
  `save_project`, `load_project`, isolated synthetic model-only fixtures with
  declared 320x180, 10 FPS metadata.
- Failure 1: v2 load returns schema 2, legacy-ripple and no track IDs;
  canonical v4 legacy-ripple normalization is missing. Schema migration is
  incorrectly conflated with confirmed absolute timing conversion.
- Failure 2: excluding the only block in a 10-second synchronized project
  leaves project/editing/final durations 10/10/0. Save rejects with
  `Project segment timeline duration must match project duration`.
- Failure 3: duration `10.0000004` saves but fails on reopen with
  source-duration mismatch; quantized ticks and original floating metadata
  are compared using incompatible `1e-9` tolerance.
- Exact validator classified all three as blocking despite wider test counts.
- Fix returned to the same worker: separate schema/timing migration, retain
  legacy operations/render projection, reconcile editing/final/playhead
  persistence, use one integer-tick contract, remove typing erasure, provide
  generated-video CLI/migration/render-plan assertions and no new duplication.
- Initial implementation is not integrated. Consumers110/112/116/119 wait
  for the verified interface; read-only119 design is not implementation.
- No publication, closeout or synchronized renderer pass is claimed.

### 2026-10-09 - Canonical migration and resume remediation checkpoint

- Category: implementation/technical; owner: retained agent; status:
  passedWithConcerns, isolated raw results only.
- Worker reports v1/v2/v3 load normalization to canonical v4 legacy-ripple,
  explicit confirmed absolute conversion, distinct editing/final durations
  and source-duration validation using canonical microsecond ticks.
- Resume RED: the changed implementation failed
  `test_export_resumes_after_cli_process_restart` in6.001s, while a clean
  `330e13b` baseline passed in1.009s. It was not a pre-existing failure.
- Root cause: one-source canonical legacy migration incorrectly projected
  `mixed_source=True`, changing the export route after process restart.
- GREEN: corrected model projection and minimum CLI split compatibility;
  resumed export passed in1.106s without modifying export/cache/session code.
- Reported isolated results:172 affected tests,510 full-suite tests in134.549s,
  real generated-media migration functionality in24.623s, Ruff, compilation,
  mypy55 source files and pinned jscpd5.0.16 with zero introduced clones.
- Raw logs are `.ticket115-resume-debug/{current-test.log,
  current-test-final.log,full-suite-restored-final.log,
  functionality-restored-final.log,duplication-final.log}` in the isolated
  worktree. Copied parent126 export-panel baseline correction is not115-owned.
- Parent reviewed canonical model/track/range/persistence projections.
  Additional tightly coupled safety work remains: reject boolean timeline
  versions and malformed timing modes with project-validation errors, and
  explicitly guard unsupported absolute export/playback boundaries rather
  than flattening tracks through legacy consumers.
- Parent authorized those narrow temporary consumer guards. They do not
  implement synchronized preview/render and must be replaced by verified
  owning consumers later.
- The candidate is still **not integrated**. No terminal aggregate115
  `automaticValidation`, shared-interface freeze or downstream implementation
  dispatch is inferred from these isolated counts.

### 2026-10-09 - Parent integration and shared-interface release

- Category: integration/technical; owner: orchestrator; status: passed.
- Applied only115-owned source/test changes, retaining109 audio-failure
  diagnostics in the overlapping `app_project.py`. Added temporary absolute
  export/playback guards and malformed-version/timing-mode regressions.
- Parent combined `make quality PYTHON=.venv/bin/python` exited0:520 tests
  in188.053s, mypy55 source files and all configured local checks passed;
  unchanged duplication baseline,46 clones, zero introduced clones.
- Log: session `files/phase010-after115-quality.log`. Real104 export integrity,
  migration/CLI/persistence functionality and existing recovery selectors are
  included in this combined run.
- Category: `automaticValidation`; owner: exact `rubber-duck /
  gpt-5.6-luna / high / all-validation`; status: PASS for shared-interface
  readiness and112/116/119 preimplementation only.
- Validator independently ran migration unit/functionality and the exact CLI
  process-restart resume selector:16 tests, zero failures/errors/skips,
  exit0 in33.447s.
- Validator has read-only file permissions. Its classified JSON decision was
  transcribed with explicit attribution to session
  `files/migration115-interface-gate/decision.json`; the parent did not
  substitute its own validation profile.
- User requested accelerated implementation.112,116 and119 are now executing
  on isolated branches with disjoint file ownership. Workers use focused
  checks and actual functionality tests; the parent owns combined quality.
- This releases dependent implementation, not ticket/phase delivery or remote
  CI.115 remains in `open`, status `verifying`; no commit/push/closure claimed.

### 2026-10-09 - Terminal local review and real GTK delta

- Exact `rubber-duck / gpt-5.6-luna / high / all-validation` accepted115 local
  automatic functionality/review and104's bounded post115 prerequisite using
  the terminal520-test combined run and its independent16-test focused flow.
- Additional executable production-GTK selector:
  `tests.test_phase010_functionality.Phase010FunctionalityTests.test_migrated_project_reopens_and_displays_playback`.
  Passed1 test in1.175s, with Ruff format/lint/diff checks and zero new clones.
- This opens real generated sources in a registered NON_UNIQUE production
  application, waits for import completion, saves and reopens through window
  commands, verifies v4 legacy-ripple/stable IDs, clears the old preview and
  waits for a newly decoded FFmpeg paintable, seeks0.25s and checks source hashes.
- Exact validator accepted the GTK delta without rerunning the full suite.
  The520-test checkpoint precedes this added test; the next combined wave
  includes it. No521-test full-suite result is claimed.
- Two earlier ad hoc smoke attempts failed due to asynchronous harness setup
  and an incorrect widget field. Their logs remain session
  `files/phase010-after115-gtk-smoke{,-corrected}.log`; the passing executable
  production-window test supersedes them, not a claimed smoke-script pass.
- Remote CI and delivery/merge remain unrun.112/116/119 implementation proceeds
  concurrently on isolated branches; this additional test does not change
  their frozen shared-interface gate.
