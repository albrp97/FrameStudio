# Harmonic Coding

<p align="center">
  <img src="../harmonic-coding-banner.svg" alt="Harmonic Coding" width="100%">
</p>

> **Human-Directed AI-assisted software development** for planning, building,
> reviewing, and shipping software in a controlled, durable, and repeatable way.

Harmonic Coding is a **repo-based operating model for Human-Directed
AI-assisted software development**. This file documents the repository-native,
evidence-first workflow used to turn an objective into focused implementation
tickets.

Harmonic Coding is the product and operating model. Its current workflow is a
modified implementation of patterns explored in the AIDD research; AIDD is not
a separate framework that adopting repositories need to introduce. Some
internal filenames retain the `aidd-` prefix for compatibility with existing
prompts, skills, and evaluations.

## Repository workflow

For the full Harmonic Coding explanation, read:

- [`docs/guide/aidd-operating-model.md`](../docs/guide/aidd-operating-model.md)
  for the runtime contract, modes, evidence, and validation ownership;
- [`docs/guide/aidd-use-case-workflows.md`](../docs/guide/aidd-use-case-workflows.md)
  for typical end-to-end workflows;
- [`docs/guide/aidd-bundle-migration.md`](../docs/guide/aidd-bundle-migration.md)
  for the integration boundary between the modified workflow and this
  repository's local extensions.

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
9. `/execute`, `/run-test`, `/evidence`, and `/review` implement and verify
   one ticket. Every ticket must finish its technical verification with an
   automated functionality test through the supported system boundary;
   `/review` also runs the deterministic static-analysis suite, checks parity
   with the pull-request pipeline, and coordinates scoped remediation through
   `/aidd-fix`.
10. `/commit` creates the reviewed local checkpoint, `/push` publishes an
    approved commit when needed, and `/aidd-pr` creates or monitors the PR
    when repository policy requires one.
11. `/phase-feedback` completes phase learning after configured delivery
    closeout.

Small fixes use a single ticket without inventing unnecessary parent layers.
Material scope or dependency changes use `/replan-when-necessary`; routine
backlog corrections use `/groom-backlog`.

## Development modes

Project bootstrap asks for exactly one development mode and persists it at
`delivery.development.mode` in `.github/aidd-config.yml`, mirroring the value
in `vision.md` and `AGENTS.md`. A missing value defaults to `guided`; use
`skills/development-mode.md` for the shared contract.

Guided development preserves configured approvals and pauses after the
functionality-only handoff for the user's functional result. Automatic
development begins after the approved, verified foundational bootstrap and
continues through mapping, planning, TDD, technical checks, automated
functionality validation, review/remediation, delivery, lifecycle closeout,
and subsequent ready phases without asking or waiting for another user
response. It records the agent-run functionality charter as
`automaticValidation`, never as `userValidation`.

Automatic mode uses safe defaults for routine decisions but does not bypass
missing tools or services, contradictory requirements, missing parents or
evidence, credential/provider limits, branch protection, remote checks,
required approvals, or merge policy. Both modes keep technical checks
agent-owned and stop on real blockers. Every automatic validation decision
uses the configured Rubber Duck validator (`gpt-5.6-luna`, high reasoning,
`all-validation` scope); deterministic tools remain authoritative for raw
results, and a missing or mismatched validator profile blocks readiness.

Runtimes must merge `delivery.mode_overrides.<mode>` over the base approval,
version-control, gate, and static-analysis settings after resolving the mode.
The automatic profile in configuration is a requirement, not an availability
claim: automatic execution also requires a runtime capability matching
`rubber-duck`, `gpt-5.6-luna`, high reasoning, and `all-validation`.

Bootstrap and planning commands are explicit about persistence. `draft`,
`status`, `inspect`, and `review` produce read-only reports. After approval, or
when `write` is requested, the owning skill must create or update the
configured artifact with a repository file operation, re-read the path, and
report the verified result. File contents shown in chat do not count as a
saved artifact, and failed writes are blockers. Persisting foundational
context or a capability map never creates downstream phases, features, or
tickets automatically.

The mode-aware delivery loop is ordered:

```text
technical verification -> automated functionality test
  -> guided user validation | automatic validation
  -> review -> commit -> push -> PR
```

Each operation is conditional. Commit requires reviewed staged scope; push
requires a successful local commit and an unpublished or ahead branch; PR
requires a published branch and applicable pull-request policy. A repository
may omit push or PR when its configured local-delivery policy permits it.

An explicit user instruction to commit or push may override incomplete
workflow readiness after one warning and confirmation. The operation records
the missing gates as `userDirectiveOverride` rather than passing them, and it
does not close the ticket. Secret exposure, unrequested destructive actions,
missing credentials or remotes, provider rejection, and impossible Git state
remain real blockers.

Automated functionality tests are separate from unit tests: they exercise a
real supported entry point such as an API, CLI, browser flow, worker, or
integration and assert the observable result plus relevant state or external
effect. Before the user handoff, the agent also runs all applicable smoke,
regression, contract, fixture, acquisition, static-analysis, security, and
quality checks. Agent or human validation scripts may document the flow, but
an executable test command or script must produce the required automated
functionality evidence; the user validates only the delivered functionality
and must not be asked to rerun technical checks.

The static-analysis layer is deterministic and repository-configured. It may
use SonarQube Community Build, the repository formatter/linter/type checker,
Semgrep, dependency-cruiser, jscpd, language-native complexity tools, and
`aidd-churn`. Review does not auto-fix these tools; it routes each actionable
introduced finding through the approved `aidd-fix` loop and reruns the suite
until findings are resolved or explicitly classified.

## Skill authoring contracts

Skills use three shared interfaces:

- `skills/lifecycle-interface.md` for mutating, orchestration, evidence,
  delivery, provider, verification, and analysis profiles;
- `skills/planning-skill-interface.md` for planning-layer ownership and
  artifact behavior;
- `skills/workflow-interface.md` for domain guidance that cannot own delivery
  side effects.

Detailed schemas and control flow belong in a skill's `references/` directory
so activation loads only the operational core. Validate the complete library
with:

```bash
python .github/skills/aidd-upskill/scripts/validate-skills.py .github/skills
```

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

Bootstrap commands write only after their configured approval gate:

```text
/project-bootstrap draft  -> propose foundational files without writing
/project-bootstrap write  -> persist the approved foundational files and verify them
/planning-bootstrap status -> inspect planning context without writing
/planning-bootstrap write  -> persist the approved bootstrap update and verify it
/create-repository-map draft -> propose the map without writing
/create-repository-map write -> persist and verify the configured repository map
/create-capability-map draft -> propose the map without writing
/create-capability-map write -> persist and verify the configured capability map
```

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

After implementation, guided mode returns a copy/paste-ready user-validation
handoff with exact setup, steps, expected results, and pass criteria. Tickets
remain in `verifying` until the guided user result or automatic validation is
recorded as evidence; technical tests alone do not close a ticket.

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
