# aidd-static-analysis

Runs deterministic repository quality checks and produces exact findings for
`aidd-review` to consume. It covers formatter, lint, type, complexity,
duplication, dependency, security, SonarQube, and churn concerns when those
tools are applicable and configured.

Use `/aidd-static-analysis` for a standalone diff or full-repository scan.
Use `/review` for the delivery workflow: review invokes this skill, compares
local settings with the pull-request pipeline, runs `aidd-structure` and
`aidd-churn`, and orchestrates scoped `/aidd-fix` remediation for actionable
new findings when configured and approved.

Reports retain the tool, rule, severity, path, line, metric, version,
configuration, baseline status, and remediation. Results are emitted as
SARIF, JSON, and Markdown when configured. Existing debt is reported rather
than hidden, and unavailable required tools or local/PR incompatibility block
readiness.

## Setup in a target repository

Keep the actual commands in the repository's package scripts, Makefile, task
runner, or CI configuration, then reference those same wrappers from
`delivery.static_analysis.tools.*.command`. Pin analyzer versions through the
repository lockfile or container image, copy the PR pipeline's rules,
exclusions, thresholds, baseline/reference, and exit policy locally, and
enable SonarQube deep mode only when a matching Community Build server and
scanner are available. Do not install tools or invent commands from this
bundle alone.

The skill does not install tools, auto-fix files, commit, push, create a PR, or
merge.
