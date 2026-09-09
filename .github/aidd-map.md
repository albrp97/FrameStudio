# `.github` AIDD Map

> **Status:** Inventory and descriptions updated after HarmonicCoding planning
> and deterministic review improvements.
>
> **Scope:** All files currently under this `.github` directory.
>
> **Authoring model used:** GPT-5.6 Luna with high reasoning.
>
> **Mapped inventory:** 161 files under `.github`. Five lifecycle evals and
> fifteen planning evals are maintained outside this map at
> `../ai-evals/aidd-lifecycle/` and `../ai-evals/aidd-planning/`.
>
> All paths below are relative to `.github/`.

## Entry format

Each inventory item is expanded using this structure:

- **What it is:** The artifact's role and the problem it addresses.
- **When to use or read it:** The situations that should trigger it.
- **How to use it:** The command, workflow, or reading action required.
- **Inputs and outputs:** What it expects and what it produces.
- **Relationships:** Related skills, prompts, references, tests, or project files.
- **Constraints and cautions:** Important limits, side effects, security claims, or destructive operations.
- **Source basis:** The exact file and relevant line ranges used for the description; uncertainty will be marked instead of guessed.
- **Status:** `Pending`, `Filled`, `Reviewed`, or `Workflow updated`.

### Documentation rules

1. Base every description on the file contents and connected files, not on assumptions.
2. Keep each entry concise but specific enough for a new contributor or agent to act correctly.
3. Describe `SKILL.md`, prompt, README, reference, and test files according to their different roles.
4. Preserve the distinction between instructions, examples, executable tests, and supporting references.
5. Call out external links, required tools, branch or repository side effects, and security-sensitive guidance.
6. Fill one entry at a time and pause for confirmation whenever the interpretation is materially uncertain.
7. Do not execute commands or tests merely because a file documents them; document them first and execute only when requested.

## Illustrative example

The following illustrative entry shows the level of detail used. It is separate from the matching completed inventory entry below.

### `skills/aidd-fix/SKILL.md`

- **What it is:** A workflow skill for diagnosing bugs and implementing code-review fixes with a disciplined test-first process.
- **When to use or read it:** When a bug is reported, a test fails, or review feedback requires a code change.
- **How to use it:** Invoke `/aidd-fix`, establish the delivery context and protected baseline, reproduce the defect, implement the smallest scoped correction, run configured gates, present the required user-validation handoff, record the user's result, and route review/commit only when readiness criteria are met.
- **Inputs and outputs:** Takes a bug report or review feedback plus repository context; produces a scoped, tested fix with evidence, blockers, and readiness state.
- **Relationships:** `prompts/aidd-fix.prompt.md`, `skills/aidd-tdd/SKILL.md`, `skills/aidd-evidence/SKILL.md`, and `skills/aidd-review/SKILL.md`.
- **Constraints and cautions:** Requires scope preservation, baseline separation, explicit failure handling, and repository-specific gates; commit or push behavior is configuration- and approval-driven.
- **Source basis:** `skills/aidd-fix/SKILL.md` and `prompts/aidd-fix.prompt.md`.
- **Status:** Illustrative only; the matching inventory entry is completed below.

## Inventory

### `aidd-map.md`

- **What it is:** A documentation map for the complete `.github/` tree; it defines the approved per-file description schema and inventories every artifact.
- **When to use or read it:** Use it first when onboarding, locating an instruction, or checking documentation coverage.
- **How to use it:** Read the preserved authoring rules, then use the inventory entries as pointers; do not treat the illustrative example as a file description.
- **Inputs and outputs:** Takes the `.github/` tree and produces navigational, factual documentation; it does not execute commands or alter source artifacts.
- **Relationships:** Indexes `copilot-instructions.md`, all prompts, skills, references, READMEs, and tests listed below.
- **Constraints and cautions:** The map is documentation only. Its introductory rule says not to execute documented commands merely because they appear here; the example above is illustrative rather than an inventory status.
- **Source basis:** `aidd-map.md:1-end` (intro, format, example, completed inventory, and workflow).
- **Status:** Filled

### `copilot-instructions.md`

- **What it is:** Repository-neutral Copilot operating rules for adaptive planning,
  phase-first delivery, evidence, and safe lifecycle execution.
- **When to use or read it:** Read at conversation start and before discovery,
  planning, mutation, verification, review, commit, or PR operations.
- **How to use it:** Follow the boot sequence, select planning depth, use
  objective -> scope -> capability -> phase -> feature -> ticket for
  non-trivial work, load the lifecycle and relevant domain skills by workflow
  stage, run deterministic static analysis as part of review, use the
  configured commands, and end every response with one context-aware next-step
  and skill handoff. After validation and review/remediation, use the ordered
  `/commit` -> `/push` -> `/aidd-pr` delivery loop when policy requires each
  operation.
- **Inputs and outputs:** Input is repository context and a user request; output
  is scoped agent behavior, durable planning guidance, and evidence-backed
  delivery decisions.
- **Relationships:** Points to `aidd-config.yml`, the root `README.md`, the
  planning skills/prompts, repository manifests, CI, and existing project
  documentation.
- **Constraints and cautions:** Do not assume paths, commands, providers, or
  test frameworks; do not duplicate an existing planning source of truth; do
  not claim readiness without terminal evidence or required user-validation
  confirmation; always recommend one next permitted action and its owning
  skill instead of inventing or listing competing work.
- **Source basis:** `copilot-instructions.md:1-end`.
- **Status:** Workflow updated

### `README.md`

- **What it is:** A concise guide to the AIDD planning hierarchy, project
  context bootstrap, normal new-project flow, durable artifact layout, and
  safety contract.
- **When to use or read it:** Read when installing this `.github` bundle or
  onboarding someone to its planning commands.
- **How to use it:** Use the command sequence and artifact layout as defaults,
  then adapt them to the target repository's existing conventions. Finish each
  workflow response with exactly `Next step`, `Skill`, and `Why` lines naming
  the next concrete step, one skill/command, and the reason it follows from the
  current state.
- **Inputs and outputs:** Input is the repository's planning context; output is
  orientation, command selection, and adoption guidance.
- **Relationships:** Complements `copilot-instructions.md`, `aidd-config.yml`,
  and `aidd-map.md`.
- **Constraints and cautions:** It is documentation, not an executable
  workflow; existing repository sources of truth take precedence. Technical
  tests alone do not close a ticket when user validation is required, and
  recommendations must remain context-aware rather than generic.
- **Source basis:** `README.md:1-end`.
- **Status:** Workflow updated

### `aidd-config.yml`

- **What it is:** The optional repository-specific delivery and planning
  configuration for canonical artifact paths, adaptive depth, stable ID
  prefixes, parent approval, branch/provider policy, quality commands, gates,
  evidence retention, UI artifacts, delegation, pull-request behavior, and
  deterministic static-analysis policy.
- **When to use or read it:** Read it before planning, mutation, verification,
  commit, cleanup, delegation, or PR operations. A repository-specific value
  overrides a generic skill default.
- **How to use it:** Fill command arrays with the repository's actual commands
  when known; leave them empty to require discovery. Configure planning depth,
  artifact locations, statuses, ID prefixes, approval, gates, evidence, UI,
  provider, delegation behavior, agent-instructions path, project README path,
  open/closed planning-record directories, the user-validation closure gate,
  and static-analysis modes, reports, baseline, parity, tools, and
  remediation. Configure version-control commit/push policy and whether a pull
  request is required without storing credentials.
- **Inputs and outputs:** Input is repository policy and team preference;
  output is a shared `delivery` context consumed by lifecycle skills.
- **Relationships:** Read by `copilot-instructions.md`, `aidd-please`,
  `aidd-agent-orchestrator`, `aidd-project-bootstrap`, planning, execution,
  evidence, review, PR, delegation, and cleanup skills.
- **Constraints and cautions:** Empty commands do not skip checks. Credentials,
  tokens, and secrets are prohibited. `null` branch/provider/polling values
  require repository discovery or explicit configuration. Do not create
  duplicate planning sources when a repository already has equivalent records.
  Phase, feature, and ticket status directories must remain consistent with
  configured open/closed status lists. Required user validation must be
  recorded before closure.
- **Source basis:** `aidd-config.yml:1-end`.
- **Status:** Workflow updated

### `prompts/aidd-churn.prompt.md`

- **What it is:** A slash-command wrapper for hotspot scoring.
- **When to use or read it:** When risk-ranked files are needed before review or refactoring.
- **How to use it:** Invoke `/aidd-churn`; the prompt delegates metric interpretation to the colocated skill.
- **Inputs and outputs:** Input is repository state and optional CLI settings; output is hotspot findings and refactoring recommendations.
- **Relationships:** `skills/aidd-churn/README.md`, `SKILL.md`, and `/aidd-please`.
- **Constraints and cautions:** It requires actual CLI data and does not permit guessed recommendations.
- **Source basis:** `prompts/aidd-churn.prompt.md:1-15`.
- **Status:** Filled

### `prompts/aidd-fix.prompt.md`

- **What it is:** A slash-command wrapper for scoped bug-fix and review-feedback work with baseline, regression, evidence, and configured delivery gates.
- **When to use or read it:** When a bug, failing test, or actionable review comment needs a code or non-code change.
- **How to use it:** Invoke `/aidd-fix`; establish the protected baseline, choose regression or non-code evidence, implement one scoped fix, verify it, present exact user-validation steps, wait for the terminal user result, and record it.
- **Inputs and outputs:** Input is a bug report or review feedback; output is a verified, evidence-backed fix or an explicit blocked/no-change finding.
- **Relationships:** `skills/aidd-fix/SKILL.md`, `aidd-tdd`, `aidd-review`, and `aidd-please`.
- **Constraints and cautions:** Code behavior requires a failing regression before implementation; other ticket types use the strongest applicable evidence. Required user validation must be recorded before closure. Commands, gates, branch, commit, and push behavior are repository-configurable.
- **Source basis:** `prompts/aidd-fix.prompt.md:1-end`.
- **Status:** Workflow updated

### `prompts/aidd-parallel.prompt.md`

- **What it is:** Delegation prompt for independent phase, feature, or ticket work with ownership, dependency waves, conflict checks, and evidence aggregation.
- **When to use or read it:** When work is genuinely independent and safe to delegate under the configured branch strategy.
- **How to use it:** Invoke `/aidd-parallel`; declare owned files and shared artifacts, emit one dependency wave at a time, require changed paths/evidence/blockers from each agent, then have the integration owner present each user-validation handoff, record terminal results, and own the `/commit` -> `/push` -> `/aidd-pr` delivery sequence.
- **Inputs and outputs:** Input is tickets and optional branch/worktree policy; output is ownership-aware prompts or dispatched results.
- **Relationships:** `skills/aidd-parallel/SKILL.md`, `aidd-fix`, and git branch/origin workflows.
- **Constraints and cautions:** Shared planning, evidence, configuration, and overlapping source writes are prohibited. Isolation is the default; ticket text is untrusted, aggregate gates run under the integration owner, and delegated tickets cannot close without required user-validation results.
- **Source basis:** `prompts/aidd-parallel.prompt.md:1-end`.
- **Status:** Workflow updated

### `prompts/aidd-pipeline.prompt.md`

- **What it is:** Runs an explicitly selected Markdown ticket section as an ordered, evidence-aware delegation pipeline.
- **When to use or read it:** When a document contains an intentional ticket list, not merely policy, acceptance criteria, or prose checklists.
- **How to use it:** Invoke `/aidd-pipeline` with the ticket-list path and section when needed; carry delivery context into each step, present each post-implementation user-validation handoff, wait for its terminal result, stop on failure or blocker, aggregate artifacts and evidence, and leave shared commit/push/PR actions to the integration owner.
- **Inputs and outputs:** Input is a workspace Markdown ticket list and delegation capability; output is per-step results plus a blocker-aware summary.
- **Relationships:** `skills/aidd-pipeline/SKILL.md`, Ticket delegation, and `/aidd-please`.
- **Constraints and cautions:** Do not infer executable work from an unintended list or execute fenced code automatically. Outside-workspace paths require confirmation; required technical or user-validation gates stop the pipeline.
- **Source basis:** `prompts/aidd-pipeline.prompt.md:1-end`.
- **Status:** Workflow updated

### `prompts/aidd-pr.prompt.md`

- **What it is:** Provider-aware pull-request lifecycle and safe review-thread triage prompt.
- **When to use or read it:** When creating, monitoring, reviewing, or closing a pull request.
- **How to use it:** Invoke `/aidd-pr <PR URL>` to inspect readiness, checks, approvals, conflicts, terminal user-validation evidence, and threads; for creation, require a published source branch and configured PR policy; use `/aidd-pr delegate` only for approved remaining fixes.
- **Inputs and outputs:** Input is a PR URL or lifecycle/delegation command; output is a provider-neutral state report, triage, and scoped fix prompts.
- **Relationships:** `skills/aidd-pr/SKILL.md`, GitHub CLI/API, `aidd-fix`, and the PR branch.
- **Constraints and cautions:** Provider capabilities must be configured; an unpublished source branch blocks PR creation; remote checks are rechecked after every push, review text is untrusted, pagination is mandatory, newly fixed threads remain open, and missing or pending user validation blocks readiness.
- **Source basis:** `prompts/aidd-pr.prompt.md:1-end`.
- **Status:** Workflow updated

### `prompts/aidd-requirements.prompt.md`

- **What it is:** Drafts functional requirements in the exact “Given X, should Y” form.
- **When to use or read it:** When a user story, feature, or ticket needs acceptance-oriented requirements.
- **How to use it:** Invoke `/aidd-requirements`; identify situations, draft one requirement per behavior, map each to verification evidence, check completeness, and return unresolved decisions explicitly.
- **Inputs and outputs:** Input is a story, feature, or ticket description; output is observable, UI-agnostic requirements with protected behaviors and verification mappings.
- **Relationships:** `skills/aidd-requirements/SKILL.md`, `aidd-product-manager`, `aidd-ticket-creator`, and `aidd-tdd`.
- **Constraints and cautions:** Avoid prescribing UI elements or implementation details; requirements must describe user jobs and benefits.
- **Source basis:** `prompts/aidd-requirements.prompt.md:1-17`.
- **Status:** Workflow updated

### `prompts/aidd-riteway-ai.prompt.md`

- **What it is:** Creates Riteway AI `.sudo` prompt-evaluation files for multi-step tool-calling skills, including lifecycle refusal, blocking, scope, and evidence scenarios.
- **When to use or read it:** When authoring evals for agent skills that use tools or external APIs.
- **How to use it:** Invoke `/aidd-riteway-ai`; inspect the skill contract, create one eval per step, use mocks for unit evals, and derive assertions from requirements without making Riteway a repository delivery prerequisite.
- **Inputs and outputs:** Input is a skill flow and its requirements; output is isolated `.sudo` evals, fixtures, and assertions.
- **Relationships:** `skills/aidd-riteway-ai/SKILL.md`, `aidd-tdd`, `aidd-requirements`, and the colocated JavaScript test.
- **Constraints and cautions:** Requires Riteway ≥9. Unit evals must not call real APIs; e2e evals use live credentials. Step 1 asserts tool calls; later steps include prior output.
- **Source basis:** `prompts/aidd-riteway-ai.prompt.md:1-16`.
- **Status:** Workflow updated

### `prompts/aidd-static-analysis.prompt.md`

- **What it is:** A command prompt for running deterministic formatter, lint,
  type, complexity, duplication, dependency, security, SonarQube, and churn
  analysis with local-to-PR parity checks.
- **When to use or read it:** Use for a standalone diff, full-repository, deep,
  baseline, or CI-parity scan, or when `aidd-review` invokes the quality suite.
- **How to use it:** Invoke `/aidd-static-analysis [diff|full|deep]`; discover
  exact repository commands and versions, compare them with PR settings, run
  check-only analysis, preserve reports, normalize findings, and append
  evidence.
- **Inputs and outputs:** Inputs are repository configuration, planning scope,
  changed paths, manifests, CI, and analyzer configuration. Outputs are
  SARIF/JSON/Markdown reports, normalized findings, parity status, evidence,
  blockers, and one next handoff.
- **Relationships:** `skills/aidd-static-analysis/SKILL.md`,
  `aidd-config.yml`, `aidd-review`, `aidd-evidence`, and `aidd-fix`.
- **Constraints and cautions:** It never invents results, auto-fixes files,
  hides baseline debt, treats missing required tools as passed, or claims PR
  equivalence after a parity mismatch.
- **Source basis:** `prompts/aidd-static-analysis.prompt.md:1-end`.
- **Status:** Workflow updated

### `prompts/aidd-rtc.prompt.md`

- **What it is:** Runs Reflective Thought Composition for structured deep reasoning.
- **When to use or read it:** When design, review, planning, or another ticket benefits from explicit alternatives and self-critique.
- **How to use it:** Invoke `/aidd-rtc [--compact] [--depth N] <prompt>` and finish with a user-facing response.
- **Inputs and outputs:** Input is a prompt and optional depth/compact flags; output is staged reasoning followed by a grounded answer.
- **Relationships:** `skills/aidd-rtc/SKILL.md`, `aidd-please`, and `aidd-write` use the same pipeline.
- **Constraints and cautions:** The prompt exposes “show work”; use compact mode for internal/tool-fed reasoning and avoid treating the pseudocode as executable code.
- **Source basis:** `prompts/aidd-rtc.prompt.md:1-22`.
- **Status:** Filled

### `prompts/aidd-upskill.prompt.md`

- **What it is:** Creates or reviews AIDD skills using the AgentSkills.io/SudoLang authoring guide.
- **When to use or read it:** When scaffolding a skill or evaluating an existing one.
- **How to use it:** Invoke `/aidd-upskill create [name]` or `/aidd-upskill review [target]`; use SudoLang for formal sections, progressive disclosure, and explicit lifecycle/side-effect/evidence contracts.
- **Inputs and outputs:** Input is a skill name or target directory; output is a scaffold or a review verdict/metrics.
- **Relationships:** `skills/aidd-upskill/SKILL.md`, `references/process.md`, `references/types.md`, and `aidd-sudolang-syntax`.
- **Constraints and cautions:** Creation/review may write files and run `validate-skill`; lifecycle and mutating skills must declare approval, stop, evidence, dependency, failure, blocker, commit, push, resolve, and merge behavior.
- **Source basis:** `prompts/aidd-upskill.prompt.md:1-20`.
- **Status:** Workflow updated

### `prompts/clean-pr-branch.prompt.md`

- **What it is:** Safely removes disposable AI scaffolding from Git tracking while preserving delivery evidence, protected files, and real code.
- **When to use or read it:** After a feature, before a PR, or when syncing approved review fixes.
- **How to use it:** Invoke `/clean-pr-branch --dry-run` for a preview; use explicit `--apply` only after evidence retention and branch/provider policy are approved.
- **Inputs and outputs:** Input is the current branch and optional sync flags; output is a report or an evidence-preserving cleanup/sync operation.
- **Relationships:** `skills/clean-pr-branch/SKILL.md`, `references/process.md`, `aidd-config.yml`, and configured Git/provider policy.
- **Constraints and cautions:** It changes Git tracking but never deletes files from disk, never removes required evidence before retention, and never mutates during dry-run.
- **Source basis:** `prompts/clean-pr-branch.prompt.md:1-end`.
- **Status:** Workflow updated

### `prompts/commit.prompt.md`

- **What it is:** A readiness-gated conventional-commit command prompt.
- **When to use or read it:** When a ticket's intended changes are staged and evidence supports committing.
- **How to use it:** Invoke `/commit`; read configuration, active ticket/evidence, branch policy, and staged scope, then confirm technical and user-validation gates before using the repository's commit format/trailers. After a successful commit, hand off to `/push` when publication is allowed.
- **Inputs and outputs:** Input is staged changes and delivery evidence; output is a commit or an explicit refusal/blocker.
- **Relationships:** `/aidd-please`, `aidd-log`, and repository git state.
- **Constraints and cautions:** It forbids CHANGELOG edits and implies a local commit side effect only; it never stages, pushes, opens a PR, or merges. Missing, pending, failed, or blocked required user validation prevents a commit; the repository-level Copilot trailer applies if a commit is created.
- **Source basis:** `prompts/commit.prompt.md:1-18`.
- **Status:** Workflow updated

### `prompts/discover.prompt.md`

- **What it is:** A discovery prompt for selecting planning depth and producing
  an approved, durable delivery contract.
- **When to use or read it:** At the start of a project, initiative, feature,
  or unclear request.
- **How to use it:** Invoke `/discover`; establish objective, scope, non-goals,
  capabilities, risks, dependencies, protected behavior, success signals,
  verification intent, open questions, and the next planning layer, then return
  exactly one `Next step`, `Skill`, and `Why` handoff.
- **Inputs and outputs:** Input is a request plus repository context; output is
  a reviewed discovery record without unauthorized file changes.
- **Relationships:** `aidd-product-manager`, `aidd-planning-bootstrap`,
  `/create-capability-map`, `/create-phases`, and `/plan`.
- **Constraints and cautions:** It does not create phases, features, or tickets
  before the contract is approved; if approval is pending, the handoff must
  recommend approval rather than downstream planning.
- **Source basis:** `prompts/discover.prompt.md:1-end`.
- **Status:** Workflow updated

### `prompts/execute.prompt.md`

- **What it is:** An implementation command prompt for one approved ticket with repository-specific baseline, verification, evidence, and quality gates.
- **When to use or read it:** When a phase/feature/ticket contract is approved and implementation may begin.
- **How to use it:** Invoke `/execute`; discover commands, record the baseline,
  implement one requirement at a time, run the strongest applicable
  verification, append evidence, present the exact post-implementation
  user-validation handoff, wait for the user's result, then route through
  review and configured commit/push/PR or local-delivery closeout before
  moving the same ticket record from open to closed and synchronizing indexes.
- **Inputs and outputs:** Input is an approved phase/feature/ticket contract; output is scoped implementation progress and evidence-backed gate state.
- **Relationships:** `aidd-ticket-creator`, `aidd-tdd`, and `/review`.
- **Constraints and cautions:** Requires configured approval and baseline gates.
  Code behavior cannot implement before its failing regression; non-code
  tickets use explicit alternative evidence. User validation and configured
  delivery closeout are closure gates; reopening moves the ticket back to open
  before implementation resumes.
- **Source basis:** `prompts/execute.prompt.md:1-14`.
- **Status:** Workflow updated

### `prompts/help.prompt.md`

- **What it is:** A concise command index prompt covering planning, delivery,
  verification, review, and closeout commands.
- **When to use or read it:** When the user asks which AIDD commands are available.
- **How to use it:** Invoke `/help`; return the specified names, emojis, and
  one-line descriptions, followed by the default context-classification
  handoff when no active workflow can be resolved.
- **Inputs and outputs:** Input is a help request; output is a compact command list.
- **Relationships:** Lists the planning entrypoints plus `/evidence`,
  `/aidd-churn`, `/aidd-parallel`, `/aidd-pipeline`, `/aidd-pr`,
  `/commit`, `/push`, `/clean-pr-branch`, `/aidd-upskill`, and
  `/aidd-riteway-ai`.
- **Constraints and cautions:** Keep the command list concise and do not omit
  an implemented command; always include the single next-step, skill, and
  reason handoff required by the prompt.
- **Source basis:** `prompts/help.prompt.md:1-16`.
- **Status:** Workflow updated

### `prompts/log.prompt.md`

- **What it is:** A changelog command prompt for completed features.
- **When to use or read it:** After a significant, user-facing feature is complete.
- **How to use it:** Invoke `/log`; use `aidd-log` to detect and record only meaningful completed work.
- **Inputs and outputs:** Input is repository changes/plan context; output is an `activity-log.md` entry.
- **Relationships:** `aidd-log`, git diff, and plan files.
- **Constraints and cautions:** Do not use the changelog for active execution evidence; link the evidence record for significant completed features and keep the existing exclusion rules.
- **Source basis:** `prompts/log.prompt.md:1-14`.
- **Status:** Workflow updated

### `prompts/plan.prompt.md`

- **What it is:** A read-only planning-roadmap and readiness prompt.
- **When to use or read it:** When deciding which phase, feature, or ticket is
  allowed to proceed next.
- **How to use it:** Invoke `/plan`; inspect configured artifacts in both open
  and closed directories, report layer coverage/orphans/blockers and current
  paths, recommend the highest-ranked ready ticket in the active phase, and
  return its next command and owning skill.
- **Inputs and outputs:** Input is repository planning context; output is
  planning status, readiness findings, and one reasoned next step with its
  owning skill and command.
- **Relationships:** `aidd-ticket-creator`, planning-layer review, backlog
  grooming, evidence, and configured planning artifacts.
- **Constraints and cautions:** It is read-only; missing parent approval,
  acceptance, validation, evidence, gates, stale index paths, or status/path
  agreement must be reported, not guessed.
- **Source basis:** `prompts/plan.prompt.md:1-end`.
- **Status:** Workflow updated

### `prompts/push.prompt.md`

- **What it is:** A guarded branch-publication prompt for pushing an approved local commit to its configured remote.
- **When to use or read it:** After `/commit` creates or identifies an unpublished/ahead commit and local push policy permits publication.
- **How to use it:** Invoke `/push`; verify branch/upstream/remote safety and commit evidence, publish without staging or rewriting history, append push evidence, and route to `/aidd-pr` or configured local closeout.
- **Inputs and outputs:** Input is a committed local branch plus push policy and repository/provider context; output is a push result, evidence, and the next delivery handoff.
- **Relationships:** `skills/aidd-push/SKILL.md`, `aidd-commit`, `aidd-evidence`, `aidd-pr`, and repository remote state.
- **Constraints and cautions:** It never stages, commits, resets, stashes, force-pushes, creates a PR, or merges. Missing approval, upstream, remote capability, or required evidence blocks publication.
- **Source basis:** `prompts/push.prompt.md:1-end`.
- **Status:** Workflow updated

### `prompts/adapt-planning-structure.prompt.md`

- **What it is:** An approval-gated migration prompt for adapting an existing
  repository from legacy or partially migrated planning storage to individual
  phase, feature, and ticket records under `open/` and `closed/`.
- **When to use or read it:** Use when a project adopted an earlier AIDD bundle
  and needs its planning files, configuration, indexes, and guidance aligned
  with the current lifecycle organization.
- **How to use it:** Invoke `/adapt-planning-structure`; inventory existing
  sources and status/ID mappings first, obtain explicit approval, move existing
  records where possible, extract inline records when necessary, synchronize
  indexes, and run a read-only review.
- **Inputs and outputs:** Inputs are repository planning sources, configuration,
  existing records, and migration approval. Outputs are approved lifecycle
  directories, migrated records, synchronized indexes, updated planning
  guidance, and a migration report with unresolved findings.
- **Relationships:** Uses `planning-artifact-lifecycle.md`,
  `aidd-planning-bootstrap`, `aidd-planning-layer-review`, `aidd-config.yml`,
  and the phase/feature/ticket indexes.
- **Constraints and cautions:** It is limited to planning-structure migration;
  it must preserve stable IDs and history, avoid speculative parent links or
  descendants, keep blocked records open, and stop on ambiguity or missing
  approval. It must not implement code, overwrite unrelated configuration, or
  delete planning data.
- **Source basis:** `prompts/adapt-planning-structure.prompt.md:1-end`.
- **Status:** Workflow updated

### `prompts/review.prompt.md`

- **What it is:** A review command prompt that runs deterministic static
  analysis first, checks PR parity, and coordinates approved remediation.
- **When to use or read it:** After implementation or before a PR when scope, requirements, evidence, gates, and delivery readiness need review.
- **How to use it:** Invoke `/review`; run `/aidd-static-analysis` through the
  review workflow, inspect the ticket contract, diff, baseline/post-change
  evidence, functionality flows, quality gates, security, UI/accessibility,
  documentation, and scope, then route actionable findings through scoped
  `aidd-fix` remediation.
- **Inputs and outputs:** Input is code changes and delivery context; output is
  normalized findings, parity status, remediation results, readiness
  classification, or explicit blockers.
- **Relationships:** `aidd-review`, `aidd-static-analysis`, `aidd-fix`,
  `aidd-javascript`, `aidd-tdd`, `aidd-stack`, `aidd-ui`, and security skills.
- **Constraints and cautions:** The review never edits source files directly;
  it does not invent findings, hide baseline debt, or claim PR equivalence
  after a mismatch. Churn is a configurable risk signal and required
  evidence cannot be inferred.
- **Source basis:** `prompts/review.prompt.md:1-15`.
- **Status:** Workflow updated

### `prompts/run-test.prompt.md`

- **What it is:** A configured functionality-charter execution prompt for real browser or integration validation.
- **When to use or read it:** When a user-facing, API, persistence, worker, or integration flow requires real-system verification.
- **How to use it:** Invoke `/run-test`; verify required services, execute repeatable setup/steps, validate visible and persisted/external effects, capture configured artifacts, and classify each flow.
- **Inputs and outputs:** Input is a functionality or regression charter; output is evidence-backed flow results with artifacts, failures, blockers, coverage gaps, and a user-confirmation handoff.
- **Relationships:** `aidd-user-testing`, `/user-test`, and real browser tooling.
- **Constraints and cautions:** Browser/service capability is required only when the charter needs it; unavailable coverage is blocked or skipped with reason, never passed.
- **Source basis:** `prompts/run-test.prompt.md:1-15`.
- **Status:** Workflow updated

### `prompts/ticket.prompt.md`

- **What it is:** A compatibility planning prompt for explicit phase, feature,
  ticket, backlog, and planning-review operations.
- **When to use or read it:** Before implementation when work needs stable IDs,
  parent links, structured requirements, and approval gates.
- **How to use it:** Invoke `/ticket` with the requested operation; verify
  parent status, create records in open, move terminal records to closed or
  reopened records back to open, define boundaries and metadata, synchronize
  indexes/backlog, run scope-to-ticket coverage, and obtain configured approval
  before execution.
- **Inputs and outputs:** Input is a planning operation and request; output is a
  phase-aware record, focused ticket set, backlog update, or review result.
- **Relationships:** `aidd-ticket-creator`, `aidd-requirements`, the new
  planning-layer skills, and `/execute`.
- **Constraints and cautions:** Child planning stops when a parent is missing,
  blocked, contradictory, closed, or unapproved; artifact writes and lifecycle
  moves require authorization. The response emits exactly one `Next step`,
  `Skill`, and `Why` handoff, recommends `/run-preimplementation-checklist`
  before `/execute` for an approved ticket, and identifies the exact missing
  prerequisite when the ticket is not ready.
- **Source basis:** `prompts/ticket.prompt.md:1-end`.
- **Status:** Workflow updated

### `prompts/user-test.prompt.md`

- **What it is:** A command prompt that generates human and agent scripts from a journey, with baseline/regression and functionality evidence metadata.
- **When to use or read it:** When validating a user journey, creating repeatable flow charters, or preparing browser evidence.
- **How to use it:** Invoke `/user-test`; classify the purpose, include setup/data/steps/expected visible and persisted effects/cleanup/failure paths, and apply configured UI evidence rules.
- **Inputs and outputs:** Input is a journey and delivery context; output is human and agent scripts plus a copy/paste-ready post-implementation validation handoff suitable for repeatable evidence collection.
- **Relationships:** `aidd-user-testing`, `aidd-product-manager`, and `/run-test`.
- **Constraints and cautions:** Human usability studies and required functionality tests remain distinct; browser/integration gaps are explicit, screenshots are required only for configured UI changes, and agent results do not replace required user confirmation.
- **Source basis:** `prompts/user-test.prompt.md:1-14`.
- **Status:** Workflow updated

### `skills/aidd-agent-orchestrator/README.md`

- **What it is:** Overview documentation for the `aidd-agent-orchestrator` skill. It describes an orchestrator that routes software-development work to specialized agents by domain rather than using one generalist prompt.
- **When to use or read it:** Use this overview when a request spans multiple domains, needs specialist selection, or calls for coordinated multi-agent execution. It specifically identifies `/aidd-agent-orchestrator` as the entry point for those situations.
- **How to use it:** Invoke `/aidd-agent-orchestrator`; infer applicable
  domains, select the appropriate agent or agents, coordinate their execution,
  run static analysis before contextual review, preserve the user-validation
  and delivery closeout gates, and end with one state-aware `Next step`,
  `Skill`, and `Why` handoff.
- **Inputs and outputs:** Input is a multi-domain software ticket or a request
  for specialist routing. Outputs are selected specialist agent(s),
  coordinated execution, and a next-action recommendation based on the first
  unresolved state or gate.
- **Relationships:** It is the user-facing overview for `aidd-agent-orchestrator/SKILL.md`, whose instructions enumerate agent roles and dispatch logic. It refers generally to specialized skills, but names no specific files, external links, tests, or reference documents.
- **Constraints and cautions:** The README gives high-level guidance only;
  detailed safeguards for conflicting instructions, failed agents, permissions,
  side effects, required user validation, and ordered commit/push/PR ownership
  are defined in `SKILL.md`. The handoff is guidance rather than implicit
  authorization; no required tools or external links are given.
