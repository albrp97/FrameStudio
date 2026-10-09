# TICKET-126 - Local Quality and CI Parity Evidence

## Context

- Chain: OBJ-001 / SCOPE-001 / PHASE-010 / FEAT-038 / TICKET-126.
- Requirement: protected workflow quality and DISC-010 delivery.
- Base: `330e13bbb451e041118304bc7f32fcf6e19b3387`.
- Branch: `phase/010-synchronized-tracks`; mode automatic through CHG-014.
- Validation profile: `rubber-duck`, `gpt-5.6-luna`, reasoning `high`,
  scope `all-validation`; exact runtime invocation confirmed availability.
- Worker: GPT-5.6 Luna max. Scope: existing test/CI repair, no product policy,
  suppression, baseline update or provider operation.

## Entries

### 2026-10-09 - Failure baseline and isolated repair

- Category: baseline/implementation; owner: agent; status: passedWithConcerns
  after exact-profile review of the raw baseline and repair.
- Before repair: 500 tests passed; quality exited 2 on the inherited
  export-panel self-clone. Report: 51 clones, 753 lines, 1.764%.
- Stale workflow called missing `tools/eval_workflows.py` and
  `ai-evals/workflow-contracts.json`; mapped `quality.yml` was absent.
- Owned paths: `.github/workflows/quality.yml`, removal of
  `.github/workflows/workflow-evals.yml`, `tests/test_editor_export_panel.py`,
  `tests/test_editor_ci_parity.py`.
- Common setup extraction retains below-50-FPS/output-route assertions.
  CI runs actual quality, CLI, generated-media smoke and production GTK
  functionality with explicit GTK/FFmpeg/Xvfb/pinned-tool prerequisites.
- Parent read and integrated only those four paths. First copy failed because
  removing the sole stale workflow removed the empty directory; parent
  created/verified `.github/workflows/` and copied the exact new files.
  No source or user changes reverted.
- Raw worker artifacts: session `files/sessionartifact-ticket126/`.

### 2026-10-09 - Integrated technical and automatic functionality validation

- Category: regression/staticAnalysis/automatedFunctionality/automaticValidation/review.
- Owner: agent; status: passed for local acceptance and review.
- Validation profile: `rubber-duck`, `gpt-5.6-luna`, reasoning `high`,
  scope `all-validation`; exact validator owns classification.
- Test IDs: `T126-quality-baseline`, `T126-ci-command-parity`,
  `REQ-010-01-selected-video-details`.
- Focused command: `python3 -m unittest tests.test_editor_ci_parity
  tests.test_editor_export_panel`; 17 passed in 2.889 seconds.
- Full command: `FRAMESTUDIO_PHASE010_ARTIFACT_DIR=<session>/files/phase010-ci-repair-gtk
  make quality PYTHON=.venv/bin/python
  STATIC_ANALYSIS_DIR=<session>/files/phase010-static-ci-repair`.
- Observed: 502 passed in 124.153 seconds; whole command exit 0.
  Compilation/diff, formatting/Ruff, mypy, complexity, dependency checks/audit,
  Bandit and churn passed. Expected negative benchmark input prints
  `--target-fps must be positive`; enclosing suite ends `OK`.
- Duplication: 50 baseline clones, 742 lines, 1.737%, zero new.
  Unchanged baseline copied to isolated report directory, SHA-256
  `a2bd1fc526d47a69a8c24d6c9d26a5c7870c3c22e2ca512e5159939879963d55`.
- Worker commands: `make contract PYTHON=.venv/bin/python` (39 passed),
  isolated `make smoke` (exit 0), and
  `python3 -m unittest tests.test_phase010_functionality.Phase010FunctionalityTests.test_selected_video_details`
  (one passed, two application snapshots).
- Boundaries/assertions: actual Makefile checks, public CLI, FFmpeg-generated
  GTK save/reopen smoke, production application/import/selection/labels/
  diagnostic/autosave and source hashes. Workflow-string unit assertions are
  additional guards, never execution evidence alone.
- Artifacts: session `files/phase010-ci-repair-quality.log`,
  `files/phase010-static-ci-repair/`, `files/sessionartifact-ticket126/`.
- Exact review found no local remediation or baseline waiver. Defined local
  and CI commands/tools/configuration/rules/scopes/thresholds/baseline/exit
  policy match; actual remote parity remains pending.

### 2026-10-09 - Remote/runtime and delivery boundary

- Category: gate; owner: agent; status: blocked for delivery, not independent
  product implementation.
- Validation profile: `rubber-duck`, `gpt-5.6-luna`, reasoning `high`,
  scope `all-validation`.
- Local: Python 3.14.7, GTK 4.22, existing display. Actual Ubuntu 24.04
  Python/GI/GTK/Xvfb execution is not yet available.
- Snapshot `to_node`, native `render_texture` and PNG portability are a remote
  boundary, not a confirmed defect or inferred pass. Local Xvfb/container
  capability is unavailable; no new dependency or silent fallback added.
- No remote CI run, commit, push, PR, merge or closeout occurred.
  TICKET-126 stays open in `verifying`; integrated125 consumes its maintenance
  result, while final delivery still requires actual provider evidence.

### Native input prerequisites and window-manager-free focus

New actual T117/T111 XTest charters require `xdotool`, but the workflow
previously installed neither it nor a window manager. Their
`windowactivate` helper depended on `_NET_ACTIVE_WINDOW`, unavailable on
bare Xvfb. Parent's new CI regression first failed on the missing tool.
Artifact: session `phase010-native-ci-parity-red.log`.

