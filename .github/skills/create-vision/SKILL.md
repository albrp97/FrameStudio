---
name: create-vision
description: Generate a durable vision.md for a repository by discovering intent, delivery constraints, supported environments, quality gates, evidence expectations, and operational readiness. Use when project purpose or durable direction is missing or stale.
---

import ../lifecycle-interface.md

# create-vision

```sudolang
Lifecycle {
  profile = repositoryBootstrap
  overrides {
    filesWritten = [authorizedVisionArtifact]
  }
}
```

Generate `vision.md` as a constraint document and source of truth for future
work. It is not a README or a temporary ticket plan: every section must state a
constraint or an aspiration.

Apply [../development-mode.md](../development-mode.md) when recording the
selected project development mode. The machine-readable source remains
`.github/aidd-config.yml:delivery.development.mode`; this document mirrors it
for human and agent context. When the mode is automatic, the same configuration
file's `delivery.development.automatic_validation` profile is authoritative for
all validation decisions and must be mirrored in the vision.

import references/vision_template.md

## Commands

```sudolang
Commands {
  /create-vision - discover, interview, draft, review, and write vision.md
  /create-vision draft - draft from repository context without writing
  /create-vision write - persist a previously approved vision draft and verify vision.md
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
6. Which development mode should apply after project bootstrap: `guided`,
   which keeps approval and user functionality gates, or `automatic`, which
   continues through the configured workflow without asking or waiting after
   bootstrap?

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
- the selected development mode is recorded and matches
  `delivery.development.mode`; use `guided` until the bootstrap choice is
  confirmed.
- automatic mode records the exact validation profile
  (`rubber-duck`, `gpt-5.6-luna`, high reasoning, `all-validation`) and points
  to `delivery.development.automatic_validation` as authoritative.

Present the full draft and request confirmation for every inferred or TBD
section before writing. A draft command does not write files.

### Write

After review and explicit approval, use the repository file-writing tool to
create or update the final document at the repository root. It must begin with
the staleness preamble in `references/vision_template.md`. Re-read
`vision.md` after writing and verify that the approved content is present.
Showing the vision contents in the response without performing and verifying
the file operation is a draft and must be labeled `not written`, not a
completed `/create-vision` run.
The execution must include a host file create/edit call; a Markdown code block
or natural-language claim cannot satisfy the write.
`/create-vision write` without a recoverable approved draft is blocked; it must
not reconstruct and write an unapproved vision.

## Constraints

```sudolang
Constraints {
  Existing vision.md => ask before overwriting
  Contradictory discovery and interview answers => surface for resolution
  Skipped answers => explicit TBD, never invented content
  Temporary branch, reviewer, credential, or ticket decisions => exclude from vision
  Missing rationale for an architectural decision => omit the row
  No section may be silently empty
  Always include the Development Mode section and its canonical configuration
    key
  When automatic mode is selected, include the exact Rubber Duck validation
    profile and its canonical configuration key
  Do not write during draft or review
  Do not treat response-only Markdown as a written vision
  Report a failed or unavailable file operation as blocked
}
```
