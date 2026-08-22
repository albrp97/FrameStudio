# Editor Architecture Refactor Evidence

**Ticket:** TICKET-030
**Feature:** FEAT-013
**Phase:** PHASE-004A
**Date:** 2026-08-22
**Status:** implementation, local verification, and user validation complete;
commit pending
**Baseline revision:** `b624234` before the uncommitted refactor
**Worktree:** `ticket/phase-004-mixed-source-footage`

## Outcome

The editor now uses focused implementation modules behind the established
`resolve_editor.app`, `cli`, `model`, `export`, and `timeline` compatibility
paths. Existing GUI, CLI, persistence, playback, editing, export, and legacy
script behavior remains covered by the protected regression suite.

## Module-size evidence

The baseline values are line counts from the baseline revision. The post-change
values are working-tree line counts.

| Compatibility surface | Baseline | Post-change | Focused responsibility |
|---|---:|---:|---|
| `resolve_editor/app.py` | 1060 | 463 | GTK application lifecycle and orchestration |
| `resolve_editor/cli.py` | 693 | 532 | CLI dispatch and compatibility seams |
| `resolve_editor/model.py` | 533 | 34 | Model compatibility facade |
| `resolve_editor/export.py` | 936 | 31 | Export compatibility facade |
| `resolve_editor/timeline.py` | 648 | 490 | GTK timeline compatibility surface |
| `resolve_editor/ffmpeg_playback.py` | 473 | 576 | Raw-frame playback backend |

Focused implementation modules are below the agreed approximate 600-line
target. The largest is `ffmpeg_playback.py` at 576 lines.

| Responsibility | Implementation modules |
|---|---|
| Application | `app_export.py`, `app_helpers.py`, `app_playback.py`, `app_project.py`, `app_timeline_actions.py`, `app_ui.py` |
| Model | `model_types.py`, `model_project.py`, `model_timeline.py`, `model_timeline_validation.py` |
| Export | `export_types.py`, `export_planning.py`, `export_ffmpeg.py`, `export_process.py`, `export_delivery.py` |
| CLI | `cli_types.py`, `cli_parser.py`, `cli_payload.py`, `cli_export.py` |
| Timeline | `timeline_geometry.py`, `timeline_rendering.py` |

## Compatibility and regression evidence

- `make check` passed: 158 tests, Python compilation, and `git diff --check`.
- `make contract` passed: 25 CLI contract tests.
- `make smoke` passed for generated-media editor open/play/edit/save/reopen
  flows.
- A direct compatibility import probe confirmed established public symbols
  remain available through `app`, `cli`, `export`, `model`, and `timeline`.
- Existing CLI monkeypatch seams remain covered by
  `tests/test_editor_cli_export.py` and `tests/test_editor_cli_editing.py`.
- `make quality PYTHON=.venv/bin/python` passed all configured local gates:
  formatting, lint, mypy, complexity, duplication, dependency boundaries,
  dependency audit, Bandit, and churn.

## Static-analysis evidence

- jscpd: 1.7575% duplication, 12 existing clones, 0 new clones, 0 new
  duplicated lines.
- Repository dependency check: `ok: true`, no findings or import cycles.
- pip-audit: no known vulnerabilities.
- Bandit: 0 findings.
- SonarQube is disabled in repository configuration.

Reports are retained under `evidence/static-analysis/`.

## User-facing evidence

- `evidence/screenshots/architecture-after.png` is a 1898x1023 active-window
  capture taken after the refactor.
- `evidence/screenshots/one-source-movement-before.png` and
  `one-source-movement-after.png` are retained 1701x684 active-window
  workflow captures for protected timeline behavior.
- The screenshots are evidence artifacts for the user-facing review.

## User validation

- On 2026-08-22, the user reviewed the completed architecture refactor and
  confirmed: "okay its validated what we have done".
- The user validation covers the preserved editor workflow, focused module
  boundaries, compatibility facades, and the recorded active-window evidence.
- Status: passed.

## Remote and approval gates

The repository contains `.github/workflows/quality.yml`, but no Git remote or
upstream is configured in this worktree. Remote checks and provider-side review
are therefore unavailable and are not claimed as passed. TICKET-030,
FEAT-013, and PHASE-004A are approved for closure; remote checks remain an
accepted warning for this local commit.

## Review and commit readiness

- Review result: passed for the approved TICKET-030 scope.
- Local regression, contract, smoke, quality, and static-analysis gates:
  passed.
- User-validation gate: passed.
- Remote-check gate: unavailable because no remote or upstream is configured.
- Commit readiness: ready for one scoped local commit.
