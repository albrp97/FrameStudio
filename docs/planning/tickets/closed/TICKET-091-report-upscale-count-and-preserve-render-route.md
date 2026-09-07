# TICKET-091 - Report Upscale Count and Preserve the Render Route

**Ticket ID:** TICKET-091
**Title:** Report eligible videos and preserve the upscale render route
**Status:** complete
**Parent feature:** FEAT-029
**Parent phase:** PHASE-008
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Capability links:** CAP-005, CAP-012
**Owner:** repository implementation in the active worktree
**Approval:** Explicitly authorized by the user's request to show how many
videos will be upscaled and ensure the upscale export path still works
**Last updated:** 2026-09-07
**Dependencies:** TICKET-079 production upscale route; TICKET-087 enhanced
export cache; TICKET-090 responsive export planning; source-level upscale
policy and GTK export panel
**Affected surfaces:** `framestudio/export_panel.py`,
`framestudio/app_export.py`, `framestudio/upscale_policy.py`,
`framestudio/export_smart_render.py`, upscale policy and export execution
tests, GTK export interaction, and evidence
**Risks:** the panel could show a stale or segment-based count, preparation
could become synchronous again, an ineligible source could reach the model,
or an upscale failure could publish a substitute output
**Evidence path:** `evidence/ticket-091-report-upscale-count-and-preserve-render-route.md`

## Observable requirements

- Given an export panel with upscale enabled, the panel should promptly show
  the number of unique eligible source videos, even while the rest of export
  planning is still preparing.
- Given upscale disabled, the panel should explicitly show zero videos to
  upscale and keep the existing non-upscale route.
- Given mixed eligible and ineligible sources, only eligible sources should
  reach the restoration/upscale stage; ineligible sources should pass through
  the established preparation path.
- Given a successful upscale export, the output should retain the fixed
  delivery profile, expected duration and frame rate, and source files should
  remain unchanged.
- Given a failed or unavailable upscale stage, the exporter should surface the
  failure, remove partial output, and avoid publishing a substitute result.

## Scope

- Make the source-level upscale count explicit in export-panel state and
  visible labels.
- Show the count immediately in the planning panel before asynchronous plan
  preparation completes.
- Add focused policy/display regressions and generated-media execution
  coverage for eligible and ineligible sources.
- Preserve the existing RVE restoration, cache, verification, and atomic
  publication behavior.

## Non-goals

- Changing orientation thresholds, target dimensions, model selection, or
  the fixed 1920x1080 delivery canvas.
- Replacing the validated RVE runtime or adding another restoration model.
- Changing the per-source render strategy or source-level audio policy.

## Validation

- Focused export-panel and upscale-policy tests, including enabled,
  disabled, mixed-eligibility, and zero-eligible cases.
- Generated-media upscale execution with restoration-call and output metadata
  assertions.
- Existing repository unit, compile, contract, smoke, quality, and review
  gates.
- Target-workstation export-panel interaction and a short representative
  upscale export, or an explicit runtime limitation with evidence.

## Definition of done

- The panel clearly reports the source-level number of videos to upscale
  without waiting for expensive backend validation.
- Focused regressions prove only eligible sources enter the upscale route.
- Successful and failure-path export behavior remains source-safe and
  atomically verified.
- User-visible behavior is validated or an explicit environment limitation
  is recorded; the ticket remains `verifying` until user confirmation.

**Path history:** Created in `docs/planning/tickets/open/` on 2026-09-05.
Moved to `docs/planning/tickets/closed/` on 2026-09-07 after user
validation.
