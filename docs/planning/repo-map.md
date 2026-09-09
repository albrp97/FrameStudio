# Repository Map

**Map ID:** RM-001
**Status:** confirmed
**Last updated:** 2026-09-07
**Repository revision:** `37d6515` (completed editor recovery and resumable export delivery)
**Owner:** repository maintainer; maintainer identity is not recorded in the repository

## Purpose

This map records the current repository surfaces, including the editor
implementation and the original preparation workflows that remain supported.
It describes ownership and validation surfaces without creating implementation
tickets.

## Source and Runtime Surfaces

| Surface | Path | Responsibility | Evidence / status |
|---|---|---|---|
| FrameStudio media preparation | `framestudio_media.py` | Probes media, classifies Resolve compatibility, converts unsupported media, manages safe partial outputs, and provides a curses TUI. | Observed and tested. |
| Concatenation and FPS workflow | `framestudio_concat.py` | Selects videos, probes clips, analyzes audio, chooses stream-copy or normalization, joins clips, and invokes FPS enhancement. | Observed and tested. |
| FPS enhancement | `framestudio_fps.py` | Runs the RIFE/VapourSynth or REAL-Video-Enhancer pipeline, preserves/remuxes audio, validates frame rate/count, and reports progress. | Observed and tested. |
| Installation wrapper | `install.sh` | Installs the canonical `~/bin/framestudio` command and removes obsolete standalone workflow aliases. | Observed. |
| Benchmark harness | `benchmarks/fps.vpy`, `benchmarks/vsrawpipe.py` | Supports the validated FPS processing path and benchmark reproduction. | Observed. |
| Editor application facade | `framestudio/app.py` | GTK application lifecycle and compatibility-preserving orchestration for source loading, playback, timeline actions, and export. | Implemented; `make check`, smoke, and UI evidence. |
| Editor application modules | `framestudio/app_*.py` | Focused UI construction, project lifecycle, timeline actions, playback, and export workflows used by the application facade. | Implemented; stable callback seams covered by editor tests. |
| Editor domain model | `framestudio/model_*.py` | Source/segment value objects, timeline invariants and operations, project lifecycle, serialization-facing behavior, and compatibility exports through `model.py`. | Implemented; model and mixed-source tests. |
| Timeline rendering | `framestudio/timeline*.py` | Pure geometry/drawing helpers and GTK timeline canvas behavior, retained through `timeline.py`. | Implemented; timeline interaction and drawing tests. |
| Export pipeline | `framestudio/export_*.py` | Export policy/value objects, planning, FFmpeg command/process execution, validation, and atomic publication, retained through `export.py`. | Implemented; export and source-safety tests. |
| Playback backend | `framestudio/ffmpeg_playback.py`, `framestudio/playback.py` | Raw-frame FFmpeg playback backend and playback state controller. | Implemented; playback and smoke coverage. |
| Editor project storage | `framestudio/persistence.py` | Versioned JSON project persistence, source-safety checks, and atomic save behavior. | Implemented; persistence and round-trip tests. |
| Editor CLI facade | `framestudio/cli.py` | Deterministic command dispatch, JSON output/error contract, and compatibility patch seams. | Implemented; `make contract` and CLI parity tests. |
| Editor CLI modules | `framestudio/cli_parser.py`, `framestudio/cli_export.py`, `framestudio/cli_payload.py`, `framestudio/cli_types.py` | Focused parser, export handler, payload serialization, and contract definitions used by the CLI facade. | Implemented; CLI contract and editing tests. |
| Compatibility surfaces | `resolve_editor/`, `resolve_editor.py`, `resolve_media.py`, `resolve_concat.py`, `resolve_fps.py` | Forward legacy imports and scripts to the canonical FrameStudio implementation without duplicating behavior. | Implemented; compatibility tests. |

## Test Surfaces

| Path | Responsibility | Evidence / status |
|---|---|---|
| `tests/test_classification.py` | Media classification, profiles, output commands, GPU/lossless behavior. | Existing unittest coverage. |
| `tests/test_concat.py` | Clip probing decisions, stream-copy eligibility, audio gain, normalization commands, cleanup. | Existing unittest coverage. |
| `tests/test_fps.py` | FPS counts, output commands, RVE behavior, progress, and pipeline branching. | Existing unittest coverage. |
| `tests/test_editor_*.py` | Editor model, operations, persistence, playback, timeline, export, CLI, and UI-helper regression coverage. | Included in the 453-test repository suite passed after the final delivery. |
| `tests/__init__.py` | Test package marker. | Observed. |

