# TICKET-101 Evidence - Preserve the CLI Export Resume Contract

**Status:** verifying
**Date:** 2026-09-06
**Repository:** `/home/ghiki/code/FrameStudio`
**Branch:** `ticket/defer-audio-analysis-during-import`
**Planning chain:** OBJ-001 -> SCOPE-001 -> PHASE-008 -> FEAT-029 -> TICKET-101
**Change control:** CHG-010

## Scope and requirements

The ticket requires explicit CLI resume, restart, and discard semantics,
backward-compatible fresh export behavior, valid JSON Lines output, separate
human progress on stderr, request-identity validation, and process-restart
coverage with real generated media.

Affected implementation:

- `framestudio/cli_parser.py`
- `framestudio/cli_export.py`
- `framestudio/cli.py`
- `framestudio/export.py`
- `framestudio/export_console.py`
- `docs/specs/cli-contract.md`
- `README.md`
- `tests/test_editor_cli_export.py`

## Implementation

The CLI export parser now accepts mutually exclusive `--resume`, `--restart`,
and `--discard` actions. Export emits structured `export.session` events
without contaminating JSON Lines stdout with human progress. Resume validates
the shared session request identity and reports prior completed stages,
reused artifacts, mismatch reasons, and terminal status. Existing invocations
without a mode remain fresh exports.

## Verification

| Requirement or flow | Command or steps | Expected | Observed | Status |
|---|---|---|---|---|
| CLI process restart and resume | `python3 -m unittest tests.test_editor_cli_export.EditorCliExportTests.test_export_resumes_after_cli_process_restart` | A new process resumes after the first process is interrupted | Generated 1920x1080 video-only media was interrupted after `cut-0`; `--resume` returned 0, emitted parseable JSON Lines, reported a previous completed stage, published verified output of approximately 3 seconds, preserved source bytes, and left no matching FFmpeg process | passed |
| CLI contract suite | `make PYTHON=.venv/bin/python contract` | Existing and new CLI contract behavior passes | 38 tests passed | passed |
| Session event and JSON Lines behavior | `python3 -m unittest tests.test_editor_cli_export` | Session events are structured and machine-readable | 38 CLI export tests passed; JSON Lines were parsed in the process-restart flow | passed |
| Fresh export compatibility | Existing CLI export tests in `tests/test_editor_cli_export.py` | No resume flag preserves fresh behavior | Existing fresh and resume/restart/discard tests passed within the CLI module | passed |
| Source preservation and final publication | Included in process-restart generated-media flow | Source is unchanged and destination appears only after verification | Source snapshot remained identical; the final destination existed after verified resume and the session directory was removed | passed |
| Full repository regression | `make PYTHON=.venv/bin/python test` | Protected behavior remains functional | 453 tests ran; 452 passed and one known unrelated composition fixture error remains | passedWithConcerns |

## Quality gates

The final repository gates were run after the last formatting changes:

- `make PYTHON=.venv/bin/python compile` passed.
- `make PYTHON=.venv/bin/python smoke` passed.
- `make PYTHON=.venv/bin/python format-check` passed with 93 files formatted.
- `make PYTHON=.venv/bin/python lint` passed.
- `make PYTHON=.venv/bin/python type-check` passed.
- `make PYTHON=.venv/bin/python security` passed.
- `make PYTHON=.venv/bin/python dependency-check` passed.
- `make PYTHON=.venv/bin/python dependency-audit` found no known vulnerabilities.
- `make diff-check` passed.
- `make PYTHON=.venv/bin/python churn` passed.

The configured complexity gate reports an unchanged benchmark function at
complexity 16 versus a threshold of 15. Duplication reports 2.2% versus
2.0%, with zero new clones. These reports are accepted concerns and are not
CLI-contract regressions.

## User validation

The user must run the canonical CLI with a disposable saved project, start an
export, cancel it, rerun with `--resume`, and inspect both stderr stage
progress and stdout JSON Lines. The user should also exercise `--restart` and
`--discard`, then repeat with a changed destination or source to confirm
identity mismatch is explicit and no source is modified.

**Status:** blocked pending user-run CLI validation and response.

## Readiness

CLI parser, event, JSON Lines, process-restart, checkpoint reuse, and source
preservation behavior are technically verified. The ticket remains open and
`verifying` until the configured user-validation response is recorded.

### User-validation closeout - 2026-09-07

- **User response:** `PASS` — the user confirmed the implemented ticket set
  is good.
- **Observed:** The user accepted explicit CLI resume behavior, staged
  console output, JSON Lines preservation, and source safety.
- **Status:** passed; this supersedes the earlier blocked validation state.

### Superseding full-suite regression - 2026-09-07

- **Command:** `.venv/bin/python -m unittest discover -s tests`
- **Observed:** 453 tests ran in 103.461 seconds and all passed after the
  empty-edit fixture correction.
- **Status:** passed; this supersedes the earlier full-suite fixture error
  recorded above.