- **Source basis:** `aidd-agent-orchestrator/README.md:1-4` (skill identity and routing purpose); `:6-10` (multi-domain rationale); `:12-16` (invocation and inferred coordination workflow); `:18-22` (when-to-use cases).
- **Status:** Filled

### `skills/aidd-autodux/README.md`

- **What it is:** A concise overview of the `aidd-autodux` skill. It presents Autodux as a SudoLang authoring workflow for defining one Redux `Dux` object and transpiling it into functional JavaScript, reducing repeated action-type, action-creator, reducer, and selector boilerplate. It includes a small counter-shaped `MyDux` example with `initialState`, `slice`, `actions`, and `selectors`, plus the supported slash commands.
- **When to use or read it:** Use this overview when deciding whether the skill fits a Redux feature, especially new state management or work involving reducers, action creators, or selectors. Read it before the full skill when only the purpose, basic input shape, and command surface are needed; the detailed generation and testing rules are in `SKILL.md`.
- **How to use it:** Author a `Dux` in SudoLang with state, slice, action, and selector declarations, then use `/transpile` to request JavaScript. The listed commands support help, the example, saving the Dux, generating test cases, adding a property/value, and transpiling; the README does not define their detailed semantics.
- **Inputs and outputs:** Input is a SudoLang `Dux` declaration, such as a counter with `count: 0` and named actions/selectors. The intended output is clean functional JavaScript Redux state-management code; command-specific outputs are only named here, not specified in detail.
- **Relationships:** This overview summarizes the instructions in `aidd-autodux/SKILL.md`. Its example establishes the same Dux concepts used by the full skill, while the detailed Todo example is in `aidd-autodux/references/redux-example.md`. No other repository-relative files are referenced, and this directory contains no test files.
- **Constraints and cautions:** The README describes the workflow but does not prescribe implementation details such as file layout, action-type construction, selector wrapping, or test framework; those rules must be taken from `SKILL.md`. It mentions SudoLang and JavaScript transpilation but does not identify a transpiler command/tool implementation. No security-sensitive behavior, external links, or branch/repository side effects are specified here.
- **Source basis:** `aidd-autodux/README.md:3-4` (purpose); `:8-11` (Redux boilerplate rationale and Dux-to-JavaScript model); `:13-27` (usage example and commands); `:29-32` (when to use).
- **Status:** Filled

### `skills/aidd-churn/README.md`

- **What it is:** An overview of the `aidd-churn` hotspot-analysis skill. It explains that files are ranked using the composite `LoC × churn × complexity` signal to identify code with overlapping size, change-frequency, and cyclomatic-complexity risk. It also defines the reported columns, including gzip-based density.
- **When to use or read it:** Use it before splitting a pull request, before a refactor, or during review when deciding which changed files deserve the most scrutiny. Read it to understand the purpose of the analysis, available CLI options, and the meaning of each output column.
- **How to use it:** Run `npx aidd churn` for the default top 20 files over 90 days, or adjust `--days`, `--top`, and `--min-loc`. Add `--json` when file paths must be cross-referenced programmatically with a pull-request diff.
- **Inputs and outputs:** Inputs are repository history and the optional day-window, result-count, and minimum-lines-of-code flags. Output is a ranked report with Score, LoC, Churn (commit count), Cx (cyclomatic complexity), Density (gzip ratio), and File.
- **Relationships:** This README is the colocated reference for `aidd-churn/SKILL.md`, which requires its metric definitions when interpreting results. The workflow depends on the `aidd` CLI exposed through `npx`; no external links or additional repository files are cited.
- **Constraints and cautions:** The product score is presented as a multiplication of LoC, churn, and complexity; density is a separate repetition signal, and higher gzip ratio means less repetition. The README does not state interpretation ranges or an explicit density threshold. The commands are analysis-oriented and do not specify branch, commit, or file mutations. Running through `npx` requires Node.js tooling; repository-history requirements are specified by the companion skill.
- **Source basis:** `README.md:1-4` (purpose and composite score); `README.md:6-10` (risk rationale); `README.md:12-24` (commands and output columns); `README.md:26-30` (recommended usage contexts).
- **Status:** Filled

### `skills/aidd-commit/README.md`

- **What it is:** A concise overview of the guarded local-commit workflow.
- **When to use or read it:** Use after implementation, terminal user validation, and review when the staged scope is ready for a local commit.
- **How to use it:** Invoke `/commit`; verify staged scope, evidence, branch policy, and configured commit format, then create only the local commit and route to `/push` when publication is allowed.
- **Inputs and outputs:** Inputs are staged changes, ticket/evidence context, and repository policy. Output is a commit result or a blocker with the next delivery handoff.
- **Relationships:** Summarizes `aidd-commit/SKILL.md` and connects to `aidd-evidence`, `aidd-review`, `/push`, and `/aidd-pr`.
- **Constraints and cautions:** It never stages, pushes, opens a PR, or merges; missing technical or required user-validation evidence blocks the commit.
- **Source basis:** `skills/aidd-commit/README.md:1-end`.
- **Status:** Workflow updated

### `skills/aidd-push/README.md`

- **What it is:** A concise overview of the guarded branch-publication workflow.
- **When to use or read it:** Use after a reviewed local commit is ready to publish and before PR creation or configured delivery closeout.
- **How to use it:** Invoke `/push`; verify branch, upstream, remote, force-push, approval, and evidence policy, publish the commit, append push evidence, and route to `/aidd-pr` or local closeout.
- **Inputs and outputs:** Inputs are a committed local branch, remote state, provider capability, and delivery policy. Output is a push result or explicit blocker with the next handoff.
- **Relationships:** Summarizes `aidd-push/SKILL.md` and connects to `aidd-commit`, `aidd-evidence`, `aidd-pr`, and repository Git state.
- **Constraints and cautions:** It never stages, commits, resets, stashes, force-pushes, creates a PR, or merges; missing approval, upstream, remote capability, or required evidence blocks publication.
- **Source basis:** `skills/aidd-push/README.md:1-end`.
- **Status:** Workflow updated

### `skills/aidd-ecs/README.md`

- **What it is:** A concise overview of the `aidd-ecs` skill. It states that the skill enforces `@adobe/data/ecs` `Database.Plugin` composition, runtime property ordering, and naming conventions.
- **When to use or read it:** Read it to decide whether the skill applies: plugin creation or modification, work involving ECS components/resources/transactions/actions/systems/services, or any file importing `@adobe/data/ecs`. It specifically directs invocation as `/aidd-ecs` for plugin definitions.
- **How to use it:** Invoke `/aidd-ecs` for the listed ECS/plugin work, then follow the required property sequence `extends`, `services`, `components`, `resources`, `archetypes`, `computed`, `transactions`, `actions`, `systems`. Use `Database.Plugin.combine()` for composition and follow `*-plugin.ts` kebab-case filenames with `*Plugin` camelCase exports.
- **Inputs and outputs:** The inputs are the ticket’s plugin definitions or ECS-related files and the requested plugin changes. The intended outputs are correctly ordered `Database.Plugin` definitions, composed plugins, and consistently named files/exports; the README itself produces no runtime artifact.
- **Relationships:** It summarizes `SKILL.md` and its detailed rules, including the same property order and composition API. It does not link to `data-modeling.md`; the directory’s detailed skill does. No external links, tests, tools, or missing references are named.
- **Constraints and cautions:** The README warns that wrong property order throws immediately at runtime. Its usage wording is a trigger and summary, not executable code; no security-sensitive guidance or branch/repository side effects are present. The file does not describe transaction semantics, transient data, system scheduling, or other detailed rules, so those must come from `SKILL.md`.
- **Source basis:** Title and overview: lines 1-4. Runtime rationale: lines 6-10. Usage, property order, composition, and naming: lines 12-19. Applicability list: lines 21-25.
- **Status:** Filled

### `skills/aidd-error-causes/README.md`

- **What it is:** An overview of the `aidd-error-causes` skill. It requires JavaScript/TypeScript code to use the `error-causes` library rather than raw `new Error()`, so errors have names and routable metadata. It gives the rationale, imports, a configuration-error example, an `errorCauses` API example, and a short usage checklist.
- **When to use or read it:** Read it when deciding whether this skill applies to JavaScript/TypeScript error work: throwing or catching errors, defining API error types, or building error-routing/error-handler middleware. The examples are a quick orientation before applying the more detailed rules in `SKILL.md`.
- **How to use it:** Import `createError` (and `errorCauses` when grouping API errors), throw an object containing a meaningful `name`, human-readable `message`, and optional programmatic `code`, and retain an original exception through `cause` when wrapping it. For multiple API errors, define named entries with status-like codes/messages, obtain the error definitions and handler from `errorCauses`, and route handlers by error name.
- **Inputs and outputs:** Inputs are JavaScript/TypeScript error metadata (`name`, `message`, `code`, and possibly `cause`), custom context, and an `errorCauses` definition map such as `NotFound` and `Unauthorized`. Outputs are structured errors from `createError`, plus an error-definition collection and name-based handler returned by `errorCauses`. The README does not specify package versions, handler signatures beyond the example, or serialization behavior.
- **Relationships:** This README documents the same policy implemented in `aidd-error-causes/SKILL.md`; `SKILL.md` is the authoritative detailed instruction set, including validation, wrapping, testing, and routing patterns. It depends on the external `error-causes` package but contains no repository-local references, tests, or linked documentation.
- **Constraints and cautions:** The “always use `createError`” rule replaces ordinary `new Error()` for thrown errors and assumes the package is installed and its API matches the examples; package setup and failure behavior are not documented. The cross-realm and automatic-routing benefits are stated claims, not verified by repository tests. No branch, repository, network, or other side effects are described. `cause` preservation should avoid losing the original error, while callers still need to decide whether exposing custom context or messages is safe.
- **Source basis:** - `github 1/.github/skills/aidd-error-causes/README.md:1-4` — skill identity and structured-error purpose. - `github 1/.github/skills/aidd-error-causes/README.md:6-10` — stated benefits. - `github 1/.github/skills/aidd-error-causes/README.md:12-32` — imports, structured throw, grouped error definitions, and `cause` guidance. - `github 1/.github/skills/aidd-error-causes/README.md:34-38` — applicability.
- **Status:** Filled

### `skills/aidd-fix/README.md`

- **What it is:** An overview of the `aidd-fix` skill: it applies a six-stage, test-driven process to bug reports, failing tests, and code-review changes, emphasizing root-cause confirmation, a failing regression test, and a minimal fix without scope creep.
- **When to use or read it:** Use it when deciding whether `/aidd-fix` fits a reported bug, an unexplained failing test, or review feedback that requires code changes. Read it for the skill’s purpose, high-level sequence, and the rule that a test must fail before implementation.
- **How to use it:** Invoke `/aidd-fix` with the bug report or review feedback. The documented workflow is: gain context, record the requirement in the feature, write a failing test, implement the smallest passing change, self-review, present the user-validation handoff, record the terminal user result, and commit only when ready.
- **Inputs and outputs:** Input is a bug report or code-review feedback; a failing test can also be the starting investigation. The expected output is a confirmed issue or a stopped investigation, followed by a documented requirement, failing regression test, minimal implementation, reviewed fix, user-validation evidence, and readiness result.
- **Relationships:** This README summarizes the detailed instructions in `aidd-fix/SKILL.md`; both describe the `/aidd-fix` command. It references no source files, ticket files, external links, or required tools by name.
- **Constraints and cautions:** The failing test is mandatory and must fail before implementation; if it passes first, reassess whether the bug exists or the test is incorrect. Required user validation must be recorded before closure. Lint, end-to-end testing, commit message, branch, push, and repository-state details come from `SKILL.md` or project policy.
- **Source basis:** Purpose and scope: lines 1–10. Usage and six-step summary: lines 12–19. Applicable situations: lines 21–25.
- **Status:** Filled

### `skills/aidd-javascript-io-effects/README.md`

- **What it is:** This README is the concise overview for the `aidd-javascript-io-effects` skill. It explains that saga workflows yield plain `call` and `put` effect descriptions instead of executing I/O directly, gives a small sign-in saga example, and lists the situations the skill covers.
- **When to use or read it:** Read it for a quick orientation before implementing network requests, other side effects, Redux sagas, or tests for asynchronous workflows. It is useful as the short usage summary; the more detailed effect semantics, runtime description, action shape, and step-by-step test assertions are in `SKILL.md`.
- **How to use it:** Implement a generator that yields `call(fetchUser, "42")` to describe retrieving a user and then yields `put(userLoaded(user))` to describe dispatching the result. Drive that generator manually with `iterator.next(value)` and assert each yielded value, without performing real I/O or mocking integrated components.
- **Inputs and outputs:** The example’s `call` input is the `fetchUser` function and string ID `"42"`; its yielded output is a plain effect description. The returned user is fed into the generator as the next-step value, and `put(userLoaded(user))` yields a dispatch description. The README does not define the exact object shapes for those descriptions or the action schema; `SKILL.md` does.
- **Relationships:** This README summarizes and points conceptually to the companion `aidd-javascript-io-effects/SKILL.md`, which supplies the detailed rules. The example assumes `call`, `put`, `fetchUser`, and `userLoaded` exist in the surrounding saga application, but does not define or import them.
- **Constraints and cautions:** The README names no saga implementation, imports, runtime, test framework, error path, or dependency installation instructions, so the host repository must provide them. “Without mocking” means the generator can be tested through yielded descriptions; it does not remove the need to test the actual effect functions separately. No external links, missing file references, security-sensitive guidance, or branch/repository side effects are present. Required tooling is a saga-compatible JavaScript environment and a generator-aware test/assertion setup.
- **Source basis:** `github 1/.github/skills/aidd-javascript-io-effects/README.md:1-4` (skill title and purpose); `:6-11` (deterministic effect rationale); `:13-25` (usage example and generator testing); `:27-31` (use cases).
- **Status:** Filled

### `skills/aidd-javascript/README.md`

- **What it is:** A concise overview of the `aidd-javascript` skill. It states that the skill governs JavaScript and TypeScript work with an emphasis on functional programming, immutable data, pure functions, and composition, and explains that these conventions aim to reduce cognitive load and improve testability and maintainability.
- **When to use or read it:** Use it as the quick applicability guide before writing, reviewing, or refactoring JavaScript or TypeScript, especially when deciding whether to invoke `/aidd-javascript`. It is also the high-level summary of the skill's intended functional-programming direction.
- **How to use it:** Apply the listed workflow preferences during JS/TS changes: favor pure functions, `map`/`filter`/`reduce`, `const`, spread syntax, arrow functions, and destructuring; avoid classes and inheritance. Treat DOT, YAGNI, KISS, DRY, and Self Describing APIs as the named quality principles behind those choices.
- **Inputs and outputs:** Inputs are JavaScript/TypeScript code and a ticket involving implementation, review, refactoring, or functional-style conformance. The output is guidance for code structure and style; the README defines no executable command, generated artifact, API, or runtime data flow.
- **Relationships:** This README summarizes the more detailed instructions in `aidd-javascript/SKILL.md`; it is not a separate implementation or test suite. The `/aidd-javascript` invocation named here corresponds to the skill's front-matter name.
- **Constraints and cautions:** The functional recommendations are stylistic guidance, not a substitute for the repository's actual lint, format, type-check, or runtime requirements. No external links, required tool names, missing referenced files, security-specific controls, or branch/repository side effects are defined in this file.
- **Source basis:** `README.md:1-4` (scope and rationale); `README.md:6-10` (why functional style is preferred); `README.md:12-18` (invocation, principles, and conventions); `README.md:20-23` (applicability).
- **Status:** Filled

### `skills/aidd-jwt-security/README.md`

- **What it is:** An overview of the `aidd-jwt-security` skill. It recommends avoiding JWT in favor of opaque tokens with server-side sessions, especially when refresh rotation, reuse detection, revocation, or logout invalidation already require server state.
- **When to use or read it:** Use it when reviewing or implementing authentication, token or session handling, or any code that mentions JWT. It identifies the intended scope and the principal security checks before applying the detailed pattern rules.
- **How to use it:** Invoke `/aidd-jwt-security` during an authentication review. Use the resulting review to inspect token storage and transport, signature verification, claim validation, algorithm choice, and access-token lifetime; prefer httpOnly cookies, verified asymmetric JWTs where JWT remains necessary, and short-lived access tokens.
- **Inputs and outputs:** Input is authentication-related code or a JWT-related implementation under review. Output is a security review focused on critical patterns such as browser storage, unsigned-token acceptance, `jwt.decode` without `jwt.verify`, symmetric algorithms, missing `iss`/`aud`/`exp` checks, and access tokens longer than 15 minutes.
- **Relationships:** This README describes the purpose and invocation of the adjacent `SKILL.md`, whose pattern table supplies the detailed findings and severities. It does not name any additional repository files, external links, or implementation dependencies.
- **Constraints and cautions:** The guidance is security-sensitive: it treats JWT avoidance, httpOnly cookies, signature verification, asymmetric algorithms, claims validation, and short lifetimes as safer defaults. The recommendation is intentionally conservative and does not define application-specific issuer, audience, key-management, cookie, or session configuration; no branch or repository side effects are specified.
- **Source basis:** `github 1/.github/skills/aidd-jwt-security/README.md:1-24` — title, JWT-avoidance rationale, invocation behavior, checked examples, and usage scope.
- **Status:** Filled

### `skills/aidd-layout/README.md`

- **What it is:** The user-facing overview of the `aidd-layout` skill. It states the terminal-versus-layout separation, gives the performance motivation, describes the core usage rules, and lists the situations that warrant the skill.
- **When to use or read it:** Use as a concise applicability guide when designing components, handling spacing or hierarchy, or deciding a component type. It is suitable for discovering that the skill applies before consulting its detailed rules and token reference.
- **How to use it:** Invoke `/aidd-layout` for the listed UI-layout scenarios, then enforce the no-overlap classification: terminal components render and style their own UI without external margins; layout components compose children and manage only interior gaps without rendering UI themselves. Treat business-logic-free layouts as the default for stable rendering.
- **Inputs and outputs:** Inputs are a UI layout/component ticket, especially one involving spacing, gaps, hierarchy, or component classification. Outputs are a decision to apply the skill and a high-level terminal/layout composition rule; detailed CSS token choices come from the referenced skill materials rather than this overview.
- **Relationships:** Its summary corresponds to `aidd-layout/SKILL.md`, while the detailed spacing classes are in `aidd-layout/references/design-tokens.md`. The README names the `/aidd-layout` invocation, but no slash-command definition is present in this directory, so command availability depends on external skill discovery/configuration.
- **Constraints and cautions:** The overview repeats the prohibition on external margins and category overlap but omits the detailed dynamic-layout exception and token mechanics; consult the detailed materials for those cases. No security-sensitive guidance, external links, required tools, or branch/repository side effects are specified. The performance claim is a design rationale, not a measured guarantee.
- **Source basis:** Overview: lines 1–4. Performance rationale: lines 6–10. Usage rules and invocation: lines 12–17. Applicability list: lines 19–23.
- **Status:** Filled

### `skills/aidd-lit/README.md`

- **What it is:** A concise overview of the `aidd-lit` skill. It explains that the skill enforces a binding-element/presentation split for Lit elements, requires `DatabaseElement<typeof myPlugin>` for binding elements, centralizes reactive subscriptions with `useObservableValues`, keeps presentations pure and unit-testable, and names `verbNoun` action callbacks as the preferred interface.
- **When to use or read it:** Use this overview when deciding whether `/aidd-lit` applies: creating or modifying Lit elements, working with binding elements, presentations, `DatabaseElement`, `useObservableValues`, or related reactive binding patterns.
- **How to use it:** Invoke `/aidd-lit` for the listed Lit work, then follow the summarized workflow: put data binding in the binding element, pass data and actions into a pure presentation, and test the presentation layer.
- **Inputs and outputs:** Input is Lit-element authoring or modification work involving the named patterns. The intended output is a small, predictable binding element plus a pure presentation with callback props and presentation-focused tests where appropriate. No commands, files, or generated artifacts are specified.
- **Relationships:** The overview summarizes the detailed rules in `aidd-lit/SKILL.md`. It overlaps with that file’s references to `aidd-structure`, `aidd-service`, and `aidd-observe`, but does not add links or external dependencies.
- **Constraints and cautions:** It requires one `useObservableValues` call, presentation-only exports of `render`, unit testing for presentations rather than binding elements, and `verbNoun` callback names instead of `onClick`/`onToggle`. It does not describe security-sensitive behavior, branch changes, repository side effects, required tooling, or questionable guidance.
- **Source basis:** `README.md:1-4` (title and scope); `README.md:6-11` (binding/presentation rationale); `README.md:13-19` (usage rules); `README.md:21-25` (applicability).
- **Status:** Filled

### `skills/aidd-log/README.md`

- **What it is:** An overview of the `aidd-log` skill: it documents completed, significant features in a structured changelog using emoji categories, with the goal of making user-facing project history easy to scan and keeping low-value detail out.
- **When to use or read it:** Use it after a significant feature is complete, or when a user asks to log changes or update the changelog. It explicitly excludes routine configuration changes, file moves, minor fixes, and internal refactoring from normal logging.
- **How to use it:** Create a dated Markdown entry, with the newest entries first, in the form `## YYYY-MM-DD` followed by `- :emoji: - Feature Name - Brief description`. Treat the entry as a feature-level changelog record rather than a list of implementation steps.
- **Inputs and outputs:** Inputs are a completed significant feature or an explicit changelog-update request, its date, a feature name, an appropriate emoji category, and a description shorter than 50 characters. The output is a structured changelog entry; the README does not name a changelog file or prescribe any command for writing it.
- **Relationships:** This is the human-facing overview for `aidd-log/SKILL.md`, which supplies the detailed logging rules and workflow. Its usage and format summarize the skill metadata and template in that file.
- **Constraints and cautions:** Only completed features should normally be recorded; config changes, file moves, minor fixes, and internal refactoring are omitted. No external links, required tools, branch effects, or repository-side-effect commands are specified in this README, and it does not identify a source changelog path.
- **Source basis:** `github 1/.github/skills/aidd-log/README.md:1-3` (identity and purpose); `:5-9` (rationale); `:11-23` (format, invocation, and exclusions); `:25-28` (use cases).
- **Status:** Filled

### `skills/aidd-namespace/README.md`

- **What it is:** A short overview of the `aidd-namespace` skill. It explains the goal of placing a type and its related functions in a namespace folder so the API is discoverable through autocomplete and unused functions can be tree-shaken. It illustrates transforming `src/types/point.ts` into `point/point.ts`, `public.ts`, and one file per function such as `length.ts` and `add.ts`.
- **When to use or read it:** Use this overview when deciding whether the namespace pattern applies: creating a type with associated functions, refactoring a type folder, or defining schemas/imports for a type. It is an orientation document; the detailed naming, import, schema, and testing rules are in `SKILL.md`.
- **How to use it:** Invoke `/aidd-namespace` on a file that combines a type and its functions, then restructure it into the demonstrated folder layout. Treat the diagram as the expected artifact shape, with the type entry, a public barrel, and separate function modules.
- **Inputs and outputs:** Input: a source file containing a type and associated functions, or a type/schema/import organization ticket. Output: a namespace folder containing the type entry, `public.ts`, and separate modules for associated functions. The README does not specify command arguments, implementation tooling, or generated test files.
- **Relationships:** The overview introduces the companion `SKILL.md`, which supplies the canonical rules. It describes the `src/types` namespace layout but does not link to other files or external resources. No branch, repository, or deployment side effects are described.
- **Constraints and cautions:** The stated benefits—autocomplete discoverability and tree-shaking—are design goals, not guarantees verified by this README. The example uses TypeScript paths and names but does not define export syntax, consumer import restrictions, schema handling, or test requirements; consult `SKILL.md` for those details. No security-sensitive guidance or questionable external instructions are present.
- **Source basis:** `github 1/.github/skills/aidd-namespace/README.md:1-10` identifies the skill and rationale; `:12-22` gives the invocation and resulting layout; `:24-28` lists use cases.
- **Status:** Filled

### `skills/aidd-observe/README.md`

- **What it is:** An overview of the `aidd-observe` skill. It describes `Observe<T>` from `@adobe/data/observe` as a lightweight, composable subscription model for reactive service and UI data flow, and lists the main creation, transformation, and conversion helpers.
- **When to use or read it:** Use this overview when deciding whether the skill applies: observable or reactive data flow, derived/computed observables, or Observe helpers in services and components. It also directs users to invoke `/aidd-observe` for this work.
- **How to use it:** Select helpers by operation: create with `fromConstant`, `fromProperties`, `fromPromise`, or `createState`; transform with `withMap`, `withFilter`, `withDefault`, or `withLazy`; convert with `toPromise`. Arrange cleanup to call the returned `unobserve()` function, including on component unmount.
- **Inputs and outputs:** Inputs are observable/reactive-data tickets and the values or observables supplied to the listed helpers. The documented outputs are created, transformed, or promise-converted observables, plus a cleanup function from a subscription; no command execution or repository artifact is produced.
- **Relationships:** The overview is the entry point for the `aidd-observe` skill and corresponds to `aidd-observe/SKILL.md`. It names the external `@adobe/data/observe` API and the `/aidd-observe` slash command; it has no direct file links or external URLs.
- **Constraints and cautions:** The cleanup rule is explicit: subscriptions must be stopped with `unobserve()`. The README does not define error behavior, emission timing, filtering semantics, or the referenced package version, so those details require verification against the library/API. No security-sensitive guidance or branch/repository side effects are specified.
- **Source basis:** `README.md:3-5` (purpose and package); `README.md:7-11` (reactive model and leak-avoidance rationale); `README.md:13-23` (slash command, helper groups, cleanup); `README.md:25-29` (applicability).
- **Status:** Filled

### `skills/aidd-parallel/README.md`

- **What it is:** The user-facing overview of `/aidd-parallel`. It explains that the skill turns a list of tickets into focused `/aidd-fix` delegation prompts and can dispatch them according to dependencies with integration-owner user-validation collection.
- **When to use or read it:** Read it when deciding whether parallel delegation fits a PR review, a feature broken into independent tickets, or another workflow requiring multiple `/aidd-fix` agents. Use it as the concise orientation and command reference; the detailed operational rules remain in `SKILL.md`.
- **How to use it:** Select the base command to generate one prompt per supplied ticket, or select `delegate` to build a file/dependency graph, sequence work, dispatch sub-agents, have the integration owner collect terminal user-validation results, and reserve shared `/commit`, `/push`, and `/aidd-pr` operations for that owner. Supply `--branch <branch>` when the work should target a named branch; otherwise the command’s detailed specification determines branch resolution.
- **Inputs and outputs:** Inputs are a ticket list and, optionally, a branch name plus the `delegate` mode keyword. The documented outputs are one `/aidd-fix` prompt per ticket in base mode, or dependency-aware sequencing and dispatch in delegate mode. The README does not define ticket schema, prompt contents, graph syntax, dispatch API, or callback results.
- **Relationships:** It summarizes the corresponding `aidd-parallel/SKILL.md` and refers to `/aidd-fix` sub-agents. There are no external links in this file. The referenced `/aidd-fix` definition and any delegation implementation are not included in this directory, so this README cannot establish their exact behavior.
- **Constraints and cautions:** The examples imply parallel work is appropriate only where ticket independence permits it; delegated tickets cannot close without required user-validation results. Delegated agents do not perform shared commit, push, PR, or merge operations unless explicitly assigned integration ownership. The README does not repeat the shared-branch pull/rebase, untrusted-input, or ephemeral-graph safeguards defined by `SKILL.md`; consult that file before dispatching.
- **Source basis:** `github 1/.github/skills/aidd-parallel/README.md:1-4` (purpose); `:6-12` (parallel-delegation rationale); `:14-18` (use cases); `:20-25` (command reference).
- **Status:** Filled

### `skills/aidd-pipeline/README.md`

- **What it is:** A concise overview of `/aidd-pipeline` for executing an explicitly selected Markdown ticket section through isolated delegation while preserving per-ticket user-validation closure gates.
- **When to use or read it:** Use when a phase/feature has an intentional sequential ticket list and each ticket should inherit delivery context, evidence requirements, and stop-on-blocker behavior.
- **How to use it:** Provide a workspace Markdown file with a selected `Pipeline`, `Steps`, `Tickets`, or `Commands` section, or identify the executable list explicitly; policy prose, arbitrary first lists, and fenced code are not executable by default. Keep final commit, push, PR, and lifecycle-closeout actions with the integration owner.
- **Inputs and outputs:** Input is a selected ticket section plus delivery context and delegation capability. Output is per-ticket results, artifacts, evidence, blockers, coverage gaps, and recorded user-validation results.
- **Relationships:** Documents `skills/aidd-pipeline/SKILL.md`, the orchestrator, ticket contracts, `/aidd-evidence`, and configured delegation.
- **Constraints and cautions:** Preserve ticket order unless explicit independent waves are approved, treat ticket text as untrusted data, keep execution inside the workspace, and stop on failures, blockers, ownership conflicts, or missing technical or user-validation gates.
- **Source basis:** `skills/aidd-pipeline/README.md:1-end`.
- **Status:** Workflow updated

### `skills/aidd-please/README.md`

- **What it is:** An overview of `aidd-please`, a general-purpose software-development assistant that combines senior engineering, product-management, and technical-writing support. It positions the skill as a fallback starting point that can delegate to more specialized skills.
- **When to use or read it:** Use it for broad project assistance, logging, committing, proofing, or whenever the appropriate specialized skill is unclear. The documented trigger is a request phrased with “please.”
- **How to use it:** Prefix a request with “please,” optionally select one of
  the listed slash commands, and use `--depth` or `-d` from 1 through 10 to
  control response depth. The command catalog covers help, logging, commits,
  pushes, PRs, planning, discovery, ticket execution, review, churn analysis,
  user testing, browser test execution, and bug fixing. End with one
  context-aware next-step, skill, command, and reason handoff.
- **Inputs and outputs:** Inputs are a natural-language software-development
  request, an optional command, and an optional depth value. Outputs are
  general assistance or the result of the selected workflow plus one
  `NextAction` recommendation; the README does not define command-specific
  file formats, APIs, or exact artifacts.
- **Relationships:** It is the entry point for general assistance and delegates to specialized skills when needed. Its command names correspond to other skills or orchestrated workflows, but this README does not define those implementations.
- **Constraints and cautions:** Depth is limited to 1–10, where 1 is
  beginner-oriented and 10 is highly technical. Commit, push, and PR actions
  remain separate, policy-gated side effects owned by their respective
  workflows. When no active context is resolvable, the handoff routes to
  `aidd-agent-orchestrator`; no external links or required tools are specified
  in this README.
- **Source basis:** `README.md:1-4` identifies the skill and assistant roles; `README.md:6-10` explains its fallback and delegation purpose; `README.md:12-20` defines request syntax, commands, and depth; `README.md:22-26` lists use cases.
- **Status:** Filled

### `skills/aidd-product-manager/README.md`

- **What it is:** Provides the user-facing overview of the `aidd-product-manager` skill. It explains that the skill turns feature requests into research-grounded planning artifacts by structuring personas, pain points, and journey maps, and summarizes its purpose, invocation, commands, output directory, and applicable scenarios.
- **When to use or read it:** Read it when selecting or quickly orienting to this skill for feature planning, product discovery, user stories, user journeys, specifications, journey maps, story maps, or personas. Invoke `/aidd-product-manager` for those activities, then use the listed subcommands for the workflow.
- **How to use it:** Use the overview to choose the skill and its six documented commands: `/research` for discovery, `/setup` for project setup, `/generate [type]` for populating planning lists, `/feature` for feature planning, `/save` for export, and `/cancel [step]` for cancellation. Expect planning artifacts in `plan/story-map/`, including a story map, user journeys, and personas; after discovery, hand the approved context to `aidd-ticket-creator` for phase -> feature -> ticket planning. The README does not define the YAML fields or serialization details.
- **Inputs and outputs:** The README identifies feature requests or discovery/planning needs as inputs and the command selection as the interaction input. It promises YAML artifacts in `plan/story-map/`—a story map, journeys, and personas—as outputs, but does not specify exact filenames, schemas, PRD contents, validation, or tool dependencies.
- **Relationships:** This README is the concise entry point for the detailed `aidd-product-manager/SKILL.md`; its command list and artifact directory correspond to the interface and file-location definitions there. No tests, reference documents, external links, or other files are referenced by the README.
- **Constraints and cautions:** The rationale says impact and frequency scoring creates a prioritized backlog, but it does not define the score range or formula; those details exist only in `SKILL.md`. It does not document security, sensitive-research handling, required tools, branch behavior, commit behavior, error handling, or missing-file behavior. Saving is described as a filesystem artifact operation only; no repository automation is promised.
- **Source basis:** Title and overview: lines 1–4. Rationale and prioritization approach: lines 6–10. Invocation and command list: lines 12–16. Artifact location and planning handoff: lines 18–24. Use cases: lines 26–30.
- **Status:** Filled

