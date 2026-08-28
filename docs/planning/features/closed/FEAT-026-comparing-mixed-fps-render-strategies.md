# FEAT-026 - Comparing Mixed-FPS Render Strategies

**Feature ID:** FEAT-026
**Parent links:** OBJ-001, SCOPE-001, PHASE-008
**Capability links:** CAP-005, CAP-011, CAP-012
**Status:** complete
**Change control:** reopened on 2026-08-26 after user approval to implement
the evidence-backed Strategy B production default through TICKET-076.
**Horizon:** future
**Priority:** 3
**Owner:** repository planning; maintainer identity is not recorded
**Approval:** user-authorized on 2026-08-26 to break down PHASE-008; ticket
execution remains separately gated by the configured approval policy
**Last updated:** 2026-08-28
**Source paths:** `docs/planning/phases/open/PHASE-008-optimizing-responsive-preview-and-media-strategy.md`,
`docs/specs/future-product-direction.md`, `resolve_editor/export_smart_render.py`,
`resolve_editor/export_interpolation.py`, `resolve_editor/export_delivery.py`,
`resolve_concat.py`, `resolve_fps.py`, `tests/test_editor_smart_render.py`,
`tests/test_editor_interpolation.py`, `FAST-CONCAT-RESEARCH.md`,
`FPS-ENHANCEMENT-RESEARCH.md`, `docs/planning/reviews/CHG-005-adopt-per-source-render-default.md`,
`.github/aidd-config.yml`
**Dependencies:** PHASE-005 audio/delivery policy; PHASE-007 target-FPS and
interpolation behavior; representative mixed-FPS media; target workstation
**Risks:** one route may appear faster because it does less work, quality
comparisons may be subjective, intermediate files may distort storage and
I/O results, and local hardware may not represent other systems
**Affected surfaces:** export planning, smart-render preparation,
interpolation routing, temporary artifacts, benchmark harnesses, output
verification, and delivery documentation
**Evidence path:** `evidence/phase-008-render-strategy-comparison.md`
**Planned tickets:** TICKET-069, TICKET-070, TICKET-071, TICKET-072, TICKET-076
**Path history:** `features/open/FEAT-026-comparing-mixed-fps-render-strategies.md`
-> `features/closed/FEAT-026-comparing-mixed-fps-render-strategies.md`
-> `features/open/FEAT-026-comparing-mixed-fps-render-strategies.md`
-> `features/closed/FEAT-026-comparing-mixed-fps-render-strategies.md`

## Outcome

The project has a measured comparison of two mixed-FPS export strategies and
uses the evidence-backed per-source strategy as the preferred enhanced-export
route while retaining safe fallbacks for media that cannot be joined directly.

## Scope

- Compare strategy A: prepare and consolidate retained source content at the
  minimum input FPS, then run one target-FPS enhancement pass.
- Compare strategy B: smart-render each source or clip with its modifications,
  enhance each prepared result to the target FPS, then concatenate the final
  outputs.
- Measure end-to-end and stage timing, frame-rate preservation, frame count,
  duration, audio, playability, intermediate and final size, resource use,
  and observable quality tradeoffs.
- Implement and verify the approved per-source default without weakening
  timeline ordering, output verification, cancellation, or source safety.

## Explicit non-goals

- Claiming either route is universally optimal.
- Changing unrelated export behavior or adding a third rendering architecture.
- Introducing a third rendering architecture in this feature.
- Treating subjective visual preference as a substitute for output-integrity
  checks.

## Observable requirements

- Given the same representative project and target FPS, both strategies
  should run with equivalent source ranges, audio policy, output profile, and
  verification gates.
- Given each run, the benchmark should report stage and total wall time,
  frame count/FPS, duration, audio/playability results, artifacts, and
  intermediate/final storage requirements.
- Given quality review, measurable output correctness and subjective visual
  observations should be reported separately.
- Given the evidence, the project should record a clear default, conditional
  routing rule, or justified decision to defer a route change.

## Validation and evidence

- Reproducible benchmark definitions and fixture descriptions.
- Strategy A and B timing/output reports from the target workstation.
- FFprobe/output-verification evidence and source-preservation checks.
- Separate visual-quality observations with known limitations.
- Review of whether the evidence justifies a production routing change.

## Protected behaviors

The measured concat-first route remains historical evidence. Its output
profile, audio decisions, atomic publication, cancellation, cleanup,
verification, legacy scripts, and source preservation remain protected.

## Definition of done

- Both strategies have comparable, reviewable measurements.
- The result states whether a second route is worth supporting and why.
- The approved production route is implemented as a focused follow-up and
  retains an explicit safe fallback for unsupported or incompatible media.

## Prior closure

The comparison work was previously closed after TICKET-069 through TICKET-072
reached complete status. That historical closure selected Strategy A before
the user approved the implementation follow-up.

## Closure

FEAT-026 is complete. TICKET-076 implemented the approved per-source
enhanced-export default with timeline-order assembly and safe fallback
behavior. The user confirmed the feature was manually validated and
requested closure of all tickets on 2026-08-28; benchmark limitations remain
documented.
