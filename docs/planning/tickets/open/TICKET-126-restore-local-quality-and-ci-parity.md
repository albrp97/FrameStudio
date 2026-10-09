# TICKET-126 - Restore Local Quality and CI Parity

**Ticket ID:** TICKET-126
**Parents:** OBJ-001, SCOPE-001, PHASE-010, FEAT-038
**Capability links:** CAP-012
**Status:** verifying
**Approval:** autonomous repair authorized 2026-10-09 through CHG-014
**Requirements:** protected workflow quality and DISC-010 delivery gates
**Dependencies:** existing Makefile, pinned quality tools and approved baseline
**Affected surfaces:** `.github/workflows/`, `tests/test_editor_export_panel.py`,
`tests/test_editor_ci_parity.py`, and native track-drag test display focus
**Evidence path:** `evidence/ticket-126-local-quality-ci-parity.md`
**Path history:** created in `tickets/open/` on 2026-10-09

## Objective, scope and non-goals

Restore executable quality/CI parity needed for PHASE-010 readiness. Refactor
only the inherited export-panel self-clone while preserving enhancement cutoff
assertions. Replace the stale evaluation job referencing a missing script with
the repository's actual Makefile quality checks and compatible system
GTK/FFmpeg tooling.

No product behavior, new quality framework, weakened rule, duplication
suppression, baseline acceptance/update or publication is in scope.

## Observable acceptance

- Given the current export-panel tests and unchanged approved duplication
  baseline, the existing checks should pass without the inherited self-clone,
  retaining strict below-50-FPS and output-route assertions.
- Given the repository CI definition, its executable quality command should
  match the local pinned-tool/configuration/rule/scope/baseline/exit policy
  and run actual CLI/GTK functionality, rather than a nonexistent script.
- Given unavailable required tooling or a failed check, the job should fail
  explicitly; GUI functionality must not silently skip.

## Verification and automated functionality

Run focused export-panel tests, configured duplication and actual quality
commands. Record tool versions and exact local/CI comparison. Use the existing
production-boundary GTK test and supported CLI contract as acceptance:

```sh
make quality PYTHON=.venv/bin/python
make contract PYTHON=.venv/bin/python
python3 -m unittest tests.test_phase010_functionality.Phase010FunctionalityTests.test_selected_video_details
```

Exercise generated-media smoke in an isolated temporary directory and execute
CI-equivalent display configuration when available. CI service results remain
separate remote evidence, not inferred from a local command.

## Parallel ownership and completion

Isolated workflow/export-panel-test ownership; no writes to model, metadata
UI, other agents' tests, shared evidence/index/config, or quality baseline.
The orchestrator owns integration, exact-profile automatic validation, final
checks and delivery. Keep this record open until those gates and configured
closeout are terminal.