### `skills/aidd-pr/README.md`

- **What it is:** A concise overview of the `aidd-pr` skill: it creates or monitors provider pull requests, checks remote readiness, triages review comments, identifies threads already addressed in code, supports resolving those threads, and creates targeted `/aidd-fix` prompts for unresolved issues.
- **When to use or read it:** Use it after the source branch is published and PR policy requires or already has a PR, or when a PR has accumulated review threads and remaining feedback needs fixes. Read it for the user-facing commands and high-level workflow before consulting the operational instructions.
- **How to use it:** Invoke `/aidd-pr [PR URL]` to create or inspect a PR, verify the source branch is published, check terminal user-validation evidence and remote readiness, inspect cited source locations, classify concerns, request approval for addressed threads, and generate one `/aidd-fix` prompt per remaining issue. Invoke `/aidd-pr delegate` to dispatch generated prompts to sub-agents and perform the described provider actions.
- **Inputs and outputs:** Inputs are an optional PR URL or lifecycle/delegation mode, published branch state, configured provider access, ticket/evidence readiness, the PR's review threads, and the current files/lines cited by comments. Outputs are PR lifecycle/readiness state, an addressed-thread list for approval, GraphQL resolutions for approved addressed threads, and focused `/aidd-fix` delegation prompts aimed at the PR branch.
- **Relationships:** The overview depends on the `/aidd-fix` workflow and GitHub GraphQL review-thread APIs, and is operationally elaborated by `aidd-pr/SKILL.md`. `/aidd-fix` is referenced but no corresponding file exists in this directory; no reference or test files are present here.
- **Constraints and cautions:** PR creation and thread resolution have provider/branch side effects; an unpublished source branch blocks creation, and required user-validation plus remote evidence is part of readiness. The README does not spell out authentication, pagination, prompt-safety, or approval safeguards; those are defined in `SKILL.md`. Newly fixed threads remain open for reviewer verification.
- **Source basis:** Overview and purpose: lines 1–9. Commands and high-level inputs/actions: lines 11–23. Use cases: lines 25–29.
- **Status:** Filled

### `skills/aidd-react/README.md`

- **What it is:** A concise overview of the `aidd-react` skill. It presents the binding-component/presentation split, reactive subscriptions through `useObservableValues` from `@adobe/data-react`, and the intended action-callback naming convention.
- **When to use or read it:** Consult it when deciding whether `/aidd-react` applies: creating or modifying React components, working with binding components or presentations, using `useObservableValues`, or applying reactive binding and action-callback patterns.
- **How to use it:** Invoke `/aidd-react` for the listed React work. Apply its summarized workflow: keep reactive data binding in a binding component, keep rendering in a pure presentation, use `useDatabase` as the single service context, make one `useObservableValues` call, and name callbacks with `verbNoun` rather than event-style names such as `onClick` or `onToggle`.
- **Inputs and outputs:** The input is React component work or a question about the named patterns. The expected output is a component design or change following the binding/presentation split, with reactive values and action callbacks passed into the presentation.
- **Relationships:** Summarizes `aidd-react/SKILL.md`, which contains the detailed rules and examples. It names the `@adobe/data-react` dependency and the `/aidd-react` command; it has no external links. The detailed skill links to `aidd-structure/SKILL.md`, `aidd-service/SKILL.md`, and `aidd-observe/SKILL.md`; all three referenced files are present.
- **Constraints and cautions:** The overview is intentionally abbreviated, so it does not spell out the full prop, testing, export, hook-order, or slow-observable rules; use the detailed skill for those decisions. No security-sensitive guidance or branch/repository side effects are specified. The “one `useObservableValues` call” and presentation-testing claims are conventions summarized here, with the detailed skill qualifying the call as “most” components and tests as “when appropriate.”
- **Source basis:** `aidd-react/README.md:1-4` (identity and core pattern), `aidd-react/README.md:6-11` (separation rationale), `aidd-react/README.md:13-19` (usage rules), `aidd-react/README.md:21-25` (applicability).
- **Status:** Filled

### `skills/aidd-requirements/README.md`

- **What it is:** A concise overview of the `aidd-requirements` skill. It defines the purpose as writing functional requirements for user stories in the standardized `Given <situation>, should <job to do>` form, with emphasis on user outcomes rather than UI details. It explains that consistent phrasing makes requirements testable and reduces scope ambiguity.
- **When to use or read it:** Use it when drafting requirements for a new user story, specifying acceptance criteria, or checking whether existing requirements are complete and testable. Read it for the skill’s high-level rationale, invocation name, format, and intended use cases before applying the more detailed workflow in `SKILL.md`.
- **How to use it:** Invoke `/aidd-requirements` with a user story, then express each requirement as a situation followed by the job or outcome the user should accomplish. Keep the wording focused on user benefit and functional behavior; do not turn the requirement into a description of particular screens, controls, or interaction mechanics.
- **Inputs and outputs:** Input: a user story supplied to the `/aidd-requirements` skill. Output: a set of functional requirements, each using the `Given <situation>, should <job to do>` template. The README does not define schemas, files, persistence, or a testing command.
- **Relationships:** This README summarizes the workflow and constraints elaborated in `aidd-requirements/SKILL.md`. It names the `/aidd-requirements` invocation, but no slash-command definition is present in this directory, so its implementation and caller integration are not documented here. No external links or other file dependencies are specified.
- **Constraints and cautions:** Requirements must describe the user’s job and expected benefit, not specific UI elements or interactions. The format is intended to make behavior unambiguous and testable, but the README does not prescribe how to resolve conflicting stories or acceptance criteria. No security-sensitive guidance, repository or branch mutation, required tool, or external service is specified; invoking the skill is documentation of a workflow, not an instruction to execute repository changes.
- **Source basis:** `github 1/.github/skills/aidd-requirements/README.md:1-4` (skill metadata and summary); `:6-10` (rationale); `:12-22` (invocation, requirement template, and user-outcome focus); `:24-28` (use cases).
- **Status:** Filled

### `skills/aidd-review/README.md`

- **What it is:** The user-facing overview for aidd-review. It explains the
  deterministic static-analysis-first review, PR parity, architecture and
  hotspot checks, and approval-gated remediation of actionable findings.
- **When to use or read it:** Read when deciding whether a review request fits
  this skill. Use it for code changes, pull requests, completed features, or
  pre-merge quality and security checks.
- **How to use it:** Invoke `/aidd-review`; the workflow runs
  `aidd-static-analysis`, compares local settings with the PR pipeline,
  performs contextual review, and routes findings through scoped `aidd-fix`
  cycles.
- **Inputs and outputs:** The input is code changes, a pull request, or a
  completed feature. The output is normalized findings, parity status,
  remediation results, blockers, and readiness classification.
- **Relationships:** This README describes `aidd-review/SKILL.md` and connects
  to `aidd-static-analysis`, `aidd-evidence`, `aidd-fix`, and `/aidd-review`.
  No external links or additional referenced artifacts are present.
- **Constraints and cautions:** Review never edits source files directly,
  invents findings, hides baseline debt, or claims PR equivalence after a
  mismatch. Tool availability and evidence requirements remain explicit.
- **Source basis:** Title and scope: lines 1–4. Rationale for deterministic
  analysis and systematic review: lines 6–10. Invocation, remediation
  workflow, and boundaries: lines 12–28. Use cases: lines 30–34.
- **Status:** Filled

### `skills/aidd-riteway-ai/README.md`

- **What it is:** A concise public-facing overview of the `/aidd-riteway-ai` skill. It states the skill's purpose, slash-command usage, seven core workflow rules, and links readers to `SKILL.md` for the complete rule set and checklist.
- **When to use or read it:** Read when discovering whether this skill applies to a multi-step tool-calling eval or when needing a quick operational summary before opening the full instructions. Invoke `/aidd-riteway-ai` when the requested work is to write `riteway ai` prompt evals for such a skill.
- **How to use it:** Follow the numbered summary as a quick decision guide: split by step; mock tools for unit tests; assert calls rather than answers in step 1; carry prior output into later steps; use the E2E suffix without mocks for live APIs; isolate one fixture condition under 20 lines; and write non-duplicated requirement-based assertions. Consult the linked `SKILL.md` for examples and checklist details.
- **Inputs and outputs:** The README takes a user request for a multi-step tool-calling skill eval as its implicit input. It describes outputs of the workflow—step-specific `.sudo` files, optional isolated fixtures, and assertions—but does not define a file schema beyond the summary or execute any tooling.
- **Relationships:** It links locally to `./SKILL.md`, which is the authoritative detailed instruction file. Its slash-command name corresponds to the `Commands` registration in `SKILL.md`; the referenced `/aidd-tdd` and `/aidd-requirements` supporting skills are not discussed in this overview.
- **Constraints and cautions:** The E2E summary says live APIs and real credentials are required, so applying that path can have security and external-state implications. The README does not itself specify tool versions, mocking syntax, fixture directory details beyond the summary, or branch/repository operations; those details are in `SKILL.md`.
- **Source basis:** Purpose and command usage: lines 1–9. Seven workflow rules: lines 11–19. Link to the detailed instructions: line 21.
- **Status:** Filled

### `skills/aidd-rtc/README.md`

- **What it is:** Overview and usage guide for Reflective Thought Composition (RTC), a deliberate reasoning workflow intended to improve answers where edge cases, assumptions, alternatives, risks, or trade-offs matter. It explains the `/rtc` command, compact mode, and adjustable reasoning depth.
- **When to use or read it:** Consult when deciding whether RTC is appropriate for design decisions, reviews, planning, or other work where a slower reasoning loop can reduce rework. Choose compact mode when the reasoning feeds another step; choose depth control when communicating more or less detail is the goal.
- **How to use it:** Run `/rtc [prompt]` on a supplied prompt or current ticket context. Add `--compact` for dense, causality-focused intermediate reasoning followed by a full natural-language answer, `--depth N` for detail from 1–10, or both options together. The documented sequence clarifies the ask, generates alternatives, self-critiques, expands from other angles, evaluates/ranks options, and then responds.
- **Inputs and outputs:** Input is a prompt or current ticket context plus optional `--compact` and `--depth N` (`N` 1–10). Output is a clear user-facing response after the reflective sequence; compact mode also defines compressed intermediate reasoning intended to feed a later review or planning step.
- **Relationships:** This is the human-facing overview for the `aidd-rtc` skill and corresponds to the detailed instructions in `aidd-rtc/SKILL.md`. The two files document different command spellings: this README uses `/rtc`, while `SKILL.md` defines `/aidd-rtc`; callers should follow the command exposed by their runtime rather than assume they are interchangeable.
- **Constraints and cautions:** The README recommends concise, load-bearing reasoning, explicit causal links in reflection/evaluation, and postponing polish until the response stage; it rejects filler, hedging, consultant-style prose, and unsupported conclusions. `--compact` is described as internal reasoning, not direct user output; treat that as process guidance and do not disclose hidden chain-of-thought or sensitive ticket data. No external links, referenced files, required tools beyond a slash-command-capable agent, branch changes, repository writes, or other side effects are specified. No missing referenced files are identified.
- **Source basis:** `github 1/.github/skills/aidd-rtc/README.md:1-38` (overview, rationale, commands, options, mode selection, and pass/fail guidance).
- **Status:** Filled

### `skills/aidd-service/README.md`

- **What it is:** A short overview of the `aidd-service` skill. It explains that asynchronous services use unidirectional flow—data down through `Observe` and actions up as void calls—and that separating interfaces from implementations improves portability, inspectability, swappability, and predictability.
- **When to use or read it:** Read or invoke `/aidd-service` when creating front-end or back-end data services, defining their interfaces or implementations, or working with Observe patterns in the service layer. It is an entry-point summary rather than a complete implementation specification.
- **How to use it:** Use the summary to select the skill and the high-level service shape: front-end services expose `Observe<Data>` and void actions, while back-end services return `Promise<Data>` or `AsyncGenerator<Data>`. Apply the stated file and design rules—one file per function, types-only interfaces, and no classes—then consult the detailed skill instructions for the full layout and decision rules.
- **Inputs and outputs:** The input is a service-layer ticket matching the listed use cases. The output is a high-level design direction and the decision to invoke `/aidd-service`; the README does not define schemas, code templates, validation commands, tools, or generated files.
- **Relationships:** It summarizes the accompanying `aidd-service/SKILL.md` and names `Observe`, `Promise<Data>`, and `AsyncGenerator<Data>` as the key service concepts. It contains no links to external resources or other files, and it does not describe dependencies beyond those concepts.
- **Constraints and cautions:** The summary omits the detailed distinction between UI call boundaries, observable targets, factory functions, namespace exports, `Service` extension, and `AsyncDataService` assertions, so it should not replace the full skill for implementation. Its “no classes” and one-file-per-function rules are stated without their detailed rationale here. No security-sensitive guidance, external link, required tool, branch/repository side effect, or executable instruction appears.
- **Source basis:** `aidd-service/README.md:1-4` identifies the skill and its unidirectional data-flow summary. `aidd-service/README.md:6-10` states the interface/implementation separation benefits. `aidd-service/README.md:12-17` gives invocation guidance and front-end/back-end, file, interface, and class rules. `aidd-service/README.md:19-23` lists the situations for using the skill.
- **Status:** Filled

### `skills/aidd-stack/README.md`

- **What it is:** An overview of the `aidd-stack` skill. It defines the intended stack as Next.js, React/Redux, and Shadcn UI deployed on Vercel, and explains that the skill exists to prevent architectural drift through functional programming, container/presentation separation, Autodux, and TDD conventions.
- **When to use or read it:** Use it when implementing a full-stack feature on this stack or when selecting architecture patterns for a Next.js + React/Redux + Shadcn project. It directs source-code work to also use `/aidd-tdd`.
- **How to use it:** Invoke `/aidd-stack` for the stated feature and architecture decisions. Apply Redux through Autodux rather than Redux Toolkit, use Redux Saga for side effects, use Shadcn for components, and follow TDD for source changes; the README is a summary rather than an implementation procedure.
- **Inputs and outputs:** Inputs are a full-stack feature request and the project’s stack context. Outputs are stack and architecture-selection guidance; it does not specify generated files, commands, APIs, or runtime data.
- **Relationships:** It summarizes the detailed rules in `aidd-stack/SKILL.md` and references `/aidd-tdd` for the testing workflow. It names Next.js, React, Redux, Autodux, Redux Saga, Shadcn UI, and Vercel as the surrounding technologies.
- **Constraints and cautions:** The README requires TDD for implementation but does not define `/aidd-tdd`; no corresponding file is present in this inspected directory. It contains no external URLs, security controls, credential guidance, branch operations, repository mutations, or deployment procedure. “Full-stack” and “deployed on Vercel” describe scope and target, not proof that those services are configured.
- **Source basis:** `github 1/.github/skills/aidd-stack/README.md:1-4` identifies the skill and stack; `:6-10` gives its rationale and conventions; `:12-17` defines usage and related technologies; `:19-22` lists use cases.
- **Status:** Filled

### `skills/aidd-static-analysis/README.md`

- **What it is:** A concise overview of the deterministic static-analysis
  skill and its role beneath `aidd-review`.
- **When to use or read it:** Read when selecting standalone quality analysis
  or understanding how review runs and remediates exact analyzer findings.
- **How to use it:** Invoke `/aidd-static-analysis` for a diff or full scan;
  use `/review` for the complete review, parity check, architecture/churn
  checks, and approved `aidd-fix` remediation loop.
- **Inputs and outputs:** Inputs are repository configuration, applicable
  analyzers, planning scope, and changed paths. Outputs are exact findings and
  SARIF/JSON/Markdown evidence with baseline and parity metadata.
- **Relationships:** Summarizes `skills/aidd-static-analysis/SKILL.md` and
  connects to `aidd-review`, `aidd-evidence`, `aidd-fix`, and `aidd-config.yml`.
- **Constraints and cautions:** It does not install tools, auto-fix files,
  commit, push, create a PR, or merge; required unavailable tools and
  local/PR incompatibility block readiness.
- **Source basis:** `skills/aidd-static-analysis/README.md:1-end`.
- **Status:** Workflow updated

### `skills/aidd-structure/README.md`

- **What it is:** A concise overview of the `aidd-structure` skill. It explains that strict layering prevents circular imports and tangled modules, states the hierarchy `types ← services ← plugins ← components`, and summarizes when the slash command applies.
- **When to use or read it:** Read when deciding whether this skill applies to a ticket involving folders, file moves, imports, architecture planning, or dependency review. Use it as the quick-start summary before consulting the detailed `SKILL.md` rules.
- **How to use it:** Invoke `/aidd-structure` for the listed structural tickets, then apply the summarized dependency policy: components may use plugins (specifically observation and void actions) and types but not services, services may use services and types, and types may use only types. The README is descriptive guidance, not a command implementation or an automated check.
- **Inputs and outputs:** Inputs are a code-organization or import-dependency ticket. Outputs are a decision to load/apply the skill and a high-level layering rule set to guide the work; it does not itself edit files, run tools, or alter branches or repository state.
- **Relationships:** It is the human-facing summary of `aidd-structure/SKILL.md`; the hierarchy and core dependency rules correspond to that file’s detailed definitions. It does not link to external resources or name missing files.
- **Constraints and cautions:** The summary omits details found in `SKILL.md`, including nested component directories, immutable service data, permitted async patterns, interface-only external dependencies, and the optional ECS plugin context; consult the skill for those cases. No security-sensitive guidance, questionable commands, external links, or branch/repository side effects are stated.
- **Source basis:** Purpose and hierarchy: lines 1–10. Slash-command usage and dependency summary: lines 12–17. Applicability list: lines 19–23.
- **Status:** Filled

### `skills/aidd-sudolang-syntax/README.md`

- **What it is:** A short overview and invocation guide for the SudoLang syntax skill. It identifies SudoLang as pseudocode used in AIDD skill definitions, Autodux dux objects, and agent prompts, and lists interfaces, constraints, functions, template strings, pipes, and ternary expressions as key constructs.
- **When to use or read it:** Use it when deciding whether the syntax skill applies to work involving SudoLang, skill-definition pseudocode, or Autodux authoring. It is an orientation document rather than a complete grammar or implementation specification.
- **How to use it:** Invoke `/aidd-sudolang-syntax` to request a syntax reference, then use the listed construct forms as a quick checklist while reading or writing SudoLang. The examples establish that interface field types may be optional, constraints may be inline or block-based, functions have several declaration forms, strings interpolate with `$`, pipelines compose transformations, and `if (...) ... else ...` expresses a ternary.
- **Inputs and outputs:** Input is a SudoLang-reading or -authoring ticket. The documented output is a syntax reference/cheat sheet; the file defines no parser, executable command, generated artifact, or file modification.
- **Relationships:** It names the `aidd-sudolang-syntax` slash command and describes SudoLang's relationship to `SKILL.md` files, Autodux dux objects, and agent prompts. Those referenced artifact types are contextual and are not included in this directory; no external URL or additional local file is specified.
- **Constraints and cautions:** The overview is intentionally non-exhaustive and should not be treated as a full language specification. No required tools, security-sensitive operations, or branch/repository side effects are described; the slash-command invocation is documentation, not an instruction to execute during file review.
- **Source basis:** `README.md:1-4` (title and purpose), `README.md:6-9` (why SudoLang matters), `README.md:11-20` (invocation and construct examples), `README.md:22-25` (use cases).
- **Status:** Filled

### `skills/aidd-ticket-creator/README.md`

- **What it is:** A concise overview of phase/feature/ticket planning with scope, dependencies, risks, verification mappings, evidence, exit gates, and approval checkpoints.
- **When to use or read it:** Use it when planning a phase, defining a feature, creating focused tickets, or checking delivery readiness.
- **How to use it:** Start with `/ticket` inside an approved phase, define the feature and sequential tickets including their user-validation plans, use `/execute` for one approved ticket, present and record the post-implementation validation result, then use `/review` and `/evidence`, route through configured `/commit` -> `/push` -> `/aidd-pr` or local closeout, and update statuses as work completes.
- **Inputs and outputs:** Inputs are a request, planning context, repository configuration, and approval mode. Outputs are phase-aware feature/ticket contracts with user-validation plans, readiness state, evidence links, and synchronized open/closed completion moves.
- **Relationships:** Summarizes `aidd-ticket-creator/SKILL.md` and integrates with requirements, plan, execute, review, evidence, commit, push, PR, and the orchestrator.
- **Constraints and cautions:** Parent artifacts must be approved before child planning; tickets remain focused and independently verifiable, while documentation/infrastructure/migration work may use non-code evidence. Required user validation and configured delivery closeout or an approved not-applicable decision are needed before ticket closure.
- **Source basis:** `skills/aidd-ticket-creator/README.md:1-end`.
- **Status:** Workflow updated

### `skills/aidd-tdd/README.md`

- **What it is:** A concise overview of repository-appropriate TDD and verification, including protected baselines, regression evidence, real-system checks, and non-code evidence methods.
- **When to use or read it:** Read when implementation or verification work needs a test/evidence strategy.
- **How to use it:** Discover the repository's framework and commands, record the baseline, use failing-first TDD for code behavior, choose the strongest alternative evidence for non-code work, and record all results.
- **Inputs and outputs:** Inputs are a ticket contract, repository stack, commands, protected flows, and evidence policy. Outputs are a test/evidence plan, implementation verification, a copy/paste-ready user-validation handoff, coverage-gap records, and delivery-gate context for review/commit/push/PR routing.
- **Relationships:** Summarizes `aidd-tdd/SKILL.md` and integrates with `/execute`, `/aidd-fix`, `/user-test`, `/run-test`, and `/evidence`.
- **Constraints and cautions:** Do not assume npm, Vitest, Riteway, Playwright, pytest, or any runner; unavailable required capabilities are blocked or skipped with reason, never passed. Technical tests alone do not close a ticket; required user validation and configured delivery closeout must be recorded.
- **Source basis:** `skills/aidd-tdd/README.md:1-end`.
- **Status:** Workflow updated

### `skills/aidd-timing-safe-compare/README.md`

- **What it is:** The skill's short overview. It mandates hashing stored and candidate secrets with SHA3-256 before comparison, rejects direct raw-secret comparisons, and explains the claimed timing, prefix-structure, and length-oracle rationale.
- **When to use or read it:** Use this overview when reviewing or implementing comparisons of secrets, CSRF tokens, API keys, session tokens, or other secret values. It directs invocation through `/aidd-timing-safe-compare` and frames the rule as applicable to all secret comparisons.
- **How to use it:** Apply the stated workflow: hash both values with SHA3-256, compare the resulting digests, and add a code comment explaining why the hash-before-compare pattern is intentional so it is not changed back to `timingSafeEqual`. It does not provide code or a named helper implementation.
- **Inputs and outputs:** Input is a secret-comparison review or implementation. The expected artifact is a comparison that receives stored and candidate secrets, hashes both, and compares fixed-length SHA3-256 digests; the documentation also expects a rationale comment. No files, branches, or runtime outputs are modified by the README.
- **Relationships:** It is the overview for `aidd-timing-safe-compare/SKILL.md`, which contains the detailed review decision rules, and links conceptually to `references/vulnerabilities.md`. The repository's test file checks the detailed skill and external fixtures rather than this README directly.
- **Constraints and cautions:** The guidance is security-sensitive and unusually absolute: it claims standard timing-safe APIs have vulnerability classes and says never to compare raw secrets. Its claim that hashing and ordinary digest equality eliminate timing and length oracles should be treated as the skill's policy, not independently verified security advice; the README does not discuss hash availability, encoding, canonicalization, lifecycle, or residual implementation risks. No external links, missing references, required tools, or branch/repository side effects appear in this file.
- **Source basis:** `aidd-timing-safe-compare/README.md:1-26` (title, SHA3-256 policy, rationale, usage, and applicability).
- **Status:** Filled

### `skills/aidd-ui/README.md`

- **What it is:** A human-readable overview of the `aidd-ui` skill. It explains the skill’s purpose, the rationale that good UI should be intuitive, accessible, and visually appealing, and the main situations in which it applies.
- **When to use or read it:** Read when deciding whether `/aidd-ui` fits a ticket. It covers building or styling UI components, animations, motion design, transitions, accessibility, responsive layouts, and design-system decisions, with a stated preference for existing project Storybook components.
- **How to use it:** Invoke `/aidd-ui` for the listed UI and design tickets, then follow the detailed role and implementation guidance in `aidd-ui/SKILL.md`. The README is an orientation and selection aid; it does not provide component APIs, code samples, workflow phases, or test procedures.
- **Inputs and outputs:** The input is a ticket involving UI construction, styling, motion, accessibility, responsiveness, or design decisions. The output is selection of the `aidd-ui` skill and a high-level design focus; no structured inputs, generated files, commands, or output schema are defined.
- **Relationships:** This README documents and advertises `aidd-ui/SKILL.md`; its usage and “When to use” sections summarize the skill metadata and instructions. It references an existing project design system and Storybook components generically, without naming files or dependencies.
- **Constraints and cautions:** The overview establishes priorities—intuitive interaction, accessibility, visual quality, responsive layouts, and thoughtful motion—but leaves implementation details to the project and the companion skill file. No security-sensitive guidance, external links, required tools, missing referenced files, branch changes, or repository side effects are present.
- **Source basis:** `.github/skills/aidd-ui/README.md:1-4` (title and overview); `:6-10` (rationale); `:12-16` (usage and scope); `:18-22` (use cases).
- **Status:** Filled

### `skills/aidd-upskill/README.md`

- **What it is:** User-facing documentation for a skill that creates and reviews reusable AIDD instruction modules. It explains the motivation (avoid bloat and mixed concerns), gives `/aidd-upskill create [name]` and `/aidd-upskill review [target]`, and lists creation, review/refactoring, and abstraction-readiness use cases.
- **When to use or read it:** Read it when deciding whether this skill applies or when looking up its two command forms and high-level behavior. Use `create` for a new skill and `review` for an existing target or refactor assessment.
- **How to use it:** Supply a skill name to create a scaffold under `.github/skills/aidd-[name]/`; supply a target to review it against the function test, required sections, size thresholds, command separation, and README quality. Expect the review to report issues and a pass/fail verdict.
- **Inputs and outputs:** `create` takes `[name]` and produces a documented skill scaffold with frontmatter, sections, and layout. `review` takes `[target]` and produces findings plus an overall pass/fail result; the README itself has no stated direct file-writing behavior beyond describing the command.
- **Relationships:** It summarizes `SKILL.md` and the detailed pipelines in `references/process.md`; the named criteria and scaffold behavior are expanded there. It is the optional README described by the skill structure.
- **Constraints and cautions:** The command descriptions are high-level and do not specify validation commands or failure handling. No security-sensitive guidance, test assertions, external links, or branch/commit operations are documented.
- **Source basis:** `README.md:1-34`.
- **Status:** Filled

### `skills/aidd-user-testing/README.md`

- **What it is:** An overview of user-journey, functionality, baseline, and regression script generation with evidence metadata.
- **When to use or read it:** Read it when creating repeatable flow charters, usability studies, browser tests, or comparable UI evidence.
- **How to use it:** Use `/user-test` to generate human and agent scripts with setup, data, steps, expected visible/persisted effects, cleanup, failure paths, and configured artifact rules; use `/run-test` to execute the supported real system and prepare the user's closure validation.
- **Inputs and outputs:** Input is a journey and delivery context. Outputs are paired scripts, a post-implementation user-validation handoff, and evidence-ready reports, screenshots, responses, logs, blockers, and coverage gaps when executed.
- **Relationships:** It summarizes the more detailed workflow and templates in `aidd-user-testing/SKILL.md`, including the `/user-test` and `/run-test` interfaces. It depends conceptually on journey data under `plan/story-map/`; that directory is absent in the inspected repository, so the documented input location is not currently present.
- **Constraints and cautions:** Usability studies and required functionality tests are distinct; unavailable browser/integration capabilities are explicit gaps, screenshots are required only for configured UI changes, and a ticket remains open until required user validation is confirmed.
- **Source basis:** `skills/aidd-user-testing/README.md:1-end`.
- **Status:** Workflow updated

### `skills/clean-pr-branch/README.md`

- **What it is:** A concise overview of evidence-preserving cleanup that removes disposable AI scaffolding from Git tracking while retaining real code and protected files.
- **When to use or read it:** Read it before previewing cleanup, applying approved cleanup, or syncing approved real-file changes to an existing PR branch.
- **How to use it:** Run `/clean-pr-branch --dry-run` first; use explicit `--apply` only after reviewing evidence retention, branch, base, and provider policy. Use `--sync --dry-run` or `--sync --apply` for the configured existing PR branch.
- **Inputs and outputs:** Inputs are the current branch, configuration, evidence, and selected mode. Outputs are a no-side-effect report or a Git-tracking cleanup/sync operation; files remain on disk.
- **Relationships:** The README links to `./SKILL.md`, which defines `AI_SCAFFOLDING_PATHS` and is the authoritative implementation specification. Its command descriptions summarize the detailed process in `references/process.md`; the referenced SKILL and reference file are present in this directory. Any cleanup commit hands publication to `/push`.
- **Constraints and cautions:** Dry-run never mutates; apply requires evidence retention and explicit authorization; cleanup uses `git rm --cached` and never deletes source or evidence files from disk. It does not publish or open a PR as part of cleanup.
- **Source basis:** `skills/clean-pr-branch/README.md:1-end`.
- **Status:** Workflow updated

### `skills/create-vision/README.md`

- **What it is:** A concise overview of the skill: its purpose is to generate a repository-root `vision.md` from codebase discovery and five targeted questions. It explains why a vision document is a source of direction and lists the sections the generated document contains.
- **When to use or read it:** Read for a quick orientation before invoking the skill, to understand what `/create-vision` produces, or to locate the template. It is an overview rather than the detailed operating procedure; use `SKILL.md` for discovery order, interview rules, drafting logic, review gates, and write constraints.
- **How to use it:** Invoke `/create-vision`; the documented behavior is to inspect the codebase, ask five targeted questions, and populate a root `vision.md`. Use the listed output sections—Overview, Goals, Non-Goals, Key Constraints, Architectural Decisions, UX/DX Principles, and Success Criteria—to understand the expected artifact. Follow the link-like relative reference to `references/vision_template.md` when the scaffold is needed.
- **Inputs and outputs:** The stated inputs are the repository codebase and five targeted questions. The output is a repository-root `vision.md` containing the seven listed direction-setting sections. The README does not define question text, inference handling, review timing, or overwrite behavior; those details are supplied by `SKILL.md`.
- **Relationships:** It summarizes `create-vision/SKILL.md` and explicitly locates the template at `create-vision/references/vision_template.md`. Its `/create-vision` command and section list should remain consistent with those files. It has no external URLs, tests, tool implementation, or additional file dependencies.
- **Constraints and cautions:** The README correctly distinguishes vision from a general project description, but it is intentionally high-level and should not be treated as the complete workflow contract. It does not specify security, legal, branch, commit, or deployment operations. The output path is described as the repository root, so use the target repository context rather than this skill directory.
- **Source basis:** Purpose and rationale: lines 1–9. Command and root output: lines 11–17. Output sections: lines 19–29. Template location: lines 31–33.
- **Status:** Filled

### `skills/aidd-autodux/references/redux-example.md`

- **What it is:** A concrete SudoLang reference example for a Todo application. It models a Todo item with `id`, `text`, and `isComplete`; declares `createTodo`, `deleteTodo`, and `toggleComplete` action creators; and defines `TodoDux` with an array initial state, the `todo` slice, actions, selectors, state/dispatch mappings, and `TodoList` as the connected component name.
- **When to use or read it:** Read it when `/example` is requested or when a Dux author needs a concrete Todo-shaped pattern for item declarations, action payload/default syntax, array state, selectors, mappings, and connected component naming. It is illustrative source, not a complete generated reducer, store, component, or test implementation.
- **How to use it:** Use the shown SudoLang as a template: declare item fields, put deterministic and defaulted values in the action-creator parameter object, list action and selector names in the Dux, and add mapping/component metadata. The header shows the intended pipeline `TodoDux |> transpile(JavaScript)`; it recommends authoring in SudoLang first and transpiling when a detailed JavaScript specification is needed for AI agents.
- **Inputs and outputs:** The example takes no runtime input; its source-level inputs are Todo item fields and the `TodoDux` declarations. Its intended output is JavaScript produced by the Autodux transpilation pipeline, but no transpiled output, reducer behavior, selector definitions, or test assertions are included. `createId()` implies the external ID-generation tool named by `SKILL.md`.
- **Relationships:** `aidd-autodux/SKILL.md:136` links this file as the `/example` source, and `aidd-autodux/README.md` describes the same Dux-to-JavaScript workflow. The example relies on the skill’s `ActionObject` and transpilation conventions but does not itself restate those constraints. The referenced file exists; no additional local files or test dependencies are referenced here.
- **Constraints and cautions:** The prose is a recommendation/comment, not an executable command. `createId()` is external and is not imported or implemented in this file; the example also omits action payload schemas for `deleteTodo` and `toggleComplete`, and omits definitions for the listed selectors and mappings, so it is not self-contained JavaScript or a complete specification. The example says to use SudoLang for detailed AI-agent specifications, which may produce inferred rather than validated behavior. It has no security-sensitive operations or branch/repository side effects, and no external URL is present.
- **Source basis:** `aidd-autodux/references/redux-example.md:1-11` (title, transpilation example, and authoring recommendation); `:13-17` (Todo item fields); `:19-21` (actions and defaults); `:23-31` (TodoDux state, slice, actions, selectors, mappings, and component name).
- **Status:** Filled

