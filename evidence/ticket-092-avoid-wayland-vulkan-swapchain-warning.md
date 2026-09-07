# TICKET-092 - Avoid Wayland Vulkan Swapchain Warnings During Editor Rendering

**Ticket:** TICKET-092
**Feature:** FEAT-029
**Phase:** PHASE-008
**Branch:** `ticket/defer-audio-analysis-during-import`
**Base:** `main` at `2702d68`
**Status:** verifying
**Evidence date:** 2026-09-04

## Context and planning chain

The ticket addresses the non-fatal `VK_SUBOPTIMAL_KHR` warning observed while
the GTK editor was rendering on the target Wayland workstation. The planning
chain is `OBJ-001 -> SCOPE-001 -> PHASE-008 -> FEAT-029 -> TICKET-092`.
The implementation is limited to guarded GTK renderer selection before GTK
initialization; FFmpeg, RVE, interpolation, upscale, and export behavior are
not changed.

## Requirements

- A Wayland editor session with no explicit renderer selects GTK's supported
  `gl` renderer before GTK initialization.
- An explicit `GSK_RENDERER` value, including an empty value, is preserved.
- A non-Wayland environment receives no injected renderer.
- Existing editor, export, CLI, and source-preservation behavior remains
  functional.

## Entries

### Planning and baseline - 2026-09-04

- **Sources:** `docs/planning/tickets/open/TICKET-092-avoid-wayland-vulkan-swapchain-warning.md`,
  `docs/planning/features/open/FEAT-029-strengthening-editor-recovery-and-export-observability.md`,
  `docs/planning/phases/open/PHASE-008-optimizing-responsive-preview-and-media-strategy.md`
- **Expected:** the ticket has explicit requirements, affected surfaces,
  non-goals, validation, parent links, and an evidence path.
- **Observed:** the ticket is linked to FEAT-029, PHASE-008, OBJ-001,
  SCOPE-001, CAP-005, and CAP-012, and preserves explicit renderer choices
  and the unchanged media pipeline as protected behavior.
- **Status:** passed

### Failing regression - 2026-09-04

- **Command:** `.venv/bin/python -m unittest tests.test_editor_graphics`
- **Expected:** renderer-environment behavior is covered by an importable
  helper.
- **Observed before the fix:** the test failed during collection with
  `ModuleNotFoundError: No module named 'framestudio.graphics'`.
- **Status:** failed
- **Fix:** added `framestudio/graphics.py` and wired it into `run_gui()` before
  the GTK import.

### Implementation - 2026-09-04

- **Expected:** only an unset renderer on Wayland is defaulted to `gl`;
  explicit and non-Wayland environments remain unchanged.
- **Observed:** `configure_graphics_environment()` checks for the presence of
  `GSK_RENDERER`, applies `gl` only when `WAYLAND_DISPLAY` is present, and
  returns the selected value without importing GTK or touching media code.
  `run_gui()` invokes it immediately before GTK initialization.
- **Sources:** `framestudio/graphics.py`, `framestudio/app.py`,
  `tests/test_editor_graphics.py`
- **Status:** passed

### Focused regression coverage - 2026-09-04

- **Command:** `.venv/bin/python -m unittest tests.test_editor_graphics`
- **Expected:** Wayland defaulting, explicit renderer preservation, explicit
  empty renderer preservation, non-Wayland behavior, and process-environment
  behavior pass.
- **Observed:** 5 tests passed.
- **Status:** passed

### Protected repository verification - 2026-09-04

- **Command:** `make check PYTHON=.venv/bin/python`
- **Expected:** existing tests, compilation, and diff checks remain
  functional.
- **Observed:** 417 repository tests passed; compilation passed; diff checks
  passed.
- **Status:** passed

### CLI contract and GTK smoke - 2026-09-04

- **Commands:** `make contract PYTHON=.venv/bin/python` and
  `make smoke PYTHON=.venv/bin/python`
- **Expected:** CLI JSON contracts and generated-media editor smoke flows
  remain functional.
- **Observed:** 35 CLI contract tests passed and the generated-media GTK
  smoke command exited successfully.
- **Status:** passed

### Target-workstation renderer behavior - 2026-09-04

