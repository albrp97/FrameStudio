# CHG-005 - Adopt Per-Source Render Strategy as the Enhanced Default

**Change ID:** CHG-005
**Type:** Material planning change
**Status:** approved-and-applied
**Date:** 2026-08-26
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Owner:** repository planning; maintainer identity is not recorded
**Approval:** User-authorized by the request to make Strategy B the default
for rendering after reviewing the corrected 1920x1080/60 FPS comparison.
**Source paths:** `evidence/phase-008-render-strategy-comparison.md`,
`evidence/phase-008-render-strategy-comparison.json`,
`docs/planning/tickets/closed/TICKET-072-select-and-document-mixed-fps-render-default.md`,
`docs/planning/features/closed/FEAT-026-comparing-mixed-fps-render-strategies.md`,
`resolve_editor/export_interpolation.py`,
`resolve_editor/export_smart_render.py`,
`resolve_editor/export_delivery.py`,
`.github/aidd-config.yml`
**Affected IDs:** FEAT-026, TICKET-076, PHASE-008, CAP-005, CAP-011, CAP-012
**Last updated:** 2026-08-26

## Request and classification

The user approved changing the enhanced-export production default from the
concat-first Strategy A route to the per-source Strategy B route after the
matched benchmark showed Strategy B completing 23.6% faster at 1920x1080 and
60 FPS, with a 2.4% final-size increase.

This is a material planning change because it reopens a completed feature,
changes production routing, and creates a new implementation and verification
boundary. The historical Strategy A decision remains preserved in TICKET-072
and the comparison evidence.

## Decision

1. Reopen FEAT-026 without changing its stable ID or path history.
2. Add TICKET-076 as the focused implementation unit.
3. Make Strategy B the preferred route whenever enhanced export is selected:
   prepare each retained segment at its native rate, enhance eligible
   segments independently, and assemble them in timeline order.
4. Use explicit safe fallback rendering when a stream-copy final join is not
   valid or when a rate/action is unsupported; fallback must preserve output
   verification, cancellation, cleanup, and source safety.
5. Keep the fixed delivery profile and existing non-enhanced export behavior
   unchanged.

## Required evidence and boundaries

- Unit coverage for routing, segment preparation, ordering, final assembly,
  and fallback selection.
- Generated-media coverage for mixed dimensions/rates, audio decisions,
  source preservation, output metadata, cancellation, and cleanup.
- The RVE backend remains subject to its existing runtime/artifact gate; the
  latest benchmark evidence measures the FFmpeg interpolation fallback.
- No restoration, model, codec dependency, or legacy-script behavior changes.

## Affected-artifact inventory

| Artifact | Impact | Action |
|---|---|---|
| FEAT-026 | Reopened for approved implementation follow-up | Move back to `features/open/` and update index |
| TICKET-076 | New focused implementation and verification unit | Add to `tickets/open/` and backlog |
| Enhanced export dispatcher | Strategy B becomes preferred enhanced route | Implement and test |
| Historical TICKET-072/evidence | Preserve prior measured decision and limits | Leave historical record intact |
| Non-enhanced and legacy routes | Protected behavior | No unrelated changes |

## Approval and remaining gates

The user approval authorizes this bounded implementation scope. Ticket
execution still requires the configured baseline, preimplementation,
evidence, local-quality, applicable real-system, static-analysis, review, and
user-validation gates before closure or delivery.
