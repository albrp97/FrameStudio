# TICKET-079 - Implement Optional Upscale Enhancement

**Ticket ID:** TICKET-079
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-008
**Feature:** FEAT-028
**Capability links:** CAP-005, CAP-011, CAP-012
**Status:** complete
**Horizon:** future
**Priority:** 1
**Owner:** repository implementation in the active worktree
**Approval:** User-authorized by the request to implement the optional
upscale enhancement; execution is proceeding with the configured evidence and
review gates.
**Last updated:** 2026-08-28
**Source paths:** `docs/planning/reviews/CHG-008-add-production-upscale-enhancement.md`,
`docs/planning/features/open/FEAT-028-adding-optional-upscale-enhancement.md`,
`docs/planning/tickets/open/TICKET-076-adopt-per-source-render-strategy.md`,
`resolve_fps.py`, `resolve_editor/model_project.py`,
`resolve_editor/fps_policy.py`, `resolve_editor/export_types.py`,
`resolve_editor/export_planning.py`, `resolve_editor/export_smart_render.py`,
`resolve_editor/export_interpolation.py`, `resolve_editor/export_delivery.py`,
`resolve_editor/export_ffmpeg.py`, `resolve_editor/composition_render.py`,
`resolve_editor/export_panel.py`, `resolve_editor/app_export.py`,
`resolve_editor/cli_parser.py`, `resolve_editor/cli.py`,
`resolve_editor/cli_export.py`, `.github/aidd-config.yml`
**Dependencies:** TICKET-076; local RVE TensorRT environment and
SuperUltraCompact weights; FFmpeg/ffprobe; existing export and composition
tests
**Risks:** model/runtime failure, spatial crop/pad semantics, repeated source
segments, combined FPS ordering, temporary storage, audio drift, and
regressions in the disabled path
**Affected surfaces:** versioned project output settings, policy resolution,
export plan serialization, RVE restoration runner, FFmpeg scale/composition,
enhanced and fallback delivery, GTK panel, CLI, tests, and evidence
**Evidence path:** `evidence/ticket-079-production-upscale-enhancement.md`
**Protected behaviors:** existing exports when disabled, fixed 1920x1080
delivery, FPS/RVE behavior, source-level audio decisions, timeline order,
atomic publication, cancellation cleanup, output verification, legacy
scripts, and source preservation
**Path history:** created at
`tickets/open/TICKET-079-implement-optional-upscale-enhancement.md` -> moved
to `tickets/closed/TICKET-079-implement-optional-upscale-enhancement.md`

## Outcome

Eligible sources use SuperUltraCompact upscale enhancement by default from the
GUI or CLI, with an explicit opt-out, persisted policy state, and a safe,
orientation-aware render path that composes enhanced media without
downscaling.

## Scope

- Add a versioned `UpscalePolicy` and source dimension decisions.
- Persist and validate the policy without breaking older project files.
- Add GUI and CLI controls and include the same decisions in export plans.
- Run the existing local RVE SuperUltraCompact restoration path, apply
  aspect-preserving spatial scaling, and integrate it with per-source FPS
  enhancement and normal/triplicate composition.
- Preserve audio, frame rate, duration, frame count, output metadata,
  cancellation, cleanup, atomic publication, and source hashes.
- Add focused tests for policy, persistence, planning, CLI/UI state, filters,
  execution, failure, and source preservation.

## Explicit non-goals

- Other models, runtime downloads, new permanent dependencies, or model
  redistribution.
- Changing existing exports when the option is disabled.
- Downscaling source pixels during the enhancement/composition stage.
- Benchmark strategy comparison and recommendation (TICKET-080).

## Observable acceptance criteria

- Given an enabled policy and a landscape source with short side <= 1000,
  `UpscaleDecision` should select SuperUltraCompact and a 1080-pixel
  short-side target.
- Given an enabled policy and a portrait source with short side <= 720,
  `UpscaleDecision` should select SuperUltraCompact and a 1080-pixel
  short-side target.
- Given an enabled policy and a square or above-threshold source, the
  decision should be passthrough and no model command should run.
- Given an old project without an upscale field, loading should preserve the
  project and default the policy to enabled for eligible sources.
- Given the GTK toggle or CLI flag, the plan should expose matching policy
  and source decisions, and successful export should persist the selected
  policy only after publication.
- Given combined FPS and upscale settings, the source should be restored and
  spatially prepared before FPS interpolation, then composed at the fixed
  output profile with exact duration, frame count, audio, and timeline order.
- Given a missing RVE environment, failed model execution, cancellation, or
  invalid output, the command should fail explicitly, remove partial output,
  and leave every original source unchanged.
- Given disabled upscale, existing stream-copy/fallback/enhanced behavior and
  output metadata should remain unchanged.

## Validation

- Focused unit tests for the policy, model persistence, planning,
  composition filters, CLI/UI state, and route selection.
- Focused generated-media execution tests for eligible landscape and portrait
  sources, triplicate composition, combined FPS behavior, failure cleanup,
  output metadata, and source hashes.
- Existing repository unit suite, compilation, and applicable smoke checks.
- Target-workstation real-media export/playability check using the local RVE
  environment, with unavailable checks recorded explicitly.

## User-validation plan

- **Setup:** open a project containing eligible landscape and portrait
  sources; ensure the local RVE Python environment and SuperUltraCompact
  weights are available.
- **Steps:** export once with upscale off, once with upscale on, and once with
  both upscale and FPS enhancement on; inspect the GTK summary and equivalent
  CLI plan; reopen the project after a successful GUI export.
- **Expected visible result:** the panel and plan identify upscale
  enhancement and eligible source decisions; the enabled output remains
  playable at 1920x1080 with the selected FPS and shows the intended normal
  or triplicate composition.
- **Expected persisted/external result:** the project stores the versioned
  policy after successful publication, source hashes are unchanged, and
  temporary partial files are absent.
- **Failure paths:** disable or interrupt the RVE runtime, cancel an export,
  or use an invalid destination; the error must be explicit and no substitute
  output may be published.
- **Cleanup:** remove only generated exports and temporary fixtures after
  inspection.
- **Evidence response:** return `PASS`, `FAIL`, `BLOCKED`, or approved
  `NOT APPLICABLE`, with metadata, source-preservation, and UI/CLI evidence.
- **Pass criteria:** every acceptance criterion and protected behavior has
  terminal evidence.

## Closure

TICKET-079 is complete. The user confirmed the optional upscale behavior was
manually validated and requested closure of all tickets on 2026-08-28.
Existing evidence retains the environment and delivery warnings without
changing the disabled-path safety contract.
