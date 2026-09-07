# PHASE-008 - Optimizing Responsive Preview and Evidence-Based Media Processing

**Phase ID:** PHASE-008
**Parent links:** OBJ-001, SCOPE-001
**Capability links:** CAP-002, CAP-003, CAP-004, CAP-005, CAP-006, CAP-009,
CAP-011, CAP-012
**Sequence:** 8
**Status:** complete
**Progress:** FEAT-024 through FEAT-029 and TICKET-061 through TICKET-101 are
complete and closed. The delivered work covers responsive source attachment,
editor recovery, scalable timeline control, composition-position preservation,
resumable ordinary and enhanced exports, staged console observability,
continuous seeking, responsive export planning, explicit upscale/FPS-count
reporting, safe post-export actions, guarded Wayland renderer selection, and
exact enhanced-export frame-count recovery.
**Horizon:** future
**Owner:** repository planning; maintainer identity is not recorded
**Approval:** user-authorized on 2026-08-26 to create the phase and its feature
and ticket planning; FEAT-029 and TICKET-084 through TICKET-093 were
authorized through follow-up requests for implementation without separate
ticket approval
**Last updated:** 2026-09-07
**Source paths:** `vision.md`, `docs/specs/project-scope.md`,
`docs/specs/capability-map.md`, `docs/specs/future-product-direction.md`,
`docs/planning/phases.md`, `docs/planning/repo-map.md`,
`docs/planning/reviews/CHG-006-real-video-enhancer-restoration-benchmark.md`,
`docs/planning/reviews/CHG-007-expand-restoration-benchmark-matrix.md`,
`docs/planning/reviews/CHG-008-add-production-upscale-enhancement.md`,
`https://github.com/k4yt3x/video2x`,
`docs/planning/features/closed/FEAT-024-optimizing-cursor-driven-preview.md`,
`docs/planning/features/closed/FEAT-029-strengthening-editor-recovery-and-export-observability.md`,
`docs/planning/tickets/closed/TICKET-091-report-upscale-count-and-preserve-render-route.md`,
`docs/planning/tickets/closed/TICKET-092-avoid-wayland-vulkan-swapchain-warning.md`,
`evidence/ticket-091-report-upscale-count-and-preserve-render-route.md`,
`evidence/ticket-092-avoid-wayland-vulkan-swapchain-warning.md`,
`docs/planning/tickets/closed/TICKET-093-fix-enhanced-export-frame-count-and-cache-reuse.md`,
`evidence/ticket-093-fix-enhanced-export-frame-count-and-cache-reuse.md`,
`docs/planning/reviews/CHG-010-generalize-export-resume-across-cancellation-and-restarts.md`,
`docs/planning/tickets/closed/TICKET-098-persist-resumable-export-session-checkpoints.md`,
`docs/planning/tickets/closed/TICKET-099-checkpoint-and-resume-all-export-stages.md`,
`docs/planning/tickets/closed/TICKET-100-offer-export-resume-restart-and-discard-controls.md`,
`docs/planning/tickets/closed/TICKET-101-preserve-cli-export-resume-contract.md`,
`.github/aidd-config.yml`
**Affected surfaces:** GTK renderer initialization, GTK timeline interaction,
FFmpeg preview playback, preview caching and seeking, segment focus controls,
transform coordinate
mapping, export benchmarking, FPS strategy selection, restoration research,
optional upscale enhancement, documentation, tests, and evidence
**Feature links:** FEAT-024, FEAT-025, FEAT-026, FEAT-027, FEAT-028, FEAT-029
**Path history:** created at
`phases/open/PHASE-008-optimizing-responsive-preview-and-media-strategy.md`
-> moved to
`phases/closed/PHASE-008-optimizing-responsive-preview-and-media-strategy.md`
-> reopened under CHG-009 at
`phases/open/PHASE-008-optimizing-responsive-preview-and-media-strategy.md`
-> moved to
`phases/closed/PHASE-008-optimizing-responsive-preview-and-media-strategy.md`
on 2026-09-07 after all linked features, tickets, review gates, and user
validation completed.

## Outcome

The editor provides responsive cursor-driven preview and direct segment-focus
controls, including horizontal source-region selection for triplicate content
at default zoom, while mixed-FPS rendering and future restoration work are
guided by reproducible measurements rather than assumptions.

## Included

