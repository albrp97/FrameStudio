# TICKET-082 Evidence - Triplicate Default-Zoom Horizontal Offset

**Phase:** PHASE-008  
**Feature:** FEAT-025  
**Ticket:** TICKET-082  
**Branch:** `ticket/phase-008-responsive-preview-media-strategy`  
**Base revision:** `93b49e8`  
**Evidence status:** technical verification passed; user validation pending

## Contract

The fix permits bounded horizontal source selection for an enabled triplicate
segment at `1.0x` zoom. The default-zoom X range is `-640..640` fixed
1920x1080-canvas pixels, matching the three 640-pixel output columns. Default
Y remains `0`; zoom `2.0x` and above retain their established bounds and
mapping. Normal full-canvas rendering remains visually centered at `1.0x`.

## Evidence entries

### E-082-001 - Focused regression coverage

- **Category:** regression
- **Requirement:** model, GUI-control, filter, CLI, and persistence behavior
- **Command:** `python3 -m unittest tests.test_editor_composition tests.test_editor_cli_parity tests.test_editor_persistence`
- **Expected:** default-zoom positive and negative offsets are accepted,
  bounded, shared, persisted, exposed by controls, and rendered.
- **Observed:** 52 tests passed.
- **Status:** passed
- **Artifacts:** `tests/test_editor_composition.py`,
  `tests/test_editor_cli_parity.py`, `tests/test_editor_persistence.py`

### E-082-002 - Generated-media movement

- **Category:** functionality
- **Requirement:** left, centered, and right default-zoom triplicate crops
  produce distinct output frames without changing the output canvas.
- **Steps:** the generated-media regression created an asymmetric 1920x1080
  source, rendered offsets `-640`, `0`, and `640`, probed every result, and
  compared first-frame `framemd5` values.
- **Expected:** all three outputs remain `1920x1080` and have distinct frame
  digests.
- **Observed:** all three output dimensions were `1920x1080`; all three frame
  digests differed.
- **Status:** passed
- **Artifacts:** temporary FFmpeg outputs are removed by the test.

### E-082-003 - Protected repository checks

- **Category:** gate
- **Commands:** `make check`, `make contract`, `make smoke`
- **Expected:** existing behavior remains functional and editor CLI/media
  flows remain valid.
- **Observed:** `make check` passed 357 tests, compilation, and diff checks;
  `make contract` passed 35 tests; `make smoke` passed.
- **Status:** passed

### E-082-004 - Local static analysis

- **Category:** staticAnalysis
- **Commands:** `make quality PYTHON=.venv/bin/python`,
  `make duplication PYTHON=.venv/bin/python`,
  `make dependency-check PYTHON=.venv/bin/python`,
  `make dependency-audit PYTHON=.venv/bin/python`,
  `make security PYTHON=.venv/bin/python`, `make churn`
- **Expected:** configured local quality checks complete without introduced
  findings.
- **Observed:** format, lint, type-check, duplication, dependency check,
  dependency audit, security, and churn passed. The aggregate quality command
  stopped at the pre-existing complexity finding
  `benchmarks/restoration_benchmark.py:1794` (`run_benchmark`, C901 16 > 15);
  this is outside TICKET-082.
- **Status:** passedWithConcerns
- **Artifacts:** `evidence/static-analysis/jscpd-report.json`,
  `evidence/static-analysis/dependencies.json`,
  `evidence/static-analysis/pip-audit.json`,
  `evidence/static-analysis/bandit.json`,
  `evidence/static-analysis/churn.json`
- **Accepted warning:** the pre-existing complexity finding prevents the
  aggregate quality target from being terminal.

## Coverage gaps and blockers

- Physical GTK gestures and visual preview screenshots were not automated.
- A target-workstation user must confirm the visible left/center/right preview
  movement and save/reopen behavior.
- Remote CI parity is unavailable because no repository remote is configured.
- The ticket remains open until the configured user-validation response and
  review/delivery gates are terminal.

## User-validation handoff

1. Open a project containing a landscape or portrait source and enable
   **Triplicate**.
2. Leave **Zoom** at `1.00x`.
3. Move **X** to a negative value, then to a positive value, and compare the
   preview with X at `0`.
4. Save and reopen the project; confirm the selected X value and triplicate
   linkage remain unchanged.
5. Optionally run `framestudio focus <project> --segment <id>
   --offset-x 640` and inspect the JSON result.

Expected result: the repeated source region moves horizontally while the
three-column 1920x1080 layout remains intact, Y stays centered, and the source
media is unchanged.

Return one terminal response: `PASS`, `FAIL`, `BLOCKED`, or approved
`NOT APPLICABLE`, including the observed positions and any output metadata.

### E-082-005 - Final post-change regression rerun

- **Category:** gate
- **Commands:** `make check`, `make format-check
  PYTHON=.venv/bin/python`, `make lint PYTHON=.venv/bin/python`,
  `make type-check PYTHON=.venv/bin/python`
- **Expected:** the final source and test state remains formatted, typed, and
  regression-safe.
- **Observed:** 357 tests passed; compilation and diff checks passed; Ruff
  format/lint and all configured mypy targets passed.
- **Status:** passed

### E-082-USER-VALIDATION-001 - User-confirmed manual validation

- **Timestamp:** 2026-08-28T08:06:41+02:00
- **Category:** userValidation
- **Requirement:** Default-zoom triplicate horizontal offsets, persistence,
  CLI parity, preview/export behavior, and source preservation are manually
  validated.
- **Steps:** The user stated, "you can close all the tickets i manually
  validated everything and you can then /aidd-commit".
- **Observed:** The user reports that the ticket behavior was manually
  validated. This response did not include a per-ticket output path,
  metadata capture, or separate failure-path notes.
- **Status:** passed
- **Accepted warning:** This terminalizes user validation only; remote
  parity and the remaining delivery-policy requirements stay unresolved.

### E-082-READINESS-002 - Current delivery state after user validation

- **Timestamp:** 2026-08-28T08:06:41+02:00
- **Category:** gate
- **Requirement:** Do not close or deliver the ticket while required review,
  remote-parity, and commit prerequisites remain nonterminal.
- **Observed:** User validation is recorded as passed. Remote CI parity is
  unavailable, the branch is shared across Phase 8, no paths are staged, and
  no commit or remote delivery exists.
- **Status:** blocked
- **Blocker:** Remote/delivery and commit-scope prerequisites are unresolved.
