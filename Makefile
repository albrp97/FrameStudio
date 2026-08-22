PYTHON ?= python3
FFMPEG ?= ffmpeg
NPX ?= npx
NPM ?= npm
STATIC_ANALYSIS_DIR ?= evidence/static-analysis
QUALITY_PATHS = resolve_editor.py resolve_editor tests/test_editor_*.py \
	tools/check_dependencies.py
COMPLEXITY_PATHS = resolve_editor.py resolve_editor/cli.py resolve_editor/operations.py

.PHONY: help setup test compile diff-check check format-check lint type-check \
	complexity duplication dependency-check dependency-audit security churn \
	static-analysis quality contract screenshot start editor cli smoke media \
	concat fps install

help:
	@printf '%s\n' \
		'make setup      Create the local quality-tool environment' \
		'make test       Run the complete unittest suite' \
		'make compile    Compile Python sources and tests' \
		'make check      Run tests, compilation, and git diff checks' \
		'make quality    Run all local quality checks and churn analysis' \
		'make screenshot LABEL=name  Capture the active Wayland window' \
		'make start      Launch the editor for in-app video selection' \
		'make editor     Launch the GTK editor (pass ARGS="...")' \
		'make cli        Run deterministic editor CLI commands (pass ARGS="...")' \
		'make smoke      Run generated-media editor smoke flows' \
		'make media      Run resolve_media.py (pass ARGS="...")' \
		'make concat     Run resolve_concat.py (pass ARGS="...")' \
		'make fps        Run resolve_fps.py (pass ARGS="...")' \
		'make install    Install command wrappers into ~/bin'

setup:
	$(PYTHON) -m venv --system-site-packages .venv
	.venv/bin/python -m pip install --requirement requirements-dev.txt
	$(NPM) ci

test:
	$(PYTHON) -m unittest discover -s tests

compile:
	$(PYTHON) -m py_compile resolve_media.py resolve_concat.py resolve_fps.py \
		resolve_editor.py resolve_editor/*.py tests/*.py tools/*.py

diff-check:
	git diff --check

check: test compile diff-check

format-check:
	$(PYTHON) -m ruff format --check $(QUALITY_PATHS)

lint:
	$(PYTHON) -m ruff check $(QUALITY_PATHS)

type-check:
	$(PYTHON) -m mypy --config-file pyproject.toml resolve_editor
	$(PYTHON) -m mypy --config-file pyproject.toml resolve_editor.py
	$(PYTHON) -m mypy --config-file pyproject.toml tools/check_dependencies.py

complexity:
	$(PYTHON) -m ruff check --select C901 $(COMPLEXITY_PATHS)

duplication:
	@mkdir -p $(STATIC_ANALYSIS_DIR)
	$(NPX) --no-install jscpd --config .jscpd.json $(QUALITY_PATHS)

dependency-check:
	@mkdir -p $(STATIC_ANALYSIS_DIR)
	$(PYTHON) tools/check_dependencies.py --json \
		> $(STATIC_ANALYSIS_DIR)/dependencies.json

dependency-audit:
	@mkdir -p $(STATIC_ANALYSIS_DIR)
	$(PYTHON) -m pip_audit --requirement requirements-dev.txt \
		--format json --output $(STATIC_ANALYSIS_DIR)/pip-audit.json

security:
	@mkdir -p $(STATIC_ANALYSIS_DIR)
	$(PYTHON) -m bandit -r resolve_editor.py resolve_editor tools/check_dependencies.py \
		--configfile pyproject.toml --format json \
		--output $(STATIC_ANALYSIS_DIR)/bandit.json

churn:
	@mkdir -p $(STATIC_ANALYSIS_DIR)
	$(NPX) --no-install aidd churn --json \
		> $(STATIC_ANALYSIS_DIR)/churn.json

static-analysis: format-check lint type-check complexity duplication \
	dependency-check dependency-audit security

quality: check static-analysis churn

contract:
	$(PYTHON) -m unittest discover -s tests -p 'test_editor_cli_*.py'

screenshots:
	@printf '%s\n' 'Use make screenshot LABEL=before or LABEL=after'

screenshot:
	@test -n "$(LABEL)" || (printf '%s\n' 'LABEL is required' >&2; exit 2)
	@case "$(LABEL)" in \
		*[!A-Za-z0-9_.-]*) printf '%s\n' 'LABEL contains invalid characters' >&2; exit 2 ;; \
	esac
	@command -v grim >/dev/null 2>&1 || \
		(printf '%s\n' 'grim is required for Wayland screenshots' >&2; exit 2)
	@command -v hyprctl >/dev/null 2>&1 || \
		(printf '%s\n' 'hyprctl is required to capture the active window' >&2; exit 2)
	@mkdir -p evidence/screenshots
	@window_geometry="$$(hyprctl activewindow -j 2>/dev/null | \
		$(PYTHON) -c 'import json, sys; data = json.load(sys.stdin); at = data.get("at"); size = data.get("size"); print(f"{at[0]},{at[1]} {size[0]}x{size[1]}" if isinstance(at, list) and len(at) == 2 and isinstance(size, list) and len(size) == 2 else "")')"; \
	test -n "$$window_geometry" || \
		(printf '%s\n' 'No active window geometry was found; focus the editor first' >&2; exit 2); \
	grim -g "$$window_geometry" "evidence/screenshots/$(LABEL).png"
	@printf 'Captured evidence/screenshots/%s.png\n' "$(LABEL)"

start: editor

editor:
	$(PYTHON) resolve_editor.py $(ARGS)

cli:
	$(PYTHON) resolve_editor.py $(ARGS)

smoke:
	@set -eu; \
	fixture="$${TMPDIR:-/tmp}/resolve-editor-make-smoke.mp4"; \
	project="$${TMPDIR:-/tmp}/resolve-editor-make-smoke.resolve.json"; \
	trap 'rm -f "$$fixture" "$$project"' EXIT INT TERM; \
	$(FFMPEG) -hide_banner -loglevel error -y \
		-f lavfi -i testsrc=size=320x180:rate=10 -t 1 \
		-pix_fmt yuv420p "$$fixture"; \
	$(PYTHON) resolve_editor.py --source "$$fixture" \
		--smoke-test --smoke-project "$$project"; \
	$(PYTHON) resolve_editor.py --project "$$project" --smoke-test

media:
	$(PYTHON) resolve_media.py $(ARGS)

concat:
	$(PYTHON) resolve_concat.py $(ARGS)

fps:
	$(PYTHON) resolve_fps.py $(ARGS)

install:
	./install.sh