- Clone and inspect the public Lossless Cut repository as a disposable,
  license-reviewed research source for preview behavior; do not vendor it.
- Establish a representative preview benchmark that measures the current
  editor during timeline cursor movement, clicking, seeking, and scrolling.
- Compare candidate preview strategies, select the best measured strategy for
  the target workstation, and document its tradeoffs and limits.
- Provide a direct interaction for changing zoom and X/Y focus values without
  repeatedly opening and waiting for a separate modification action.
- Keep timeline scrolling as cursor navigation outside the focus-control
  interaction area.
- Verify that zoom levels 2x and 4x can reach the four corners and relevant
  edges through bounded X/Y offsets without clipping or unreachable regions.
- Allow triplicate segments to move their selected horizontal source region at
  the default 1x zoom without changing the established 2x/4x semantics.
- Compare concat-first enhancement with per-source smart-render, enhancement,
  and final-concatenation strategies using comparable media and output gates,
  then implement the approved per-source route as the enhanced-export default.
- Research video upscaling, denoising, deblocking, and low-bitrate restoration
  approaches; run the approved focused RVE benchmark and expanded cross-model
  comparison where runtimes and licenses permit; produce an implementation
  recommendation.
- Add an optional, bounded SuperUltraCompact upscale path for eligible
  landscape and portrait sources, enabled by default with an explicit opt-out,
  preserve the fixed delivery contract, and benchmark its render-order
  tradeoffs with the requested fixtures.
- Keep source import responsive with truthful per-clip progress, allow
  timeline zoom below 100%, and preserve the validated GPU interpolation
  encoder defaults.
- Attach a successfully probed source project before full-file audio analysis,
  report each source's pending/analyzing/terminal audio state, and preserve
  export-time analysis and failure gates.
- Maintain one current-project autosave with explicit source-safe recovery
  without changing normal project-save destinations.
- Support timeline zoom beyond the former 1200% ceiling and provide a
  30-minute viewport-fit action without changing focus/composition bounds.
- Preserve the live playhead and play/pause state when triplicate composition
  is enabled or disabled.
- Retain and validate completed enhanced-export intermediates across failed
  attempts, cleaning the cache only after verified publication.
- Preserve the exact selected video-frame count during enhanced mixed-source
  final composition without weakening strict output verification.
- Persist validated export-session checkpoints for ordinary and enhanced
  routes across cancellation, late failure, process restart, and project
  reopen, with explicit Resume, Start over, and Discard controls.
- Allow bounded time-sliced rendering to continue from the last valid stage
  without rerunning completed cutting, interpolation, upscale, or composition
  work.
- Report numbered export stages to interactive terminal users while preserving
  the machine-readable CLI contract.
- Avoid the known non-fatal Wayland Vulkan swapchain warning by selecting the
  supported GTK GL renderer only when no explicit renderer is configured.

## Explicit non-goals

- Replacing the existing editor or legacy scripts with Lossless Cut code.
- Vendoring, copying, or making the public Lossless Cut checkout a runtime
  dependency.
- Claiming a preview strategy is universally faster outside the measured
  target workstation and media set.
- Adding keyframes, arbitrary effects, transitions, or full compositor
  behavior to the focus controls.
- Changing the production render default without a controlled, approved
  implementation ticket and regression evidence.
- Integrating unapproved upscalers, denoisers, deblocking models, proprietary
  software, or new runtime dependencies in this phase.
- Changing the fixed output canvas, source-preservation guarantees, or safe
  export verification policy.
- Adding multiple autosave slots, silent startup recovery, a remote backup
  service, or a second machine-readable progress protocol.
- Silently resuming an export, supporting multiple concurrent checkpoint
  sessions for one destination, or reusing artifacts after source, project,
  policy, runtime, tool, or destination identity changes.

## Entry conditions

- PHASE-007 is complete and its target-FPS/export behavior is available as the
  protected baseline.
- The current GTK preview, timeline interaction, focus controls, mixed-source
  model, and smart-render export route are reproducible on the target
  workstation.
- Representative local media is available for preview and render
  measurements, including mixed dimensions and frame rates where practical.
- The repository-native test, smoke, contract, quality, and review commands
  are known; unavailable checks remain explicit rather than assumed.
- The public Lossless Cut source can be inspected, or its unavailable access
  is recorded as a research limitation.