Parent added the required existing input utility and an explicit executable
guard, and fixed X11 selection for the initial GTK check and all four
execution flows. The T117 helper now uses direct `windowfocus --sync`
against its uniquely titled fixture, avoiding a new window-manager
dependency. The T111 worker applied the same change in its owned test.
No production gesture, application, system permission or baseline changed.

Three CI contract checks plus the strict real T117 physical pointer,
modifier/key, collision, clipboard, split, persistence and source-hash
charter passed: **4 tests in 3.123 seconds**, zero skips/errors.
Ruff format/lint and diff checks passed. Configured duplication remained
**46 clones, 1.047%, zero new**, unchanged baseline. Artifacts: session
`phase010-native-ci-parity-final.log` and
`phase010-native-ci-parity-static.log`.

Exact validator `c15ca413-4e1d-4a85-b995-5f7d558d2505`, turn 5,
classified **bounded local T117/T126 PASS** under the configured profile.
Actual Ubuntu/bare-Xvfb/provider execution remains unverified and blocks
delivery readiness. Workflow assertions and workstation input are not
reported as a remote CI run.

### Final Cairo runtime correction and shared verification

The final configuration-only CI guard first reproduced the missing
`python3-gi-cairo` dependency. The workflow now installs it and explicitly
requires the Cairo foreign bridge in system and virtual-environment GTK
verification. This is the runtime needed by actual timeline draw callbacks,
not a new GUI architecture or dependency manager.

Three final CI guards and real workstation GTK/Cairo initialization pass:
`files/phase010-ci-cairo-bridge-final.log`. The final configured static suite
passes: `files/phase010-root-final-ci-static.log`. The canonical shared
production suite completed **719 cases, OK, no skips**, **42 CLI contracts,
OK**, and both generated-media GTK smoke flows:
`files/phase010-root-final-cancellation-complete-quality.log`.
No production source changed after that complete runner.
Duplication is 46 existing clones, 0.905%, zero new; baseline SHA-256 remains
`a2bd1fc526d47a69a8c24d6c9d26a5c7870c3c22e2ca512e5159939879963d55`.

Exact validator `d3c2c166-b1dc-4485-9583-e30a348b34ba`, turn 8,
`rubber-duck / gpt-5.6-luna / high / all-validation`,
classified final local technical/automatic functionality/review evidence
PASS and authorized bounded commit/push. Actual Ubuntu/provider execution
and delivery closure remain pending, not inferred from the local guards.

### Actual Ubuntu execution and scoped follow-up

Published source commit `70a26cb23f361ff46d9389827c63a075cef8123b`
ran Quality workflow `37993006614`. Actual runtime/tool installation,
system checks and virtual-environment GTK verification succeeded.
The discovered suite then failed 10 cases, with one supplemental RVE skip,
in 467.416 seconds. Later contracts/smoke/charter stages did not run.
Raw log: `files/phase010-provider-first-failure.log`.
These facts replace the previously unavailable-provider observation, not the
historical workstation PASS; remote readiness is failed.

The CI-shaped TMPDIR fixture assumption was reproduced locally and corrected
without changing benchmark production code or privacy formatting. Both
outside-HOME basename and inside-HOME tilde outputs are asserted.
All 13 benchmark cases pass under that TMPDIR arrangement.
Repeated native pointer targeting no longer relies on the older xdotool
no-op synchronization behavior; actual server coordinates are asserted
before click dispatch. All five Backspace/Undo native cases pass.
The initial empty snapshot now waits for a real bounded GTK frame and native
texture; the strong integrated Root charter passes in 39.883 seconds.

Exact validator turns 10/11 classify these focused corrections PASS.
Final configured static/compile/diff gates pass:
`files/phase010-provider-root-portability-final-static.log`.
Turn 12 distinguishes the supplemental GPU/RVE skip, already executed on
the real workstation, from mandatory portable/native CI coverage.
FFmpeg 6 frame/framing remediation and actual final provider reexecution
remain required before closure.

### Final bounded observer and display geometry

The shared functionality observer's unbounded GLib pending-event drain was
reproduced with a deterministic continuously pending context, then replaced
with a bounded nonblocking iteration per round. Interrupted affected runners
are not PASS evidence. Strict native pointer checks then exposed a planner
button center below the physical screen. The uniquely titled fixture is
positioned at the origin, and all five CI Xvfb screens now use 1920x1200.
Regression/parity/native/strong-journey coverage passes 10 cases in 50.747
seconds: `files/phase010-provider-final-bounded-gtk.log`.
Final configured static, compile and diff checks pass:
`files/phase010-provider-final-bounded-static.log`.
An isolated FFmpeg 6.1 run passes five of seven affected cases but exposes
two workstation-RVE/runtime differences requiring explicit disposition.
Neither this partial result nor the successful local geometry proof replaces
the required final Ubuntu provider execution.

The existing native-display parity guard now checks every actual Xvfb
invocation's 1920x1200 screen geometry. It fails against the published
1280x720 workflow and all three guards pass against the corrected workflow:
`files/phase010-ci-geometry-red-green.log`. Final configured static/compile/
diff checks were rerun after this guard, with the unchanged baseline reporting
46 total clones and zero new clones.

Exact validator turn 16 grants bounded local commit/non-force-push GO after
the corrected authentic FFmpeg 6.1 / empty-HOME eight-case run and final
configured static/compile/diff gates pass. The existing final compositor's
RVE availability behavior is reused by standalone source planning. No baseline
update or check waiver is introduced. The required replacement Ubuntu run and
lifecycle closeout remain pending.
