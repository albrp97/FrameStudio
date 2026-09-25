---
name: Set Up Project Delivery Workflow
description: Research a project's purpose and stack, then set up a lean workflow for branching, commits, PRs, CI/CD, tests, quality gates, and releases.
---

You have to set up the delivery workflow for `${PROJECT_OR_REPO}` end to end.

Use the Harmonic Coding docs in this repository as the workflow source of truth:
- `README.md`
- `docs/guide/setup-guide.md`
- `docs/guide/developer-guide.md`
- `docs/guide/advanced-playbook.md`
- any directly relevant research docs

## Outcome

Leave the target project with a practical, documented, working setup for:
- project context and tech-stack understanding
- feature branches, commit style, and pull request flow
- CI/CD pipelines
- format, lint, type-check, unit, integration, and functional test gates
- versioning and release flow when the project actually needs it
- review and repair loops so work does not stop at the first "done"

## Operating rules

1. Research the actual repository before choosing tools.
2. Prefer the tools and conventions the project already uses unless they are clearly missing or broken.
3. Prefer the smallest stack-native toolset that covers the need.
4. Do not overengineer. One clear path is better than overlapping tools.
5. Add SonarQube, release automation, preview environments, or extra jobs only when the project type justifies them.
6. Document every choice in the repo so the next engineer can follow the workflow without guessing.
7. If a quality layer does not exist yet, add the leanest useful baseline instead of a placeholder.

## Required workflow

### 1. Research the project

- Read the README, package manifests, lockfiles, Docker files, deployment files, existing CI files, and test/config files.
- Summarize:
  - what the project does
  - who/what it serves
  - the primary runtime and framework
  - package manager and build tools
  - test stack
  - deployment target
  - what quality automation already exists

### 2. Choose the lean baseline

Select the minimum effective workflow for this specific project:

- **CI runner:** default to GitHub Actions
- **Branching:** protected `main` plus short-lived feature branches
- **Commits:** use the repo's existing convention; if none exists, choose a simple imperative style and use Conventional Commits only when release/changelog automation benefits from them
- **PR flow:** PR template, required checks, and at least one approval when the repo is collaborative
- **Formatting/linting:** prefer one formatter and one lint entrypoint per language
- **Static analysis:** SonarQube only if the repo/org already uses it or clearly benefits from centralized quality reporting
- **Tests:** use the existing stack; if absent, add the smallest practical split between unit tests and higher-level integration/functional coverage
- **Versioning:** only add release/version automation if the project ships packages, images, or tagged releases

### 3. Define the target pipeline

Specify the jobs, triggers, and gates:

- pull request validation
- push-to-main validation
- optional release workflow
- optional deployment workflow

For each job, define:
- trigger
- command(s)
- failure policy
- cache needs
- secrets needed
- whether it is blocking

At minimum, cover:
- install
- format/lint/type-check
- unit tests
- integration tests when the project has integrations
- functional or end-to-end tests when there is user-facing behavior
- build/package step when artifacts matter

### 4. Implement the setup

Make the repo changes needed to support the chosen workflow:
- workflow files
- formatter/linter/test config
- PR template / contributing docs / release docs
- branch protection guidance
- local developer commands
- versioning or release config when justified

### 5. Validate and repair

- Run the smallest meaningful local checks first, then the full project gates you added or changed.
- Fix workflow, docs, or config gaps until the setup is coherent.
- Do not stop at "the files exist." Stop when the workflow is understandable and executable.

## Default tool guidance

Use this as a default only when the repo does not already have a good answer:

| Concern | Default |
|---|---|
| JS/TS formatter + linter | Biome for new repos, or stay with ESLint + Prettier if already established |
| JS/TS unit/integration tests | Vitest |
| Web functional tests | Playwright |
| Python lint/format | Ruff |
| Python typing | mypy or pyright, whichever best matches the repo |
| Python tests | pytest |
| CI platform | GitHub Actions |
| Release/versioning | Changesets for packages, manual semver tags for apps unless release automation is clearly needed |

## Deliverables

Produce all of the following in the target repo:

1. A short project/stack summary.
2. The chosen delivery workflow and why it is not overengineered.
3. The implemented files and commands.
4. The branch / commit / PR / release conventions.
5. Any follow-up gaps that require human input, but only after completing everything that can be done autonomously.
