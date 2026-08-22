# Delivery Evidence: TICKET-024

- Phase: `PHASE-004` - Combining Mixed-Source Footage
- Feature: `FEAT-012` - Previewing and Exporting Mixed-Source Edits
- Ticket: `TICKET-024` - Define Mixed-Source Output Canvas and Timing Policy
- Status: `verifying`
- Branch: `ticket/phase-004-mixed-source-footage`
- Evidence path: `evidence/phase-004-output-policy.md`

## Historical implementation policy (superseded by CHG-002)

The entries in this section record the prior mixed-source policy and remain
for traceability. The current fixed-canvas policy is appended below.

- Mixed output uses the maximum input width and height, rounded to even
  dimensions.
- Inputs are contain-scaled and padded, so portrait and landscape media are
  not silently stretched or cropped.
- Mixed output uses the highest input frame rate.
- Mixed inputs use normalized H.264/AAC MP4 fallback composition because
  dimensions, timing, or stream formats differ.
- Sources without audio receive generated silence when the composed output
  requires an audio stream.
- The policy reports normalization reasons and keeps one-source fast/fallback
  behavior unchanged.

## Evidence entries

### POLICY-001

- Evidence: `resolve_editor/export.py`,
  `tests/test_editor_mixed_source.py`, and
  `docs/specs/cli-contract.md`.
- Observed: Deliberately different dimensions and frame rates resolve to the
  deterministic mixed output policy and report why fallback is required.
- Status: `passed`

### USER-001

- Required: Maintainer review of portrait/landscape canvas behavior and the
  explicit deferral of automatic audio normalization and FPS enhancement.
- Status: `pending`

## Superseding evidence: CHG-002 fixed project canvas

The `POLICY-001` entry above is retained as historical evidence for the
superseded maximum-dimension policy. The current project policy is recorded
below without removing that history.

### POLICY-002

- Evidence: `resolve_editor/export.py`,
  `tests/test_editor_export.py`, `tests/test_editor_mixed_source.py`, and
  `docs/specs/phase-002-export-policy.md`.
- Observed: One-source and mixed-source policies resolve to a fixed
  1920x1080 canvas. Non-1080p one-source inputs select fallback rendering;
  matching 1920x1080 inputs remain eligible for the existing stream-copy
  route.
- Observed: Source codec/container changes do not change the established
  output profile, and current frame-rate selection remains separate from the
  deferred 60 FPS capability.
- Status: `passed`

### POLICY-USER-001

- Required: Maintainer confirmation of fixed-canvas preview and export on the
  target workstation.
- Status: `pending`
