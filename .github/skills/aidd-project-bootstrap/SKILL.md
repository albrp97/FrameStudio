---
name: aidd-project-bootstrap
description: Bootstrap a repository's durable project context by combining intent discovery, vision, agent guidance, repository mapping, scope, and delivery configuration. Use when starting a project or when its foundational context is missing or inconsistent.
---

# aidd-project-bootstrap

Create a trustworthy project context before capability, phase, feature, or
ticket planning. This skill orchestrates the existing vision, discovery,
repository-map, and planning-bootstrap skills; it does not replace their
contracts or silently generate downstream delivery work.

## Contract

```sudolang
ProjectBootstrapContract {
  inputs[]
  proposedArtifacts[]
  filesRead[]
  filesWritten[]
  approvalConditions[]
  stopConditions[]
  handoff[]
  blockers[]
  mayImplement = false
  mayCommit = false
  mayPush = false
  mayMerge = false
}
```

## Use when

- A new repository needs durable project context before implementation
  planning.
- `vision.md`, `AGENTS.md`, the repository map, scope record, or delivery
  configuration is absent, stale, or contradictory.
- The user can describe the project intent but the repository does not yet
  contain a reliable handoff for future agents.
- Several foundational files need to be drafted together without duplicating
  interviews or creating conflicting sources of truth.

For an existing project with trustworthy context, use the narrower planning
skill that matches the requested layer instead.

## Inputs

- The repository root and observed repository files, structure, manifests,
  CI, contribution guidance, and existing planning artifacts.
- `.github/aidd-config.yml` when present. Resolve
  `delivery.artifacts.agent_instructions` or default to `AGENTS.md`, and
  `delivery.artifacts.project_readme` or default to `README.md`.
- The user's description of what the project is, who it serves, the problem it
  solves, and the intended outcome.
- Existing `vision.md`, `AGENTS.md`, `README.md`, repository maps, scope
  records, and configuration. Treat unknown or inferred values as unresolved.

## Outputs

The skill produces a file-by-file draft and, only after explicit approval, may
create or update the following durable context:

- **Vision:** `vision.md`, using the `create-vision` contract, for project
  purpose, users, goals, non-goals, durable constraints, principles, and
  success criteria.
- **Agent guidance:** `AGENTS.md` or the configured equivalent, for
  repository-specific setup, commands, architecture boundaries, validation,
  security rules, and agent operating conventions. It must complement rather
  than duplicate `.github/copilot-instructions.md`.
- **Repository map:** the configured map path, using
  `aidd-create-repository-map`, for source, test, documentation, automation,
  infrastructure, ownership, tooling, and unknown surfaces.
- **Scope handoff:** the configured scope artifact, using the
  `aidd-product-manager` discovery contract, for the current horizon,
  exclusions, dependencies, risks, protected behavior, and verification
  intent.
- **Delivery configuration:** an authorized, secret-free update to
  `.github/aidd-config.yml` when project-specific commands, provider, branch,
  or artifact settings are confirmed.
- **README:** the configured project README only when it is missing or the
  user explicitly requests it. A README is human-facing onboarding, not a
  substitute for vision or agent guidance.

The result also reports created, updated, skipped, unresolved, and blocked
artifacts plus the next approved planning command. It does not create
capability, phase, feature, or ticket children as a side effect.

## Process

```sudolang
projectBootstrap(request) => BootstrapReport {
  1. inspect repository and existing sources of truth
  2. resolve configured artifact paths and identify conflicts or missing context
  3. reuse existing facts and ask only the unanswered intent and delivery questions
  4. draft every proposed file and show inferred values, TBDs, and overwrite risks
  5. wait for explicit approval of the complete draft
  6. write only approved foundational artifacts in dependency order
  7. run planning-bootstrap reconciliation and report the next planning layer
}
```

### Inspect and reconcile