- **Environment:** Linux Wayland workstation with GTK 4/PyGObject and the
  existing editor runtime.
- **Default command:** `env -u GSK_RENDERER GSK_DEBUG=renderer timeout 8s
  .venv/bin/python framestudio.py`
- **Default expected:** the editor selects `gl` and does not emit the
  Vulkan swapchain warning.
- **Default observed:** GTK reported
  `Environment variable GSK_RENDERER=gl set, trying GskGLRenderer` and
  `Using renderer 'GskGLRenderer' for surface 'GdkWaylandToplevel'`; no
  `VK_SUBOPTIMAL_KHR` warning was emitted.
- **Explicit command:** `GSK_RENDERER=vulkan GSK_DEBUG=renderer timeout 8s
  .venv/bin/python framestudio.py`
- **Explicit expected:** the user's explicit renderer choice remains
  unchanged.
- **Explicit observed:** GTK reported
  `Environment variable GSK_RENDERER=vulkan set, trying GskVulkanRenderer`
  and used `GskVulkanRenderer`.
- **Status:** passed

### Static analysis and review - 2026-09-04

- **Commands:** `make quality PYTHON=.venv/bin/python` and
  `make -k complexity duplication dependency-check dependency-audit security
  churn PYTHON=.venv/bin/python`
- **Expected:** changed surfaces have no introduced formatting, lint, typing,
  duplication, dependency, or security findings; existing repository debt
  remains visible.
- **Observed:** Ruff formatting passed; Ruff lint passed; mypy passed for all
  configured targets; jscpd reported 0 new clones; dependency boundaries
  reported 0 findings; pip-audit reported no known vulnerabilities; Bandit
  reported no findings; churn completed. The configured quality command
  stopped at the pre-existing `C901` finding at
  `benchmarks/restoration_benchmark.py:1794` (`run_benchmark`, complexity
  `16 > 15`), outside this ticket's scope.
- **Status:** passedWithConcerns
- **Accepted warning:** the complexity finding predates this ticket and is
  unchanged. The remaining static-analysis targets were run with `make -k`.
- **Artifacts:**
  - `evidence/static-analysis/jscpd-report.json`
  - `evidence/static-analysis/dependencies.json`
  - `evidence/static-analysis/pip-audit.json`
  - `evidence/static-analysis/bandit.json`
  - `evidence/static-analysis/churn.json`

### Local-to-PR parity and delivery gates - pending publication

- **Source:** `.github/workflows/quality.yml`
- **Expected:** local review uses the same quality entry point and analyzer
  configuration as the pull-request workflow.
- **Observed:** both local and CI use `make quality PYTHON=.venv/bin/python`.
  The remote workflow has not run because this branch is not published.
- **Status:** blocked
- **Blocker:** configured remote checks require a published branch.

### Maintainer validation handoff - pending

- **Required response:** the maintainer must validate the renderer behavior and
  return one of:
  `PASS: every required check succeeded; evidence: <paths or notes>`,
  `FAIL: <failed check and observed result>`,
  `BLOCKED: <missing service, data, permission, or capability>`, or
  `NOT APPLICABLE: <reason and approval>`.
- **Status:** blocked pending user response

## Review judgment

The change is scoped to the GTK initialization boundary and uses a small,
isolated, testable helper. The default is guarded by the Wayland
environment and the presence check preserves explicit configuration. Focused
and full repository tests, CLI contracts, GTK smoke, target-workstation
renderer launches, and configured analyzers show no introduced correctness,
security, dependency, or duplication finding.

## Readiness

Implementation, focused regressions, protected repository verification, CLI
contract coverage, GTK smoke, and target-workstation renderer evidence are
complete. The ticket remains `verifying` because the required maintainer
validation and remote checks are not terminal. The existing repository
complexity finding remains an accepted concern outside this ticket's scope.

## Open blockers

- Required maintainer/user validation response is pending.
- Required remote checks are unavailable until the branch is published.
- Existing repository-wide complexity debt remains at
  `benchmarks/restoration_benchmark.py:1794`.

### User-validation closeout - 2026-09-07

- **User response:** `PASS` — the user confirmed the implemented ticket set
  is good.
- **Status:** passed; this supersedes the earlier pending user-validation
  state.
