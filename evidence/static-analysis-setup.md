# Evidence - Repository Quality and Static-Analysis Setup

**Scope:** Establish repository-owned local quality gates, CI parity, and UI
evidence capture for the editor/CLI work.
**Evidence path:** `evidence/static-analysis-setup.md`
**Recorded:** 2026-08-21T14:22:11Z

## Setup

- Pinned Python tools are declared in `requirements-dev.txt`.
- Pinned Node tools are declared in `package.json` and locked in
  `package-lock.json`.
- Ruff, mypy, and Bandit policy is in `pyproject.toml`.
- jscpd policy is in `.jscpd.json`.
- Dependency-boundary checking is implemented in
  `tools/check_dependencies.py`.
- `Makefile` is the local command authority.
- `.github/workflows/quality.yml` runs the same `make quality` entry point
  used locally.
- `.github/aidd-config.yml` maps delivery and static-analysis gates to those
  commands.
- Verified local tool versions: Python 3.14.7, Ruff 0.12.10, mypy 1.17.1,
  Bandit 1.9.4, pip-audit 2.9.0, Node 22.19.0, jscpd 5.0.16, and AIDD 3.1.0.

## Verification

| Check | Command | Result | Artifact |
|---|---|---|---|
| Tests, compilation, diff checks | `make check` | passed; 123 tests | repository output |
| Formatting | `make format-check PYTHON=.venv/bin/python` | passed | - |
| Ruff lint | `make lint PYTHON=.venv/bin/python` | passed | - |
| Source type checking | `make type-check PYTHON=.venv/bin/python` | passed | - |
| Scoped complexity | `make complexity PYTHON=.venv/bin/python` | passed with existing UI debt noted | - |
| Duplication | `make duplication PYTHON=.venv/bin/python` | passed with 1.7% baseline under 2% ceiling | `evidence/static-analysis/jscpd-report.json` |
| Dependency boundaries | `make dependency-check PYTHON=.venv/bin/python` | passed | `evidence/static-analysis/dependencies.json` |
| Python dependency audit | `make dependency-audit PYTHON=.venv/bin/python` | passed; no known vulnerabilities | `evidence/static-analysis/pip-audit.json` |
| Bandit | `make security PYTHON=.venv/bin/python` | passed | `evidence/static-analysis/bandit.json` |
| Complete local quality gate | `make quality PYTHON=.venv/bin/python` | passed | `evidence/static-analysis/` |
| CLI contract tests | `make contract PYTHON=.venv/bin/python` | passed; 20 tests | repository output |
| Generated-media integration smoke | `make smoke PYTHON=.venv/bin/python` | passed | temporary media cleaned up |
| Reproducible setup | `make setup PYTHON=python3` | passed | `.venv/`, `package-lock.json` |
| UI evidence capture | `make screenshot LABEL=quality-before`, `make screenshot LABEL=quality-after` | passed; screenshots differ | `evidence/screenshots/quality-before.png`, `evidence/screenshots/quality-after.png` |

## Findings and coverage

- The GTK/rendering/export adapter functions have existing high C901 complexity
  and are outside the current CLI/domain complexity gate. This is an accepted
  warning, not a claim that the full application is below the configured
  complexity threshold.
- No Git remote or provider-backed check is configured locally. The workflow
  file establishes CI parity, but remote-check execution remains unavailable
  until a provider remote is configured.
- Optional SonarQube deep analysis is explicitly disabled because no local
  server or scanner is configured; it is not represented as a passed check.
- The screenshots are repository evidence artifacts; they do not replace the
  required maintainer/user validation of the editor flow.
