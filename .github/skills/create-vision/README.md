# create-vision

Generate a `vision.md` for any repository by reading the codebase and asking
targeted questions about intent, durable delivery constraints, supported
environments, and operational readiness.

## Why

A vision document is the source of truth for project direction. It is not a README — it is a set of constraints that governs all future work and enables agents to evaluate whether a request conflicts with the project's goals.

Without a vision document, agents operate on guesswork. With one, they can answer: *does this request align with what the project is supposed to be?*

## Command

```
/create-vision
```

Use `/create-vision draft` for a read-only proposal and
`/create-vision write` to persist a previously approved draft. The write mode
re-reads `vision.md` and reports a blocker if the file operation or verification
fails. A write request without a recoverable approved draft is also blocked.

Produces a `vision.md` at the repository root, populated from codebase
discovery and 5 targeted questions. After approval, the skill writes the file
with a repository file operation and verifies it; returning the Markdown alone
does not create `vision.md`.

## What it produces

A `vision.md` file containing:

- **Overview** — what the project does and who it is for
- **Goals** — what the project must achieve
- **Non-Goals** — what it must never become
- **Key Constraints** — non-negotiable technical, legal, and organisational constraints
- **Delivery / Operational Readiness** — durable quality, evidence, support, and environment expectations
- **Architectural Decisions** — major choices with rationale
- **UX / DX Principles** — how the project should feel to use or extend
- **Success Criteria** — measurable outcomes that define success
- **Development Mode** — the selected `guided` or `automatic` workflow mode
  and the canonical `delivery.development.mode` configuration key. Automatic
  mode also records the required Rubber Duck validator profile:
  `gpt-5.6-luna` with high reasoning and `all-validation` scope.

## Template

The vision template lives at `references/vision_template.md` in this skill directory.
