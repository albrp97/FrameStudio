# PHASE-009 - Selecting and Delivering Efficient Export Pipelines

**Phase ID:** PHASE-009
**Parent links:** OBJ-001, SCOPE-001
**Capability links:** CAP-005, CAP-011, CAP-012
**Sequence:** 9
**Status:** active
**Horizon:** future
**Owner:** repository implementation in the active worktree
**Approval:** user-authorized by the 2026-09-09 request to measure and
implement the most efficient export pipeline
**Last updated:** 2026-09-09
**Source paths:** `vision.md`, `docs/specs/project-scope.md`,
`docs/specs/future-product-direction.md`,
`docs/planning/phases/closed/PHASE-008-optimizing-responsive-preview-and-media-strategy.md`,
`docs/planning/features/closed/FEAT-026-comparing-mixed-fps-render-strategies.md`,
`docs/planning/features/closed/FEAT-028-adding-optional-upscale-enhancement.md`,
`docs/planning/tickets/closed/TICKET-076-adopt-per-source-render-strategy.md`,
`docs/planning/tickets/closed/TICKET-080-benchmark-upscale-render-strategies.md`,
`framestudio/export_smart_render.py`, `framestudio/export_interpolation.py`,
`framestudio/export_cache.py`, `framestudio/export_session.py`,
`benchmarks/render_strategy_benchmark.py`, `.github/aidd-config.yml`
**Affected surfaces:** export planning, smart-render preparation,
interpolation, restoration/upscale ordering, composition, audio
normalization, resumable artifacts, benchmark harnesses, output verification,
CLI/GUI progress, tests, and evidence
**Feature links:** FEAT-030, FEAT-031
**Path history:** created at
`phases/open/PHASE-009-selecting-and-delivering-efficient-export-pipelines.md`

## Outcome

FrameStudio measures and uses the fastest export route that remains safe for
mixed sources, deleted boundaries, visual focus and triplicate composition,
audio normalization, frame-rate enhancement, optional restoration/upscale, and
resumable execution. The selected route is conditional and evidence-bounded,
not a universal hardware claim.

## Included

- Define one reproducible comparison protocol for current per-segment export,
  grouped boundary-safe export, source/run batching, and relevant enhancement
  orderings.
- Measure equivalent edits with mixed dimensions, codecs, frame rates, cuts,
  visual transforms, triplicate composition, audio policy, FPS policy, and
  optional upscale policy.
- Record end-to-end and per-stage timing, process counts, CPU, memory, GPU
  observations, intermediate storage, output metadata, playability, frame
  boundaries, source preservation, cleanup, and resume reuse.
- Select a conditional production route from the measured candidates.
- Implement grouped or source-level work only where the route preserves exact
  timeline order and hard edit boundaries.
- Retain explicit verified fallbacks when a backend cannot batch safely or a
  stream-copy join is rejected.
- Preserve existing cache/session identity, atomic publication, cancellation,
  source safety, and user-visible progress contracts.

## Explicit non-goals

- Claiming the measured route is optimal on hardware or media not represented
  by the benchmark.
- Replacing the validated RVE or SuperUltraCompact models, adding dependencies,
  or changing the fixed 1920x1080 delivery contract.
- Interpolating across deleted boundaries when the selected backend cannot
  prove boundary-safe behavior.
- Processing full source media by default when a retained-range route is
  measurably safer and faster.
- Removing the existing per-segment route or historical benchmark evidence.
- Changing editor scope, project semantics, legacy scripts, or source files.

## Entry conditions

- PHASE-008 is complete and its mixed-FPS, restoration, upscale, and
  resumable-export behavior is available as the protected baseline.
- The existing export test suite and compilation baseline pass.
- FFmpeg/ffprobe and the target workstation resource probes are available.
- The local RVE/TensorRT runtime and model availability are recorded before
  any RVE benchmark row is treated as runnable.
- Representative media or reproducible fixtures cover the required route
  combinations.

## Exit conditions

- A benchmark protocol fixes equivalent inputs, output profile, enhancement
  policy, verification gates, warm/cold-run handling, and unavailable-row
  behavior.
- Baseline and candidate reports contain actual measurements and explicit
  evidence limits.
- The selected route preserves output duration, frame rate/count, dimensions,
  codecs, audio policy, timeline order, hard boundaries, source bytes, atomic
  publication, cleanup, and resume behavior.
- Functionality tests prove that safe grouping reduces redundant work without
  changing protected output behavior.
- The implementation documents why a candidate is selected or rejected and
  records unavailable or subjective checks as limitations.
- The user receives exact real-media validation steps before the phase or its
  tickets are closed.

## Dependencies and risks

- Depends on the existing fixed output policy, source-level audio decisions,
  interpolation artifact gate, restoration runtime, and export session/cache
  identity.
- Model startup, GPU memory, storage throughput, codec seek behavior, and
  encoder settings can dominate different candidates.
- A single concatenated stream can blend frames across deleted ranges unless
  cuts occur after enhancement or the backend supports explicit safe ranges.
- Subjective visual quality requires separate human review and must not replace
  machine-readable output checks.

## Validation and evidence

- Machine-readable and Markdown benchmark reports under `evidence/` or the
  configured benchmark result directory.
- Unit and automated functionality tests for route selection, grouping,
  metadata, hard boundaries, cache reuse, cancellation, and fallback.
- Existing repository tests, compilation, smoke, contract, quality, and
  static-analysis commands where available.
- Target-workstation real-media output probes and source-hash evidence.
- Explicit blocked/skipped rows for unavailable runtimes, hardware, or visual
  review.

