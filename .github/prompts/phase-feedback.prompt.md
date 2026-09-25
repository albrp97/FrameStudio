---
agent: agent
description: "/phase-feedback — record active phase feedback"
---

# Phase-Feedback

Use [../skills/aidd-phase-feedback/SKILL.md](../skills/aidd-phase-feedback/SKILL.md) as the executable contract.
Read `delivery.development.mode` from `.github/aidd-config.yml`. In automatic
mode, validate closeout through the exact `rubber-duck` / `gpt-5.6-luna` /
high-reasoning / `all-validation` profile and continue to the next ready phase
after verified closeout; in guided mode, preserve the configured approval
handoff.

userPrompt = """
Record source-linked feedback for one phase against its outcome, entry conditions, exit conditions, children, and evidence. Classify observations, corrections, blockers, and material changes; preserve history and stable IDs. Update status only with evidence and configured approval. Route material changes to change control and do not generate descendants silently.
"""

Constraints {
  Treat paths as repository-relative and read `.github/aidd-config.yml` when present
  Read the phase from either lifecycle directory and linked children from both;
  when approved status changes cross the boundary, move the same phase file and
  synchronize the phase index
  Never close a phase while required child features remain open or incomplete
  Use canonical objective -> scope -> capability -> phase -> feature -> ticket ancestry
  Use adaptive depth, stable IDs, parent/child links, explicit statuses, and evidence/coverage links
  Do not silently generate downstream artifacts, expand scope, or claim readiness without terminal evidence
  Stop and report the exact blocker for missing parent, approval, evidence, ownership, or required capability
  In automatic mode, do not ask or wait after terminal phase feedback; use the
    exact `rubber-duck` / `gpt-5.6-luna` / high-reasoning / `all-validation`
    profile, preserve true blockers, and route them to the orchestrator
  Do not assume npm, GitHub, Azure, credentials, or a particular test runner
}
