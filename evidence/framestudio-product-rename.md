# CHG-006 - FrameStudio Product Rename Evidence

**Change:** CHG-006
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Branch:** `ticket/phase-008-responsive-preview-media-strategy`
**Base revision:** `348ceeb7034204a4e3658d8676301cf7c8371b6a`
**Evidence status:** verifying
**Evidence path:** `evidence/framestudio-product-rename.md`

## Context

This record covers the approved rename from Resolve to FrameStudio. The
canonical product identity, Python package, commands, project suffix, GTK
application ID, cache/temp naming, documentation, and planning surfaces now
use FrameStudio. Existing `resolve_*` scripts, `resolve-*` commands,
`resolve_editor` imports, legacy cache paths, generated media suffixes, and
`.resolve.json` projects remain compatibility surfaces.

## Planning chain

`OBJ-001 -> SCOPE-001 -> CHG-006`

## Requirements and protected flows

- R1: New product-facing paths and identifiers use the FrameStudio identity.
- R2: Existing Resolve-named scripts, imports, commands, caches, generated
  media, and project files remain usable through compatibility behavior.
- R3: Editor CLI, GUI startup, project persistence, media preparation, FPS
  enhancement, export, and source-media safety retain their existing behavior.
- R4: README, agent guidance, specifications, planning records, research
  references, evidence references, installer behavior, and quality tooling
  describe the current canonical paths.
- R5: The rename is covered by automated regression, CLI contract, generated
  media smoke, installer, syntax, and repository quality checks.

## Entries

### Planning and scope

- **Category:** planning
- **Status:** passed
- **Expected:** The material product rename is recorded with approval,
  affected surfaces, protected behavior, compatibility policy, and closure
  gates before delivery.
- **Observed:** CHG-006 records the approved FrameStudio identity, bounded
  scope, compatibility policy, affected artifacts, and remaining gates.
- **Artifacts:** `docs/planning/reviews/CHG-006-framestudio-product-rename.md`

### Canonical implementation and compatibility

- **Category:** implementation
- **Status:** passed
- **Expected:** The implementation package and primary scripts use
  FrameStudio names while legacy surfaces forward to the same implementation.
- **Observed:** `framestudio/`, `framestudio.py`, `framestudio_media.py`,
  `framestudio_concat.py`, and `framestudio_fps.py` are canonical. The
  `resolve_editor` package and legacy script wrappers forward to canonical
  modules; canonical and legacy imports resolve to the same module objects.
- **Artifacts:** `framestudio/`, `framestudio.py`, `resolve_editor/`,
  `resolve_editor.py`, `resolve_media.py`, `resolve_concat.py`,
  `resolve_fps.py`, `tests/test_framestudio_compatibility.py`

### Automated regression

- **Category:** regression
- **Command:** `make check`
- **Expected:** Existing behavior remains functional after the rename;
  compilation and whitespace checks pass.
- **Observed:** 364 tests passed, Python compilation passed, and
  `git diff --check` passed.
- **Status:** passed

### CLI contract

- **Category:** contract
- **Command:** `make contract`
- **Expected:** Canonical deterministic CLI operations retain their structured
  contract and project-path behavior.
- **Observed:** 35 editor CLI contract tests passed.
- **Status:** passed

### Generated-media editor smoke

- **Category:** functionality
- **Command:** `make smoke`
- **Expected:** A generated source can be opened, exercised, saved as a
  `.framestudio.json` project, reopened, and cleaned up without altering
  source media.
- **Observed:** The smoke flow completed successfully and removed its
  temporary fixture and project.
- **Status:** passed

### Installer and command aliases

- **Category:** functionality
- **Steps:** Run `install.sh` with an isolated temporary `HOME`; invoke
  `framestudio --version`, `framestudio-editor --version`,
  `resolve-editor --version`, and `resolve-media --version`; list installed
  wrappers.
- **Expected:** Canonical commands and legacy aliases are installed and
  dispatch successfully.
- **Observed:** Canonical and legacy entrypoints returned successfully. The
  isolated bin directory contained `framestudio`, `framestudio-editor`,
  `framestudio-media`, `framestudio-concat`, `framestudio-fps`,
  `resolve-editor`, `resolve-media`, `resolve-concat`, and `resolve-fps`.
- **Status:** passed

### Static analysis and local quality

- **Category:** staticAnalysis
- **Command:** `PYTHON=.venv/bin/python make quality`
- **Expected:** The repository quality workflow is executable with the pinned
  environment and reports all configured checks.
- **Observed:** Formatting, Ruff lint, mypy, duplication, dependency graph,
  dependency audit, and Bandit completed without introduced findings.
  Duplication reported 0 new clones; dependency analysis reported 0 findings;
  pip-audit reported no known vulnerabilities; Bandit reported 0 results.
  The command stopped at the existing C901 finding
  `benchmarks/restoration_benchmark.py:1794 run_benchmark` with complexity
  `16 > 15`. That file is unchanged by CHG-006.