### `skills/aidd-ecs/data-modeling.md`

- **What it is:** A focused reference for modeling ECS components, global resources, and archetypes. It intentionally excludes transactions, systems, and higher-level plugin structure, and uses a particle simulation plugin as its concrete example.
- **When to use or read it:** Read it while defining the `components`, `resources`, or `archetypes` sections of an ECS plugin, especially when deciding whether data is per-entity or global and which component set describes an entity kind. For full plugin authoring rules, use the linked `SKILL.md`.
- **How to use it:** Follow the example’s `Database.Plugin.create()` shape: import `Database` from `@adobe/data/ecs`, import typed schemas such as `Vec3`, `Vec4`, and `F32` from `@adobe/data/math`, assign schemas to per-entity components, declare a resource as `{ default: 9.8 as number }`, and define an archetype whose component list contains every required particle component. Apply the three guidelines: schema imports/type namespaces for components, only `{ default: value as Type }` for resources, and one complete component list per entity kind.
- **Inputs and outputs:** Inputs are component schema definitions or type-namespace shapes, resource default values with explicit types, and entity-kind component memberships. Outputs are a plugin data model containing `position`, `velocity`, `color`, and `mass` components, a global `gravity` resource, and a `Particle` archetype in the example. The document has no executable side effects.
- **Relationships:** The opening text links to `SKILL.md` for full plugin authoring, and `SKILL.md` links back to this reference for component/resource/archetype patterns. The example depends on the external packages `@adobe/data/ecs` and `@adobe/data/math`, including their `Database.Plugin`, `Vec3.schema`, `Vec4.schema`, and `F32.schema` APIs.
- **Constraints and cautions:** This reference is deliberately limited to data modeling and does not cover transactions, systems, or composition rules. Resources are constrained to the `{ default: value as Type }` form, and archetypes should include all required components; omitting one would make the model incomplete. The package APIs and type behavior are assumed rather than verified here. No tests, security-sensitive operations, external web links, or branch/repository side effects are specified.
- **Source basis:** Scope and link to full authoring: lines 1-3. Particle simulation imports and plugin model: lines 7-27. Modeling guidelines: lines 31-35.
- **Status:** Filled

### `skills/aidd-layout/references/design-tokens.md`

- **What it is:** A CSS token reference for layout components. It defines flex-direction classes (`.stack`, `.row`, `.cluster`), gap overrides, padding/inset classes, alignment helpers, and child sizing helpers (`.fill`, `.fit`).
- **When to use or read it:** Use when implementing a layout component that needs standard direction, spacing, inset, alignment, wrapping, or child sizing. Prefer these classes before writing component-specific layout CSS.
- **How to use it:** Provide application-level values for `--layout-gap`, `--layout-gutter`, and `--layout-padding`, then apply the classes to flex layout elements. Use `.stack` for vertical flow, `.row` for horizontal flow, `.cluster` for wrapping rows; override gaps with `.gap-gutter`, `.gap-padding`, or `.gap-none`; apply `.inset*` for padding; use alignment helpers and apply `.fill`/`.fit` to children as appropriate. The guidance suggests global `common.css`; Lit consumers should import the styles into a root element or shared base class.
- **Inputs and outputs:** Inputs are the desired flow direction, wrapping behavior, spacing scale, padding, alignment, and child growth behavior, plus defined custom-property values. Outputs are reusable CSS class selections and the resulting flexbox/padding behavior; the file does not define the custom-property values or a framework-specific import mechanism beyond the Lit suggestion.
- **Relationships:** It is referenced by `aidd-layout/SKILL.md` as the preferred layout-token source and links back to that file for terminal/layout rules. No `common.css` or Lit component is included in this skill directory; the consuming application must supply integration and variable definitions.
- **Constraints and cautions:** Classes assume a flex layout context where relevant, and the spacing variables must exist or CSS values will be unresolved. `.fill` and `.fit` affect children rather than establishing a parent layout. `.center` sets both axes, while `.spread` only sets main-axis distribution. The Lit-specific instruction is conditional and does not apply automatically to React or other stacks. No security-sensitive guidance, external links, or branch/repository side effects are present.
- **Source basis:** Purpose and integration requirements: lines 1–5. Direction classes: lines 9–31. Gap overrides: lines 33–48. Insets: lines 50–65. Alignment: lines 67–93. Child sizing: lines 95–105.
- **Status:** Filled

### `skills/aidd-review/references/review-example.md`

- **What it is:** A static example of a highly positive comprehensive review for a “Release Latest Tag Management” feature. It demonstrates the expected review-report shape and claims successful implementation of prerelease detection, latest-tag updates, release-it integration, and end-to-end testing.
- **When to use or read it:** Read as a formatting and content example when preparing a review that covers requirements, architecture, JavaScript standards, TDD, comments, performance, security, integration, metrics, findings, readiness, and methodology. It is not a test file and does not provide executable validation.
- **How to use it:** Model a report on its sections: establish phase/feature/ticket scope, assess file organization and separation of concerns, discuss naming and functional patterns, evaluate unit/integration/E2E tests and edge cases, inspect comments, performance, security, integration, and metrics, then give findings, an overall score, a production recommendation, and a methodology/date/status summary. The snippets illustrate `isPrerelease`, `shouldUpdateLatestTag`, `updateLatestTag`, async-pipe composition, structured error results, and an `after:release` hook. Treat all claims and snippets as illustrative source text rather than commands to execute.
- **Inputs and outputs:** The example assumes a release feature with a four-ticket plan, a `lib/` tree containing async-pipe, release-helper, latest-tag hook, and test files, and reported results such as 39/39 tests passing and zero lint errors. Its output is a sample “98/100,” production-ready review concluding “SHIP IT,” not a machine-readable result or test artifact. The example does not identify the repository, provide diff contents, or include commands for reproducing its assertions.
- **Relationships:** It exemplifies the review dimensions and methodology described by `aidd-review/SKILL.md`, especially requirements and phase/feature/ticket-plan adherence, TDD, security, architecture, and actionable assessment. It references release-it, Git operations, AsyncPipe, JavaScript/TDD guidance, and a hypothetical `lib/` layout, but no corresponding source files are included in this directory. The hook example would depend on Node/release-it and Git in the represented project.
- **Constraints and cautions:** The document reports exhaustive success without supplying evidence, so its 39-test, zero-lint, 100%-coverage, 98/100, and production-ready claims must not be treated as independently verified. It describes real Git operations, `git rev-parse`, tag updates, release hooks, and cleanup; executing analogous hooks can mutate tags or release state and affect the repository, so the sample must remain review evidence only. The security section asserts input sanitization and no injection risk but does not show implementation; those claims require direct verification. The JSON-labelled code block contains a JavaScript-style comment and an unexpanded `${version}`/`${name}` placeholder, so it is illustrative rather than guaranteed valid standalone JSON. No external links are present; no branches or commits are explicitly created in the example, but release/tag operations are repository side effects if implemented.
- **Source basis:** Feature scope and four tickets: lines 1–12. Structure and file layout: lines 16–33. JavaScript standards and examples: lines 37–66. TDD and reported tests: lines 70–99. Comment policy: lines 103–111. Performance and security claims: lines 115–127. Architecture, AsyncPipe, errors, and release-it hook: lines 131–169. Integration claims: lines 173–180. Metrics and qualitative assessment: lines 184–198. Findings and limitations claimed by the example: lines 202–219. Final score, readiness, recommendation, and conclusion: lines 223–246. Methodology and metadata: lines 250–264.
- **Status:** Filled

### `skills/aidd-timing-safe-compare/references/vulnerabilities.md`

- **What it is:** A reference catalog of alleged or reported timing-comparison vulnerabilities and historical timing-attack examples. It lists five implementation/API examples, four exploit narratives, and four external explanatory references.
- **When to use or read it:** Consult it when evaluating the threat rationale behind the skill's ban on direct or library-based comparisons, or when a review needs examples of timing, length-disclosure, early-exit, or implementation-error failure modes. It is background material, not an implementation recipe or test specification.
- **How to use it:** Use the named CVEs/issues/bugs and exploit summaries as leads for security research, then follow the linked Paragon Initiative, BearSSL, “A Lesson in Timing Attacks,” or Free60 pages for supporting detail. Treat the listed claims and historical figures as assertions in this document; no verification procedure, version scope, or remediation code is supplied.
- **Inputs and outputs:** Input is a security review requiring context about timing attacks. Output is contextual evidence: examples involving Python, Node.js, Go, OpenSSL, Java, Xbox 360, OAuth/OpenID, Google Keyczar, and Unix login, plus four URLs. It performs no code, file, branch, or repository changes.
- **Relationships:** `SKILL.md:19` links to this file to support its timing-safe comparison policy. The references are external and are not consumed by `timing-safe-compare.test.js`; the test instead inspects skill text and other repository paths.
- **Constraints and cautions:** The material is security-sensitive and includes claims that may be version-, platform-, or implementation-specific; it does not establish that every named issue applies to current releases or that SHA3-256 plus `===` universally removes side channels. All four references are external links requiring network access and independent source verification. No local files are referenced as missing, and there are no required tools or branch/repository side effects.
- **Source basis:** `aidd-timing-safe-compare/references/vulnerabilities.md:1-3` (title and scope); `:5-11` (example vulnerabilities); `:13-18` (known exploits); `:20-25` (external references).
- **Status:** Filled

### `skills/aidd-upskill/index.md`

- **What it is:** A directory index for `aidd-upskill`. It links to `references/index.md`, attempts to link to `scripts/index.md`, and identifies `SKILL.md` as the skill file with a one-line purpose statement.
- **When to use or read it:** Use it for quick navigation when locating the skill definition or reference index. It is useful for discovering the intended directory layout, but it is not an authoring or review workflow.
- **How to use it:** Follow the `references/index.md` link to enumerate reference documents and open `SKILL.md` for instructions. Treat the `scripts/index.md` link as stale: no `scripts/` directory or `scripts/index.md` file exists in this directory.
- **Inputs and outputs:** Input is the directory's file structure and documented contents. Output is navigation metadata and the stated purpose of `SKILL.md`; it performs no generation, validation, or repository mutation.
- **Relationships:** It points to `references/index.md` and `SKILL.md` within this skill. Its `scripts/index.md` reference is missing, while `README.md` is present but not listed.
- **Constraints and cautions:** The index is incomplete because it documents a nonexistent scripts index and omits `README.md`; do not infer that scripts are available. No tests are present here, and there are no security-sensitive instructions or branch/commit side effects.
- **Source basis:** `index.md:1-21`.
- **Status:** Filled

### `skills/aidd-upskill/references/index.md`

- **What it is:** A minimal index of the `references/` directory. It names `process.md` as “Skill Creation Process” and `types.md` as “Types & Interfaces,” but explicitly supplies no descriptions for either.
- **When to use or read it:** Use it to locate the two reference documents imported or implied by `SKILL.md`. Read the named file directly for workflow details or type/interface definitions; this index adds no operational guidance.
- **How to use it:** Follow the listed filenames, using the relative links to `process.md` and `types.md` only as the directory inventory. Do not treat “No description available” as evidence that the files are empty.
- **Inputs and outputs:** Input is the contents of the references directory. Output is a two-file navigation list; it performs no validation, testing, or writes.
- **Relationships:** `SKILL.md` imports both listed references, and `process.md` relies on `SkillPlan`, `RequiredSections`, `SizeMetrics`, and the Function Test described in `SKILL.md`/`types.md`. The links resolve to actual files.
- **Constraints and cautions:** Descriptions are intentionally absent, so purpose must be inferred from the target files. There are no tests, external links, security-sensitive guidance, or branch/repository side effects in this index.
- **Source basis:** `references/index.md:1-17`.
- **Status:** Filled

### `skills/aidd-upskill/references/process.md`

- **What it is:** The detailed process specification for `createSkill` and `reviewSkill`. Creation gathers related skills and web research, infers requirements, names the skill, builds and self-reviews a plan, drafts/writes `SKILL.md` and README, validates, and reports metrics. Review reads a target, runs the function/section/size/separation/README/deduplication checks, synthesizes findings, and reports a verdict table.
- **When to use or read it:** Read it when implementing either command or when determining the exact ordered stages, checks, artifacts, and report format. Use the creation pipeline for new skills and the review pipeline for an existing skill, including a quality gate before file generation.
- **How to use it:** For creation, search project skill metadata, research domain practices with web search, infer requirements without waiting for clarification, produce a `SkillPlan`, present and iteratively fix the plan, draft required frontmatter/sections, write files and optional directories, run `/validate-skill` (or `skills-ref validate`), and report `SizeMetrics`. For review, apply all six named checks, deduplicate repeated material, use compact `think()` synthesis, and render one result/detail row per check followed by an overall verdict.
- **Inputs and outputs:** `createSkill` accepts `userRequest` and outputs a named skill directory containing `SKILL.md`, `README.md`, and any needed optional directories, plus size metrics/warnings. `reviewSkill` accepts `target` and outputs per-check findings and an overall verdict; `writeSkill` and `writeReadme` have filesystem side effects.
- **Relationships:** The process uses `SkillName`, `SkillPlan`, `RequiredSections`, and `SizeMetrics` from `types.md`, and the five-question Function Test plus RTC `think()` dependency from `SKILL.md`/`aidd-please`. `README.md` summarizes this process without its implementation detail.
- **Constraints and cautions:** It instructs agents not to ask clarifying questions and instead proceed with explicit assumptions, which can reduce requirements certainty. It assumes project search, web search, `/validate-skill` or `skills-ref`, and RTC `think()` are available; if validation CLI access is unavailable it permits careful emulation. Web search introduces external-source dependence; no security review or security controls are specified. Creation writes files under `$skillHome/${skillName}/` and may create directories, but it does not direct branch creation, commits, pushes, or deployment.
- **Source basis:** `references/process.md:1-18`, `references/process.md:20-72`, `references/process.md:74-97`.
- **Status:** Filled

### `skills/aidd-upskill/references/types.md`

- **What it is:** A type/interface reference defining constraints for skill names and descriptions, the `SizeMetrics` and `SkillPlan` records, frontmatter fields, the `metadata.alwaysApply` extension, and the required body headings for generated skills.
- **When to use or read it:** Read it while planning or validating a skill so names, descriptions, plans, frontmatter, preload behavior, and required sections conform to the documented contract. Use it with `process.md` when constructing `SkillPlan` or interpreting validation metrics.
- **How to use it:** Validate `SkillName` as 1–64 lowercase alphanumeric/hyphen characters with no edge or consecutive hyphens, matching the parent directory, normally prefixed `aidd-`, and using a verb or role noun. Ensure `SkillDescription` states both behavior and activation timing; populate plan/frontmatter fields as needed; set `metadata.alwaysApply: "true"` only for broadly applicable skills; include a title and `## Steps` or `## Process` in every generated body.
- **Inputs and outputs:** Inputs are candidate names, descriptions, plans, frontmatter, preload decisions, and body sections. Outputs are schema-like acceptance criteria for `SkillPlan`, `Frontmatter`, `SizeMetrics`, and `RequiredSections`; it does not calculate metrics or mutate files.
- **Relationships:** `process.md` produces `SkillPlan`, writes frontmatter and required sections, and reports `SizeMetrics` using these definitions. `SKILL.md` references the same required structure, progressive disclosure, and validation concepts.
- **Constraints and cautions:** The `aidd-` prefix is required for shared ecosystem skills but exempt for project/org-specific skills; `compatibility` is limited to 1–500 characters and `allowed-tools` is an optional space-delimited field. Size thresholds are intentionally delegated to the current `validate-skill` implementation rather than specified here. `alwaysApply` can preload the full skill and should therefore be used sparingly; no security-sensitive behavior, tests, external links, or branch/commit side effects are defined.
- **Source basis:** `references/types.md:1-20`, `references/types.md:22-45`, `references/types.md:47-64`, `references/types.md:66-74`.
- **Status:** Filled

### `skills/clean-pr-branch/references/process.md`

- **What it is:** The detailed process reference for all four command modes. It specifies shell-based tracked-path detection, the ordered full cleanup pipeline, the pathspec-excluded sync pipeline, conventional-commit requirements, and dry-run behavior.
- **When to use or read it:** Read it when implementing or reviewing the skill’s actual decision logic and side effects. Use the first section to validate a cleanup without changing the repository, the full pipeline to create and commit a clean PR branch, the sync section to carry real feature-branch fixes onto an existing PR branch, and the final section to preview only the scoped sync diff.
- **How to use it:** For cleanup dry-run, derive the grep pattern from `AI_SCAFFOLDING_PATHS`, list tracked matches, report protected matches and the proposed branch, then stop. For full cleanup, detect first, create `pr/<name>` (defaulting by replacing `feature/`), remove matched paths from the index with `git rm -r --cached`, add missing scaffold entries under `# AI scaffolding — not for production`, restore a caught protected file from `main`, commit with a short conventional message, and run `git diff main --name-only`. For sync, build `:!` pathspec exclusions from the SKILL constant, diff `pr/<name>..feature/<name>`, stop if empty, check out the PR branch, pipe the scoped diff to `git apply --index`, commit a diff-specific conventional message, and verify. Sync dry-run performs only the scoped diff, empty check, and printed review output.
- **Inputs and outputs:** Inputs include `AI_SCAFFOLDING_PATHS` and `PROTECTED_FILES` from `SKILL.md`, the current/feature/PR branch names, Git repository state, `.gitignore`, and shell tools (`git`, `grep`, `printf`, `sed`). Cleanup outputs are tracked-path reports or a branch/index/ignore update plus commit and verification names. Sync outputs are a printed patch, an applied and indexed patch with commit, or `nothing to sync`; dry-run modes must not checkout, apply, commit, or otherwise alter the repository.
- **Relationships:** The reference explicitly imports its path constants from `SKILL.md` and must not re-enumerate them. `README.md` summarizes these flows. The full pipeline and sync both finish with a diff against `main`; protected-file restoration also relies on `main`.
- **Constraints and cautions:** The commands have material branch and repository side effects: checkout changes the active branch, `git rm --cached` changes tracking while retaining files on disk, `.gitignore` is staged, `git apply --index` changes both worktree/index, and commits persist history. The process assumes feature and PR branch naming, a usable `main`, clean/applicable Git state, and compatible pathspecs. The detection example uses shell interpolation and `grep`/`sed`; it escapes periods but does not document escaping every possible regular-expression metacharacter in path constants. The sync pseudocode labels its detector `detectSdkDiff` although the documented scope is all non-scaffolding real files, which is questionable terminology rather than a separate SDK restriction. The reference contains no external links or security-sensitive payloads, but restoring from `main` and applying a branch diff should be reviewed before execution; source text is documentation and is not itself an instruction to run here.
- **Source basis:** `github 1/.github/skills/clean-pr-branch/references/process.md:1-14` (cleanup dry-run); `:18-31` (full pipeline decision flow); `:33-57` (detection, branch creation, untracking, ignore update, restoration); `:59-84` (commit and verification); `:88-113` (sync scope, exclusions, preconditions, flow); `:115-132` (sync detection, checkout, apply); `:134-161` (sync commit and verification); `:165-173` (sync dry-run).
- **Status:** Filled

### `skills/create-vision/references/vision_template.md`

- **What it is:** A Markdown scaffold for the project vision document. It begins with a staleness/source-of-truth preamble, then provides headings and placeholder guidance for Overview, Goals, Non-Goals, Key Constraints, Architectural Decisions, User Experience Principles, and Success Criteria.
- **When to use or read it:** Read and populate it during the draft stage of `create-vision`, and preserve its opening preamble in the final repository-root `vision.md`. It is also useful as the authoritative section shape when reviewing whether a draft covers direction, boundaries, decisions, user-facing principles, and measurable outcomes.
- **How to use it:** Replace the prose placeholders with project-specific, user-validated content. State goals and non-goals as intended outcomes or explicit exclusions, record technical/business/legal/organisational constraints, and use the two-column Architectural Decisions table for decisions paired with rationales. Define success with measurable outcomes rather than activities, and write UX principles from the user’s perspective. The file itself contains no executable commands.
- **Inputs and outputs:** Inputs are discovery facts and interview answers supplied by `SKILL.md`. The output is a completed Markdown vision document with the template’s headings and preamble; the template alone does not write a file or validate content. Its placeholders are incomplete until replaced.
- **Relationships:** `SKILL.md` imports this reference and requires its preamble and section structure. `README.md` identifies it as the skill’s template. No other files, external links, tests, or tool dependencies are referenced.
- **Constraints and cautions:** The example text is scaffolding, not project policy: do not leave example goals, constraints, or decisions in a final document. The template does not itself enforce the skill’s constraint test, user review, TBD handling, contradiction handling, or overwrite guard; those rules remain in `SKILL.md`. The GDPR example is illustrative only and is not legal guidance. It specifies no branch, commit, deployment, or other repository side effects.
- **Source basis:** Source-of-truth and staleness preamble: lines 1–6. Overview and Goals placeholders: lines 8–15. Non-Goals and Key Constraints: lines 17–25. Architectural Decisions table: lines 27–31. User Experience Principles: lines 33–35. Success Criteria guidance: lines 37–39.
- **Status:** Filled

### `skills/aidd-riteway-ai/riteway-ai.test.js`

- **What it is:** A Vitest test module that verifies the `aidd-riteway-ai` skill's source metadata, required instructional phrases, command integration, and discovery integration. It uses `fs-extra` for filesystem reads, `riteway/vitest` assertions, Vitest `describe`/`test`, and `parseFrontmatter` from `../../../lib/index-generator.js`.
- **When to use or read it:** Read or run it when changing this skill, its frontmatter, the `/aidd-riteway-ai` command, or the `/aidd-please` discovery listing. It is a structural/content regression test, not a runner for `.sudo` evaluations or a test of actual tool calls, fixture behavior, live APIs, or generated eval quality.
- **How to use it:** The first describe block locates `SKILL.md`, checks existence, parses frontmatter, and asserts the name, string description, and `Use when` phrase. Further tests read `SKILL.md` and check for `/aidd-tdd`, `/aidd-requirements`, per-step `.sudo` guidance, mocks, step-1 wording, previous-step wording, the E2E suffix, and fixture guidance. The command block checks for `.github/commands/aidd-riteway-ai.md`, then reads it for the skill path and `/aidd-please`; the integration block reads `../aidd-please/SKILL.md` and checks `/aidd-riteway-ai`.
- **Inputs and outputs:** Inputs are the three referenced source files, their text, the parsed frontmatter object, and filesystem availability. Outputs are pass/fail assertions through Vitest; no files, branches, repositories, APIs, or generated evals are modified.
- **Relationships:** It tests `aidd-riteway-ai/SKILL.md`, expects a sibling command at `../../commands/aidd-riteway-ai.md`, and expects the neighboring `aidd-please/SKILL.md`. It imports the repository's frontmatter parser and external test libraries (`fs-extra`, `riteway`, and `vitest`).
- **Constraints and cautions:** Assertions mostly use substring checks, so they verify that guidance words or paths occur, not that the rules are complete, internally consistent, or executable. The command-file existence assertion currently targets a path that is absent in the inspected repository (`.github/commands/aidd-riteway-ai.md`), so that test will fail unless the file is supplied elsewhere or the repository layout changes. The test has no branch or repository side effects and does not exercise the security risk of E2E credentials/live APIs described by the skill.
- **Source basis:** Imports and test setup: lines 1–11. Frontmatter and skill-content checks: lines 12–140. Command existence/content checks: lines 143–187. `aidd-please` integration check: lines 190–203.
- **Status:** Filled

### `skills/aidd-timing-safe-compare/timing-safe-compare.test.js`

- **What it is:** A Vitest test module using Node path/URL utilities, `fs-extra`, and `riteway/vitest` assertions. It defines three asynchronous tests that validate documentation wording and a fixture's hash-before-compare pattern by reading files as text.
- **When to use or read it:** Use it when changing this skill, the related `aidd-review` skill, or the referenced AI-evaluation fixture, to understand the repository's text-contract expectations. It is limited to static content checks; it does not execute comparison code or prove timing behavior.
- **How to use it:** Run it with the repository's existing Vitest setup and dependencies. The first test reads `./SKILL.md` and requires a literal Node-style `createHash("sha3-256")`/template-literal form plus “named helper”, “do not flag”, and “major”. The second reads `../aidd-review/SKILL.md` and requires `SHA3-256`, `digest`, `aidd-timing-safe-compare`, and “do not flag”. The third reads `../../../ai-evals/aidd-review/fixtures/utils.js` and requires `createHash("sha3-256")`, `===`, and `hashSecret`.
- **Inputs and outputs:** Inputs are the three referenced text files and the regex/string predicates. Output is Vitest/Riteway pass/fail assertions; missing files cause read failures rather than a meaningful assertion result. The test has no write, branch, or repository side effects.
- **Relationships:** It directly tests `SKILL.md` and `../aidd-review/SKILL.md`; it indirectly expects `ai-evals/aidd-review/fixtures/utils.js`. The related `aidd-review/SKILL.md` exists, but the resolved repository-root fixture path is missing in the inspected tree, so the third test cannot currently pass unless that fixture is restored or the path is corrected. It does not inspect `README.md` or `references/vulnerabilities.md`.
- **Constraints and cautions:** Required tooling/dependencies are Node.js with ESM support, Vitest, `fs-extra`, and `riteway/vitest`, plus the repository's test configuration. Because checks are regex/string based, they can pass on wording without validating semantics, cryptographic correctness, input encoding, or actual timing resistance; the first assertion is also inconsistent with the current `SKILL.md`, which names SHA3-256 but not `createHash(...)`. No external links or security side effects are present in the test itself.
- **Source basis:** `aidd-timing-safe-compare/timing-safe-compare.test.js:1-7` (imports and module directory setup); `:9-34` (SKILL.md wording assertions); `:36-51` (aidd-review cross-skill assertion); `:53-69` (AI-eval fixture assertion and required markers).
- **Status:** Filled

### `skills/aidd-user-testing/user-testing.test.js`

- **What it is:** A Vitest test module that checks the presence and basic integration of the user-testing skill and its surrounding documentation/commands. It imports filesystem helpers, `riteway/vitest` assertions, Vitest's `describe`/`test`, and a frontmatter parser from `../../../lib/index-generator.js`.
- **When to use or read it:** Run or inspect it when changing this skill's metadata, required templates, command files, documentation, or root README integration. It is a structural smoke test, not an end-to-end user-testing runner: it never generates a script, launches a browser, evaluates screenshots, or checks journey behavior.
- **How to use it:** Vitest loads the module, computes the test directory from `import.meta.url`, and executes grouped assertions. The first group checks that `SKILL.md` exists, parses its frontmatter, requires a string description, and requires the name `aidd-user-testing`; the next checks literal presence of `HumanScript:template` and `AgentScript:template`. Further groups check existence and skill references for two command files, existence of `docs/user-testing.md`, and root README inclusion of `/user-test` plus `docs/user-testing.md`.
- **Inputs and outputs:** Inputs are the repository files at the relative paths used in the tests and the parser module. Successful execution produces assertion results through Vitest; failures identify missing files, missing frontmatter fields, or absent literal strings. Required runtime/dependencies are Node.js ESM support, Vitest, `fs-extra`, `riteway/vitest`, and the repository's `parseFrontmatter`; the parser path is missing in the inspected repository, so the suite cannot load as written. The command files, docs file, and root README paths checked by this test are also missing in the inspected repository.
- **Relationships:** Tests `SKILL.md` directly and expects the command/documentation/README integration described by the README and SKILL. Its relative imports and path assertions couple it to a repository layout with `lib/index-generator.js`, `.github/commands/`, `docs/`, and a root `README.md`; these dependencies are outside this skill directory and are not supplied here.
- **Constraints and cautions:** Assertions use exact literal checks and existence checks, so they do not validate correctness of templates, inferred persona behavior, retry policy, stochastic execution, screenshot capture, report contents, or external-link safety. The test description says “ai/skills” and “ai/commands” although the actual file path is under `.github/skills`; this is wording only but may confuse maintenance. It performs only reads and has no browser, network, branch, commit, or repository mutation side effects.
- **Source basis:** `user-testing.test.js:1-9` (imports and path setup); `user-testing.test.js:11-60` (frontmatter and template checks); `user-testing.test.js:62-112` (command existence/reference checks); `user-testing.test.js:114-126` (documentation existence check); `user-testing.test.js:128-148` (root README integration checks).
- **Status:** Filled

### `skills/aidd-agent-orchestrator/SKILL.md`

- **What it is:** The delivery-state orchestrator for routing lifecycle and domain work while preserving phase, feature, ticket, scope, gates, approvals, and evidence.
- **When to use or read it:** Use it when a request needs lifecycle routing, multiple domains, safe delegation, or provider-aware delivery operations.
- **How to use it:** Initialize context from `aidd-config.yml`, planning
  artifacts in both lifecycle directories, repository evidence, and the user
  request; route by lifecycle and `VersionControlState`; load domain skills
  progressively; aggregate delegated evidence; transition only through
  configured gates while keeping status and folder in agreement; and return
  one context-aware `Next step`, `Skill`, and `Why` handoff.
- **Inputs and outputs:** Inputs are the request, delivery context, active planning artifacts, selected lifecycle/domain skills, and provider policy. Outputs are routed work, aggregated evidence, blockers, a lifecycle state, and one authoritative next action.
- **Relationships:** Coordinates `aidd-please`, product, requirements, ticket, TDD,
  evidence, static analysis, review, PR, delegation, commit, cleanup, and
  relevant domain skills.
- **Constraints and cautions:** Missing gate-affecting context or required
  user-validation evidence is a blocker. Review invokes static analysis before
  readiness; delivery routing is ordered review/remediation -> commit -> push ->
  PR/local closeout, with remote-only checks deferred until publication. Every
  routed response must recommend the first permitted next action and its owning
  skill; it must not invent work or list competing commands.
  Delegated agents cannot declare readiness, modify shared artifacts without
  ownership, or conceal baseline failures; record moves preserve stable IDs,
  indexes, and path history; only the integration owner performs shared commit,
  push, PR, or merge operations unless explicitly assigned; provider
  credentials and commands remain behind adapters.
- **Source basis:** `skills/aidd-agent-orchestrator/SKILL.md:1-end`.
- **Status:** Workflow updated

### `skills/aidd-autodux/SKILL.md`