Baseline command:
`python3 -m unittest discover -s tests` — 453 tests passed after the final
editor recovery and resumable-export delivery.

## Documentation and Research

| Path | Responsibility | Evidence / status |
|---|---|---|
| `README.md` | Human-facing current product guide, safety policy, commands, export recovery, compatibility, and research links. | Current authoritative project README. |
| `FAST-CONCAT-RESEARCH.md` | Benchmarks and design rationale for parallel normalization and stream-copy joining. | Existing research; informs future export decisions but is not a GUI specification. |
| `FLOWFRAMES-RESEARCH.md` | Flowframes and interpolation implementation research. | Existing research. |
| `FPS-ENHANCEMENT-RESEARCH.md` | Current FPS/VFI research, local GPU findings, and RIFE/RVE recommendations. | Existing research. |
| `docs/specs/future-product-direction.md` | Historical record of broader multi-video editing, segment operations, audio, triplicate composition, render, FPS, project, and CLI intent. | Partly delivered; remaining items are future context, not an implementation backlog. |
| `.github/copilot-instructions.md` | Repository-neutral AIDD operating guidance. | Existing guidance; preserved and not duplicated in `AGENTS.md`. |
| `README.md` | Authoritative human-facing FrameStudio product guide, including installation, editor usage, CLI operations, safe export, and current boundaries. | Current project README. |
| `.github/aidd-map.md` | AIDD artifact inventory and workflow map. | Existing guidance; not the configured repository map. |

## Configuration and Automation

| Path / surface | Responsibility | Evidence / status |
|---|---|---|
| `.github/aidd-config.yml` | Configured artifact paths, planning depth, approvals, gates, evidence policy, and provider defaults. | Existing configuration; unit, integration, contract, and local quality commands are configured. |
| `.github/prompts/` | Prompt wrappers for planning and delivery skills. | Existing automation guidance. |
| `.github/skills/` | Colocated lifecycle and domain skill contracts. | Existing automation guidance. |
| `.github/workflows/quality.yml` | GitHub Actions quality workflow for Python, GTK/FFmpeg, npm, and static-analysis checks. | Observed; runs `make quality PYTHON=.venv/bin/python`. |
| `pyproject.toml`, `requirements-dev.txt`, `package.json`, `package-lock.json` | Ruff/mypy/Bandit configuration and pinned development quality dependencies. | Observed; runtime dependencies remain system-provided. |
| Ownership/contribution file | Maintainer or ownership rules. | None observed; TBD. |

## External Dependencies and Integrations

- `python3` is the current runtime.
- `ffmpeg` and `ffprobe` are required for media inspection and processing.
- GTK 4 and PyGObject are required by the editor GUI.
- `curses` is required by the interactive TUIs.
- `nvidia-smi`, CUDA/NVENC, `powerprofilesctl`, and `gio` are supported
  optional Linux integrations in the existing scripts.
- The FPS workflow may use an external REAL-Video-Enhancer checkout and local
  model/cache paths.
- Input and output media live on the local filesystem.

## Current Commands

- `python3 -m unittest discover -s tests`
- `python3 -m py_compile framestudio_media.py framestudio_concat.py framestudio_fps.py framestudio.py framestudio/*.py tests/*.py tools/*.py`
- `make check`
- `make contract`
- `make smoke`
- `make quality PYTHON=.venv/bin/python`
- `./install.sh`
- `./framestudio.py --help`
- `framestudio inspect <project>`
- `framestudio export <project> --output <video> [--resume|--restart|--discard]`
- `./framestudio_media.py --help`
- `./framestudio_media.py --dry-run --root <directory>`
- `framestudio concat --dry-run <directory>`

The media-dependent script commands require suitable media/tooling; no claim
is made that they pass for every environment.

## Protected Existing Behavior

- Existing command names and scripts remain available.
- Existing tests remain green.
- Source-safe partial output, verification, and atomic rename behavior is not
  weakened.
- Existing research remains available as evidence, not as an automatic
  product requirement.
- The current TUI preparation and concat/FPS flows are not silently replaced
  by the new editor.
- The editor uses focused implementation modules with compatibility facades at
  `model.py`, `export.py`, `timeline.py`, `app.py`, and `cli.py`.

## Unknowns and Planning Blockers

- Packaging and distribution beyond the current local Python/GTK/FFmpeg
  runtime.
- Advanced audio editing, multiple tracks, and compositor behavior beyond the
  delivered source-level and segment-focused features.
- Maintainer/ownership and remote PR/check configuration.