- **Status:** passedWithConcerns
- **Artifacts:** `evidence/static-analysis/dependencies.json`,
  `evidence/static-analysis/jscpd-report.json`,
  `evidence/static-analysis/pip-audit.json`,
  `evidence/static-analysis/bandit.json`,
  `evidence/static-analysis/churn.json`
- **Accepted warning:** The complexity finding is pre-existing and outside
  the rename scope. It remains visible and was not suppressed or relabeled.

### Local-to-PR parity

- **Category:** gate
- **Expected:** Local quality commands and the pull-request workflow use the
  same repository-native wrapper and pinned quality environment.
- **Observed:** `.github/workflows/quality.yml` runs
  `make quality PYTHON=.venv/bin/python`; the same command was run locally.
  No Git remote is configured, so provider-side checks cannot be executed.
- **Status:** blocked
- **Blocker:** Remote checks are unavailable until a remote is configured.
- **Artifacts:** `.github/workflows/quality.yml`, `.github/aidd-config.yml`

### Remaining-reference audit

- **Category:** review
- **Steps:** Search tracked files for Resolve product identifiers and classify
  every remaining occurrence.
- **Expected:** No stale canonical product reference remains; intentional
  compatibility, migration, external terminology, semantic code names, and
  historical workspace paths remain explicit.
- **Observed:** Remaining references are limited to documented compatibility
  facades and aliases, legacy cache/project/media migration, DaVinci Resolve
  compatibility terminology, `resolve_*` semantic function names, or the
  unchanged physical workspace path.
- **Status:** passed

### Final post-review regression

- **Category:** regression
- **Commands:** `make check`, `make contract`, `make smoke`, and the
  configured format/lint/type checks through
  `PYTHON=.venv/bin/python make quality`.
- **Expected:** The branding cleanup and compatibility alias preserve all
  existing behavior and remain inside the configured quality scope.
- **Observed:** 365 tests passed, compilation and diff checks passed, 35 CLI
  contract tests passed, and the generated-media smoke flow passed. Ruff
  format, Ruff lint, and mypy passed for the configured source and test
  paths. The exact quality command still stops at the unchanged benchmark
  C901 finding recorded above.
- **Status:** passedWithConcerns
- **Accepted warning:** The sole quality-suite failure is pre-existing and
  outside CHG-006.

## User-validation handoff

The technical rename was ready for manual validation, and the user-validation
result is recorded below. The change remains subject to the review and
configured delivery gates:

```text
PASS: every required check succeeded; evidence: <paths or notes>
FAIL: <failed check and observed result>
BLOCKED: <missing service, data, permission, or capability>
NOT APPLICABLE: <reason and approval>
```

### Setup

- Use the current branch checkout.
- Use a disposable test video and project path.
- Ensure `python3`, `ffmpeg`, and `ffprobe` are available.

### Exact steps

1. Run `python3 framestudio.py --version` and confirm it reports
   `framestudio 0.1.0`.
2. Run `python3 resolve_editor.py --version` and confirm it reports the same
   FrameStudio identity.
3. Run `python3 framestudio.py --source <video> --smoke-test
   --smoke-project <temporary-project.framestudio.json>`.
4. Reopen the generated project with
   `python3 framestudio.py --project <temporary-project.framestudio.json>
   --smoke-test`.
5. If the GTK window is available, confirm the application opens as
   FrameStudio and the save dialog defaults to `.framestudio.json`.
6. Run `./install.sh` only with the user's normal `HOME` if command-wrapper
   installation is desired, then verify `framestudio`, `framestudio-editor`,
   and the legacy `resolve-editor` alias.
7. Remove only the disposable project and generated fixture.

### Expected results

- Canonical and legacy entrypoints launch the same editor behavior.
- New projects use `.framestudio.json`.
- Existing `.resolve.json` projects remain loadable.
- Source media is unchanged.
- Canonical and legacy command wrappers are both usable.

### Failure paths

Report `FAIL` or `BLOCKED` for an entrypoint mismatch, missing compatibility
alias, inability to load a legacy project, incorrect project suffix,
application identity failure, source modification, or an unavailable GTK or
media dependency.

### User validation

- **Category:** userValidation
- **Status:** passed
- **Observed:** The user reported that everything works and confirmed the
  validation request affirmatively. No per-step screenshot or output metadata
  paths were supplied.
- **Accepted warning:** User confirmation is terminal, but the evidence is
  limited to the user's confirmation rather than attached visual artifacts.

## Readiness

- **Passed:** Canonical implementation, compatibility coverage, regression,
  contract, smoke, installer, syntax, reference-audit, and user-validation
  checks.
- **Passed with concerns:** Full local quality command is stopped by the
  unchanged benchmark complexity finding.
- **Blocked:** Provider-side remote checks; no Git remote is configured.
- **Commit:** Not created; commit remains gated by review and configured
  delivery policy.