Read the repository root, README, AGENTS guidance, manifests, source layout,
tests, CI, contribution rules, `vision.md`, `.github/aidd-config.yml`, and
configured planning artifacts. Preserve an existing authoritative issue
tracker, project board, `plan/`, or `docs/` layout instead of creating a
parallel source of truth.

Classify each fact as observed, user-confirmed, inferred, stale, conflicting,
or unknown. Never convert a filename, dependency, or convention guess into a
project rule without evidence or confirmation.

### Interview

Ask one focused question at a time and reuse answers across all artifacts.
Cover, as applicable:

1. Who is the primary user and what problem or opportunity does the project
   address?
2. What outcome should the project create, and how will success be measured?
3. What is included in the current horizon, and what must remain out of scope?
4. What must the project never become or do?
5. Which technical, legal, organizational, environment, security, or support
   constraints are durable?
6. Which setup, quality, security, deployment, rollback, observability, and
   evidence expectations must agents preserve?
7. Which repository commands, architecture boundaries, naming rules, and
   contribution practices are confirmed rather than inferred?

Do not ask questions whose answers are already supported by repository evidence
unless the fact is consequential and needs user confirmation.

### Draft and review

Present a consolidated draft before writing. For every proposed artifact,
show its path, purpose, source basis, changed sections, confidence, unresolved
TBDs, and any existing content that would be preserved or replaced.

The `AGENTS.md` draft should contain only project-specific agent guidance:

- links to `vision.md`, the repository map, and authoritative planning sources;
- confirmed setup, format, lint, type-check, build, test, and validation
  commands;
- repository structure and layer boundaries grounded in the map;
- required evidence, security, data-handling, and contribution rules;
- instructions for handling uncertainty, scope, and existing sources of truth.

Do not copy the entire generic workflow into `AGENTS.md`, and do not put
temporary ticket branches, individual reviewers, credentials, tokens, or
one-off delivery choices into durable files.

### Write after approval

After explicit approval, write only the approved files in this order:

1. `vision.md` through the `create-vision` rules.
2. Repository map through `aidd-create-repository-map`.
3. Scope and discovery handoff through `aidd-product-manager`.
4. `AGENTS.md` or the configured agent-instructions path.
5. Authorized configuration updates and optional README changes.

If an existing file is present, preserve its history and content not covered by
the approved change. If the requested change would replace or merge
contradictory instructions, stop and report the exact conflict.

### Handoff

After foundational context is approved, load `aidd-planning-bootstrap` to
reconcile statuses, paths, and planning depth. Recommend
`aidd-create-capability-map` for cross-cutting or full-depth work, but do not
create capabilities, phases, features, or tickets until the user approves the
next planning layer.

## Failure and blocker behavior

Missing user intent, contradictory existing guidance, unavailable repository
evidence, unresolved overwrite decisions, or missing approval is a blocker.
Report the exact artifact and decision required; do not fill gaps with
plausible defaults. A draft or rejected approval never writes files.

## Constraints

```sudolang
Constraints {
  Read existing sources before proposing replacements
  Ask one question at a time and reuse confirmed answers
  Show a complete file-by-file draft before any write
  Require explicit approval before creating or updating foundational artifacts
  Never overwrite vision, AGENTS, README, configuration, or planning sources silently
  Never create capabilities, phases, features, tickets, branches, commits, pushes, or merges as a side effect
  Never store credentials, tokens, private keys, cookies, or sensitive data
  Preserve project-specific guidance separately from generic .github policy
  Record observed versus confirmed versus inferred facts and explicit TBD values
  Route material scope or architecture changes to a controlled planning review
}
```

## Commands

```sudolang
Commands {
  /aidd-project-bootstrap [request]
  - inspect, interview, draft, approve, and write foundational project context

  /aidd-project-bootstrap draft [request]
  - produce the complete file-by-file draft without writing

  /aidd-project-bootstrap status
  - report existing foundational artifacts, conflicts, and the next handoff
}
```
