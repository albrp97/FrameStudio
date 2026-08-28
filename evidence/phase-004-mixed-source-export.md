# Delivery Evidence: TICKET-026

- Phase: `PHASE-004` - Combining Mixed-Source Footage
- Feature: `FEAT-012` - Previewing and Exporting Mixed-Source Edits
- Ticket: `TICKET-026` - Implement Verified Mixed-Source Export
- Status: `verifying`
- Branch: `ticket/phase-004-mixed-source-footage`
- Evidence path: `evidence/phase-004-mixed-source-export.md`

## Evidence entries

### REALMEDIA-001

- Command: `framestudio export <mixed-project> --output <output>.mp4`
- Observed: Progress events reached 100 percent for 60 frames and the final
  result reported route `fallback`, `verified: true`, 4.0 seconds, 320x320,
  15 FPS, H.264 video, and AAC audio.
- Status: `passed`

### VALIDATION-001

- Command: `ffprobe -v error -show_entries
  format=duration:stream=codec_type,width,height,codec_name -of compact`
- Observed: The output is independently playable and contains the expected
  normalized video and audio streams. The export destination is separate from
  the project and both input source files remain unchanged.
- Status: `passed`

### QUALITY-001

- Commands: `make check PYTHON=python3`,
  `make contract PYTHON=.venv/bin/python`, and
  `make quality PYTHON=.venv/bin/python`
- Observed: 135 tests, 23 contract tests, compilation, formatting, lint,
  typing, complexity, duplication, dependency, audit, security, and churn
  checks passed.
- Status: `passed`

### USER-001

- Required: Maintainer confirmation of GUI export progress and final output
  behavior.
- Status: `pending`

## Superseding evidence: CHG-002 fixed project canvas

The `REALMEDIA-001` 320x320 result above is retained as historical evidence
for the superseded mixed-source policy.

### REALMEDIA-002

- Commands: Generated 320x180 landscape and 180x320 portrait MP4 fixtures,
  imported both with `framestudio.py import`, exported with
  `framestudio.py export`, and inspected with `ffprobe`.
- Observed: The mixed export completed with a verified fallback route,
  2.2-second duration, 1920x1080 H.264 video, 15 FPS, and no audio stream.
  Progress reported 33 total frames and reached 100 percent.
- Observed: Both source files retained their original size and modification
  timestamp during export.
- Status: `passed`

### REALMEDIA-003

- Commands: Generated a 320x180 one-source MP4 fixture, imported it, exported
  it through the CLI, and inspected the result with `ffprobe`.
- Observed: The non-1080p one-source export completed with H.264 video at
  exactly 1920x1080.
- Status: `passed`

### QUALITY-002

- Commands: `.venv/bin/python -m unittest discover -s tests`,
  `make contract PYTHON=.venv/bin/python`, `make quality
  PYTHON=.venv/bin/python`, and `make smoke PYTHON=.venv/bin/python`.
- Observed: 137 tests and 23 CLI contract tests passed; compilation,
  formatting, lint, typing, complexity, duplication, dependency, audit,
  security, churn, and generated-media smoke checks passed.
- Status: `passed`
