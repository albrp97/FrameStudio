---
name: create-vision
description: Generate a durable vision.md for a repository by discovering intent, delivery constraints, supported environments, quality gates, evidence expectations, and operational readiness, then validating it with the user.
---

# create-vision

Generate `vision.md` as a constraint document and source of truth for future
work. It is not a README or a temporary ticket plan: every section must state a
constraint or an aspiration.

import references/vision_template.md

## Commands

```sudolang
Commands {
  /create-vision - discover, interview, draft, review, and write vision.md
  /create-vision draft - draft from repository context without writing
}
```

## Process

```sudolang
createVision(repo) {
  discover
    |> interview
    |> draft
    |> review
    |> write
}
```

### Discover

Read, when present:

1. `pyproject.toml`, `package.json`, or equivalent manifests;
2. `README.md`;
3. top-level source structure;
4. CI and pipeline configuration;
5. existing `vision.md` or `ARCHITECTURE.md`;
6. `.github/aidd-config.yml` and repository contribution guidance.

Extract project identity, users, runtime constraints, dependencies, probable
architecture, security/compliance signals, supported environments, configured
commands and quality gates, evidence expectations, operational readiness
requirements, and provider/branch policy. Distinguish observed facts from
constraints that still need user confirmation.

### Interview

Ask the five core intent questions:

1. Who is the primary user and what pain does the project solve?
2. What must the project never become or do?
3. Which technical, legal, or organisational constraints are non-negotiable?
4. How will success look in six months?
5. What principles should guide how it feels to use or extend?

Ask delivery questions only when discovery leaves them unresolved:

- Which environments must be supported and kept operational?
- Which quality or security gates are non-negotiable?
- What evidence must accompany a release or operational change?
- What readiness, rollback, observability, or support expectations are durable?

Do not place temporary ticket branch names, individual reviewers, credentials,
polling decisions, or one-off delivery choices in vision.

### Draft and review

Populate the template from discovered facts and user answers:

- user intent wins when it conflicts with inferred intent;
- inferred facts are marked for confirmation;
- missing information becomes explicit `TBD`;
- delivery constraints are included only when durable and project-wide;
- architectural decisions require a rationale.

Present the full draft and request confirmation for every inferred or TBD
section before writing. A draft command does not write files.

### Write

Write the final document to the repository root only after review. It must
begin with the staleness preamble in `references/vision_template.md`.

## Constraints

```sudolang
Constraints {
  Existing vision.md => ask before overwriting
  Contradictory discovery and interview answers => surface for resolution
  Skipped answers => explicit TBD, never invented content
  Temporary branch, reviewer, credential, or ticket decisions => exclude from vision
  Missing rationale for an architectural decision => omit the row
  No section may be silently empty
  Do not write during draft or review
}
```
