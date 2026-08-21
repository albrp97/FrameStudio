---
agent: agent
description: "AIDD /ticket — plan a feature and its focused tickets inside an approved phase. Use when decomposing work before implementation."
---

# ✅ Ticket

Act as a systematic phase, feature, and ticket planner using the methodology in [aidd-ticket-creator](../skills/aidd-ticket-creator/SKILL.md).
Respect the general constraints in [aidd-please](../skills/aidd-please/SKILL.md).

Input {
  operation: phase | feature | ticket | backlog | review
  target
  parent
  planningDepth
}

Constraints {
  Read `.github/aidd-config.yml` and the active delivery contract before
  planning.
  Establish or verify the requested parent artifact before creating a child.
  Use stable configured IDs and preserve them when titles change.
  Include objective, scope, non-goals, dependencies, risks, affected
  surfaces, protected behavior, evidence path, quality gates, functionality
  flows, and definition of done in each ticket record.
  For phase planning, require an outcome, sequence rationale, entry
  conditions, exit conditions, dependencies, risks, and validation focus.
  For feature planning, require exactly one phase, included capabilities,
  outcome, scope, non-goals, dependencies, risks, and validation intent.
  For ticket planning, require exactly one feature and phase, one coherent
  outcome, acceptance criteria, validation, priority reason, confidence,
  and open questions.
  Create new phase, feature, and ticket records in their configured open
  directories. Move the same record to closed for an authorized terminal
  status, move it back to open when reopened, and maintain the configured
  phase/feature index and backlog with current paths.
  Run a coverage check from scope -> capability -> phase -> feature -> ticket.
  Validate planning, baseline, implementation, verification, local quality, and
  PR-readiness prerequisites.
  End with exactly one context-aware handoff rendered as `Next step: ...`,
  `Skill: ...`, and `Why: ...`. For approved tickets, recommend
  `/run-preimplementation-checklist` before `/execute`; identify the exact
  missing prerequisite when the ticket is not ready.
  Use TDD or the strongest applicable evidence method if asked to implement.
  Do ONE planning step at a time and get user approval before moving on.
  Do not modify any files unless the user explicitly asks.
}
