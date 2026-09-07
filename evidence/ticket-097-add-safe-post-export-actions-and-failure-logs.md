# TICKET-097 Evidence - Safe Post-Export Actions

**Status:** verifying
**Date:** 2026-09-06
**Branch:** `ticket/defer-audio-analysis-during-import`
**Scope:** Prevent unintended system power actions while preserving explicit
post-export sleep and shutdown behavior.

## Requirements

- The export panel default remains `Nothing`.
- Explicit sleep or shutdown remains dispatched only after export completion
  or after a failure log has been written.
- Automated tests must not invoke real `systemctl suspend` or
  `systemctl poweroff` commands.
- Dispatch failures remain visible to the caller.

## Baseline

**Command:** `journalctl -b -1 --no-pager -n 200`

**Observed:** The previous boot recorded both `poweroff requested from client
PID ... ('systemctl')` and `suspend requested from client PID ... ('systemctl')`
at approximately 21:04:44 while the full test run was being attempted.

**Root cause:** `execute_post_export_action()` captured `shutil.which` and
`subprocess.run` in default argument values at module import time. Tests patched
the module attributes, but the function continued using the original real
callables.

**Status:** failed baseline; reproduced by system journal evidence.

## Implementation

Changed `execute_post_export_action()` to resolve `shutil.which` and
`subprocess.run` at call time when no dependency is explicitly supplied.
Existing explicit dependency injection remains supported.

Added regression coverage proving that module-level patches are honored for
default dispatch and that the test suite uses mocked power-command execution.

## Verification

| Command | Expected | Observed | Status |
|---|---|---|---|
| `python3 -m unittest tests.test_editor_post_export` | All post-export safety tests pass without a power action | 6 tests passed | passed |
| `python3 -m unittest tests.test_editor_post_export tests.test_editor_performance` | Focused export completion regressions pass | 17 tests passed | passed |
| `make compile` | Python sources compile | Passed | passed |
| `make contract` | CLI contract tests pass | 37 tests passed | passed |
| `make smoke` | Generated-media smoke flows pass | Passed | passed |
| `make PYTHON=.venv/bin/python lint` | Lint passes | Passed | passed |
| `make PYTHON=.venv/bin/python type-check` | Type checks pass | Passed | passed |
| `make PYTHON=.venv/bin/python security` | Security analysis completes | Passed; report in `evidence/static-analysis/bandit.json` | passed |
| `make test` | Full suite passes | 447 passed, 1 unrelated fixture error in `test_empty_edit_refresh_stops_preview_without_reporting_an_error` | passedWithConcerns |

After the fix, the current boot journal contains no new `poweroff requested`
or `suspend requested` entries from the test run.

## Coverage gaps and blockers

- The full suite still has one unrelated pre-existing test-fixture failure in
  `tests/test_editor_composition.py`; it is outside this safety fix.
- The repository Makefile invokes system Python for `format-check`, `lint`, and
  `type-check`; system Python lacks Ruff and mypy. The configured checks were
  rerun successfully with the repository `.venv`.
- Target-workstation validation with the default `Nothing` action remains
  pending user confirmation.

## User validation

The ticket remains open and verifying until the user confirms the default
export action does not suspend or power off the workstation and returns
`PASS`, `FAIL`, `BLOCKED`, or approved `NOT APPLICABLE`.

### User-validation closeout - 2026-09-07

- **User response:** `PASS` — the user confirmed the implemented ticket set
  is good.
- **Status:** passed; this supersedes the earlier pending user-validation
  state.