## Exit conditions

- The current preview baseline and candidate strategies have measured
  interaction latency, frame freshness, and failure behavior for the defined
  pointer workflows.
- One preview strategy is selected as the default, or the evidence records
  why no change is justified; the implementation and tradeoffs are
  documented.
- Focus controls work directly from the intended interaction area, while
  ordinary timeline scrolling still moves the cursor.
- At 2x and 4x zoom, the focus view can reach all four corners and relevant
  edges, with bounds and coordinate semantics covered by regression tests.
- At default zoom, triplicate horizontal offsets move the repeated source
  region consistently through GUI, CLI, preview, and export.
- The two mixed-FPS render strategies have comparable timing, output-integrity,
  audio, frame-count, quality, and resource evidence, followed by the
  approved per-source routing implementation and its regression evidence.
- A restoration research report compares the requested candidates and
  controls, records model/runtime/license availability, separates measured
  and visual evidence, and identifies integration gates without claiming
  production support for candidates outside the approved SuperUltraCompact
  path.
- The approved SuperUltraCompact upscale path and its render-order benchmark
  have implementation, output-integrity, source-preservation, and
  target-workstation evidence, with unavailable capability limits explicit.
- Existing editing, export, source-safety, CLI, and legacy-script behavior
  remains protected by automated and applicable real-system evidence.
- A newly imported project is usable after metadata probing even while audio
  analysis continues, and background completion cannot mutate a replaced
  project or produce a false ready state.
- Wayland editor launches select the supported default renderer without
  changing explicit renderer choices or the media export pipeline.
- Enhanced mixed-source exports preserve the exact target frame count even
  when retained segment durations are frame-quantized differently from the
  original timeline durations. Compatible ordinary and enhanced exports can
  also resume from validated checkpoints after cancellation, failure, process
  restart, and project reopen without silently starting work.

## Dependencies and risks

- Depends on PHASE-006 focus/composition semantics and PHASE-007 timing/export
  behavior.
- Preview results may depend on codec, keyframe spacing, storage, cache state,
  CPU/GPU load, and window interaction timing.
- A public repository clone may be unavailable or may change independently;
  research must pin the inspected revision and preserve license attribution.
- Benchmark fixtures may favor one strategy, and target-workstation results
  must not be generalized to other hardware.
- Scroll-based controls can conflict with timeline navigation or accessibility
  expectations if the hit area and feedback are unclear.
- Background source analysis can race with project replacement, editing,
  saving, playback refresh, or export snapshot creation if generation and
  project identity are not checked.
- High zoom can expose coordinate, aspect-ratio, and crop-boundary errors.
- Per-source enhancement can preserve source FPS at the cost of repeated
  setup, intermediate storage, and concatenation overhead.
- Restoration models can require large downloads, specific GPU runtimes, or
  licenses incompatible with the project.

## Validation and evidence

- Preview baseline and candidate results with reproducible media, interaction
  scripts or harness inputs, latency percentiles, frame freshness, and
  resource observations.
- GUI and model tests for scroll context, zoom bounds, offset mapping,
  default-zoom triplicate movement, persistence, and CLI parity.
- Comparable A/B render reports with commands, media fingerprints or
  non-sensitive fixture descriptions, elapsed stages, output metadata,
  audio/playability checks, and quality observations kept separate.
- Research evidence for restoration candidates, including the machine-readable
  and human-readable cross-model reports, contact sheets, licensing and
  runtime constraints, and explicit unavailable/failed rows.
- Existing repository baseline, contract, smoke, quality, static-analysis,
  review, and applicable target-workstation evidence.
- Explicit warnings for unavailable network, hardware, model, or remote
  checks.
- Import responsiveness evidence must separate time to usable project from
  total audio-analysis time so normalization work is not silently removed.

## Reopening

PHASE-008 was reopened under CHG-009 on 2026-08-28 because the completed
responsive-preview outcome still left project attachment behind full-file
audio analysis. The reopened scope includes the import lifecycle and its
truthful audio-status, generation-safety, playback-refresh, export-gating, and
measurement evidence, plus the user-authorized FEAT-029 editor-resilience
outcomes. FEAT-025 through FEAT-028 remain closed and are not replanned by
this change.

Unavailable runtimes, remote checks, target-specific limitations, and
benchmark confidence boundaries remain preserved in the evidence records.
