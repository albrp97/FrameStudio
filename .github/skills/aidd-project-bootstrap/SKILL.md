---
name: aidd-project-bootstrap
description: Bootstrap a repository's durable project context by combining intent discovery, vision, agent guidance, repository mapping, scope, and delivery configuration. Use when starting a project or when its foundational context is missing or inconsistent.
---

import ../lifecycle-interface.md

# aidd-project-bootstrap

```sudolang
Lifecycle {
  profile = repositoryBootstrap
}
```

Create a trustworthy project context before capability, phase, feature, or
ticket planning. This skill orchestrates the existing vision, discovery,
repository-map, and planning-bootstrap skills; it does not replace their
contracts or silently generate downstream delivery work.

Apply [../development-mode.md](../development-mode.md) when selecting and
persisting the project's development mode.

## Contract

```sudolang
ProjectBootstrapContract {
  mode: draft | status | write
  developmentMode: guided | automatic
  automaticValidationProfile
  inputs[]
  proposedArtifacts[]
  filesRead[]
  filesWritten[]
  writeResults[]
  approvalConditions[]
  stopConditions[]
  handoff[]
  bootstrapAuthorized
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
- The required development-mode choice: `guided` preserves interactive
  approvals and user functionality validation; `automatic` continues through
  the configured workflow after bootstrap without asking or waiting for the
  user.
- Existing `vision.md`, `AGENTS.md`, `README.md`, repository maps, scope
  records, and configuration. Treat unknown or inferred values as unresolved.

## Outputs

Load [artifacts](./references/artifacts.md) when drafting or writing the
foundational project files and reporting write results.

## Process

```sudolang
projectBootstrap(request) => BootstrapReport {
  1. inspect repository and existing sources of truth
  2. resolve configured artifact paths and identify conflicts or missing context
  3. reuse existing facts and ask only the unanswered intent, delivery, and
     development-mode questions
  4. draft every proposed file and show inferred values, TBDs, selected mode,
     and overwrite risks
  5. wait for explicit approval of the complete foundational draft
  6. enter write mode and use repository file operations for every approved artifact
  7. re-read every written path and record an ArtifactWriteResult; stop if verification fails
  8. resolve and persist the mode in configuration, vision, and AGENTS before
     reporting bootstrap completion
  9. run planning-bootstrap reconciliation and report the next planning layer
  10. if the selected mode is automatic, immediately hand off to the
      orchestrator's automatic development loop; do not ask or wait for another
      user response
}
```

### Detailed bootstrap behavior

Load [bootstrap details](./references/bootstrap-details.md) when interviewing,
drafting, writing, verifying, or handing off foundational artifacts.

## Failure and blocker behavior

Missing user intent, contradictory existing guidance, unavailable repository
evidence, unresolved overwrite decisions, or missing approval is a blocker.
Report the exact artifact and decision required; do not fill gaps with
plausible defaults. A draft or rejected approval never writes files. After a
verified automatic handoff, a downstream uncertainty is handled from
repository evidence or reported as a blocker; it must not become a follow-up
question.

## Constraints

```sudolang
Constraints {
  Read existing sources before proposing replacements
  Ask one question at a time and reuse confirmed answers
  Show a complete file-by-file draft before any write
  Require explicit approval before creating or updating foundational artifacts
  Treat response-only artifact content as not written
  Use a repository file-writing tool after approval; do not stop at a response draft
  Re-read every written path and report its verified write result
  Stop and report a blocker when a requested file operation fails
  Never overwrite vision, AGENTS, README, configuration, or planning sources silently
  Never create capabilities, phases, features, tickets, branches, commits, pushes, or merges as a side effect
  Ask for the development mode during bootstrap and persist it in all required
    project-context artifacts
  In automatic mode, never ask or wait after the verified foundational
    bootstrap; route internally until completion or a real blocker
  In automatic mode, require the exact Rubber Duck `gpt-5.6-luna`
    high-reasoning profile for every validation decision
  Never record automatic agent validation as user confirmation
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

  /aidd-project-bootstrap write [request]
  - persist the previously approved foundational artifacts and verify each path
}
```
