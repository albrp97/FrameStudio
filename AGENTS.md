# Agent Guidance

This file contains project-specific guidance. Follow the repository-neutral
workflow in `.github/copilot-instructions.md` as well.

## Project context

- Vision: [`vision.md`](vision.md)
- Scope handoff: [`docs/specs/project-scope.md`](docs/specs/project-scope.md)
- Future product direction: [`docs/specs/future-product-direction.md`](docs/specs/future-product-direction.md)
- Repository map: [`docs/planning/repo-map.md`](docs/planning/repo-map.md)
- Delivery configuration: [`.github/aidd-config.yml`](.github/aidd-config.yml)
- Human-facing usage: [`README.md`](README.md)

The first approved horizon is a local Linux editor for one source video:
playback, seek, split, delete, save/reopen, and export. It is not a full
DaVinci Resolve replacement.

The future product direction document preserves deferred intent such as
multi-video timelines, per-input audio handling, reusable segment
modifications, triplicate portrait/focused-action layouts, efficient rendering,
60 FPS enhancement, and agent-controlled editing. Do not pull those items into
the first horizon without an approved scope change.

## Existing repository surfaces

- `framestudio_media.py`: FrameStudio/Resolve-compatible media preparation and
  curses TUI, exposed globally as `framestudio media`.
- `framestudio_concat.py`: video selection, concatenation, audio analysis, and
  integrated FPS workflow, exposed globally as `framestudio concat`.
- `framestudio_fps.py`: direct and integrated RIFE/FPS processing, exposed
  globally as `framestudio fps`.
- `tests/`: Python `unittest` coverage for the existing scripts.
- `benchmarks/`: FPS pipeline harnesses.
- `FAST-CONCAT-RESEARCH.md`, `FLOWFRAMES-RESEARCH.md`, and
  `FPS-ENHANCEMENT-RESEARCH.md`: research evidence, not automatic product
  requirements.
- `install.sh`: installs the single canonical `framestudio` command into
  `~/bin` and removes obsolete workflow aliases.

FrameStudio is the canonical product identity. The `resolve_*` scripts, legacy
`resolve_editor` imports, and `.resolve.json` projects are compatibility
surfaces and must continue to work unless an approved migration removes them.
The old `resolve-*` and separate `framestudio-*` global command aliases are no
longer installed.

The editor UI, project model, playback layer, and editor CLI now live under
`framestudio/` and `framestudio.py`. The approved foundation uses GTK 4,
PyGObject, FFmpeg raw-frame playback, and versioned JSON project files. Do not
claim later segment, multi-source, composition, audio, or FPS behavior before
the relevant planning/architecture work is approved.

## Setup and commands

Required media tools:

- `python3`
- `ffmpeg`
- `ffprobe`

Optional integrations used by existing workflows include NVIDIA tooling,
`powerprofilesctl`, `gio`, curses support, and the local RIFE/RVE setup.

Existing validation commands:

```sh
python3 -m unittest discover -s tests
python3 -m py_compile framestudio_media.py framestudio_concat.py framestudio_fps.py \
  framestudio.py framestudio/*.py resolve_media.py resolve_concat.py \
  resolve_fps.py resolve_editor.py resolve_editor/__init__.py tests/*.py
```

The Makefile provides equivalent shortcuts plus editor workflows:

```sh
make help
make test
make check
make start
make editor ARGS="--source <video>"
make smoke
```

Existing operational commands documented in `README.md` include:

```sh
./install.sh
./framestudio_media.py --help
./framestudio_media.py --dry-run --root <directory>
framestudio concat --dry-run <directory>
```

Do not add a formatter, linter, type checker, build system, or dependency
manager without an approved planning decision and repository evidence.

## Boundaries and protected behavior

- Preserve the existing command names and scripts while the editor is
  introduced.
- Do not overwrite, delete, or move original source media.
- Preserve atomic partial-output, verification, and failure-cleanup behavior
  when reusing or extending FFmpeg operations.
- Keep editor project state separate from source media.
- Do not silently broaden the first horizon to multiple clips, composition,
  audio normalization, or FPS enhancement.
- Do not treat local benchmark results as universal claims for other hardware.
- The editor foundation decision is recorded in
  `docs/specs/editor-foundation-decision.md`: GTK 4/PyGObject is the GUI,
  FFmpeg is the initial raw-frame playback backend, and projects use
  versioned JSON with atomic saves. The future CLI contract remains a
  separate decision.

## Media and data handling

- Treat input media, project files, and generated outputs as local user data.
- Avoid logging full private paths or media metadata when not needed for
  evidence.
- Never place credentials, tokens, private keys, cookies, or sensitive sample
  data in source, project files, logs, tests, or evidence.
- Export to a temporary/partial path, validate it, and only then expose the
  final output.
- Surface unsupported codecs, timestamp ambiguity, and FFmpeg failures
  explicitly; do not use silent success fallbacks.

## Validation and evidence

For editor changes, provide:

- Automated tests for changed project/timeline/export logic.
- Existing-suite results to show protected behavior remains functional.
- A target-workstation real-media smoke test for playback and export when the
  change affects the interface or media path.
- Output metadata/duration and source-preservation evidence for export changes.
- Clear records of unavailable checks or environment-dependent limitations.

No readiness claim should be made from an unrun or unavailable check.

## Handling uncertainty

When the repository or media behavior does not establish an answer:

- record the uncertainty and affected surface;
- preserve the existing behavior;
- avoid choosing a new dependency or architecture by guesswork;
- route material scope or architecture changes through the configured planning
  and approval process;
- add follow-up planning work rather than silently expanding the first horizon.
