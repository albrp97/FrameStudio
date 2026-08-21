# Evidence - TICKET-012

**Phase:** PHASE-003  
**Feature:** FEAT-007  
**Ticket:** TICKET-012  
**Objective:** OBJ-001  
**Scope:** SCOPE-001  
**Status:** baseline  
**Planning chain:** `OBJ-001 -> SCOPE-001 -> CAP-004/CAP-006/CAP-012 ->
PHASE-003 -> FEAT-007 -> TICKET-012`  
**Repository:** `/home/ghiki/code/resolve-media-tui`  
**Branch:** `main`  
**Base revision:** `150d2f7`  
**Dependency evidence:** `evidence/verified-safe-export.md`,
`evidence/persist-cut-state-recovery.md`  
**Evidence path:** `evidence/phase-003-cli-contract.md`

## Requirements

- Define a versioned machine-readable success contract.
- Define structured errors and non-success exit statuses.
- Preserve stable project, source, and segment identifiers.
- Redact local paths by default with explicit full-path opt-in.
- Define deterministic output and compatibility behavior.

## Protected flows

Existing project serialization, source identity, segment invariants, atomic
project saves, safe export behavior, GUI interactions, legacy scripts, and
the complete repository test suite remain protected.

## E-1201 - Protected baseline

- **Category:** baseline
- **Command:** `make check`
- **Expected:** Existing editor and legacy behavior passes before CLI changes.
- **Observed:** 99 tests passed, Python compilation passed, and
  `git diff --check` passed. The existing PyGObject deprecation warning was
  emitted.
- **Status:** passedWithConcerns
- **Artifacts:** terminal output; existing repository test suite.
- **Failure:** none.
- **Fix:** none.
- **Accepted warning:** `GLib.unix_signal_add_full` is deprecated in the
  installed PyGObject bindings.

## E-1202 - Intentional TDD red state

- **Category:** baseline
- **Command:** `python3 -m unittest tests.test_editor_cli_contract`
- **Expected:** New contract tests fail because the CLI contract has not yet
  been implemented.
- **Observed:** Test collection failed because `resolve_editor.cli` does not
  exist.
- **Status:** passedWithConcerns
- **Artifacts:** `tests/test_editor_cli_contract.py`; terminal output.
- **Failure:** expected missing implementation.
- **Fix:** implement the contract and CLI adapter.
- **Accepted warning:** This is an intentional red-state test-first record.

## E-1203 - Contract implementation and focused verification

- **Category:** implementation
- **Command:** `python3 -m unittest tests.test_editor_cli_contract`
- **Expected:** Versioned success/error payloads, path redaction, full-path
  opt-in, and malformed-argument handling pass.
- **Observed:** 5 tests passed.
- **Status:** passed
- **Artifacts:** `resolve_editor/cli.py`,
  `tests/test_editor_cli_contract.py`.
- **Failure:** The initial parser implementation passed an unsupported
  `parser_class` keyword to `add_parser`.
- **Fix:** Configured the JSON parser class on `add_subparsers`, then reran
  the focused suite successfully.

## E-1204 - Contract documentation review

- **Category:** review
- **Command or steps:** Reviewed the implemented command grammar, payload
  fields, exit statuses, redaction behavior, progress framing, and version
  evolution rules against TICKET-012 and FEAT-007.
- **Expected:** The documented contract matches the implementation without
  claiming deferred multi-source or composition capabilities.
- **Observed:** Contract documentation is recorded in
  `docs/specs/cli-contract.md` and linked from `README.md`.
- **Status:** passed
- **Artifacts:** `docs/specs/cli-contract.md`, `README.md`,
  `Makefile`, `resolve_editor.py`.
- **Failure:** none.
- **Fix:** none.

## Final readiness

- **Passed:** E-1203 and E-1204.
- **Passed with concerns:** E-1201 through E-1204 because the existing
  PyGObject deprecation warning remains non-failing.
- **Failed:** none.
- **Blocked:** no local contract blocker.
- **Remote checks:** required by `.github/aidd-config.yml`, but unavailable
  in this environment.
- **Readiness:** The TICKET-012 implementation and local contract evidence
  are complete; the ticket record remains open for the configured review and
  delivery lifecycle.