- **What it is:** The operational skill specification for acting as a senior JavaScript/React/Redux/Next.js engineer and building Redux state handling with Autodux. It defines the `help`, `transpile`, `ActionObject`, `ActionCreator`, `Selector`, reducer, mapping, test, test-case, Dux, and Autodux command/inference rules. It also defines generated artifacts: a dux module, store, connected container, presentation component, and test file.
- **When to use or read it:** Use it for Redux state work that needs a SudoLang Dux, generated action creators/reducer/selectors, React-Redux connection mappings, transpiled JavaScript, or inferred requirements and tests. Read it before authoring or transpiling so the Dux includes `initialState`, `slice`, `actions`, and `selectors`, and before testing so reducer setup, selector usage, API boundaries, and isolation rules are followed.
- **How to use it:** Start from a Dux containing the required state-management declarations; infer requirements, test cases, `mapStateToProps`, `mapDispatchToProps`, a connected component name, tools, and output files as needed. Use `/help` for a SudoLang-format explanation and command list, `/example` for the linked Todo source, `/save` for the Dux, `/test cases` for `TestCases [ ... ]`, `/add [prop] [value]` to update the Dux, and `/transpile` (equivalent to `Dux |> transpile(JavaScript)`) for separate JavaScript blocks for every declared file. Generated reducers default state and destructured actions, use action-creator types in cases, selectors read through the slice, and `withSlice` wraps reducers when selector tests need the sliced state shape.
- **Inputs and outputs:** Inputs include a SudoLang Dux (`initialState`, `slice`, `actions`, `selectors`), optional natural-language requirements, connected component name, inferred mappings, and optional tools such as `{createId} from @paralleldrive/cuid2`. Outputs include a saved/updated SudoLang Dux, natural-language-derived test cases, and transpiled JavaScript files for `dux`, `store`, `container`, `component`, and `test`; the dux file contains reducer/actions/selectors, the store builds the root reducer/store, and the container/component split connected and presentation concerns.
- **Relationships:** `SKILL.md` is the authoritative instruction file summarized by `aidd-autodux/README.md`. `/example` points to the existing `aidd-autodux/references/redux-example.md`, which demonstrates the Dux shape and Todo actions. The skill requires JavaScript arrow-function output and names Riteway for tests, while `@paralleldrive/cuid2` is an external package used for `createId`; no local implementation of either tool is included in this directory.
- **Constraints and cautions:** Generated code must be concise, readable, functional, use arrow functions and implicit returns where possible, avoid `return` in action creators, default payloads to `{}`, and inline action types as `"$slice/$actionName"` rather than constants. Non-deterministic defaults belong in parameter positions. Selectors must use `state[slice]`; reducers must use `actionCreator().type`; `mapDispatchToProps` must use object-literal form; tests must use selectors, initialize through reducer/action creators, treat creators/selectors as the reducer API, and isolate cases without shared setup. Do not use Redux Toolkit or other Redux-specific helper libraries. Filenames must be lowercase kebab-case, slice-based, use `-component`, `-dux`, and `-container` extensions where applicable, and end in `.js`; comments are reserved for multi-step state updates. The “infer” and SudoLang notation is AI-interpreted rather than an executable specification, and no concrete transpiler, package manifest, or test command is supplied. The external `@paralleldrive/cuid2` dependency and generated IDs/timestamps can affect determinism. The instruction to avoid AI disclaimers is presentation guidance, not application logic. `/add` and `/save` describe in-memory/content changes only; no git branch, commit, repository, deployment, or other external side effects are specified.
- **Source basis:** `aidd-autodux/SKILL.md:1-8` (metadata and role); `:10-25` (help/transpile); `:28-65` (action objects, creators, slice wrapper, selectors, reducer, mappings); `:67-90` (5 Questions, RITE, and test rules); `:92-103` (requirements, test-case generation, transpilation); `:105-123` (Dux fields, inferred outputs, files, and external tool); `:125-140` (Autodux constraints and slash commands).
- **Status:** Filled

### `skills/aidd-churn/SKILL.md`

- **What it is:** The operational instruction set for hotspot analysis. It defines a three-stage pipeline: collect ranked hotspot data, identify the dominant risk signal for each file, and produce file-specific refactoring or review recommendations. It also defines a standalone mode and a pull-request-review mode.
- **When to use or read it:** Use before reviewing a pull request, splitting a large diff, refactoring, or identifying high-risk code. Read it when recommendations must be evidence-based: the CLI must run first, named files and driving metrics must be reported, and each recommendation must include a concrete strategy.
- **How to use it:** Run the collection step with defaults of 90 days, top 20 results, and minimum 50 LoC; use `--days`, `--top`, and `--min-loc` to change those values. In PR-review context, also run `npx aidd churn --json` and cross-reference returned paths with the diff. Interpret high LoC as surface-area risk, high churn as instability, high Cx as branch/comprehension risk, and low density as likely repetition. For each hotspot, state its path and score, explain the dominant metric(s), propose extraction/decomposition/complexity-reduction/shared-helper work as appropriate, and estimate the metric most likely to fall. If any file has Cx > 9, LoC > 400, or density < 35%, check whether the current diff caused the threshold crossing and, when a refactor lowers `LoC × churn × Cx` by more than 15%, recommend it before merge.
- **Inputs and outputs:** Inputs include a git repository with history, Node.js 16+ and `npx`, CLI options, the hotspot report, and—when reviewing a PR—the current diff. Intermediate artifacts are `hotspotReport`, `analysis`, and `recommendations`; the user-facing output is friendly Markdown describing scores, signals, concrete strategies, estimated metric effects, and PR-risk matches. No files are generated by the documented workflow.
- **Relationships:** The skill explicitly depends on the colocated `aidd-churn/README.md` for metric definitions, score interpretation, and the claimed formula. It invokes the external `aidd` package via `npx` and exposes the `/aidd-churn` command. Its `analyze = collectHotspots |> interpretResults |> recommend` pipeline connects collection, interpretation, and recommendation stages.
- **Constraints and cautions:** Churn is an optional/configurable risk signal, not a substitute for functional evidence or a universal blocker. The CLI must run before hotspot claims; unavailable tooling is reported as a coverage gap. The skill contains no instructions to edit files, commit, create branches, or alter repositories.
- **Source basis:** `SKILL.md:1-9` (metadata, compatibility, and required environment); `SKILL.md:11-21` (role and competencies); `SKILL.md:23-30` (mandatory evidence, thresholds, and refactor rule); `SKILL.md:32-39` (collection and PR JSON workflow); `SKILL.md:41-56` (signal interpretation); `SKILL.md:58-87` (recommendation and PR-review logic); `SKILL.md:89-104` (CLI examples and `/aidd-churn` command).
- **Status:** Workflow updated

### `skills/aidd-commit/SKILL.md`

- **What it is:** The authoritative local-commit workflow for reviewed, validated, staged ticket scope.
- **When to use or read it:** Use after technical checks, required user validation, and review are terminal, before publishing or opening a PR.
- **How to use it:** Resolve configuration, active ticket, evidence, branch policy, and staged scope; refuse unstaged or mixed scope; apply the configured commit format and trailers; append commit evidence; and return the next push/PR/local-closeout handoff.
- **Inputs and outputs:** Inputs are staged Git changes, delivery evidence, branch state, approval, and commit policy. Outputs are a local commit or an explicit blocker with evidence and `NextAction`.
- **Relationships:** Coordinates `aidd-evidence`, `aidd-review`, `aidd-push`, `aidd-pr`, and the orchestrator; `/commit` is its entrypoint.
- **Constraints and cautions:** It never stages, pushes, creates a PR, merges, resets, or rewrites history. Required user validation, technical evidence, review, clean scope, and configured approval must be present before committing.
- **Source basis:** `skills/aidd-commit/SKILL.md:1-end`.
- **Status:** Workflow updated

### `skills/aidd-push/SKILL.md`

- **What it is:** The authoritative branch-publication workflow for pushing an approved local commit to a configured remote.
- **When to use or read it:** Use after `/commit` when the branch has an unpublished or upstream-ahead local commit and policy allows publication.
- **How to use it:** Resolve branch/upstream/remote/provider policy, verify commit and evidence state, refuse unsafe or rewritten history, push only the approved ref, append push evidence, verify remote state, and route to PR or configured local closeout.
- **Inputs and outputs:** Inputs are a committed local branch, upstream/remote state, delivery evidence, approval, and provider capability. Outputs are a push result, remote evidence, or an explicit blocker with `NextAction`.
- **Relationships:** Coordinates `aidd-commit`, `aidd-evidence`, `aidd-pr`, provider adapters, and the orchestrator; `/push` is its entrypoint.
- **Constraints and cautions:** It never stages, commits, resets, stashes, force-pushes, creates a PR, or merges. Missing upstream, remote capability, approval, evidence, or safe branch state blocks publication.
- **Source basis:** `skills/aidd-push/SKILL.md:1-end`.
- **Status:** Workflow updated

### `skills/aidd-ecs/SKILL.md`

- **What it is:** The executable skill specification for authoring `Database.Plugin` objects from `@adobe/data/ecs`. It defines runtime-sensitive property ordering, plugin composition, each plugin property’s data-flow role, naming conventions, type utilities, and a final checklist.
- **When to use or read it:** Use when `@adobe/data/ecs` is imported or when creating or changing plugins, ECS components, resources, archetypes, computed observables, transactions, actions, services, or systems. Read the relevant property section before editing that part of a plugin, and use the checklist before completing the change.
- **How to use it:** Create plugins with `Database.Plugin.create()`, ordering optional properties as `extends`, `services`, `components`, `resources`, `archetypes`, `computed`, `transactions`, `actions`, `systems`. Use `extends` for one parent and `Database.Plugin.combine()` for multiple peers or final app composition; model schemas and global resources in their sections, keep mutations in synchronous transactions, keep side-effect functions in actions, and initialize or tick behavior through systems. Name plugin files, exports, and systems according to the listed conventions, and export `ToDatabase`/`ToStore` types when consumers need them.
- **Inputs and outputs:** Inputs are plugin definitions, parent or peer plugins, ECS schemas, resource defaults and types, service factories, observable factories, transaction payloads, action arguments, and system scheduling constraints. Outputs are composed plugins, typed database/store aliases, singleton services, ECS data definitions, observables, mutations, general actions, and synchronous initializer or per-frame system functions.
- **Relationships:** It links to `aidd-ecs/data-modeling.md` for component, resource, and archetype examples and points consumers to `Database.Plugin` APIs, `Observe`, `Entity`, and `Database.observeSelectDeep`. Extended services initialize before child services, enabling child factories to use inherited `db.services`; the composition examples establish the parent/peer relationships used by later plugins.
- **Constraints and cautions:** Property order is enforced at runtime and an incorrect order throws. Non-persistable component values require `transient: true`; resources need `as Type` (or the documented deferred `null as unknown as Type`) to avoid literal typing. UI callers must not consume action return values, and each action should call at most one transaction because multiple calls are stated to corrupt undo/redo. Systems run synchronously when `database.extend(plugin)` runs, and `before`/`after` are hard ordering constraints while `during` is only a soft same-tier preference. The guidance is documentation, not an instruction to execute; no branch or repository side effects, security-sensitive operations, tests, or external URLs are specified. The examples assume the referenced ECS/math/service APIs and symbols exist; `data-modeling.md` is present.
- **Source basis:** Front matter and scope: lines 1-8. Property order and runtime constraint: 10-30. Composition: 34-71. Property details: 75-230. Naming and type utilities: 234-252. Authoring checklist and related resource: 256-272.
- **Status:** Filled

### `skills/aidd-error-causes/SKILL.md`

- **What it is:** The executable skill instruction document for enforcing structured error handling with `error-causes` in JavaScript/TypeScript. It defines the import, replaces plain throws with `createError`, specifies required metadata, shows how to preserve causes and validate factory inputs, gives a test pattern, and defines name-based routing with `errorCauses`; seven numbered rules summarize the policy.
- **When to use or read it:** Load it for any JavaScript/TypeScript ticket involving thrown or caught errors, error-type definitions, factory-parameter validation, error tests, or API middleware/handler routing. Apply it at the point where an error is created, wrapped, asserted, or dispatched, rather than treating it as a general JavaScript style guide.
- **How to use it:** Import `createError` from `error-causes` and construct errors with `name` and `message`; add `code` for programmatic handling and custom properties for relevant context. When rethrowing from a `catch`, put the caught value in `cause`. In factories, validate required parameters at creation time and throw a `ValidationError` with a stable code. For APIs with several error types, pass a definition map to `errorCauses`, use the returned definitions with `createError`, and pass a map of name-specific callbacks to the returned handler for automatic routing. Tests should capture the thrown value and assert cause presence plus expected cause name/code.
- **Inputs and outputs:** Inputs include the `error-causes` package, error metadata, caught exceptions, factory arguments such as `requiredParam`, API error-definition maps, and handler callbacks. Outputs include structured errors carrying `name`, `message`, optional `code`, `cause`, and custom context; factory functions that either throw validation errors or return middleware; and routed handler execution based on error names. The test example assumes an `assert` helper and a throwing `functionThatThrows`, neither of which is defined here.
- **Relationships:** This is the detailed counterpart to `aidd-error-causes/README.md`, expanding its brief examples into implementation and test rules. It references only the external `error-causes` import and illustrative `assert`, `someOperation`, `functionThatThrows`, `someAsyncCall`, and `redirect` symbols; no local source, reference, or test files are supplied in this directory.
- **Constraints and cautions:** The document is guidance to apply to source code, not a command script; its examples must be adapted to the project’s runtime and error-handler API. It presents `code` as optional generally but expects stable codes where callers branch programmatically. The test assertions are internally assumption-heavy: they require the thrown value to be a wrapper whose `cause` itself has the expected `name` and `code`, and the first assertion still uses `instanceof Error` despite the skill’s cross-realm rationale against relying on `instanceof` for matching. The examples do not test message, custom properties, routing fallbacks, non-`Error` causes, async rejection handling, or factory behavior. The stated `errorCauses` callback map includes `redirect('/login')`, which may have application-specific security/navigation implications and is not defined here. No branch or repository mutations are instructed, and no security-sensitive implementation details or external links are provided; installing or upgrading the external package would be a dependency change outside this file.
- **Source basis:** - `github 1/.github/skills/aidd-error-causes/SKILL.md:1-8` — metadata and overall mandate. - `github 1/.github/skills/aidd-error-causes/SKILL.md:10-22` — rationale and import. - `github 1/.github/skills/aidd-error-causes/SKILL.md:24-52` — plain-error replacement and metadata rules. - `github 1/.github/skills/aidd-error-causes/SKILL.md:54-89` — cause wrapping and factory validation. - `github 1/.github/skills/aidd-error-causes/SKILL.md:91-123` — test assertions and their assumed helpers/shape. - `github 1/.github/skills/aidd-error-causes/SKILL.md:125-160` — multi-error definition and routed-handler pattern. - `github 1/.github/skills/aidd-error-causes/SKILL.md:162-170` — summarized rules.
- **Status:** Filled

### `skills/aidd-fix/SKILL.md`

- **What it is:** The scoped bug-fix and review-feedback workflow with baseline, regression/non-code evidence, verification, review, and configured delivery gates.
- **When to use or read it:** Use it for a reported bug, failing test, or review finding that requires a controlled change.
- **How to use it:** Read the active contract and configuration, establish the protected baseline, document the requirement, choose the strongest evidence method, implement within scope, verify, review, present the user-validation handoff, record the terminal user result, and append evidence.
- **Inputs and outputs:** Inputs are a bug report/review finding, active phase/feature/ticket, repository commands, and gate policy. Outputs are a verified fix, evidence record, blockers, or an explicit no-change finding.
- **Relationships:** Coordinates `aidd-tdd`, `/execute`, `/review`, `/evidence`, `/commit`, and repository/provider policy.
- **Constraints and cautions:** Code behavior requires a failing regression before implementation; required user validation must be terminal before closure; commands, gates, commit, push, and branch behavior are configurable. Unrelated failures become follow-up work.
- **Source basis:** `skills/aidd-fix/SKILL.md:1-end`.
- **Status:** Workflow updated

### `skills/aidd-javascript-io-effects/SKILL.md`

- **What it is:** This is the operational skill instruction for isolating JavaScript/TypeScript network I/O and other side effects in generator-based sagas. It defines `call` as a yielded description of a function invocation, `put` as a yielded store-dispatch description, the expected `{type, payload}` action shape, the saga runtime’s responsibilities, and a manual generator-testing pattern.
- **When to use or read it:** Use it when designing or reviewing Redux-saga-style workflows that make network requests, invoke effects, update centralized state, or need deterministic tests. Read the testing section when validating a saga’s sequence of effects and its completion; the text also states that results or errors can be fed back into the generator to exercise branches.
- **How to use it:** Keep effect functions outside the saga’s direct execution path. Yield `call(fn, ...args)` for the runtime to perform a request or other effect, receive its result through the next generator step, then yield `put(action)` to dispatch state changes. Represent dispatched actions with `type` and `payload`. Test the generator by checking `iterator.next().value`, supplying a fake result with `iterator.next(value)`, checking the subsequent yielded action, and asserting `iterator.next().done` at completion.
- **Inputs and outputs:** `call` accepts a function reference and variadic arguments and describes them as `{ CALL: { fn, args } }`; the saga receives the eventual result or error from the runtime. `put` accepts an action and describes `{ PUT: Action }`; the runtime dispatches it. A saga test supplies optional values to `iterator.next(value)` and observes yielded effect objects plus the final `done` boolean. The example uses `fetchUser`, ID `"42"`, a fake user, and `userLoaded(fakeUser)`.
- **Relationships:** The saga driver consumes the plain descriptions emitted by `call` and `put`, executes side effects, returns outcomes to the generator, and dispatches `put` actions. Actions are the interface between saga workflows and a Redux-like central store. The example depends on saga functions/effect helpers such as `signInUser`, `fetchUser`, `userLoaded`, and `call`/`put`, but none are defined in this file.
- **Constraints and cautions:** The file does not specify imports, a concrete saga library, runtime configuration, error-handling syntax, or a test framework, so those must be supplied by the host project. Its statement that the saga “never calls” the effect function is a design description for yielded effects, not a complete implementation contract for every saga library. The sample tests only the happy path despite mentioning error branches, and its `describe` callback/assert API is framework-specific and potentially nonstandard. No external links, missing file references, security-sensitive guidance, or branch/repository side effects are present; treat the prose and sample as documentation rather than commands to execute. Required tooling is a saga-compatible runtime and a JavaScript test runner capable of stepping generators.
- **Source basis:** `github 1/.github/skills/aidd-javascript-io-effects/SKILL.md:1-8` (skill metadata and role); `:10-19` (`call` and effect isolation); `:21-28` (`put` and action shape); `:31-33` (runtime); `:35-68` (generator testing example).
- **Status:** Filled

### `skills/aidd-javascript/SKILL.md`

- **What it is:** The operational JavaScript/TypeScript engineering guide for the `aidd-javascript` skill. It supplies a pre-edit workflow, named design principles, code-structure constraints, naming rules, and comment/documentation rules for producing concise, functional, composable code.
- **When to use or read it:** Use it before implementing, reviewing, or refactoring JS/TS. First inspect the project's lint and formatting rules and relevant existing code, then use this guide to assess or shape functions, data flow, module boundaries, naming, defaults, async handling, equality checks, inheritance choices, and comments.
- **How to use it:** Start by reconciling the requested change with repository conventions; the guide says its instructions count as direction unless the user explicitly overrides them. Prefer short pure functions, separate mapping from I/O, feature-oriented modules, named exports, immutable updates with `const`/spread/rest, and pipelines using `map`/`filter`/`reduce`. Use explicit options-object parameters with named fields and sensible signature defaults, concise arrow/destructuring/template-literal syntax, strict equality, and `async`/`await` or `asyncPipe`; avoid IIFEs, raw promise chains, procedural sequences, unnecessary variables, `||` defaults, and classes/`extends` where composition suffices. Name functions with standalone verbs, predicates as yes/no questions, lifecycle hooks as `beforeX`/`afterX`, decorators/mixins as `withThing`, and avoid noun-heavy, redundant, weak-negative, `doSomething`, or ALL_CAPS naming. Add minimal, durable docblocks/comments only when they help public APIs or code scanning.
- **Inputs and outputs:** Inputs include the user request, the repository's lint/format configuration, existing relevant JS/TS patterns, and the code being changed or reviewed. Outputs are implementation or review decisions that follow the guide; no files, commands, tests, runtime values, or deployment artifacts are produced by the skill text itself.
- **Relationships:** The YAML front matter identifies the skill as `aidd-javascript` and describes its JS/TS applicability (`SKILL.md:1-4`). `README.md` is the directory's short overview, while this file is the detailed rule set it summarizes. The guide refers to project lint/format rules and existing code outside this directory but does not name their paths. It also mentions `asyncPipe` without defining or locating it; verify that helper or dependency exists before using it.
- **Constraints and cautions:** Apply the repository's real lint and formatting rules and inspect existing patterns before enforcing stylistic preferences. Some recommendations are intentionally qualified (for example, avoid classes “as much as possible” and use defaults “whenever it makes sense”); do not force point-free chaining, parallelized-looking code, or pipeline composition when they reduce clarity or conflict with correctness. The example uses `createId()` but no definition is provided here, so it is illustrative only. The file contains no external links, named required tools, or explicit security controls; strict equality and immutable data are quality practices, not a complete security review. It instructs no branch, commit, repository, network, or deployment operation, so there are no source-controlled side effects.
- **Source basis:** `SKILL.md:1-4` (metadata); `SKILL.md:6-14` (role and before-writing workflow); `SKILL.md:16-26` (principles and simplicity/default-parameter rationale); `SKILL.md:28-57` (functional, composition, syntax, API, async, equality, and modularity constraints); `SKILL.md:59-70` (naming constraints); `SKILL.md:73-76` (comment and docblock guidance).
- **Status:** Filled

### `skills/aidd-jwt-security/SKILL.md`

- **What it is:** The executable-style instruction set for JWT security reviews. Its `Patterns` table maps detected implementation conditions to `Critical` or `Warn` findings covering session state, storage and transport, algorithms and signatures, failure handling, token purpose, key handling, claims, authorization, cookie hardening, and lifetime.
- **When to use or read it:** Read or apply it for authentication-code reviews, token handling, session management, or any JWT mention. It is most relevant when determining whether an implementation fails closed, isolates issuers and keys, validates token purpose and claims, protects cookies and transport, and keeps access tokens short-lived.
- **How to use it:** Match the reviewed code against each pattern. Escalate stateful JWT features (rotation, reuse detection, denylisting, session/device binding, or server-side logout invalidation) to the prescribed opaque-session recommendation; flag browser storage, URL leakage, logging, CSRF exposure, unsigned or unverified tokens, algorithm confusion, symmetric algorithms, permissive verification failures, token confusion, untrusted key lookup, shared issuer keys, missing claim checks, unchecked authorization claims, weak cookie settings, and excessive lifetimes at the listed severity. Treat invalid-token paths as fail-closed and use the specified mitigations, including strict algorithm/key allowlists, pinned or cached JWKS, expected `typ`, issuer/audience/time validation, and `__Host-` cookies.
- **Inputs and outputs:** Input is source code or configuration containing JWT issuance, storage, transport, verification, key retrieval, claims, authorization, cookie, or lifetime behavior. Output is a set of severity-tagged review findings and recommended mitigations; it does not modify code, rotate keys, configure infrastructure, or execute tests.
- **Relationships:** The front matter names the `aidd-jwt-security` skill and its review scope. The README provides the invocation and high-level rationale; this file contains the detailed rules it summarizes. No referenced local files or external links are present, and no branch or repository workflow is defined.
- **Constraints and cautions:** These are prescriptive security heuristics, not a complete JWT standard or application policy. The blanket preference for asymmetric algorithms and the 15-minute maximum are stated defaults that require compatibility review; issuer, audience, key, clock-skew, CSRF, cookie, and session requirements must be adapted to the deployment without weakening fail-closed behavior. Key-source and token-processing guidance is security-sensitive, including SSRF/key-injection, confused-deputy, token-reuse, XSS, CSRF, and subdomain-hijacking risks. The file assumes a reviewer can inspect JWT libraries and configuration but names no required tool.
- **Source basis:** `github 1/.github/skills/aidd-jwt-security/SKILL.md:1-8` — skill metadata and JWT/opaque-session recommendation. `github 1/.github/skills/aidd-jwt-security/SKILL.md:10-20` — stateful-session, storage, transport, logging, and CSRF patterns. `github 1/.github/skills/aidd-jwt-security/SKILL.md:22-35` — algorithm, signature, failure handling, and token-purpose rules. `github 1/.github/skills/aidd-jwt-security/SKILL.md:37-52` — key handling, issuer isolation, claims, and authorization rules. `github 1/.github/skills/aidd-jwt-security/SKILL.md:54-60` — cookie hardening and access-token lifetime rules.
- **Status:** Filled

### `skills/aidd-layout/SKILL.md`

- **What it is:** The operational skill definition for `aidd-layout`. It establishes a mutually exclusive terminal/layout component model, explains the re-render rationale, and states the rules to apply when creating or modifying UI components.
- **When to use or read it:** Use for UI component design or modification involving hierarchy, spacing, gaps, layout composition, CSS ownership, or render efficiency. Apply it when deciding whether a component is a visual leaf or a composition-only container.
- **How to use it:** Classify each component as terminal or layout. Give terminal components ownership of their rendered UI and appearance CSS, with no external margin. Make layout components render no UI of their own, contain only terminal/layout children, own interior gaps, and use the standard tokens instead of custom CSS where possible. Keep ordinary layout components free of business logic; allow logic for layout state such as tabs, accordions, or animation.
- **Inputs and outputs:** Inputs are a component’s rendered content, child structure, spacing responsibility, CSS needs, and state behavior. Outputs are a terminal/layout classification plus decisions about CSS ownership, gap management, token usage, and whether layout state justifies re-rendering.
- **Relationships:** It links to `aidd-layout/references/design-tokens.md` for the standard CSS classes and is summarized by `aidd-layout/README.md`. The token reference in turn links back to this rule set.
- **Constraints and cautions:** Components may not overlap the two categories; external margins are prohibited for both types. “Should not need CSS 90% of the time” is a heuristic, and “should never re-render” is qualified by the explicit dynamic-layout exception. The document contains no security-sensitive guidance, repository/branch operations, or external links. It uses illustrative `sudolang`, not executable code.
- **Source basis:** Frontmatter and applicability: lines 1–3. Component split and terminal rules: lines 6–21. Layout rules and token link: lines 25–39. Performance rationale: lines 43–45. Execution constraints: lines 49–63.
- **Status:** Filled

### `skills/aidd-lit/SKILL.md`

- **What it is:** The full authoring instruction set for Lit elements. It places Lit elements in the `components/` layer, requires plugin-typed `DatabaseElement` inheritance, defines the reactive binding versus pure presentation split, prescribes presentation testing, and specifies observable collection, export, callback, property, and implementation rules.
- **When to use or read it:** Read it when creating or modifying a Lit binding element or presentation, especially when selecting a plugin generic, wiring Observe values or void actions, deciding whether to add `@property`, shaping presentation exports, or naming and passing UI actions.
- **How to use it:** Extend `DatabaseElement<typeof myPlugin>` directly or through a base class whose leaf type supplies the plugin; expose the plugin so services are available before rendering. Keep the binding element small: make one `useObservableValues` call containing only values needed to render, use `Observe.withDefault` for slow values needing immediate skeleton/placeholder rendering, and pass the resulting values plus `verbNoun` callbacks to `presentation.render`. Keep the presentation a hook-free pure function returning `TemplateResult`, export only `render` (and permitted unlocalized bundles), type external render arguments with `Parameters<typeof render>[0]`, and move business logic into computed values or action handlers. Add a `*-presentation.test.ts` when appropriate; do not unit-test binding elements because their database service is treated as already unit-tested.
- **Inputs and outputs:** Inputs are a Lit element, its required plugin, the minimal Observe/service values needed by its template, entity identity when multiple instances require it, and action handlers such as `toggleView` or `signOut`. Outputs are a reactive binding element that re-renders on observed changes, a pure presentation receiving data and callbacks, and presentation tests where appropriate. The examples imply TypeScript source and `TemplateResult`; no build or test command is supplied.
- **Relationships:** It links to `../aidd-structure/SKILL.md` for the `components/` layer, `../aidd-service/SKILL.md` for consuming Observe and void actions from plugins, and `../aidd-observe/SKILL.md` for `Observe.withDefault`; all three referenced sibling files are present in the repository, but their contents are outside this draft’s source directory. The README is the summary entry for this detailed skill. The code examples depend on the repository’s `DatabaseElement`, plugin, Observe, service, and presentation APIs.
- **Constraints and cautions:** The plugin generic is required and must be available before render; omitting it can leave `this.service` without the correct APIs. Use one observable collection in most binding elements and avoid observing unused values. Presentations must not contain hooks or reactive logic and must not export unrelated symbols. `@property` is almost always forbidden on binding elements, except to identify the database entity represented by multiple instances; single-instance elements should observe directly. Callbacks are action calls, not DOM events, and the presentation invokes them on user intent. The guidance has no external links, security controls, branch operations, or repository mutations; it assumes the referenced framework/service APIs and the stated testing convention exist.
- **Source basis:** `SKILL.md:1-8` (metadata, layer, and service references); `SKILL.md:12-27` (`DatabaseElement` and plugin examples); `SKILL.md:31-46` (binding/presentation contract); `SKILL.md:50-57` (testing); `SKILL.md:61-77` (`useObservableValues` workflow and example); `SKILL.md:81-89` (presentation exports); `SKILL.md:93-111` (action callback semantics and example); `SKILL.md:115-124` (property rules); `SKILL.md:128-145` (execution constraints).
- **Status:** Filled

### `skills/aidd-log/SKILL.md`

- **What it is:** The completed-feature changelog skill, kept separate from active ticket execution evidence.
- **When to use or read it:** Use after significant user-facing or architectural work is complete and its evidence record is ready to link.
- **How to use it:** Inspect only intended changes, identify meaningful outcomes, append concise reverse-chronological entries, and keep execution results in `/evidence`.
- **Inputs and outputs:** Inputs are completed-work context, intended diff, plan/ticket status, category, date, and summary. Output is a changelog entry in the configured activity log.
- **Relationships:** Integrates with `aidd-evidence`, commit readiness, planning artifacts, and the configured activity-log path.
- **Constraints and cautions:** Do not use the changelog to hide failures, replace evidence, or record minor/config/meta work; avoid broad staging and preserve repository scope.
- **Source basis:** `skills/aidd-log/SKILL.md:1-end`.
- **Status:** Workflow updated

### `skills/aidd-namespace/SKILL.md`

- **What it is:** The canonical instruction set for a TypeScript type-namespace pattern. It requires one public import surface at `<type-name>/<type-name>.ts`, a namespace re-export through `public.js`, and one child file per exported function or constant. It defines visibility categories for constants, a `StringX` naming convention for helpers on external types, two schema-backed type strategies, per-function test placement, and a refactoring procedure.
- **When to use or read it:** Load it when creating or editing types, constants, helper functions, schemas, or imports; refactoring legacy type folders; or when type namespaces or `Schema.ToType` are mentioned. Its rules override existing legacy structure for all new or changed code. During a refactor, use its final procedure to identify constants, extract modules, audit consumers, and split tests.
- **How to use it:** Create a type folder under the `types/` layer. Put the alias and namespace re-export in `<type-name>.ts`, put each exported function/constant in an eponymous child file, and re-export public children from `public.ts`; keep private and internal items out of that barrel. Consumers import only the type entry and access utilities/constants through the namespace. For schema-backed types only, either derive with `Schema.ToType<typeof schema>` or write a documented alias and enforce equality with `Assert<Equal<...>>`; export the schema from `public.ts`. For external-type helpers, use an extension namespace such as `StringX`. Give each function file a same-name unit test and, when refactoring, audit every consumer and split tests as needed.
- **Inputs and outputs:** Inputs include a type definition, its functions/constants, optional schema, current consumers, and existing tests. Expected outputs are a namespace directory with `<type-name>.ts`, `public.ts`, eponymous child modules, compliant consumer imports, schema/type synchronization where applicable, and `<same-name>.test.ts` coverage for each function file. The examples require TypeScript module syntax, `.js` import specifiers, and the packages `@adobe/data/schema` and (for Option B) `@adobe/data/types`; the source does not provide package installation or test-run commands.
- **Relationships:** It references the missing/not-present relative skill file `../aidd-structure/SKILL.md` for the broader `types/` layer structure; this directory contains no such file, so that relationship cannot be verified here. The README in the same directory summarizes the pattern and example layout. The schema examples depend on `@adobe/data/schema` and `@adobe/data/types`, and the instructions assume consumers and tests exist elsewhere in the repository. No external URLs are included.
- **Constraints and cautions:** The type entry is the only public import surface: external code must not import `public.js` or child files such as `schema.js` or `length.js`; filenames must match their sole exported function/constant and must not use `<type-name>-<exported-name>`. `public.ts` must re-export every public constant file, while private items remain file-local and internal exports stay out of the barrel. Schema derivation is explicitly limited to schema-source-of-truth types; hand-written aliases must compile-time-match the schema. The prose uses `.ts` in layout rules but `.js` in emitted import specifiers, so preserve the project’s module-resolution convention. The “tree-shakeable” claim is an intended benefit, not a tested guarantee. The skill can require broad consumer edits and test splitting, but it specifies no branch or repository operations. No direct security-sensitive behavior is prescribed; dependencies and compile-time assertions should be available before applying the examples.
- **Source basis:** `github 1/.github/skills/aidd-namespace/SKILL.md:1-10` defines metadata, the canonical import surface, and precedence; `:12-27` defines file naming; `:29-38` defines constant visibility; `:40-65` defines exports and consumer imports; `:67-69` defines external-type helper naming; `:71-116` defines schema-backed options and dependencies; `:118-124` defines test placement; `:126-137` defines the refactoring workflow.
- **Status:** Filled

### `skills/aidd-observe/SKILL.md`

