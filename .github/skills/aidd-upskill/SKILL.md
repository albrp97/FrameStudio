---
name: aidd-upskill
description: Create and review AIDD skills with clear contracts, progressive disclosure, command separation, and explicit lifecycle safety. Use when authoring or refactoring skills in .github/skills/.
---

# aidd-upskill

Craft skills that are clear, minimal, recomposable, and safe to activate.
Skills must give agents the context they need without hiding side effects or
delivery assumptions.

import references/types.md
import references/process.md

## Role and abstraction

Model every skill as `f: Input -> Output`. Name shared abstractions, expose
meaningful parameters, and keep deterministic logic separate from judgment.
Use natural language for explanation and SudoLang for formal interfaces,
constraints, commands, and pipelines.

## Lifecycle contract

Every new or refactored lifecycle or mutating skill must declare:

```sudolang
LifecycleContract {
  inputs[]
  outputs[]
  filesRead[]
  filesWritten[]
  sideEffects[]
  approvalConditions[]
  stopConditions[]
  requiredEvidence[]
  repositoryDependencies[]
  providerDependencies[]
  failureAndBlockerBehavior
  mayCommit
  mayPush
  mayResolve
  mayMerge
}
```

Domain-only skills must still declare inputs, outputs, risks, assumptions,
limitations, expected evidence, and blockers, while explicitly stating that
they do not own delivery side effects.

## Progressive disclosure

1. frontmatter name and description are loaded for discovery;
2. `SKILL.md` is loaded on activation;
3. references, scripts, and assets are loaded on demand.

Keep the body concise and move detailed material to references when size or
reuse warrants it.

## Eval tests

Separate pure thinking from effects. Use `aidd-riteway-ai` for `.sudo` evals and
include lifecycle assertions for refusal, stop, scope, evidence, and readiness
behavior in mutating skills.

## Commands

```sudolang
Commands {
  /aidd-upskill create [name] - scaffold a skill with a lifecycle/domain contract
  /aidd-upskill review [target] - validate structure, size, contracts, safety, and README
}
```

## Constraints

```sudolang
Constraints {
  Required frontmatter includes name and actionable use-when description
  Every skill declares its function, inputs, outputs, and side-effect boundary
  Mutating skills declare approval, stop, evidence, and failure behavior
  Provider, repository, credential, and stack assumptions remain configurable
  Commands mixing thought and effects are split into independently testable stages
  Shared functions become named abstractions instead of duplicated prose
  Do not declare readiness or success without an evidence contract
}
```
