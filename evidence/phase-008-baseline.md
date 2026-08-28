# Phase 8 Baseline

**Date:** 2026-08-26
**Branch:** `ticket/phase-008-responsive-preview-media-strategy`
**Baseline scope:** protected editor, CLI, export, and legacy-script behavior

## Commands

| Command | Result |
|---|---|
| `make test` | PASS — 260 tests |
| `make contract` | PASS — 29 CLI contract tests |
| `make smoke` | PASS — generated-media editor smoke, verified export, and performance-mode restoration |

## Environment observations

- GTK/PyGObject, FFmpeg, ffprobe, and the local RVE preflight were available.
- The smoke flow restored the prior performance profile after export.
- This is a target-workstation baseline; it is not a claim about other hardware,
  codecs, displays, or GPU runtimes.

## Coverage limits

- Phase 8 preview interaction, focus-scroll controls, render-strategy
  comparison, and restoration research have not yet been implemented or
  measured.
- Remote checks are unavailable because no remote/upstream is configured.

## Final verification addendum - 2026-08-26

The final review remediation established bounded cancellation and publication
ordering for the protected export path. Silent FFmpeg output is interruptible,
VapourSynth/RVE process cleanup uses bounded terminate-then-kill escalation,
and GUI cancellation cannot interleave with the final verified `os.replace`.

The exact focused regression suite passed four tests. `make quality
PYTHON=.venv/bin/python` passed 304 tests and all configured formatting, lint,
type, complexity, duplication, dependency, audit, security, and churn gates.
`make contract PYTHON=.venv/bin/python` passed 31 CLI tests and `make smoke
PYTHON=.venv/bin/python` passed. Regenerated preview and render benchmark
artifacts report terminal `passed` statuses.

**Status:** passedWithConcerns

**Artifacts:** `evidence/phase-008-preview-benchmark-one-source.json`,
`evidence/phase-008-preview-benchmark-mixed-source.json`,
`evidence/phase-008-render-strategy-comparison.json`

**Open blockers and warnings:** no remote/upstream is configured; target-
workstation GTK interaction and visual validation, physical focus gestures,
and real RVE/model-quality validation remain unavailable and cannot be
inferred from automated backend tests.

## User-validation addendum - 2026-08-26

The requested target-workstation functionality handoff covered preview
freshness during timeline interaction, 2x/4x focus placement and persistence,
export cancellation safety, normal export playability, and source
preservation.

**User response:** `PASS`

**Status:** passed

No separate evidence paths were supplied with the response. This closes the
required user-validation gate for the covered editor flows; no remote or
upstream publication check is available.