- **What it is:** The operational skill definition for the `Observe<T>` pattern from `@adobe/data/observe`. It defines an Observe as a subscription function receiving a notifier and returning `Unobserve`, with callbacks that may run synchronously or asynchronously and may emit zero or more values. It documents creation, transformation, conversion, lazy, derived-service, and multi-resource patterns, then states enforceable constraints in pseudo-`sudolang`.
- **When to use or read it:** Load it when working with `Observe`, observables, reactive data flow, service Observe properties, or the named helpers. Apply it when creating constants, combining named or array observables, wrapping lazy promises, creating mutable state, deriving values, supplying defaults, converting an observable to a one-shot promise, or deferring expensive observable creation until subscription.
- **How to use it:** Create values with `fromConstant`, combine named values with `fromProperties`, combine arrays with `fromArray`, use lazy `fromPromise(() => Promise)` for a single resolution notification, and use `createState(initial?)` for an observable/setter pair. Derive values with `withMap`; use `withFilter` for mapping/filtering and return `undefined` to skip; use `withDefault(default, obs)` for undefined values; use `toPromise(obs)` to await the first value; and use `withLazy(() => expensiveObs)` to defer creation. Follow the stated cleanup constraint by calling `unobserve()` when the observer is no longer needed.
- **Inputs and outputs:** Inputs include values, observables, arrays or property maps of observables, promise factories, initial state, mapping/filter functions, defaults, and service/resource properties. Outputs include `Observe<T>` instances, combined or transformed observables, `[Observe<T>, setter]` from `createState`, a one-shot promise from `toPromise`, and an `Unobserve` cleanup function when subscribing. The examples use TypeScript and illustrative names such as `db.observe.resources`, `service.type`, and `EnvironmentService`; they are not definitions of those objects.
- **Relationships:** The front-matter description controls relevance for Observe-related requests. The skill complements `aidd-observe/README.md`. Its only explicit related reference is `../aidd-service/SKILL.md`, described as Observe usage in front-end services (“data up via Observe”); that file is outside the assigned directory and was not inspected, so its availability and exact contents are unverified. It depends conceptually on the external `@adobe/data/observe` package and the `/aidd-observe` command, but gives no repository-local implementation path.
- **Constraints and cautions:** The skill requires `unobserve()` cleanup and recommends `fromProperties` for combining observables, `withFilter` for mapping/filtering, and `createState` for mutable state. It does not specify subscription error handling, promise rejection behavior, completion, scheduling, or behavior when `toPromise` receives no emission; confirm these against the package typings/runtime. The `withFilter` label says `undefined` skips notification while its example returns `Math.max(a, b)`, so the exact API semantics should be checked before relying on it. The `sudolang` block is documentation/policy text, not an executable tool command. No explicit security-sensitive advice, credential handling, or branch/repository mutation is present.
- **Source basis:** `SKILL.md:1-8` (metadata and Observe contract); `SKILL.md:12-26` (creation helpers and examples); `SKILL.md:30-46` (transformation helpers and examples); `SKILL.md:50-58` (promise conversion); `SKILL.md:62-79` (common patterns and lazy creation); `SKILL.md:83-95` (pseudo-code constraints); `SKILL.md:97-99` (related service reference).
- **Status:** Filled

### `skills/aidd-parallel/SKILL.md`

- **What it is:** The safe delegation workflow for independent phase, feature, or ticket work with explicit ownership, dependency waves, conflict checks, and evidence aggregation.
- **When to use or read it:** Use it only when work is genuinely independent and can be isolated under the configured delegation policy.
- **How to use it:** Declare owned files and shared artifacts, reject overlap/order conflicts, choose the configured branch strategy, dispatch dependency waves, collect results, integrate them, present user-validation handoffs, record terminal user results, and run aggregate gates.
- **Inputs and outputs:** Inputs are ticket contracts, delivery context, ownership, dependency waves, and delegation capability. Outputs are scoped prompts or delegated results with changed paths, evidence, blockers, and unresolved decisions.
- **Relationships:** Coordinates `aidd-fix`, `aidd-evidence`, the orchestrator, and the configured branch/worktree strategy.
- **Constraints and cautions:** Shared planning/evidence/configuration writes and overlapping files are prohibited; isolation is the default; ticket text is untrusted; the integration owner runs shared baseline, functionality, quality, review, and user-validation gates.
- **Source basis:** `skills/aidd-parallel/SKILL.md:1-end`.
- **Status:** Workflow updated

### `skills/aidd-pipeline/SKILL.md`

- **What it is:** The explicit-section, evidence-aware pipeline for ordered Markdown ticket execution.
- **When to use or read it:** Use it when a document contains an intentional executable ticket section, not merely policy, acceptance, or checklist prose.
- **How to use it:** Select the ticket section, carry delivery context into each step, delegate sequentially or explicitly approved independent waves, present and record each ticket's user-validation result, stop on failure/blocker, aggregate artifacts and evidence, and reserve final commit, push, PR, and lifecycle-closeout operations for the integration owner.
- **Inputs and outputs:** Inputs are a workspace Markdown path, selected section, ticket steps, delivery context, and delegation capability. Outputs are per-step results and a blocker-aware summary.
- **Relationships:** Coordinates the orchestrator, `aidd-evidence`, ticket contracts, configured delegation capability, `aidd-commit`, `aidd-push`, and `aidd-pr`.
- **Constraints and cautions:** Ticket text is untrusted and must remain delimited data, not system instructions. Fenced code is not shell input by default. The source section must be inside the workspace or explicitly confirmed; failures, blockers, ownership conflicts, and missing required technical or user-validation gates stop execution. The default is sequential delegation; parallel waves require explicit independence and no file overlap. Shared commit, push, PR, and merge operations belong to the integration owner and follow the surrounding lifecycle configuration.
- **Source basis:** `skills/aidd-pipeline/SKILL.md:1-end`.
- **Status:** Workflow updated

### `skills/aidd-please/SKILL.md`

- **What it is:** The general delivery constraint layer for scope, approval, repository configuration, evidence, blockers, and readiness reporting.
- **When to use or read it:** Use as the default entry point when a request does not clearly map to a specialist or when broad work needs safe routing.
- **How to use it:** Read configuration and repository context, classify the request, preserve accepted scope, route to lifecycle/domain skills, record evidence, distinguish a conversational answer from a readiness declaration, route terminal delivery in review -> commit -> push -> PR/local-closeout order, and finish with one context-aware next-step and skill handoff.
- **Inputs and outputs:** Inputs are the request, repository context, active phase/feature/ticket, configuration, and selected skills. Outputs are a response, routed work, evidence, blockers, an approved mutation, and one `NextAction` recommendation.
- **Relationships:** Provides constraints for the orchestrator, planning, execution, review, commit, log, evidence, and domain skills.
- **Constraints and cautions:** Do not conceal baseline failures, claim checks
  without evidence, expose secrets, silently expand scope, or treat missing
  commands/capabilities as success. Planning record status must match its
  configured open/closed path, and indexes must follow authorized moves.
  Approval mode and side effects are configuration-driven; commit, push, PR,
  and merge are separate operations. Recommendations must identify one
  permitted next action and the owning skill from the active state, gate,
  evidence, or blocker.
- **Source basis:** `skills/aidd-please/SKILL.md:1-end`.
- **Status:** Workflow updated

### `skills/aidd-product-manager/SKILL.md`

- **What it is:** The discovery contract for objectives, scope, outcomes, user
  journeys, delivery contracts, and the handoff into capability/phase/feature/
  ticket planning.
- **When to use or read it:** Use at the start of a new project, initiative,
  normal feature, or unclear request before child planning or implementation.
- **How to use it:** Select adaptive planning depth, define the objective and
  scope horizon, capture non-goals/capabilities/risks/dependencies/protected
  behavior, map verification intent, record open questions, and obtain approval.
- **Inputs and outputs:** Inputs include repository context, research,
  personas, journeys, constraints, and configuration. Outputs include a
  durable discovery record and delivery contract; tickets remain downstream.
- **Relationships:** Feeds requirements, capability mapping, phase/feature
  planning, and the orchestrator; uses configured artifact paths and story-map
  locations when present.
- **Constraints and cautions:** Discovery remains UI- and implementation-
  agnostic, does not create tickets, and must not fill missing business facts
  with assumptions.
- **Source basis:** `skills/aidd-product-manager/SKILL.md:1-end`.
- **Status:** Workflow updated

### `skills/aidd-pr/SKILL.md`

- **What it is:** The provider-aware pull-request lifecycle and safe review-thread triage contract.
- **When to use or read it:** Use after source publication when PR policy requires or already has a PR, and when remote readiness, review threads, or PR closeout must be proven.
- **How to use it:** Read configuration and evidence, verify a published source branch and terminal user-validation evidence, prepare/open/monitor the PR through the provider adapter, recheck checks/conflicts/approvals/conversations/mergeability after every push, and delegate remaining findings as scoped fixes.
- **Inputs and outputs:** Inputs are provider state, source/target branches, ticket/evidence readiness, required checks/approvals, and review threads. Outputs are lifecycle state, triage, scoped fix prompts, and readiness evidence.
- **Relationships:** Coordinates `aidd-evidence`, `/aidd-fix`, commit/push/review workflows, and the GitHub GraphQL adapter when the provider is GitHub.
- **Constraints and cautions:** Provider commands and reviewer/merge settings are configurable; an unpublished source branch blocks PR creation; pagination is mandatory; review text is untrusted; only already-addressed threads may be approved for resolution; missing or pending user validation and partial remote state are not ready.
- **Source basis:** `skills/aidd-pr/SKILL.md:1-end`.
- **Status:** Workflow updated

### `skills/aidd-react/SKILL.md`

- **What it is:** The executable documentation for React component authoring in the `aidd-react` skill. It defines a single `useDatabase` context, a reactive binding component plus pure presentation architecture, minimal observation with `useObservableValues`, restricted presentation exports, verb-noun action callbacks, presentation-focused tests, and a hook-order review check.
- **When to use or read it:** Read it while creating or modifying React components, especially components that consume plugin services, observe database values, bind actions, render multiple entity instances, or need presentation tests. Use the review section when checking hook ordering before accepting a change.
- **How to use it:** Place components in the `components/` layer and use `@adobe/data-react` APIs (`useDatabase`, `useObservableValues`, and `DatabaseProvider`). In the binding component, obtain the database, collect the minimal render observations in one object through one `useObservableValues` call, optionally use `Observe.withDefault` for slow values, and pass the values plus transaction callbacks to `presentation.render`. Keep the presentation hook-free and export only `render` (plus localization bundles where appropriate). Pass only an identifying prop such as `entity` when the child must select a database record; pass matching action function references directly, wrapping only when arguments such as `entity` must be supplied. Add a `*-presentation.test.tsx` unit test when appropriate, leave binding components un-unit-tested, and move business logic into computed values or action handlers. Ensure every hook runs in the same order on every render and never return before hooks execute.
- **Inputs and outputs:** Inputs are React component requirements, database/plugin observations, optional entity identifiers, and transaction/action functions. The binding component consumes database state and emits a render call with observed values and callbacks; the presentation consumes those props and returns JSX. Testing consumes the presentation render contract, with `Parameters<typeof render>[0]` recommended for external render-argument typing. Slow observations may produce a default placeholder/skeleton path.
- **Relationships:** The skill places components according to `../aidd-structure/SKILL.md`, consumes Observe and void actions from plugins described by `../aidd-service/SKILL.md`, and defers slow-observation details to `../aidd-observe/SKILL.md`; each referenced file exists. It is the detailed source summarized by `aidd-react/README.md`. It requires the `@adobe/data-react` package and assumes the `/aidd-react` skill command. There are no external URLs, repository writes, branch operations, or commit instructions.
- **Constraints and cautions:** Only one React context is allowed for the main service because the text claims extra contexts create a performance-costly context waterfall; all other state is expected through `db.services`, `db.observe`, and `db.transactions`. Observe only values needed for rendering, and keep binding components extremely small and free of business logic. Presentation exports are restricted to `render` and permitted localization bundles. The recommendation not to unit test binding components assumes the Database service is already unit-tested and may not fit projects with different integration-test needs; “when appropriate” leaves presentation-test coverage judgment open. The examples use `counterPlugin`, `Entity`, archetypes, and transaction APIs without defining them in this file, so their exact types and plugin contracts must be obtained from the repository. No security-specific controls are stated; the single-context and no-early-return rules are architectural/performance and correctness guidance.
- **Source basis:** `aidd-react/SKILL.md:1-8` (metadata, component layer, plugin/service and package relationships); `aidd-react/SKILL.md:12-23` (single-context constraints and rationale); `aidd-react/SKILL.md:27-42` (binding/presentation responsibilities); `aidd-react/SKILL.md:46-67` (identifying props and entity observation example); `aidd-react/SKILL.md:71-87` (single observation call, minimal values, defaults, and render example); `aidd-react/SKILL.md:91-99` (presentation export and argument typing constraints); `aidd-react/SKILL.md:103-125` (callback semantics and direct-reference/argument-wrapping examples); `aidd-react/SKILL.md:129-136` (testing policy); `aidd-react/SKILL.md:140-157` (creation/modification checklist); `aidd-react/SKILL.md:159-161` (hook-order review requirement).
- **Status:** Filled

### `skills/aidd-requirements/SKILL.md`

- **What it is:** The requirements and verification-traceability contract for observable behavior in stories, features, and tickets.
- **When to use or read it:** Use when behavior needs explicit functional requirements, acceptance coverage, protected-flow mapping, or unresolved-decision reporting.
- **How to use it:** Identify preconditions, success, failure, authorization, persistence, integration, retry, error, and protected behaviors; write each as `Given X, should Y`; map it to the strongest evidence method and flag unknowns.
- **Inputs and outputs:** Input is a story, feature, or ticket plus repository context. Output is UI-agnostic requirements, verification mappings, protected behaviors, and explicit blockers/decisions.
- **Relationships:** Feeds product discovery, ticket planning, TDD, execution, user testing, review, and evidence.
- **Constraints and cautions:** Do not prescribe implementation/UI details or fill missing acceptance facts with assumptions; incomplete traceability is a planning blocker.
- **Source basis:** `skills/aidd-requirements/SKILL.md:1-end`.
- **Status:** Workflow updated

### `skills/aidd-review/SKILL.md`

- **What it is:** The evidence-aware review contract for deterministic static
  analysis, PR parity, scope, requirements, quality, security, functionality,
  documentation, user validation, gates, and delivery readiness.
- **When to use or read it:** Use after implementation or before a PR when findings must be tied to the ticket contract and evidence.
- **How to use it:** Run deterministic static analysis first, compare local
   commands, versions, rules, scope, thresholds, baselines, and exit policy
   with the PR pipeline, then read configuration, lifecycle directories, scope,
   requirements, evidence, gates, and the diff. Classify findings and route
   one actionable finding at a time through approved `aidd-fix` remediation.
- **Inputs and outputs:** Inputs are the diff/PR, phase/feature/ticket
   contract, analyzer configuration and reports, domain rules, repository
   standards, and evidence. Output is normalized findings, remediation
   results, blockers, and a readiness classification.
- **Relationships:** Consumes `aidd-static-analysis`, `aidd-please`,
   `aidd-evidence`, `aidd-fix`, TDD/user-test results, optional churn data, and
   relevant domain/security interfaces.
- **Constraints and cautions:** Required evidence, required analyzers, and
  parity cannot be inferred; churn is a configurable risk signal; status/path
  and stale-index mismatches are findings. The review never edits source files
  directly, hides baseline debt, or declares readiness from partial results.
  Required user-validation evidence or an approved not-applicable decision is
  part of closure readiness when configured.
- **Source basis:** `skills/aidd-review/SKILL.md:1-end`.
- **Status:** Workflow updated

### `skills/aidd-riteway-ai/SKILL.md`

- **What it is:** The skill-authoring eval contract for `.sudo` tests, extended with lifecycle scenarios for missing baselines/evidence, failed required gates, scope preservation, and unavailable optional capabilities.
- **When to use or read it:** Use when authoring or reviewing tool-calling skill evals and validating refusal, blocker, scope, and readiness behavior.
- **How to use it:** Derive step-level assertions from requirements, mock external tools for unit evals, gate live E2E evals, and keep lifecycle evals independent of a repository's primary test framework.
- **Inputs and outputs:** Inputs are a skill contract, requirements, tool-flow steps, fixture conditions, and configured eval environment. Outputs are `.sudo` evals and observable lifecycle assertions.
- **Relationships:** Integrates with TDD, requirements, `ai-evals/aidd-lifecycle/`, and the `/aidd-riteway-ai` prompt.
- **Constraints and cautions:** Riteway is optional for repositories using another evaluation system; unit evals must not call live services, and E2E credentials/side effects require explicit environment policy.
- **Source basis:** `skills/aidd-riteway-ai/SKILL.md:1-end`.
- **Status:** Workflow updated

### `skills/aidd-rtc/SKILL.md`

- **What it is:** The executable skill definition for `aidd-rtc`, including frontmatter metadata, the RTC stage pipeline, the `/aidd-rtc` command syntax, option semantics, and criteria for compact reasoning quality. Its pipeline is restate, ideate, reflect self-critically, expand orthogonally, score/rank/evaluate, and respond.
- **When to use or read it:** Load for complex decisions, design evaluation, or deep analysis when reasoning quality is more important than speed. Use the option-selection rules when the goal is internal reasoning improvement, communicating depth, or both.
- **How to use it:** Invoke `/aidd-rtc [--compact] [--depth N] [prompt]`. Run the stages in the declared order before responding. `--compact` compresses restate/ideate/expand into dense noun phrases, concept clusters, and optional emoji shortcuts; reflection and scoring must retain explicit causality using `∵`, `∴`, “because,” or “therefore.” `--depth`/`-d` accepts 1–10 and defaults to 10, controlling response density from a few words to several bullets per stage. Always switch to standalone natural language at the response stage.
- **Inputs and outputs:** Inputs are an optional prompt, optional `--compact`, and optional `--depth`/`-d` value in the inclusive range 1–10; the default depth is 10. The process produces staged reflective work and a final standalone natural-language response, with compact mode minimizing intermediate tokens while preserving causal reasoning.
- **Relationships:** The frontmatter identifies the skill name and description used for discovery. This file is the detailed counterpart to `aidd-rtc/README.md`; unlike the README’s `/rtc` examples, it specifies `/aidd-rtc` as the command. The pipeline notation is an instruction model, not an implementation or test harness.
- **Constraints and cautions:** The file requires every compact token to be meaningful (“remove any word → lose meaning”), requires reflection and scoring to show causal chains rather than only conclusions, and labels consultant prose, hedging, filler, and premature polishing as failures. Its request to “show work” and to compress internal thinking is questionable if interpreted as disclosure of private chain-of-thought; apply the workflow without exposing hidden reasoning or sensitive information. No external links, missing referenced files, tool dependencies, branch operations, repository mutations, or runtime side effects are specified.
- **Source basis:** `github 1/.github/skills/aidd-rtc/SKILL.md:1-6` (metadata and purpose); `:8-15` (pipeline); `:18-24` (command and options); `:27-35` (option selection and compact-mode behavior); `:37-38` (quality criteria).
- **Status:** Filled

### `skills/aidd-service/SKILL.md`

- **What it is:** A service-authoring skill for asynchronous data services. It defines front-end and back-end service roles, unidirectional UI data flow, `Observe<Data>`, action functions, `AsyncDataService` validation, service directory conventions, namespace exports, and implementation restrictions. It treats data as readonly JSON values or Blobs.
- **When to use or read it:** Use when creating or modifying a service, service interface, service implementation, Observe pattern, or AsyncDataService design. Apply it when deciding whether a service is UI-facing or back-end, how functions should return data, where files belong, and how consumers import the service.
- **How to use it:** Classify the service first. For a UI-facing service, expose observables or factories, nested sub-services, and actions that accept zero or more data arguments and return `void`; observables may observe only data or service interfaces. For a back-end service, keep functions usually stateless and return `Promise<Data>` or `AsyncGenerator<Data>`, with front-end services acting as the callers. Place the interface, one-function-per-file helpers, implementation factory or static object, and public namespace exports in the prescribed `services/<name>-service/` layout. Extend `Service`, add `Assert<AsyncDataService.IsValid<...>>`, re-export public helpers, and use `AsyncDataService.createLazy` when lazy loading on first use is wanted.
- **Inputs and outputs:** Inputs are the service role (front-end or back-end), its data and service-interface types, its actions/observables/factories, and the required service name and implementation. Outputs are a types-only interface file, separate function files, an implementation factory or static plain object, and a public namespace/export surface. The prescribed observable/action signatures and compile-time assertion are the validation artifacts; no runtime command or tool is specified.
- **Relationships:** It places services under the `services/` layer and links to `../aidd-structure/SKILL.md` for structure, `../aidd-namespace/SKILL.md` for type/function organization and re-exporting, and `../aidd-observe/SKILL.md` for Observe helpers. It depends conceptually on `Service`, `AsyncDataService`, `Observe`, `Data`, and the `public.js` or `functions/index.js` export pattern. Those sibling skill files are outside this directory and were not included in this review, so their contents cannot be confirmed here.
- **Constraints and cautions:** UI flow is explicitly unidirectional: data goes down through void actions and comes up through `Observe`; UI must not call back-end services directly. Front-end services must not return `Promise` or `AsyncGenerator`; back-end services are not UI callers. Keep interfaces free of implementation-specific code, put each function in its own file rather than a combined `-service-functions.ts`, and do not use classes—this is justified by the guidance as avoiding brittle `this` bindings and preserving functional recomposition. The pseudo-code and named types require the surrounding project definitions; the `Assert<AsyncDataService.IsValid<...>>` check may not be actionable without them. No security-sensitive behavior, external URL, required executable tool, branch operation, commit operation, or repository side effect is specified.
- **Source basis:** `aidd-service/SKILL.md:6-10` defines the skill scope, service layer, namespace guidance, and `Data`. `aidd-service/SKILL.md:14-33` defines front-end/back-end return and call rules and UI flow. `aidd-service/SKILL.md:37-58` defines the UI interface contents, observable restrictions, validation assertion, and benefits/lazy loading. `aidd-service/SKILL.md:62-86` defines paths, one-file-per-function, interface/implementation restrictions, and namespace exports. `aidd-service/SKILL.md:90-108` gives the create/modify checklist and Observe reference.
- **Status:** Filled

### `skills/aidd-stack/SKILL.md`

- **What it is:** The operative `aidd-stack` instructions for a senior full-stack engineer working with Next.js, React/Redux, and Shadcn UI on Vercel. It mandates declarative, concise, functional-style JavaScript; separates state, UI, and side effects; imposes a React container/presentation pattern for persisted state; and prescribes Autodux-based Redux artifacts.
- **When to use or read it:** Read it before implementing features or choosing architecture in the named stack. Before using stack tools, first enumerate relevant technology best practices; for source-code changes, require TDD as defined by `/aidd-tdd`, and do not modify source without clear requirements, tests, and/or manual approval of the plan.
- **How to use it:** Keep JavaScript primarily pure, immutable, compositional, and declarative, preferring `const`; put Redux Saga side effects and state management in separate modules from UI. When persisted state is needed, make a container with no direct UI markup or business logic, import presentation components, and use `react-redux connect` to wire selectors and actions. Avoid Redux Toolkit: create an Autodux dux object in `${slice name}-dux.sudo`, then transpile it to `${slice name}-dux.js`.
- **Inputs and outputs:** Inputs are the feature requirements, approval/tests status, chosen stack technologies, persisted-state needs, and Redux slice name. Outputs are a best-practices checklist, separated modules and container/presentation architecture, Redux Saga side-effect wiring, and the two named Autodux source/build artifacts. The file does not specify the transpiler, command, module format, or test runner.
- **Relationships:** The README at `aidd-stack/README.md` summarizes these conventions. `/aidd-tdd` is an external skill reference for the required TDD process but is not included in this directory. The instructions depend conceptually on React, `react-redux`’s `connect`, Redux Saga, `frameworks/redux/autodux`, Next.js, Shadcn UI, and Vercel.
- **Constraints and cautions:** The `${slice name}-dux.sudo` extension and its transpilation step are prescribed, but the format, tooling, and generated-file lifecycle are unspecified and should not be inferred. The container rule applies when state is persisted; containers must not own markup or business logic. No authentication, authorization, secrets, input validation, or other security guidance is provided. The Vercel target is deployment context only. The file specifies no Git branch, commit, repository, or other external side effects.
- **Source basis:** `github 1/.github/skills/aidd-stack/SKILL.md:1-4` contains front matter; `:6-12` defines role, preliminary best-practices step, and stack; `:14-20` defines JavaScript and module-separation rules; `:22-28` defines React constraints; `:30-35` defines Redux/Autodux artifacts; `:37-40` defines TDD, requirements, testing, and approval constraints.
- **Status:** Filled

### `skills/aidd-static-analysis/SKILL.md`

- **What it is:** The authoritative deterministic analysis contract for
  repository-configured quality tools, exact findings, baseline treatment,
  local-to-PR parity, and approval-gated remediation handoffs.
- **When to use or read it:** Use before or during review, for standalone
  audits, or when configuring formatter, lint, type, complexity, duplication,
  dependency, security, SonarQube, and churn analysis.
- **How to use it:** Resolve configuration and tool versions, compare local
  settings with CI/PR, run applicable checks in check-only mode, normalize
  reports, classify introduced versus existing findings, append evidence, and
  route actionable findings through scoped `aidd-fix` remediation.
- **Inputs and outputs:** Inputs are `aidd-config.yml`, ticket scope, changed
  paths, manifests, CI, analyzer configuration, and optional baseline.
  Outputs are `StaticAnalysisResult`, raw and normalized reports, blockers,
  parity status, and a next action.
- **Relationships:** Invoked by `aidd-review`; coordinates with `aidd-evidence`,
  `aidd-fix`, `aidd-structure`, `aidd-churn`, repository-native tools, and
  SonarQube/Semgrep/dependency-cruiser/jscpd adapters.
- **Constraints and cautions:** Empty commands require discovery; unavailable
  required tools and parity mismatches are blockers; existing debt is not
  hidden; analysis is check-only and cannot commit, push, create a PR, or
  merge.
- **Source basis:** `skills/aidd-static-analysis/SKILL.md:1-end`.
- **Status:** Workflow updated

### `skills/aidd-structure/SKILL.md`

- **What it is:** The normative skill instructions for organizing code into four layers: `types`, `services`, `plugins`, and `components`. It defines the dependency graph, the responsibilities of each layer, a nested component layout, and a checklist for adding or moving code.
- **When to use or read it:** Use for folder creation, file moves, new imports, architecture planning, or dependency-violation reviews. Read it before placing code so the layer and allowed imports are decided before implementation.
- **How to use it:** Classify each new or moved file into one layer, then compare every dependency with the rules: components can use plugins and types, plugins can use services, types, and other plugins, services can use services and types, and types can use only types. For components with implementation-specific parts, mirror `components`, `plugins`, and `types` beneath the component directory. Services should expose interfaces to external code, use immutable data, and restrict asynchronous APIs to `Observe<Data>`, `Promise<Data>`, `AsyncGenerator<Data>`, or void actions. The final pseudocode directs the agent to place code, check dependencies, and repair violations such as component-to-service imports; it is documentation, not an executable command.
- **Inputs and outputs:** Inputs are the intended file location, layer classification, imports/dependencies, and—when state plugins are used—the `@adobe/data/ecs` model. Outputs are a structurally placed module, an allowed dependency graph, or identified and corrected layering violations. No files, branches, or repository state are changed by these instructions alone.
- **Relationships:** `components` sit above `plugins`, `services`, and `types`; `plugins` may coordinate services, types, and other plugins; `services` sit above types but below plugins; `types` are the base layer. The file links to `../aidd-namespace/SKILL.md`, which exists in the skills tree and supplies namespace guidance for services and types. It also names the external `@adobe/data/ecs` package for the optional plugin/state pattern.
- **Constraints and cautions:** Never allow components to depend directly on services, services to depend on components or plugins, or types to depend on anything except types. The “plugins” section is conditional on using `@adobe/data/ecs`; verify that dependency and project conventions before applying it. The file gives architectural guidance rather than an automated validator, and its use has no stated security, branch, or repository side effects. No external web links are present.
- **Source basis:** Metadata and applicability: lines 1–4. Layer diagram and dependency rules: lines 6–35. Layer responsibilities and async/interface restrictions: lines 39–59. Nested component structure: lines 61–70. Add/move execution checklist: lines 74–84.
- **Status:** Filled

### `skills/aidd-sudolang-syntax/SKILL.md`

- **What it is:** The complete quick-reference skill for reading and writing SudoLang pseudocode. It supplies examples and rules for interface-like records, inline and block constraints, semantic pattern-to-result mappings, function declarations and modifiers, object/array literals, interpolated strings, comments, logical/math/set/comparison/assignment operators, ternaries, pipelines, and disallowed keywords.
- **When to use or read it:** Use it when a ticket authors or interprets SudoLang in AIDD skills, agent prompts, or related objects. Consult the relevant section while constructing syntax: interfaces for data shapes, constraints and semantic patterns for declarative rules, function sections for callable behavior, literals/templates/comments for data and prose, and operators/control expressions for computation and composition.
- **How to use it:** Model records with brace-delimited names and optional field types; express rules inline or in `Constraints { ... }`; map semantic conditions to outcomes with `(pattern) => result`, including inside constraints. Define inferred functions with `fn`/`function` or use a body without the keyword, optionally add `:modifier` values or a call-time block mixing assignments and constraints, and represent objects/arrays with literal syntax. Use double-quoted or backtick strings with `$` interpolation, compose functions with `|>`, write the shown logical/math/set/comparison/compound-assignment operators and ternary form, and emit a warning when class/inheritance-style disallowed keywords appear.
- **Inputs and outputs:** Input is SudoLang-like pseudocode or an authoring requirement. Output is guidance for valid/readable SudoLang forms and a warning expectation for disallowed class/inheritance syntax; the file performs no parsing, compilation, execution, or artifact generation.
- **Relationships:** The front matter names this skill and its trigger conditions. Its examples connect constraints to agent behavior, including a deterministic-logic mapping to a CLI tool/compiled Bun bundle and judgment-dependent logic mapping to an AI prompt (`SKILL.md:39-61`). The skill is the detailed reference behind the shorter `README.md`; it mentions no required companion files, external links, or repository integration points.
- **Constraints and cautions:** Avoid single-quoted strings because the document says apostrophes in natural language can break syntax highlighting (`SKILL.md:105-118`). `cup` and `cap` are marked deprecated in favor of `union` and `intersection` due to reported Claude 3.5 instability (`SKILL.md:175-179`). Block comments are available but discouraged in nested functions because of token consumption (`SKILL.md:133-147`). The `class Foo extends Bar` example is explicitly disallowed and should trigger a warning (`SKILL.md:215-223`). These are documentation claims, not verified compiler behavior; no security-sensitive guidance, required tools, or branch/repository side effects are present. The `require user to be signed in` example is a pseudocode constraint, not an authentication implementation.
- **Source basis:** `SKILL.md:1-8` (front matter and purpose), `SKILL.md:10-36` (interfaces and constraints), `SKILL.md:39-61` (semantic pattern matching), `SKILL.md:63-98` (functions and modifiers), `SKILL.md:100-131` (object, template, array syntax), `SKILL.md:133-147` (comments), `SKILL.md:149-212` (operators, ternary, and pipe), `SKILL.md:215-223` (disallowed keywords).
- **Status:** Filled

### `skills/aidd-ticket-creator/SKILL.md`

- **What it is:** The coordinator for adaptive phase -> feature -> ticket
  planning, stable IDs, backlog traceability, execution ownership, evidence,
  and exit gates.
- **When to use or read it:** Use for phase/feature/ticket creation, backlog
  grooming, execution of an approved ticket, and lifecycle closeout.
- **How to use it:** Resolve configured artifacts and both open/closed record
  directories, select planning depth, approve each parent before child
  planning, map scope/capabilities/requirements/evidence, maintain current
  index paths, and execute one ticket at a time.
- **Inputs and outputs:** Inputs include the delivery contract, planning
  artifacts, requirements, risks, dependencies, commands, user-validation
  plans, and approval mode. Outputs include stable-ID records, coverage links,
  ticket gates, statuses, evidence links, and completion updates.
- **Relationships:** Coordinates the new planning skills, requirements,
  orchestrator, `/plan`, `/execute`, TDD, review, evidence, commit, and PR.
- **Constraints and cautions:** Missing, blocked, or closed parents stop child
  planning; tickets are focused by observable scope rather than line count; no
  silent scope expansion, stale indexes, duplicate records, skipped gates,
  invented commands, or ticket closure without user-validation evidence.
- **Source basis:** `skills/aidd-ticket-creator/SKILL.md:1-end`.
- **Status:** Workflow updated

### `skills/aidd-tdd/SKILL.md`

