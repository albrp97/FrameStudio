# aidd-agent-orchestrator

Coordinates specialized agents for software development delivery states,
routing requests to the right lifecycle and domain skill while preserving
phase, feature, ticket, scope, gates, and evidence.

## Why

Complex tickets span multiple domains — UI, state, testing, product planning.
The orchestrator dispatches work to the agent with the deepest expertise for
each concern instead of relying on a single generalist prompt. It aggregates
delegated evidence and does not allow a sub-agent to declare readiness alone.

## Usage

Invoke `/aidd-agent-orchestrator` when a request touches multiple domains, needs
lifecycle routing, or requires safe delegation. The orchestrator reads
`.github/aidd-config.yml`, identifies the current delivery state, selects the
appropriate lifecycle and domain skills, and coordinates execution.
It does not declare a ticket ready or complete while required user validation
is missing, pending, failed, or blocked.
For review requests, it runs `aidd-static-analysis` before contextual review
and keeps remediation inside the configured approval and `aidd-fix` workflow.
Every routed response ends with one `Next step`, `Skill`, and `Why` handoff
selected from the current delivery state and first unresolved gate. Delivery
operations are ordered as `/commit`, `/push`, and `/aidd-pr` when the
configured version-control and pull-request policies require them.

## When to use

- A ticket spans multiple technical domains
- You need to route a request to the right specialist
- You want coordinated multi-agent execution
