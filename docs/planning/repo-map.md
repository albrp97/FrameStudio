# Repository Map

**Map ID:** RM-001
**Status:** confirmed
**Last updated:** 2026-08-21
**Repository revision:** `150d2f7`
**Owner:** repository maintainer; maintainer identity is not recorded in the repository

## Purpose

This map records the current repository surfaces before editor planning. It
does not create implementation tickets or decide the future editor stack.

## Source and Runtime Surfaces

| Surface | Path | Responsibility | Evidence / status |
|---|---|---|---|
| Resolve media preparation | `resolve_media.py` | Probes media, classifies Resolve compatibility, converts unsupported media, manages safe partial outputs, and provides a curses TUI. | Observed and tested. |
| Concatenation and FPS workflow | `resolve_concat.py` | Selects videos, probes clips, analyzes audio, chooses stream-copy or normalization, joins clips, and invokes FPS enhancement. | Observed and tested. |
| FPS enhancement | `resolve_fps.py` | Runs the RIFE/VapourSynth or REAL-Video-Enhancer pipeline, preserves/remuxes audio, validates frame rate/count, and reports progress. | Observed and tested. |
| Installation wrappers | `install.sh` | Installs `resolve-media`, `resolve-concat`, and `resolve-fps` wrappers into `~/bin`. | Observed. |
| Benchmark harness | `benchmarks/fps.vpy`, `benchmarks/vsrawpipe.py` | Supports the validated FPS processing path and benchmark reproduction. | Observed. |
| Editor UI | not present | Future primary editing interface with playback and timeline. | Unknown; requires architecture decision. |
| Editor project storage | not present | Future non-destructive, reopenable project representation. | Unknown; schema and path TBD. |
| Editor CLI | not present | Future deterministic automation surface for project inspection, editing, and export. | Unknown; command contract TBD. |

## Test Surfaces

| Path | Responsibility | Evidence / status |
|---|---|---|
| `tests/test_classification.py` | Media classification, profiles, output commands, GPU/lossless behavior. | Existing unittest coverage. |
| `tests/test_concat.py` | Clip probing decisions, stream-copy eligibility, audio gain, normalization commands, cleanup. | Existing unittest coverage. |
| `tests/test_fps.py` | FPS counts, output commands, RVE behavior, progress, and pipeline branching. | Existing unittest coverage. |
| `tests/__init__.py` | Test package marker. | Observed. |

Baseline command:
`python3 -m unittest discover -s tests` — 34 tests passed on 2026-08-21.

## Documentation and Research

| Path | Responsibility | Evidence / status |
|---|---|---|
| `README.md` | Human-facing usage, safety policy, current commands, supported profiles, and research links. | Existing authoritative project README. |
| `FAST-CONCAT-RESEARCH.md` | Benchmarks and design rationale for parallel normalization and stream-copy joining. | Existing research; informs future export decisions but is not a GUI specification. |
| `FLOWFRAMES-RESEARCH.md` | Flowframes and interpolation implementation research. | Existing research. |
| `FPS-ENHANCEMENT-RESEARCH.md` | Current FPS/VFI research, local GPU findings, and RIFE/RVE recommendations. | Existing research. |
| `docs/specs/future-product-direction.md` | Durable record of deferred multi-video editing, segment operations, audio, triplicate composition, render, FPS, project, and CLI intent. | Confirmed context; not an implementation backlog. |
| `.github/copilot-instructions.md` | Repository-neutral AIDD operating guidance. | Existing guidance; preserved and not duplicated in `AGENTS.md`. |
| `.github/README.md` | AIDD workflow and artifact inventory. | Existing guidance. |
| `.github/aidd-map.md` | AIDD artifact inventory and workflow map. | Existing guidance; not the configured repository map. |

## Configuration and Automation

| Path / surface | Responsibility | Evidence / status |
|---|---|---|
| `.github/aidd-config.yml` | Configured artifact paths, planning depth, approvals, gates, evidence policy, and provider defaults. | Existing configuration; the unit command is configured and other command arrays remain discovery states. |
| `.github/prompts/` | Prompt wrappers for planning and delivery skills. | Existing automation guidance. |
| `.github/skills/` | Colocated lifecycle and domain skill contracts. | Existing automation guidance. |
| CI workflows | Continuous integration. | None observed. |
| Package manifest | Dependency/runtime declaration. | None observed. |
| Ownership/contribution file | Maintainer or ownership rules. | None observed; TBD. |

## External Dependencies and Integrations

- `python3` is the current runtime.
- `ffmpeg` and `ffprobe` are required for media inspection and processing.
- `curses` is required by the interactive TUIs.
- `nvidia-smi`, CUDA/NVENC, `powerprofilesctl`, and `gio` are supported
  optional Linux integrations in the existing scripts.
- The FPS workflow may use an external REAL-Video-Enhancer checkout and local
  model/cache paths.
- Input and output media live on the local filesystem.

## Current Commands

- `python3 -m unittest discover -s tests`
- `python3 -m py_compile resolve_media.py resolve_concat.py resolve_fps.py tests/*.py`
- `./install.sh`
- `./resolve_media.py --help`
- `./resolve_media.py --dry-run --root <directory>`
- `resolve-concat --dry-run <directory>`

The last two commands require suitable media/tooling; no claim is made that
they pass for every environment.

## Protected Existing Behavior

- Existing command names and scripts remain available.
- Existing tests remain green.
- Source-safe partial output, verification, and atomic rename behavior is not
  weakened.
- Existing research remains available as evidence, not as an automatic
  product requirement.
- The current TUI preparation and concat/FPS flows are not silently replaced
  by the new editor.

## Unknowns and Planning Blockers

- GUI runtime and packaging approach.
- Playback/timeline backend and how frames are presented in real time.
- Versioned project-file schema and source-path relinking behavior.
- Exact split semantics, frame accuracy, and deletion/ripple behavior.
- Smart-render eligibility and fallback policy at cut boundaries.
- First-horizon audio preservation behavior.
- CLI command grammar, output format, and error contract.
- Maintainer/ownership and CI/remote-check setup.