- **What it is:** The authoritative repository-appropriate test and verification process for approved tickets, covering baseline, code TDD, real-system flows, local gates, evidence, and coverage gaps.
- **When to use or read it:** Use for implementation, test writing, bug fixes, functionality validation, and any ticket that needs a defensible verification method.
- **How to use it:** Discover commands from configuration, manifests, CI, and guidance; classify the ticket method; record protected baseline; run failing-first tests for code behavior or the strongest non-code evidence; rerun regressions and configured gates; return exact user-validation steps and wait for the user's result; then hand off to review and the configured commit/push/PR or local-delivery closeout.
- **Inputs and outputs:** Inputs are requirements, protected flows, repository tooling, local stack, commands, and gate policy. Outputs are a `TestPlan`, recorded results, implementation verification, and explicit blockers or coverage gaps.
- **Relationships:** Integrates with `aidd-evidence`, `/execute`,
  `/run-preimplementation-checklist`, `/aidd-fix`, user testing, review, and
  domain workflow interfaces.
- **Constraints and cautions:** Never assume a framework or command, hide a
  baseline failure, claim an unrun result, or treat unavailable
  browser/service/integration capability as passed. Code TDD still requires a
  failing regression before implementation; the post-implementation handoff,
  user result, review, and configured delivery closeout are required before
  closure.
- **Source basis:** `skills/aidd-tdd/SKILL.md:1-end`.
- **Status:** Workflow updated

### `skills/aidd-timing-safe-compare/SKILL.md`

- **What it is:** The executable-style skill instruction and review policy for timing-safe secret comparison. It describes prefix-timing “hangman” attacks, bans direct raw-secret comparison and several named APIs/techniques, requires SHA3-256 hashing of both operands, gives three reasons for the policy, and defines Guide and Review patterns with finding severities and messages.
- **When to use or read it:** Read it when implementing or reviewing secret-token comparisons, including token validation, CSRF checks, API-key checks, and related authentication decisions. In review, use its branches to distinguish raw equality (critical), SHA3-256 digest equality (approved), and a standard timing-safe API applied directly to raw secrets (medium).
- **How to use it:** For implementation, put SHA3-256 in a named helper, hash the stored and candidate values, compare the digests, and retain a comment explaining the choice. For review, raise the specified CRITICAL finding for raw or plaintext equality without prior SHA3-256, do not flag SHA3-256 digests compared with `===`, and raise the specified MEDIUM finding for standard-library timing-safe comparison of raw secrets. It says the hash strategy may be used with or without an additional timing-safe compare call.
- **Inputs and outputs:** Inputs are source code containing a secret comparison and the stored/candidate token values. Outputs are an implementation pattern or a review classification: approved digest equality, a CRITICAL security bug with the quoted “hangman attacks” message, or a MEDIUM security bug with the quoted non-hash timing-safe-algorithm message. The skill itself has no file or branch side effects.
- **Relationships:** The front matter identifies this as `aidd-timing-safe-compare`; line 19 links to `references/vulnerabilities.md`. `timing-safe-compare.test.js` expects this file to mention Node `createHash("sha3-256")`, a named helper, `do not flag`, and “major”; the current file contains the named-helper and review wording but does not contain `createHash("sha3-256")`, so that assertion would fail as written. The test also references `../aidd-review/SKILL.md`, which exists, and a repository-root `ai-evals/aidd-review/fixtures/utils.js`, which is missing.
- **Constraints and cautions:** This is security-sensitive guidance that overrides library defaults and categorically rejects `crypto.timingSafeEqual`, `hmac.compare_digest`, `subtle.ConstantTimeCompare`, XOR accumulation, and raw string comparison. Its assertion that digest `===` is safe and its claims about eliminating timing/length oracles are policy claims with questionable generality; reviewers should not infer that hashing alone addresses encoding, input normalization, hash misuse, side channels in surrounding code, or secret storage. The file uses a nonstandard `Patterns { ... }` notation rather than executable syntax. It has no required tools, external URLs, or branch/repository side effects.
- **Source basis:** `aidd-timing-safe-compare/SKILL.md:1-4` (metadata); `:6-24` (threat model, prohibitions, required SHA3-256 process, and rationale); `:26-35` (Guide/Review decision rules and finding severities).
- **Status:** Filled

### `skills/aidd-ui/SKILL.md`

- **What it is:** The executable skill definition for a UI/UX Engineer persona. It directs the agent to produce polished, friendly interfaces and subtle motion, while applying accessibility, responsive-design, and existing design-system practices. Its metadata identifies the skill as `aidd-ui` and scopes it to UI components, styling, animation, accessibility, responsive design, and design systems.
- **When to use or read it:** Use for frontend UI work or design decisions involving CSS, HTML, JavaScript, React, visual design, animation or motion, accessibility, responsive layouts, or design systems. It is especially relevant before building components because it explicitly requires using the project’s existing design system and Storybook components.
- **How to use it:** Adopt the stated UI/UX and motion-design role; inspect and reuse the project design system and Storybook components; then implement interfaces that are intuitive, accessible, visually appealing, and enhanced by restrained, satisfying motion. Treat the listed skills as the scope of expertise rather than as a prescribed command sequence.
- **Inputs and outputs:** Inputs are a UI implementation or design-decision ticket, the project’s existing design-system and Storybook components, and the applicable frontend context. Outputs are UI/component implementations or design decisions covering the listed technologies and qualities; the file does not define a schema, command, generated artifact format, or acceptance-test format.
- **Relationships:** The skill complements `aidd-ui/README.md`, whose overview explains when and why to invoke it. It expects an existing project design system and Storybook component library, but names no concrete files, packages, routes, or external resources.
- **Constraints and cautions:** The guidance is qualitative and uses subjective language such as “top-tier,” “extraordinarily good taste,” and “most beautiful,” so concrete design decisions still require project context. Accessibility, responsiveness, and design-system reuse are explicit requirements; motion should remain subtle and UX-oriented. No security-sensitive instructions, external links, required tools, branch operations, repository side effects, or missing referenced files are specified.
- **Source basis:** `.github/skills/aidd-ui/SKILL.md:1-4` (metadata); `:6-10` (UI/UX and design-system instructions); `:12-24` (skill scope).
- **Status:** Filled

### `skills/aidd-upskill/SKILL.md`

- **What it is:** The skill-authoring and maintenance contract for creating, reviewing, refactoring, and evaluating reusable AIDD skills.
- **When to use or read it:** Use when a repeated workflow needs a new skill, an existing skill is stale or duplicated, or a skill needs clearer inputs, outputs, boundaries, and tests.
- **How to use it:** Start with the smallest useful contract, define the skill's trigger and interface, separate deterministic checks from judgment, load detailed references progressively, and evaluate pure reasoning separately from side effects.
- **Inputs and outputs:** Inputs are the candidate behavior, repository conventions, affected workflow, dependencies, interfaces, and evaluation needs. Outputs are a focused `SKILL.md`, supporting references/README/evals when needed, and a change record with evidence.
- **Relationships:** Integrates with skill discovery, SudoLang syntax, workflow-interface, delegation, evidence, and lifecycle evaluation.
- **Constraints and cautions:** Do not duplicate lifecycle ownership in domain skills, do not hide side effects in prose-only reasoning, and do not claim a skill is complete without validating its interface, examples, references, and applicable evals.
- **Source basis:** `skills/aidd-upskill/SKILL.md:1-end`.
- **Status:** Workflow updated

### `skills/aidd-user-testing/SKILL.md`

- **What it is:** The user-journey testing and functionality-evidence contract for human studies, browser-agent flows, baselines, regressions, screenshots, artifacts, and blockers.
- **When to use or read it:** Use when a journey needs usability research, repeatable functionality validation, baseline/regression coverage, or real-browser evidence.
- **How to use it:** Classify the purpose, build a charter with setup/data/steps/expected visible and persisted effects/cleanup/failure paths, generate paired scripts, execute only with supported capabilities, return the post-implementation user-validation handoff, and record each flow outcome.
- **Inputs and outputs:** Inputs are a journey/persona, ticket requirements, protected flows, repository stack, and UI evidence policy. Outputs are human/agent scripts, user-validation handoffs, reports, artifacts, statuses, and coverage gaps.
- **Relationships:** It explicitly depends on `UserJourney`/`Persona` from `/aidd-product-manager` and on journey YAML at `$projectRoot/plan/story-map/${journey-name}.yaml`; the referenced story-map directory is missing in the inspected repository, while the `aidd-product-manager` skill directory exists. Its commands are also expected by `user-testing.test.js` as `.github/commands/user-test.md` and `.github/commands/run-test.md`, but those files are missing here.
- **Constraints and cautions:** Usability and required functionality tests are distinct; unavailable browser/integration capability is blocked or skipped with reason, not passed; secrets and destructive test-state cleanup require explicit handling; tickets remain open until required user validation is confirmed.
- **Source basis:** `skills/aidd-user-testing/SKILL.md:1-end`.
- **Status:** Workflow updated

### `skills/aidd-write/SKILL.md`

- **What it is:** The `aidd-write` skill is a writing-authoring and writing-evaluation guide. Its frontmatter identifies it as a top-tier author skill for writing, reviewing, editing, or scoring content, with the goal of communicating essential truths persuasively and inspiring constructive change. It names supporting disciplines including creative and technical writing, storytelling, psychology, empathy, conversion optimization, solution-space mapping, and qualitative discernment.
- **When to use or read it:** Use it when a ticket requires creating, reviewing, revising, or quantitatively evaluating content. Before writing, it requires restating the prompt and inferring or restating the desired metrics, goals, and criteria. For evaluation work, choose the review or score command; for revision, use edit with a supplied review or have edit perform review first.
- **How to use it:** Structure the thinking workflow as: restate the ticket, generate ideas, reflect critically, expand from orthogonal perspectives, score/rank/evaluate, then respond. `--compact` compresses the intermediate stages into dense associative phrases and requires explicit causal links in reflection and scoring; the final response remains complete, standalone, and structured. `--depth` accepts 1–10 and controls response density, defaulting to 10. The base `/aidd-write` command applies the writing guidance to a prompt plus optional context, goal, and criteria. `review` scores and lists quality-principle violations without changing the writing; `edit` applies a review to produce an improved version; `score` gives quantified and qualitative criterion scores justified by passages from the supplied writing.
- **Inputs and outputs:** Inputs are a writing prompt, optional context, goal, criteria, existing writing, and optionally a review. The base command outputs a finished response. `review` outputs scores and reasons for any failure to achieve the goal, with no edits. `edit` outputs revised writing. `score` outputs criterion-by-criterion quantified and qualitative assessments tied to source passages. The file defines pseudo-code functions and slash-command interfaces; it does not define a program or create repository artifacts.
- **Relationships:** The frontmatter description determines when the skill is relevant. The `write()` rule delegates its prewriting restatement to the compact `think` workflow. The style constraints govern the base writing command and provide the principles assessed by `review` and `score`. The command variants form a workflow: write, optionally review, then edit; score independently evaluates the supplied text.
- **Constraints and cautions:** Write with purpose using simple declarative sentences, complete thoughts, strong voice, layered meaning, high signal-to-noise, empathy, kindness, confidence, and plain truth. Avoid clichés, filler, condescension, hedging, and excessive em dashes; cut words that do not add value. The instruction to “show work” and expose an explicit reasoning chain is questionable for systems that must not disclose private chain-of-thought; interpret it as a request for concise rationale or structured results rather than hidden internal reasoning. “CBT” and psychology are listed as influences, not as clinical advice or a substitute for professional care. No referenced files or external links are present, no tools are required, and no branch or repository side effects are specified.
- **Source basis:** - Lines 1–7: frontmatter name and applicability description. - Lines 9–14: authorial purpose and reader-facing approach. - Lines 16–31: listed supporting skills and disciplines. - Lines 33–37: staged `think` workflow. - Lines 39–49: `--compact` and `--depth` options. - Lines 51–53: mandatory prewriting restatement rule. - Lines 55–74: writing principles and stylistic constraints. - Lines 76–84: base, review, edit, and score command behavior.
- **Status:** Filled

### `skills/clean-pr-branch/SKILL.md`

- **What it is:** The executable evidence-preserving cleanup specification for removing disposable AI scaffolding from Git tracking while preserving real code, evidence, and protected files.
- **When to use or read it:** Use before a PR or when syncing approved real-file changes, with dry-run as the default.
- **How to use it:** Read configuration and active evidence, preview tracked paths and retention risks, require explicit `--apply` for mutation, use `git rm --cached`, update ignore rules, preserve evidence, and verify against the configured base.
- **Inputs and outputs:** Inputs are the current branch, configuration, evidence, provider/base policy, path constants, and mode. Outputs are a report or a cleanup/sync commit; source and evidence files remain on disk.
- **Relationships:** `references/process.md` supplies the concrete detection, branch, untracking, ignore-file, restoration, commit, verification, and sync procedures. `README.md` is the user-facing overview and links back to this file for the single source of truth. The protected `cdaas_manifest.json` is specifically preserved even though broad path handling otherwise defaults to treating non-scaffold paths as real code.
- **Constraints and cautions:** Scaffolding is never deleted from disk: tracked paths are removed only from Git with `git rm --cached`; already-untracked or already-ignored paths are skipped without duplicate work. A protected file caught by removal is restored from `main` with a warning, which assumes that branch exists and may replace the working copy with the version from `main`. A no-op cleanup must not create a branch, and a no-op sync reports `nothing to sync`; sync also requires an existing PR branch. Branch checkout, index changes, commits, and later verification affect repository state. No external links or security-specific instructions are present, but the workflow has consequential Git side effects and treats every new non-scaffold top-level path as code by default.
- **Source basis:** `github 1/.github/skills/clean-pr-branch/SKILL.md:1-8` (metadata and purpose); `:10-35` (scaffold/protected constants and default path policy); `:37-50` (commands and process reference); `:52-67` (constraints).
- **Status:** Workflow updated

### `skills/create-vision/SKILL.md`

- **What it is:** The executable specification for the `create-vision` skill. It defines a repository-discovery, user-interview, drafting, review, and write pipeline for producing `vision.md` as a constraint document and source of truth, rather than as a descriptive README.
- **When to use or read it:** Use when starting a project, onboarding a repository into the AIDD workflow, or creating a missing `vision.md`. Use `/create-vision` for the complete pipeline or `/create-vision draft` for independently testable thinking that only populates the template and does not perform the final write.
- **How to use it:** Run repository discovery, ask or infer the five core questions, optionally capture durable delivery constraints, quality gates, supported environments, evidence expectations, and operational-readiness rules, populate the template, present inferred/TBD sections for confirmation, and write only after approval.
- **Inputs and outputs:** Inputs are repository files and structure, any existing vision or architecture material, and user answers to the five interview questions. Discovery facts can pre-fill sections and suppress redundant questions. The full command outputs `vision.md` at the target repository root; draft mode produces only a thinking-stage template population. The write step can modify the repository by creating or updating that root file.
- **Relationships:** It imports `references/vision_template.md` (line 20) and uses that file’s sections and preamble. `README.md` provides a shorter user-facing overview of the same command and output. The workflow expects an interactive question capability (`vscode_askQuestions` or equivalent), but no implementation of that tool is included here. The discovery list names conditional target-repository inputs; they are not bundled with this skill. No external links are present.
- **Constraints and cautions:** The resulting document must govern future work and must not merely describe the current system. Existing `vision.md` requires user approval before overwrite; contradictions between discovery and interview must be surfaced for user resolution; skipped answers become explicit TBD content; no section may be silently empty; and architectural rows without rationales are omitted rather than invented. Inferred sections require confirmation during review. The discovery mentions GDPR, security, and compliance signals, but this is an extraction prompt, not a compliance or security assessment. The only stated repository side effect is writing the root `vision.md`; no branch, commit, push, or deployment behavior is specified.
- **Source basis:** Metadata and vision framing: lines 1–20. Commands and pipeline: lines 22–41. Discovery inputs and extracted facts: lines 43–61. Interview questions and tool behavior: lines 63–82. Draft rules and constraint test: lines 84–105. Review and write behavior: lines 106–117. Safety and completeness constraints: lines 119–128.
- **Status:** Workflow updated

### `skills/aidd-evidence/README.md`

- **What it is:** A user-facing overview of the append-only delivery-evidence
  skill. It explains requirement and flow traceability, baseline and gate
  outcomes, artifacts, blockers, warnings, redaction, and readiness summaries.
- **When to use or read it:** Read it when a ticket needs auditable proof,
  uncertain results need explicit classification, or a review/PR needs a
  readiness decision.
- **How to use it:** Use `/evidence` or the detailed skill to create one record
  per ticket, append execution, verification, and `userValidation` results, and
  summarize whether the ticket is ready, blocked, or complete with concerns.
- **Inputs and outputs:** Inputs are the ticket contract, requirements,
  commands, results, artifacts, blockers, warnings, and the user's terminal
  validation result. Output is `evidence/{ticket-slug}.md` or the configured
  evidence path.
- **Relationships:** Summarizes `skills/aidd-evidence/SKILL.md` and
  `prompts/evidence.prompt.md`; it is consumed by planning, execution, review,
  PR, testing, and cleanup workflows.
- **Constraints and cautions:** Records are append-only, required gates cannot
  be silently skipped, sensitive data must be redacted, unavailable evidence is
  not a success result, and required user validation is part of closure
  readiness.
- **Source basis:** `skills/aidd-evidence/README.md:1-end`.
- **Status:** Workflow updated

### `skills/aidd-evidence/SKILL.md`

- **What it is:** The authoritative delivery-evidence and readiness contract
  for requirements, user flows, baselines, gates, artifacts, blockers,
  warnings, and final status.
- **When to use or read it:** Load it for any implementation, test, review,
  bug fix, PR, delegation, or closeout that must prove what happened.
- **How to use it:** Initialize or locate the ticket record, preserve the
  baseline, append each check with command/result/artifact details, map
  requirements and flows to evidence, append user-validation, review, commit,
  push, and PR results, classify missing or failed proof, and produce a
  readiness summary.
- **Inputs and outputs:** Inputs are delivery context, ticket requirements,
  verification steps, command results, UI artifacts, remote states, and
  blockers. Output is an append-only markdown evidence record plus a
  `ready`, `readyWithConcerns`, `blocked`, or `notReady` classification.
- **Relationships:** Shared by `aidd-please`, orchestrator, ticket creator,
  TDD, execution, fix, user testing, review, PR, pipeline, parallel,
  cleanup, and commit workflows.
- **Constraints and cautions:** Use the configured evidence path; distinguish
  `passed`, `passedWithConcerns`, `failed`, `blocked`, and
  `skippedWithReason`; never infer a required gate from another check or claim
  readiness without evidence. Review and configured commit/push/PR evidence
  are separate delivery gates, and required user-validation evidence is part
  of closure readiness when configured.
- **Source basis:** `skills/aidd-evidence/SKILL.md:1-end`.
- **Status:** Workflow updated

### `prompts/evidence.prompt.md`

- **What it is:** The `/evidence` command prompt for initializing, appending,
  and summarizing a ticket's delivery-evidence record.
- **When to use or read it:** Use after discovery, planning, execution,
  verification, review, or PR activity when the evidence record needs an
  explicit update.
- **How to use it:** Invoke `/evidence` with the ticket context and requested
  action; follow the evidence skill and configured path, and report blockers or
  unavailable proof instead of manufacturing a pass.
- **Inputs and outputs:** Input is a ticket, requirement, flow, check, artifact,
  or readiness request. Output is an append-only evidence update or readiness
  summary.
- **Relationships:** Loads `skills/aidd-evidence/SKILL.md` and honors
  `aidd-config.yml`, `copilot-instructions.md`, and the active ticket contract.
- **Constraints and cautions:** Do not overwrite prior records, expose secrets,
  silently skip required gates, or treat a missing command/artifact as a pass.
- **Source basis:** `prompts/evidence.prompt.md:1-end`.
- **Status:** Workflow updated

### `skills/workflow-interface.md`

- **What it is:** A shared interface for domain skills to consume delivery
  context without owning lifecycle orchestration.
- **When to use or read it:** Read it whenever a domain skill is loaded during
  implementation, review, testing, security, UI, or infrastructure work.
- **How to use it:** Apply the active ticket scope, requirements, configured
  commands and gates, evidence rules, approval state, and provider boundaries;
  return domain findings, verification evidence, and an advisory next-step hint
  to the lifecycle owner.
- **Inputs and outputs:** Input is the shared workflow context. Output is
  domain-scoped implementation guidance, findings, evidence contributions, and
  an optional next-step hint.
- **Relationships:** Imported by the domain skills listed in the file; lifecycle
  ownership remains with `aidd-agent-orchestrator` and the relevant workflow
  skill.
- **Constraints and cautions:** Domain skills must not create phases/features/
  tickets, own branches or PRs, approve their own work, or declare delivery
  readiness without the lifecycle evidence contract. Their next-step hint is
  advisory; the orchestrator owns the authoritative recommendation.
- **Source basis:** `skills/workflow-interface.md:1-end`.
- **Status:** Workflow updated

### `skills/planning-artifact-lifecycle.md`

- **What it is:** The shared storage and transition contract for individual
  phase, feature, and ticket records.
- **When to use or read it:** Read whenever a planning record is created,
  reviewed, groomed, completed, cancelled, reopened, or moved by an approved
  change.
- **How to use it:** Resolve configured layer indexes and `open`/`closed`
  directories, create new records in `open`, move the same stable-ID file when
  status classification changes, and synchronize indexes, parent links, and
  path history.
- **Inputs and outputs:** Input is delivery configuration and a planning record
  status transition; output is a single current record path plus synchronized
  indexes and auditable movement metadata.
- **Relationships:** Used by phase, feature, ticket, planning bootstrap,
  grooming, feedback, review, change-control, checklist, execution, and
  orchestrator workflows.
- **Constraints and cautions:** Blocked records remain open; closed records
  cannot receive new children or implementation work; never delete, duplicate,
  or silently archive a record.
- **Source basis:** `skills/planning-artifact-lifecycle.md:1-end`.
- **Status:** Workflow updated

### `prompts/planning-bootstrap.prompt.md`

- **What it is:** The `/planning-bootstrap` entrypoint for inspecting planning
  context, selecting adaptive depth, and stopping before unauthorized child generation.
- **When to use or read it:** Use when onboarding a repository or reconciling
  missing, stale, or inconsistent planning artifacts.
- **How to use it:** Invoke `/planning-bootstrap`, resolve configured paths and
  IDs, inspect both open and closed records and their current paths, and report
  the next approval or blocker.
- **Inputs and outputs:** Input is a repository request and existing context;
  output is a planning-context report or authorized bootstrap artifact.
- **Relationships:** `skills/aidd-planning-bootstrap/SKILL.md`,
  `aidd-config.yml`, and repository-map/capability planning.
- **Constraints and cautions:** It is not an implementation command and must
  not silently create phases, features, or tickets.
- **Source basis:** `prompts/planning-bootstrap.prompt.md:1-end`.
- **Status:** Workflow updated

### `prompts/create-repository-map.prompt.md`

- **What it is:** The `/create-repository-map` entrypoint for documenting
  important source, test, documentation, automation, and infrastructure surfaces.
- **When to use or read it:** Use before capability or feature planning when
  repository structure is unknown or stale.
- **How to use it:** Invoke the prompt, inspect the repository evidence, group
  paths by role, and record unknown or unverified areas rather than guessing.
- **Inputs and outputs:** Input is the repository and configured map path;
  output is a durable map or a read-only coverage report.
- **Relationships:** `skills/aidd-create-repository-map/SKILL.md`,
  `aidd-planning-bootstrap`, and the discovery contract.
- **Constraints and cautions:** It must not infer architecture from filenames
  alone or modify source code.
- **Source basis:** `prompts/create-repository-map.prompt.md:1-end`.
- **Status:** Workflow updated

### `prompts/create-capability-map.prompt.md`

- **What it is:** The `/create-capability-map` entrypoint for mapping approved
  scope to system or operational abilities.
- **When to use or read it:** Use after objective and scope approval and before
  creating phases or features.
- **How to use it:** Invoke the prompt, assign stable capability IDs, link each
  ability to scope and evidence, and run the coverage check.
- **Inputs and outputs:** Input is approved objective/scope and repository map;
  output is a capability map and approval/blocker report.
- **Relationships:** `skills/aidd-create-capability-map/SKILL.md`,
  `aidd-requirements`, and `/create-phases`.
- **Constraints and cautions:** Describe abilities, not technical buckets;
  do not create phase, feature, or ticket children.
- **Source basis:** `prompts/create-capability-map.prompt.md:1-end`.
- **Status:** Workflow updated

### `prompts/create-phases.prompt.md`

- **What it is:** The `/create-phases` entrypoint for defining top-level
  delivery stages and their boundaries.
- **When to use or read it:** Use after scope and capability coverage are
  approved, before feature decomposition.
- **How to use it:** Invoke the prompt, define sequence rationale, outcomes,
  entry/exit conditions, dependencies, risks, validation focus, and current
  open/closed record paths.
- **Inputs and outputs:** Input is approved objective, scope, and capabilities;
  output is an ordered phase index and phase records in the configured open or
  closed directories, plus an approval decision.
- **Relationships:** `skills/aidd-create-phases/SKILL.md`,
  `aidd-ticket-creator`, and `/create-features`.
- **Constraints and cautions:** A phase must have delivery meaning; arbitrary
  calendar buckets and unapproved child generation are rejected.
- **Source basis:** `prompts/create-phases.prompt.md:1-end`.
- **Status:** Workflow updated

### `prompts/create-features.prompt.md`

- **What it is:** The `/create-features` entrypoint for grouping capabilities
  into outcome-based features inside one phase.
- **When to use or read it:** Use after a phase is approved and ready for
  outcome decomposition.
- **How to use it:** Invoke the prompt with a phase, assign stable feature IDs,
  define outcome/scope/non-goals, link capabilities, record validation intent,
  and create new records in the configured open directory.
- **Inputs and outputs:** Input is one approved phase and its capabilities;
  output is a feature index with current open/closed paths or a blocker for
  missing parent coverage.
- **Relationships:** `skills/aidd-create-features/SKILL.md`, `/create-tickets`,
  and `aidd-planning-layer-review`.
- **Constraints and cautions:** Each feature belongs to exactly one phase and
  must not be a technical layer disguised as an outcome.
- **Source basis:** `prompts/create-features.prompt.md:1-end`.
- **Status:** Workflow updated

### `prompts/create-tickets.prompt.md`

- **What it is:** The `/create-tickets` entrypoint for deriving focused
  implementation and validation tickets from one approved feature.
- **When to use or read it:** Use when a feature has approved scope and needs
  an executable backlog.
- **How to use it:** Invoke the prompt with a feature ID, create stable ticket
  IDs in the configured open directory, define boundaries/acceptance/
  validation/dependencies, and update the backlog with current paths.
- **Inputs and outputs:** Input is one approved feature and its phase/capability
  ancestry; output is focused ticket records in open/closed directories and
  backlog coverage.
- **Relationships:** `skills/aidd-create-tickets/SKILL.md`,
  `aidd-ticket-creator`, `/execute`, and `/groom-backlog`.
- **Constraints and cautions:** Reject oversized or cross-feature tickets and
  do not mark readiness without evidence prerequisites.
- **Source basis:** `prompts/create-tickets.prompt.md:1-end`.
- **Status:** Workflow updated

### `prompts/review-planning-layer.prompt.md`

- **What it is:** The `/review-planning-layer` read-only gate for checking one
  planning artifact against its ancestors, children, and evidence.
- **When to use or read it:** Use before deriving a child layer or after a
  planning change.
- **How to use it:** Invoke the prompt with a layer or stable ID and classify
  coverage, link, status, boundary, approval, and evidence findings.
- **Inputs and outputs:** Input is a planning artifact and related records;
  output is an approved, noted, or needs-revision review.
- **Relationships:** `skills/aidd-planning-layer-review`, planning prompts,
  `aidd-evidence`, and the orchestrator.
- **Constraints and cautions:** Review does not create missing children, move
  files, rewrite upstream plans, or declare delivery readiness from missing
  evidence; it reports status/path and stale-index mismatches.
- **Source basis:** `prompts/review-planning-layer.prompt.md:1-end`.
- **Status:** Workflow updated

### `prompts/groom-backlog.prompt.md`

- **What it is:** The `/groom-backlog` entrypoint for routine backlog
  clarification, ordering, deduplication, and stale-status handling.
- **When to use or read it:** Use while implementation is underway to keep the
  next ticket executable.
- **How to use it:** Invoke the prompt, inspect both lifecycle directories,
  dependencies, and readiness, make traceable hygiene updates, move a record
  only for an authorized status transition, and route material changes to
  change control.
- **Inputs and outputs:** Input is the configured backlog and planning context;
  output is a grooming report or authorized routine update.
- **Relationships:** `skills/aidd-groom-backlog`, `/plan`, and
  `/replan-when-necessary`.
- **Constraints and cautions:** Grooming must not silently change outcomes,
  scope, capabilities, phase boundaries, or stable IDs; it must not duplicate
  or archive records outside the open/closed transition protocol.
- **Source basis:** `prompts/groom-backlog.prompt.md:1-end`.
- **Status:** Workflow updated

### `prompts/phase-feedback.prompt.md`

- **What it is:** The `/phase-feedback` entrypoint for comparing planned phase
  outcomes with delivered evidence and lessons.
- **When to use or read it:** Use after a phase reaches delivery or has
  significant evidence, review, or stakeholder feedback.
- **How to use it:** Invoke the prompt with a phase ID, inspect its current
  open/closed path and linked records, classify observations, blockers,
  corrections, and material changes, then record follow-up work.
- **Inputs and outputs:** Input is a phase, linked features/tickets, and
  evidence; output is a durable feedback record and bounded dispositions.
- **Relationships:** `skills/aidd-phase-feedback`, `aidd-evidence`, and change
  control.
- **Constraints and cautions:** Preserve history and do not silently rewrite
  downstream planning from an observation; a terminal phase move requires
  evidence, child completion, approval, and index synchronization.
- **Source basis:** `prompts/phase-feedback.prompt.md:1-end`.
- **Status:** Workflow updated

### `prompts/replan-when-necessary.prompt.md`

- **What it is:** The `/replan-when-necessary` entrypoint for deciding whether
  new evidence needs local correction or material replanning.
- **When to use or read it:** Use when scope, outcome, capability, dependency,
  sequence, risk, or gates materially change.
- **How to use it:** Invoke the prompt, compare approved and requested state,
  identify the smallest affected subtree, record impact, and obtain approval.
- **Inputs and outputs:** Input is a change request and planning/evidence
  context; output is a no-change, routine, or material-change decision.
- **Relationships:** `skills/aidd-change-control`, `/groom-backlog`,
  `/phase-feedback`, and planning-layer review.
- **Constraints and cautions:** Do not use formal replanning for routine
  backlog hygiene or bypass stable IDs and history.
- **Source basis:** `prompts/replan-when-necessary.prompt.md:1-end`.
- **Status:** Workflow updated

### `prompts/run-preimplementation-checklist.prompt.md`

- **What it is:** The `/run-preimplementation-checklist` stop/go gate for an
  active ticket.
- **When to use or read it:** Use immediately before implementing a ticket in
  a non-trivial planning hierarchy.
- **How to use it:** Invoke the prompt with a ticket ID and verify ancestry,
  approvals, open/closed path, scope, dependencies, baseline, commands, gates,
  ownership, user-validation plan, and evidence.
- **Inputs and outputs:** Input is the active ticket and all required planning
  records; output is an auditable ready or not-ready decision.
- **Relationships:** `skills/aidd-preimplementation-checklist`, `/execute`,
  `aidd-tdd`, and `aidd-evidence`.
- **Constraints and cautions:** Missing or non-terminal prerequisites keep the
  ticket not ready; a closed ticket or ancestor is rejected as active work, and
  the checklist never implements or moves records.
- **Source basis:** `prompts/run-preimplementation-checklist.prompt.md:1-end`.
- **Status:** Workflow updated

### `skills/aidd-planning-bootstrap/README.md`

- **What it is:** Overview of the planning bootstrap skill and its safe
  repository-onboarding role.
- **When to use or read it:** Use when installing the planning workflow or
  deciding how to start a new project.
- **How to use it:** Follow the adaptive-depth and artifact-reconciliation
  flow described by the detailed skill, including both open and closed
  planning-record directories.
- **Inputs and outputs:** Input is repository context; output is a planning
  context and explicit next-layer decision.
- **Relationships:** Summarizes `skills/aidd-planning-bootstrap/SKILL.md` and
  `/planning-bootstrap`.
- **Constraints and cautions:** It does not authorize downstream generation
  or implementation by itself.
- **Source basis:** `skills/aidd-planning-bootstrap/README.md:1-end`.
- **Status:** Workflow updated

### `skills/aidd-create-repository-map/README.md`

- **What it is:** Overview of the repository-surface mapping skill.
- **When to use or read it:** Use before capability planning when repository
  structure or tooling is not yet durable.
