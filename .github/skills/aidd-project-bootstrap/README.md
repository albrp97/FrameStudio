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
before writing. After approval it performs the repository file operations,
re-reads every written path, and reports the verified result; response-only
file contents are not treated as created artifacts.
During this bootstrap interview it also requires a development-mode choice:
`guided` preserves approval gates and human functionality validation, while
`automatic` continues through the configured planning, implementation,
verification, review, and delivery loop after the foundational writes verify.
The selected mode is persisted in `.github/aidd-config.yml` under
`delivery.development.mode` and mirrored in `vision.md` and `AGENTS.md`.
Automatic mode also persists and mirrors the exact Rubber Duck validation
profile from `delivery.development.automatic_validation`:
`gpt-5.6-luna` with high reasoning and `all-validation` scope.
The planning-bootstrap handoff occurs only after all authorized writes verify
successfully. Automatic mode then continues internally and does not ask or
wait for another user response.

Use `draft` or `status` for read-only work. Use `write` to persist a previously
approved bootstrap draft. A write request without a recoverable approved draft
is blocked rather than reconstructed from the request.

## Boundaries

This skill orchestrates `create-vision`, `aidd-product-manager`,
`aidd-create-repository-map`, and `aidd-planning-bootstrap`. It does not create
capabilities, phases, features, tickets, source code, branches, commits, or
pull requests during foundational bootstrap itself. In automatic mode, the
verified handoff starts the orchestrator loop that owns those later operations
under configured policy and stops on real blockers.
