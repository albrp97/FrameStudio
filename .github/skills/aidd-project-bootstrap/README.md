# aidd-project-bootstrap

Initialize the durable context of a repository before deeper planning.

## Use when

- Starting a new project or onboarding an existing repository.
- `vision.md`, `AGENTS.md`, repository mapping, scope, or delivery configuration
  is missing or inconsistent.
- Several foundational artifacts should be drafted from one approved interview.

## Command

Use `/aidd-project-bootstrap` in Copilot CLI, or the
`/project-bootstrap` prompt wrapper where prompt files are supported.

The skill inspects the repository, asks focused intent and delivery questions,
drafts `vision.md`, project-specific `AGENTS.md`, repository mapping, scope,
configuration, and optionally README changes, then waits for explicit approval
before writing.

## Boundaries

This skill orchestrates `create-vision`, `aidd-product-manager`,
`aidd-create-repository-map`, and `aidd-planning-bootstrap`. It does not create
capabilities, phases, features, tickets, source code, branches, commits, or
pull requests automatically.