- **How to use it:** Inspect real paths and record source, test, docs,
  automation, infrastructure, ownership, and unknowns.
- **Inputs and outputs:** Input is a repository; output is a map or coverage
  report.
- **Relationships:** Summarizes the colocated skill and `/create-repository-map`.
- **Constraints and cautions:** The map is evidence-backed documentation, not
  an implementation plan.
- **Source basis:** `skills/aidd-create-repository-map/README.md:1-end`.
- **Status:** Workflow updated

### `skills/aidd-create-capability-map/README.md`

- **What it is:** Overview of capability mapping from approved scope.
- **When to use or read it:** Use before phase and feature decomposition.
- **How to use it:** Link stable capabilities to outcomes, scope, evidence,
  prerequisites, and coverage.
- **Inputs and outputs:** Input is approved objective/scope and a repository
  map; output is a capability map and approval report.
- **Relationships:** Summarizes the colocated skill and `/create-capability-map`.
- **Constraints and cautions:** Capabilities describe abilities, not technical
  implementation buckets.
- **Source basis:** `skills/aidd-create-capability-map/README.md:1-end`.
- **Status:** Workflow updated

### `skills/aidd-create-phases/README.md`

- **What it is:** Overview of outcome-oriented phase planning.
- **When to use or read it:** Use after capability coverage is approved.
- **How to use it:** Define sequence, outcome, boundaries, entry/exit
  conditions, dependencies, risks, and validation focus; create new records in
  `open` and move terminal records to `closed`.
- **Inputs and outputs:** Input is approved scope/capabilities; output is a
  reviewed phase index with current record paths.
- **Relationships:** Summarizes the colocated skill and `/create-phases`.
- **Constraints and cautions:** Phases need delivery meaning and approved
  parents; they are not arbitrary calendar buckets.
- **Source basis:** `skills/aidd-create-phases/README.md:1-end`.
- **Status:** Workflow updated

### `skills/aidd-create-features/README.md`

- **What it is:** Overview of outcome-based features inside a phase.
- **When to use or read it:** Use after phase approval and before ticket
  decomposition.
- **How to use it:** Group capabilities into one-phase outcome slices with
  explicit scope, non-goals, risks, and validation; create new records in
  `open` and move terminal records to `closed`.
- **Inputs and outputs:** Input is an approved phase; output is a feature index
  with current record paths and coverage report.
- **Relationships:** Summarizes the colocated skill and `/create-features`.
- **Constraints and cautions:** A feature is not a backend/frontend bucket and
  cannot span multiple phases.
- **Source basis:** `skills/aidd-create-features/README.md:1-end`.
- **Status:** Workflow updated

### `skills/aidd-create-tickets/README.md`

- **What it is:** Overview of focused ticket decomposition from one feature.
- **When to use or read it:** Use when an approved feature is ready for an
  executable backlog.
- **How to use it:** Create stable, independently verifiable ticket records in
  `open` with scope, non-goals, dependencies, acceptance, validation, and
  evidence links; move terminal records to `closed`.
- **Inputs and outputs:** Input is one approved feature; output is ticket
  records and backlog updates with current paths.
- **Relationships:** Summarizes the colocated skill, `/create-tickets`, and
  `/execute`.
- **Constraints and cautions:** Oversized, cross-feature, or under-specified
  tickets are rejected.
- **Source basis:** `skills/aidd-create-tickets/README.md:1-end`.
- **Status:** Workflow updated

### `skills/aidd-planning-layer-review/README.md`

- **What it is:** Overview of the read-only review gate for planning layers.
- **When to use or read it:** Use before generating child artifacts or after
  plan changes.
- **How to use it:** Check stable IDs, parent links, coverage, boundaries,
  statuses, approvals, evidence, both lifecycle directories, and index paths.
- **Inputs and outputs:** Input is a planning layer and its context; output is
  an approval, notes, or revision decision.
- **Relationships:** Summarizes the colocated skill and
  `/review-planning-layer`.
- **Constraints and cautions:** Review does not create children, move files, or
  rewrite upstream artifacts; it reports status/path mismatches.
- **Source basis:** `skills/aidd-planning-layer-review/README.md:1-end`.
- **Status:** Workflow updated

### `skills/aidd-groom-backlog/README.md`

- **What it is:** Overview of routine backlog hygiene without silent replanning.
- **When to use or read it:** Use during implementation to keep the next
  ticket clear and correctly ordered.
- **How to use it:** Clarify, deduplicate, resequence, or mark stale items,
  move records only for authorized status transitions, synchronize indexes,
  then route material changes to change control.
- **Inputs and outputs:** Input is the backlog and planning context; output is
  a grooming report or authorized hygiene update.
- **Relationships:** Summarizes the colocated skill and `/groom-backlog`.
- **Constraints and cautions:** Preserve IDs, parent links, scope, path history,
  and index synchronization; do not archive or duplicate records.
- **Source basis:** `skills/aidd-groom-backlog/README.md:1-end`.
- **Status:** Workflow updated

### `skills/aidd-phase-feedback/README.md`

- **What it is:** Overview of phase-outcome feedback and learning capture.
- **When to use or read it:** Use after phase delivery or meaningful evidence.
- **How to use it:** Compare intended and actual outcomes, classify findings,
  record bounded follow-up work, and move a phase between open/closed only
  after approved evidence and child completion.
- **Inputs and outputs:** Input is a phase and evidence; output is a feedback
  record and disposition.
- **Relationships:** Summarizes the colocated skill, `/phase-feedback`, and
  change control.
- **Constraints and cautions:** Feedback preserves history and does not
  silently replan descendants; phase indexes must follow authorized moves.
- **Source basis:** `skills/aidd-phase-feedback/README.md:1-end`.
- **Status:** Workflow updated

### `skills/aidd-change-control/README.md`

- **What it is:** Overview of controlled material-change assessment.
- **When to use or read it:** Use when evidence may invalidate approved
  scope, outcomes, capabilities, sequencing, risks, or gates.
- **How to use it:** Compare approved and proposed states, identify the smallest
  affected subtree, obtain approval before replanning, and preserve path history
  when an approved status move is required.
- **Inputs and outputs:** Input is a change and planning context; output is a
  no-change, routine, or material-change decision.
- **Relationships:** Summarizes the colocated skill and
  `/replan-when-necessary`.
- **Constraints and cautions:** Routine backlog maintenance belongs to
  `/groom-backlog`; IDs, paths, indexes, and history must be preserved.
- **Source basis:** `skills/aidd-change-control/README.md:1-end`.
- **Status:** Workflow updated

### `skills/aidd-preimplementation-checklist/README.md`

- **What it is:** Overview of the auditable ticket readiness gate.
- **When to use or read it:** Use immediately before implementing an approved
  ticket.
- **How to use it:** Verify ancestry, approval, open lifecycle path, scope,
  dependencies, baseline, commands, gates, ownership, and evidence.
- **Inputs and outputs:** Input is a ticket and planning context; output is a
  ready/not-ready decision with blockers.
- **Relationships:** Summarizes the colocated skill and
  `/run-preimplementation-checklist`.
- **Constraints and cautions:** A missing or non-terminal prerequisite, closed
  ticket, or closed ancestor blocks implementation; the skill never edits
  source or moves records.
- **Source basis:** `skills/aidd-preimplementation-checklist/README.md:1-end`.
- **Status:** Workflow updated

### `skills/aidd-planning-bootstrap/SKILL.md`

- **What it is:** The planning bootstrap contract for repository context,
  adaptive depth, stable IDs, and safe downstream gating.
- **When to use or read it:** Use for new-project onboarding or inconsistent
  planning artifacts.
- **How to use it:** Inspect configured artifacts in both open and closed
  directories, classify depth, validate hierarchy/status/path consistency, and
  report the next approval or exact blocker.
- **Inputs and outputs:** Input is repository context and request; output is a
  planning context, authorized bootstrap artifact, or blocker report.
- **Relationships:** Coordinates repository mapping, discovery, configuration,
  and all child planning skills.
- **Constraints and cautions:** It is read-only unless authorized and never
  implements, commits, pushes, merges, or silently creates children.
- **Source basis:** `skills/aidd-planning-bootstrap/SKILL.md:1-end`.
- **Status:** Workflow updated

### `skills/aidd-create-repository-map/SKILL.md`

- **What it is:** The evidence-backed skill for mapping repository surfaces
  before deeper planning.
- **When to use or read it:** Use during onboarding or when architecture,
  tooling, ownership, or affected surfaces are unclear.
- **How to use it:** Inspect real paths, manifests, tests, CI, docs, and
  infrastructure, classify their roles, and record unknowns.
- **Inputs and outputs:** Input is a repository and configured map path; output
  is a durable repository map or coverage report.
- **Relationships:** Feeds bootstrap, discovery, capabilities, requirements,
  and domain-skill selection.
- **Constraints and cautions:** Do not infer behavior from names alone or
  modify source code; path and secret handling remain explicit.
- **Source basis:** `skills/aidd-create-repository-map/SKILL.md:1-end`.
- **Status:** Workflow updated

### `skills/aidd-create-capability-map/SKILL.md`

- **What it is:** The capability-layer contract connecting approved scope to
  system or operational abilities.
- **When to use or read it:** Use after objective/scope approval and before
  phase or feature planning.
- **How to use it:** Create stable CAP IDs, describe abilities independent of
  implementation, link evidence/prerequisites, and run scope coverage.
- **Inputs and outputs:** Input is approved objective/scope and repository map;
  output is a capability map and approval/blocker report.
- **Relationships:** Connects product discovery, requirements, phases, and
  feature planning.
- **Constraints and cautions:** Do not create children or infer unsupported
  capabilities; missing evidence remains a gap.
- **Source basis:** `skills/aidd-create-capability-map/SKILL.md:1-end`.
- **Status:** Workflow updated

### `skills/aidd-create-phases/SKILL.md`

- **What it is:** The phase-planning contract for meaningful top-level
  delivery outcomes and gates.
- **When to use or read it:** Use after scope and capability coverage are
  approved and before feature creation.
- **How to use it:** Assign PHASE IDs, define sequence rationale, outcome,
  boundaries, entry/exit conditions, dependencies, risks, and validation;
  create new records in open and move terminal records to closed.
- **Inputs and outputs:** Input is approved objective, scope, and capabilities;
  output is an ordered phase index with current paths and review decision.
- **Relationships:** Feeds feature planning, ticket creation, orchestration,
  and phase feedback.
- **Constraints and cautions:** Reject arbitrary calendar phases, missing
  outcomes, blocked parents, and silent child generation.
- **Source basis:** `skills/aidd-create-phases/SKILL.md:1-end`.
- **Status:** Workflow updated

### `skills/aidd-create-features/SKILL.md`

- **What it is:** The feature-planning contract for outcome slices inside one
  approved phase.
- **When to use or read it:** Use after phase approval and capability mapping.
- **How to use it:** Assign FEAT IDs, map each feature to exactly one phase
  and at least one capability, define outcome, scope, risks, and validation,
  create new records in open, and move terminal records to closed.
- **Inputs and outputs:** Input is one approved phase; output is a feature index
  with current paths and child-planning approval/blocker report.
- **Relationships:** Feeds ticket decomposition, requirements, backlog
  grooming, and planning-layer review.
- **Constraints and cautions:** Technical buckets, cross-phase ownership, and
  draft-parent fan-out are prohibited.
- **Source basis:** `skills/aidd-create-features/SKILL.md:1-end`.
- **Status:** Workflow updated

### `skills/aidd-create-tickets/SKILL.md`

- **What it is:** The focused-ticket decomposition contract for stable IDs,
  one-feature ownership, evidence, and backlog traceability.
- **When to use or read it:** Use when an approved feature is ready to become
  executable work.
- **How to use it:** Derive one coherent outcome per ticket, create records in
  open, link ancestry and requirements, define boundaries/dependencies/
  validation/user-validation/gates, move terminal records to closed, and reject
  oversized or cross-feature work.
- **Inputs and outputs:** Input is one approved feature and its ancestry; output
  is ticket records, current-path backlog entries, user-validation plans, and
  readiness decisions.
- **Relationships:** Connects requirements, ticket creator, execute, TDD,
  evidence, review, and grooming.
- **Constraints and cautions:** Do not generate children under blocked or
  unapproved parents or claim readiness without terminal evidence; do not close
  a ticket while required user-validation evidence is missing, failed, or
  blocked.
- **Source basis:** `skills/aidd-create-tickets/SKILL.md:1-end`.
- **Status:** Workflow updated

### `skills/aidd-planning-layer-review/SKILL.md`

- **What it is:** The read-only consistency and coverage gate for every
  objective, scope, capability, phase, feature, or ticket layer.
- **When to use or read it:** Use before child generation, implementation
  readiness, or after a material planning change.
- **How to use it:** Compare the layer with ancestors/children in both
  lifecycle directories, check stable links, metadata, status/path agreement,
  approval, boundaries, coverage, and evidence.
- **Inputs and outputs:** Input is a layer ID and planning context; output is a
  review classification and concrete blockers/corrections.
- **Relationships:** Used by planning prompts, orchestrator, evidence, and
  pre-implementation checklist.
- **Constraints and cautions:** It does not mutate artifacts, move files,
  create children, or infer missing evidence; it reports duplicate IDs and
  stale index paths.
- **Source basis:** `skills/aidd-planning-layer-review/SKILL.md:1-end`.
- **Status:** Workflow updated

### `skills/aidd-groom-backlog/SKILL.md`

- **What it is:** The routine backlog-maintenance contract for keeping planned
  work clear without silently changing the plan.
- **When to use or read it:** Use during active delivery to clarify, order,
  deduplicate, or mark stale tickets.
- **How to use it:** Inspect both lifecycle directories, status/dependencies/
  evidence, make only traceable hygiene changes, move records for authorized
  status transitions, synchronize indexes, and route material changes to
  change control.
- **Inputs and outputs:** Input is the configured backlog and planning context;
  output is a grooming report or authorized routine update.
- **Relationships:** Works with `/plan`, ticket planning, phase feedback, and
  `/replan-when-necessary`.
- **Constraints and cautions:** Preserve IDs, ownership, parent links, phase
  boundaries, path history, and index synchronization; grooming alone cannot
  make a ticket ready.
- **Source basis:** `skills/aidd-groom-backlog/SKILL.md:1-end`.
- **Status:** Workflow updated

### `skills/aidd-phase-feedback/SKILL.md`

- **What it is:** The phase closeout contract for comparing intended and
  delivered outcomes and recording learning.
- **When to use or read it:** Use after phase delivery or when evidence and
  stakeholder feedback reveal a planning lesson.
- **How to use it:** Compare phase outcome/conditions with evidence, classify
  findings, preserve history, move an authorized terminal/reopened phase
  between lifecycle directories, and create bounded follow-up dispositions.
- **Inputs and outputs:** Input is a phase and linked evidence; output is a
  feedback record and targeted planning recommendation.
- **Relationships:** Connects evidence, reviews, backlog grooming, and change
  control.
- **Constraints and cautions:** Observations do not silently rewrite children;
  material changes require approval and controlled replanning; phase indexes
  must follow authorized moves.
- **Source basis:** `skills/aidd-phase-feedback/SKILL.md:1-end`.
- **Status:** Workflow updated

### `skills/aidd-change-control/SKILL.md`

- **What it is:** The material-change decision contract that protects approved
  planning from silent downstream drift.
- **When to use or read it:** Use when new evidence changes an outcome, scope,
  capability, phase, feature, dependency, risk, or gate materially.
- **How to use it:** Compare states, classify impact, record a stable change
  ID and affected subtree, obtain approval, move only approved records across
  lifecycle directories, then replan only that subtree.
- **Inputs and outputs:** Input is a change request and planning/evidence
  context; output is a controlled change decision.
- **Relationships:** Coordinates phase feedback, backlog grooming, planning
  review, and orchestrator state.
- **Constraints and cautions:** Routine corrections stay in grooming; preserve
  stable IDs, current paths, indexes, and history, and block readiness while
  approval is missing.
- **Source basis:** `skills/aidd-change-control/SKILL.md:1-end`.
- **Status:** Workflow updated

### `skills/aidd-preimplementation-checklist/SKILL.md`

- **What it is:** The auditable stop/go contract for implementing one active
  ticket.
- **When to use or read it:** Use immediately before `/execute` for work with
  planning ancestry.
- **How to use it:** Verify objective-to-ticket links, open lifecycle paths,
  statuses, approvals, scope, dependencies, baseline, commands, gates,
  ownership, user-validation plan, and evidence.
- **Inputs and outputs:** Input is a ticket and all required planning records;
  output is a ready/not-ready decision with exact blockers.
- **Relationships:** Gates execution, TDD, evidence, review, and the
  orchestrator's `implementationReady` state.
- **Constraints and cautions:** Missing, blocked, unapproved, closed, or
  non-terminal prerequisites keep readiness false; a missing user-validation
  plan is also a blocker when the closure gate is enabled; it never edits source
  or moves records.
- **Source basis:** `skills/aidd-preimplementation-checklist/SKILL.md:1-end`.
- **Status:** Workflow updated

### `prompts/project-bootstrap.prompt.md`

- **What it is:** The `/project-bootstrap` entrypoint for creating approved
  foundational project context before downstream planning.
- **When to use or read it:** Use when a repository needs a vision, project
  agent guidance, repository map, scope handoff, or delivery configuration.
- **How to use it:** Invoke the prompt, answer one focused question at a time,
  review the complete file-by-file draft, and explicitly approve before any
  foundational artifact is written.
- **Inputs and outputs:** Input is repository evidence, existing sources of
  truth, and user intent; output is an approved or blocked bootstrap proposal
  covering `vision.md`, `AGENTS.md`, mapping, scope, configuration, and an
  optional README.
- **Relationships:** `skills/aidd-project-bootstrap/SKILL.md`, `create-vision`,
  `aidd-product-manager`, `aidd-create-repository-map`, and
  `aidd-planning-bootstrap`.
- **Constraints and cautions:** It preserves existing files and planning
  sources, does not invent project facts, and never creates capabilities,
  phases, features, or tickets as a side effect.
- **Source basis:** `prompts/project-bootstrap.prompt.md:1-end`.
- **Status:** Workflow updated

### `skills/aidd-project-bootstrap/README.md`

- **What it is:** User-facing overview of the project-context bootstrap
  orchestrator.
- **When to use or read it:** Use when starting a repository or deciding which
  foundational documents should be created before planning.
- **How to use it:** Invoke `/aidd-project-bootstrap` or the
  `/project-bootstrap` prompt wrapper, then review and approve the draft.
- **Inputs and outputs:** Input is repository context and project intent; output
  is coordinated foundational context and a planning handoff.
- **Relationships:** Summarizes the colocated skill and composes
  `create-vision`, product discovery, repository mapping, and planning
  bootstrap.
- **Constraints and cautions:** It does not silently overwrite existing
  instructions, generate downstream planning layers, or implement code.
- **Source basis:** `skills/aidd-project-bootstrap/README.md:1-end`.
- **Status:** Workflow updated

### `skills/aidd-project-bootstrap/SKILL.md`

- **What it is:** The approval-gated orchestrator for durable project context:
  vision, project-specific agent guidance, repository mapping, scope,
  configuration, and optional human-facing README content.
- **When to use or read it:** Use for new-project onboarding or when
  foundational context is missing, stale, or contradictory.
- **How to use it:** Inspect existing sources, interview the user one question
  at a time, draft all proposed files with source basis and confidence, obtain
  explicit approval, write only approved artifacts, and hand off to planning
  bootstrap.
- **Inputs and outputs:** Inputs are repository evidence, configured artifact
  paths, existing instructions, and user intent. Outputs are a bootstrap
  report, approved durable artifacts, unresolved decisions, blockers, and the
  next planning command.
- **Relationships:** Reuses `create-vision`, `aidd-product-manager`,
  `aidd-create-repository-map`, and `aidd-planning-bootstrap`; feeds capability,
  phase, feature, and ticket planning.
- **Constraints and cautions:** Existing `vision.md`, `AGENTS.md`, README,
  configuration, and planning sources require explicit approval before
  replacement. The skill never creates downstream planning children, source
  code, branches, commits, pushes, or merges.
- **Source basis:** `skills/aidd-project-bootstrap/SKILL.md:1-end`.
- **Status:** Workflow updated

## Implementation workflow we will use

This is the implemented default for a new project, product initiative, or
other multi-step change. It uses durable planning artifacts, one focused ticket
at a time, explicit evidence, configurable quality gates, and approval at the
configured transition points. Read `.github/aidd-config.yml` first; empty
command arrays require discovery and do not mean that a check is skipped.

The complete planning hierarchy is **objective -> scope -> capability -> phase
-> feature -> ticket**:

- An objective explains why the work exists and what outcome matters.
- Scope defines the current horizon, exclusions, and deferred work.
- A capability is an ability, not an endpoint, class, table, component, or
  technical layer.
- A phase is a top-level delivery stage with an outcome, ordering rationale,
  boundaries, entry conditions, and exit conditions.
- A feature is an outcome slice inside exactly one phase and links to one or
  more capabilities.
- A ticket is a focused unit inside exactly one feature and phase that can be
  implemented, verified, reviewed, and merged coherently.

### Adaptive planning depth

- **Small fix or documentation change:** one focused ticket -> validation ->
  implementation.
- **Normal feature:** discovery/scope -> active phase -> feature -> tickets.
- **Cross-cutting feature:** discovery/scope -> capabilities -> phase ->
  feature -> tickets.
- **New project or broad initiative:** repository map -> objective -> scope ->
  capabilities -> phases -> features -> tickets.

The workflow preserves omitted context in the ticket record when it collapses
layers. It never uses a lightweight path to skip acceptance criteria,
validation, scope boundaries, or evidence.

### 1. Bootstrap the repository

- Read `copilot-instructions.md`, `aidd-config.yml`, `vision.md` when present,
  repository README/AGENTS guidance, manifests, CI, tests, and existing
  planning artifacts.
- Run `/project-bootstrap` when `vision.md`, `AGENTS.md`, repository mapping,
  scope, or delivery configuration is missing or inconsistent. It drafts the
  foundational context and waits for explicit approval before writing.
- Run `/planning-bootstrap` to reconcile the repository context and select
  adaptive planning depth.
- Run `/create-repository-map` when important source, test, documentation,
  automation, infrastructure, ownership, or tooling surfaces are unknown.
- Preserve an existing authoritative planning system instead of creating
  duplicate `docs/` or `plan/` trees.

### 2. Discover and scope

- Run `/discover` to establish the objective, problem, users, success signals,
  scope horizon, non-goals, constraints, dependencies, risks, affected
  surfaces, protected behavior, definition of done, verification intent,
  confidence, source references, and open questions.
- Obtain the configured approval before creating child planning artifacts.
- For work beyond a normal feature, write or review the configured scope
  artifact and keep deferred work explicit.
- Discovery remains UI-agnostic and does not create implementation tickets.

### 3. Map capabilities

- Run `/create-capability-map` for a cross-cutting feature, new project, or
  broad initiative.
- Assign stable capability IDs and link each ability to objective, scope,
  outcomes, prerequisites, risks, affected surfaces, and evidence.
- Run `/aidd-requirements` when behavior needs `Given X, should Y` requirements
  and verification mappings.
- Review capability coverage before creating phases; missing or contradictory
  coverage blocks downstream planning.

### 4. Create and review phases

- Run `/create-phases` from approved objective, scope, and capabilities.
- Define ordered phases such as repository setup, research, backend/frontend
  delivery, integration, validation, and release only when each has a
  meaningful outcome and boundary.
- Give every phase entry conditions, exit conditions, dependencies, risks,
  validation focus, status, stable ID, and parent/child links.
- Run `/review-planning-layer` and obtain phase approval before creating
  features.

### 5. Create and review features

- Run `/create-features` inside one approved phase.
- Group capabilities into outcome-based features; a feature may span backend,
  frontend, tests, infrastructure, and documentation when they deliver one
  outcome.
- Define feature scope, non-goals, stakeholders, dependencies, risks,
  affected surfaces, acceptance outcomes, validation intent, stable ID, and
  exactly one phase link.
- Review the feature before ticket generation; do not create a feature for a
  technical bucket such as "backend work" unless that is the actual outcome.

### 6. Create, groom, and ready tickets

- Run `/create-tickets` or `/ticket` for one approved feature. Create one
  coherent outcome per ticket with stable ID, parent links, scope,
  out-of-scope, requirements, protected behavior, dependencies, priority and
  reason, risks, confidence, affected surfaces, validation, evidence path,
  gates, and definition of done.
- Maintain the configured backlog and one ticket record per file for
  non-trivial work.
- Run `/review-planning-layer` before marking tickets ready.
- Run `/groom-backlog` for routine clarification, deduplication, sequencing,
  stale-status updates, and priority changes. Route material changes to
  `/replan-when-necessary`.
- Run `/plan` to show active phase, features, ready/blocked tickets, planning
  gaps, and the reason for the recommended next ticket. Prefer a ready ticket
  in the active phase over later-phase work.

### 7. Check implementation readiness

- Run `/run-preimplementation-checklist` for the selected ticket.
- Verify objective -> scope -> capability -> phase -> feature -> ticket
  ancestry, stable IDs, approvals, scope, dependencies, the configured
  baseline prerequisite or approved baseline plan, commands, gates, ownership,
  acceptance, validation, and evidence path.
- Do not implement when any required parent is missing, blocked,
  contradictory, unapproved, or lacking terminal evidence.

### 8. Implement one ticket

- Run `/execute` for one approved ticket and preserve its scope, dependencies,
  approval state, active-phase ownership, and protected baseline.
- Record the baseline before mutation. For code behavior, follow TDD with a
  focused failing regression, minimum change, and rerun. For documentation,
  configuration, migration, infrastructure, or exploratory work, use the
  strongest applicable non-code evidence.
- Keep code in the correct layer and apply relevant domain skills through
  `skills/workflow-interface.md`.
- Append commands, results, artifacts, blockers, warnings, and coverage gaps
  to `/evidence`.
- Use `/aidd-parallel` or `/aidd-pipeline` only for explicitly independent
  ownership waves; otherwise remain sequential.

### 9. Verify and review

- Run targeted existing lint, unit, integration, end-to-end, browser, security,
  contract, or migration checks discovered from the repository.
- Use `/user-test` and `/run-test` for human-style or real-browser flows when
  required; retain screenshots and reports as configured UI evidence.
- Run `/review` to check planning coverage, scope, requirements, architecture,
  quality, security, functionality, documentation, evidence, and gates.
- Use `/aidd-fix` for findings that need a scoped change; preserve baseline and
  record regression or non-code evidence.
- Run `/evidence summarize` only when mapped requirements, critical flows, and
  required gates have terminal results. Missing capability is blocked or
  skipped with reason, never passed.

### 10. Close the ticket, feature, and phase

- Update directly related documentation and use `/log` only for significant
  completed outcomes; keep active evidence in `/evidence`.
- Use `/clean-pr-branch --dry-run` before any approved cleanup and never
  delete source files from disk.
- Use `/commit` with only intended staged files after readiness evidence and
  configured approval.
- Use `/aidd-pr` for provider-neutral remote checks, approvals, conflicts,
  conversations, and mergeability; recheck after every push.
- Mark a ticket complete only with terminal evidence. Complete a feature only
  when its tickets and outcome are complete, and complete a phase only after
  its exit conditions are satisfied.
- Run `/phase-feedback` after phase delivery and route material learning
  through change control.

### Normal new-project example

```text
PHASE-000: Repository setup
  FEAT-000: Establish a reproducible development baseline
    TICKET-000: Document runtime, setup, and quality commands

PHASE-001: Research
  FEAT-001: Validate the problem and technical approach
    TICKET-001: Record research findings, decisions, and open risks

PHASE-002: Backend capability
  FEAT-002: Deliver the core system ability
    TICKET-002: Implement the domain behavior
    TICKET-003: Expose and verify the service contract

PHASE-003: Frontend workflow
  FEAT-003: Deliver the user-facing outcome
    TICKET-004: Implement the primary user flow
    TICKET-005: Cover loading, empty, and failure states

PHASE-004: Integration
  FEAT-004: Connect the complete workflow
    TICKET-006: Verify the end-to-end and persisted behavior

PHASE-005: Validation and release
  FEAT-005: Prove and prepare the delivery
    TICKET-007: Run regression, user, and release checks
```

The example is a planning shape, not a mandatory technical sequence. Actual
phases and features come from the approved objective, scope, capabilities,
dependencies, risks, and evidence.

## Workflow improvements implemented

The following workflow-impact changes are now wired into the configuration,
skills, prompts, documentation, and behavioral evaluations. This is the
implementation summary for the completed HarmonicCoding-inspired planning
pass.

| Area | Current implementation |
| --- | --- |
| Canonical planning model | Objective -> scope -> capability -> phase -> feature -> ticket is documented in `copilot-instructions.md`, `README.md`, prompts, planning skills, and this map. |
| Adaptive depth | Small changes use a focused ticket; normal, cross-cutting, and new-project work progressively adds phases, features, capabilities, scope, and repository mapping without losing omitted context. |
| Durable planning artifacts | `aidd-config.yml` defines repository map, objective, scope, capability, phase, feature, backlog, ticket, review, and evidence paths while preserving existing repository sources of truth. |
| Project context bootstrap | `aidd-project-bootstrap` coordinates intent interview, `vision.md`, project-specific `AGENTS.md`, repository mapping, scope, configuration, optional README, approval, and planning handoff without generating child planning layers. |
| Repository bootstrap | `aidd-planning-bootstrap` and `aidd-create-repository-map` reconcile planning context, inspect repository surfaces, detect existing planning systems, and identify missing setup before downstream planning. |
| Discovery and scope | `aidd-product-manager` and `/discover` produce a durable objective/scope handoff with outcomes, non-goals, dependencies, risks, confidence, open questions, and verification intent. |
| Capability coverage | `aidd-create-capability-map` and `aidd-requirements` define system abilities, link them to scope and outcomes, and expose uncovered or contradictory planning inputs. |
| Phase-first delivery | `aidd-create-phases` defines meaningful ordered stages with boundaries, entry/exit conditions, dependencies, risks, and validation focus. |
| Outcome-based features | `aidd-create-features` groups capabilities into outcomes within exactly one approved phase instead of technical or calendar buckets. |
| Focused tickets | `aidd-create-tickets` and `aidd-ticket-creator` create stable, traceable, independently verifiable tickets with scope, non-goals, dependencies, priority, risks, acceptance, validation, user-validation handoff, evidence, and definition of done. |
| Planning record lifecycle | `planning-artifact-lifecycle.md`, configuration, creation skills, execution, grooming, feedback, review, checklist, and change control keep phase/feature/ticket files in `open` or `closed`, move the same stable-ID record on authorized status changes, and synchronize indexes and path history. |
| Planning-layer approvals | `aidd-planning-layer-review` reviews each artifact against its ancestors, children, coverage, status, and evidence before downstream generation. |
| Backlog grooming | `aidd-groom-backlog` handles routine clarification, deduplication, sequencing, and priority hygiene; it cannot silently change scope or make an unready ticket ready. |
| Change control | `aidd-change-control` and `/replan-when-necessary` route material changes to targeted replanning while preserving stable IDs, history, and unaffected subtrees. |
| Pre-implementation readiness | `aidd-preimplementation-checklist` blocks implementation when ancestry, approvals, dependencies, scope, commands, gates, acceptance, validation, or evidence paths are incomplete. |
| Delivery context | `aidd-config.yml` centralizes approvals, commands, gates, providers, branches, evidence, UI artifacts, security, and delegation policy. |
| Evidence and gates | `aidd-evidence` and `/evidence` maintain append-only requirement/flow traces, baselines, results, user-validation responses, artifacts, blockers, warnings, and readiness classifications; missing capability never passes. |
| Execution and review | `execute`, `tdd`, `review`, `aidd-fix`, and `aidd-pr` preserve baselines, implement one ticket at a time, run applicable checks, present the user-validation handoff, and keep remote lifecycle state current. |
| Phase feedback | `aidd-phase-feedback` compares planned and delivered outcomes, records lessons and residual risk, and feeds material learning through change control. |
| Delegation | Parallel and pipeline work declare ownership and dependency waves, default to isolation, stop on blockers, and return evidence rather than unsupported success claims. |
| Cleanup | `clean-pr-branch` previews by default, requires explicit `--apply` to mutate, preserves evidence, and never deletes source files from disk. |
| Lifecycle and domain boundaries | Lifecycle skills own delivery state; domain skills consume `workflow-interface.md` and return scoped guidance/evidence without owning branches, PRs, planning, or readiness. |
| Behavioral evaluation | `../ai-evals/aidd-lifecycle/` and `../ai-evals/aidd-planning/` cover missing baselines/evidence, failed gates, scope preservation, parent blockers, traceability, adaptive depth, grooming, change control, and readiness. |
