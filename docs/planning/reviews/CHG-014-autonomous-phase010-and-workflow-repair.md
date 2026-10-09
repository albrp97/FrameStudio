# CHG-014 - Autonomous PHASE-010 and Necessary Workflow Repair

**Change ID:** CHG-014
**Parents:** OBJ-001 / SCOPE-001 / PHASE-010
**Status:** approved
**Approved:** 2026-10-09
**Owner:** orchestrator

## Authorization and scope

The user explicitly authorized everything needed to finish the implementation,
testing and working behavior, requested autonomous orchestration, and directed
the assistant to stop asking routine questions. This approves the focused
test/CI repair proposed immediately before that response and switches this
PHASE-010 run from guided to automatic execution.

Persist automatic mode in the authoritative delivery configuration and mirror
it in vision/agent guidance. The existing foundational context and product
contract remain authoritative; do not bootstrap a duplicate hierarchy.
Routine subsequent contracts use confirmed behavior and the smallest safe
implementation decisions, recorded as agent decisions rather than human
functionality results.

Implementation workers remain bounded GPT-5.6 Luna max agents. Every automatic
validation decision is owned by the exact configured Rubber Duck GPT-5.6 Luna
high `all-validation` capability. Deterministic tool output is still raw
evidence. No agent may fabricate a user result.

## Necessary additional maintenance

Add TICKET-126 under existing PHASE-010 / FEAT-038 for:

- Refactor the inherited export-panel test duplication without weakening its
  assertions or suppressing/updating the approved baseline.
- Restore the repository's CI workflow to actual existing quality commands,
  removing the reference to the missing evaluation script.
- Prove executable local quality and CI-command parity, not merely valid YAML.

This adds one focused maintenance ticket to the existing 17-ticket product
plan. It does not add product capabilities or a new phase. It is independent
of track-model writes and can run in isolation alongside TICKET-115.

## Gates and boundaries

Automatic execution replaces pending guided functionality handoffs with
executable agent-owned charters and `automaticValidation`. It does not
retroactively claim old tickets passed, close unrelated phases, waive missing
tools, suppress failed checks, expose secrets, bypass provider/branch/merge
policy, or authorize destructive operations. Commit/push/PR operations remain
integration-owner tasks after actual configured readiness.

TICKET-104's required export-integrity evidence remains a real prerequisite;
the orchestrator must establish the appropriate terminal validation rather
than treating its old `verifying` status as a pass. Necessary prerequisite
verification belongs to this authorized delivery path, not unrelated feature
expansion.
