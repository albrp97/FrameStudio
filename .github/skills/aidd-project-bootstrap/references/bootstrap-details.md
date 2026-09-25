# Bootstrap details

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
8. Which development mode should govern work after this bootstrap?
   - `guided`: retain approval gates and the functionality-only user
     validation handoff.
   - `automatic`: after the foundational bootstrap is approved and verified,
     continue through mapping, planning, implementation, verification,
     review, delivery, and remaining phases without asking or waiting.

Do not ask questions whose answers are already supported by repository evidence
unless the fact is consequential and needs user confirmation.

### Draft and review

Present a consolidated draft before writing. For every proposed artifact,
show its path, purpose, source basis, changed sections, confidence, unresolved
TBDs, and any existing content that would be preserved or replaced.

The `AGENTS.md` draft should contain only project-specific agent guidance:

- links to `vision.md`, the repository map, and authoritative planning sources;
- the selected development mode, with
  `.github/aidd-config.yml:delivery.development.mode` as the canonical source;
- the automatic validation profile, with
  `.github/aidd-config.yml:delivery.development.automatic_validation` as the
  canonical source when automatic mode is selected;
- the automatic-mode rule that no user questions or validation waits occur
  after the verified bootstrap handoff, when automatic mode is selected;
- confirmed setup, format, lint, type-check, build, test, and validation
  commands;
- repository structure and layer boundaries grounded in the map;
- required evidence, security, data-handling, and contribution rules;
- instructions for handling uncertainty, scope, and existing sources of truth.

Do not copy the entire generic workflow into `AGENTS.md`, and do not put
temporary ticket branches, individual reviewers, credentials, tokens, or
one-off delivery choices into durable files.

### Write after approval

After explicit approval, enter `write` mode and use the repository's file
creation/editing tool for every approved path. Do not replace this step with
printing the proposed contents in the response. Create missing parent
directories when needed, preserve unrelated existing content, and write only
the approved files in this order:

1. `vision.md` through the `create-vision` rules.
2. Repository map through `aidd-create-repository-map`.
3. Scope and discovery handoff through `aidd-product-manager`.
4. `AGENTS.md` or the configured agent-instructions path.
5. Authorized configuration updates and optional README changes.

If an existing file is present, preserve its history and content not covered by
the approved change. If the requested change would replace or merge
contradictory instructions, stop and report the exact conflict.

After each write, re-read the path (or use the repository's equivalent
post-write inspection) and verify that the approved content is present. Record
the operation and verification in `writeResults[]`. If a file operation fails,
the artifact is `blocked`; do not report it as created or updated.
For every `created` or `updated` result, the execution must include a call to
the host's file create/edit tool. A code block, patch shown in the response, or
natural-language claim is not a file operation. Creating a missing parent
directory is part of the approved write and must also be reported and verified.

### Draft, status, and write modes

- `draft` and `status` are read-only and must not create directories or files.
- The default bootstrap flow drafts first and waits for explicit approval.
- The development-mode choice is part of this bootstrap approval boundary.
- Selecting `automatic` authorizes routine downstream planning, implementation,
  evidence, and delivery continuation after the foundational writes verify;
  it does not bypass security, branch, provider, credential, remote-check,
  merge, or unavailable-tool blockers.
- Explicit approval authorizes only the listed artifacts and approved sections.
- `write` persists the previously approved draft; it is not a request to print
  the draft again.
- A `write` request without a recoverable approved draft is blocked; do not
  reconstruct unapproved contents and write them.
- A response containing Markdown, YAML, or SudoLang content without a file
  operation is still a draft and must be labeled `not written`.

### Handoff

After foundational context is approved and every authorized write has a
verified result, load `aidd-planning-bootstrap` to reconcile statuses, paths,
and planning depth. If any write is blocked or unverified, keep the bootstrap
blocked instead. In guided mode, recommend
`aidd-create-capability-map` for cross-cutting or full-depth work and preserve
the next approval gate. In automatic mode, invoke the orchestrator's loop,
which creates and reviews each downstream layer in order without waiting for
user approval.
