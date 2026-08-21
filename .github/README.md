# AIDD Repository Workflow

This directory contains a repository-neutral, evidence-first workflow for
turning an objective into focused implementation tickets.

## Planning hierarchy

```text
objective -> scope -> capability -> phase -> feature -> ticket
```

- **Objective:** why the work exists.
- **Scope:** what belongs in the current delivery horizon.
- **Capability:** an ability the system or operation must provide.
- **Phase:** a top-level delivery stage with entry and exit conditions.
- **Feature:** an outcome slice inside one phase.
- **Ticket:** a focused unit that can be implemented and verified coherently.

Stable IDs and durable parent links preserve traceability when names change.

## Normal new-project flow

1. `/project-bootstrap` or `/aidd-project-bootstrap` creates approved
   foundational context: `vision.md`, project-specific `AGENTS.md`,
   repository mapping, scope, and delivery configuration.
2. `/discover` establishes or refines the approved objective, scope, non-goals,
   risks, dependencies, success signals, and verification intent.
3. `/create-capability-map` records system abilities and scope coverage.
4. `/create-phases` defines ordered delivery stages.
5. `/create-features` groups capabilities into outcomes inside each phase.
6. `/create-tickets` creates the focused backlog; `/groom-backlog` keeps it
   ordered and executable.
7. `/review-planning-layer` reviews each artifact before child generation.
8. `/run-preimplementation-checklist` confirms the selected ticket is ready.
9. `/execute`, `/evidence`, and `/review` implement and verify one ticket.
   `/review` runs the deterministic static-analysis suite, checks parity with
   the pull-request pipeline, and coordinates scoped remediation through
   `/aidd-fix`.
10. `/commit` creates the reviewed local checkpoint, `/push` publishes an
    approved commit when needed, and `/aidd-pr` creates or monitors the PR
    when repository policy requires one.
11. `/phase-feedback` completes phase learning after configured delivery
    closeout.

Small fixes use a single ticket without inventing unnecessary parent layers.
Material scope or dependency changes use `/replan-when-necessary`; routine
backlog corrections use `/groom-backlog`.

The default delivery loop is ordered:

```text
technical verification -> user validation -> review -> commit -> push -> PR
```

Each operation is conditional. Commit requires reviewed staged scope; push
requires a successful local commit and an unpublished or ahead branch; PR
requires a published branch and applicable pull-request policy. A repository
may omit push or PR when its configured local-delivery policy permits it.

The static-analysis layer is deterministic and repository-configured. It may
use SonarQube Community Build, the repository formatter/linter/type checker,
Semgrep, dependency-cruiser, jscpd, language-native complexity tools, and
`aidd-churn`. Review does not auto-fix these tools; it routes each actionable
introduced finding through the approved `aidd-fix` loop and reruns the suite
until findings are resolved or explicitly classified.

## Durable artifacts

The default paths are configured in `aidd-config.yml`:

```text
AGENTS.md
README.md
vision.md
docs/
  specs/
    project-scope.md
    capability-map.md
  planning/
    repo-map.md
    phases.md
    features.md
    backlog.md
    phases/
      open/
      closed/
    features/
      open/
      closed/
    tickets/
      open/
      closed/
    reviews/
evidence/
```

Existing repository conventions take precedence. Do not create duplicate
sources of truth when a repository already has an equivalent planning system.

For a repository using the older planning layout, run
`/adapt-planning-structure` first. It inventories the current records, waits
for approval, then migrates them to the open/closed organization without
discarding stable IDs or history.

`phases.md`, `features.md`, and `backlog.md` are synchronized indexes. Each
phase, feature, and ticket is a separate Markdown record under its layer's
`open/` or `closed/` directory. New records are created in `open`; terminal
statuses move the same record to `closed`, and reopening moves it back to
`open`. Preserve stable IDs and history, update indexes and parent links after
every move, keep blocked records open, and never use deletion or duplication as
an archive operation.

After implementation, the TDD workflow returns a copy/paste-ready
user-validation handoff with exact setup, steps, expected results, and pass
criteria. Tickets remain in `verifying` until the user returns a result and it
is recorded as evidence; technical tests alone do not close a ticket.

Every workflow response also ends with one context-aware handoff naming the
next concrete step, the single skill and command to use, and why it follows
from the current planning state, evidence, approval, or blocker. When no active
context exists, use the orchestrator to classify the request before selecting
the next skill. Render the handoff as:

```text
Next step: <one concrete action or decision>
Skill: <one skill> — <one command>
Why: <why it follows from the current state, gate, or blocker>
```

## Safety contract

Planning stops when a parent is missing, blocked, contradictory, or awaiting
approval. Tickets must declare scope, non-goals, dependencies, acceptance
criteria, validation, risks, evidence, and affected surfaces. Implementation
does not claim readiness without terminal evidence for required gates, and
unavailable tooling is recorded as a blocker or coverage gap. Project
bootstrap drafts foundational files before writing, preserves existing
instructions and sources of truth, and never creates downstream planning
children without approval.

See [`copilot-instructions.md`](copilot-instructions.md) for the operating
rules and [`aidd-map.md`](aidd-map.md) for the complete artifact inventory.
