---
agent: agent
description: "/planning-bootstrap — initialize trustworthy planning context"
---

# Planning-Bootstrap

Use [../skills/aidd-planning-bootstrap/SKILL.md](../skills/aidd-planning-bootstrap/SKILL.md) as the executable contract.

userPrompt = """
Initialize planning context for the requested repository change. Resolve configured artifact paths and canonical vocabulary, inspect existing objective/scope/maps and all phase, feature, and ticket records in both open and closed directories, validate status/path and index consistency, classify adaptive depth, and report inconsistencies or approval blockers. Write only explicitly authorized bootstrap artifacts; do not generate phases, features, or tickets as a side effect.
Read `delivery.development.mode` from `.github/aidd-config.yml`. In `guided`
mode preserve the normal approval handoffs. In `automatic` mode, after the
verified project-bootstrap handoff, continue through each planning layer
without asking for downstream approval or waiting for a user response; record
the bootstrap-authorized decision, use the exact Rubber Duck `gpt-5.6-luna`
high-reasoning `all-validation` profile for planning validation, and stop
only on a real blocker.
When an artifact update is explicitly approved, use repository file operations to
create or update the configured path, re-read it, and report the verified
created/updated/unchanged or blocked result. Do not return artifact contents as
a substitute for writing them. Each created or updated result requires a host
file create/edit tool call and read-back verification. `draft` and `status` are
read-only; `write` persists a previously approved update.
If no recoverable approved update exists for `write`, report a blocker instead
of reconstructing or writing new content.
"""

Constraints {
  Treat paths as repository-relative and read `.github/aidd-config.yml` when present
  Reconcile configured open/closed planning directories and current index paths
  Do not move records or silently repair status/path mismatches
  Use canonical objective -> scope -> capability -> phase -> feature -> ticket ancestry
  Use adaptive depth, stable IDs, parent/child links, explicit statuses, and evidence/coverage links
  Do not silently generate downstream artifacts, expand scope, or claim readiness without terminal evidence
  Do not stop at a response-only planning report when a write is authorized
  Verify every authorized write by reading the resulting path
  Report failed or unavailable writes as blockers
  Stop and report the exact blocker for missing parent, approval, evidence, ownership, or required capability
  In automatic mode, do not ask follow-up questions or wait for user
    validation; route the next action internally after each verified write and
    require the exact Rubber Duck `gpt-5.6-luna` high-reasoning
    `all-validation` profile for every planning validation decision
  Never record automatic agent validation as user confirmation
  Do not assume npm, GitHub, Azure, credentials, or a particular test runner
}
