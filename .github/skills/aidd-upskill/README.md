# aidd-upskill

Creates and reviews AIDD skills — the reusable instruction modules that guide
agent behavior across a project — with explicit lifecycle safety contracts.

## Why

Skills written without a clear structure accumulate bloat, mix concerns, and
become hard to maintain. `aidd-upskill` applies a consistent authoring
standard: each skill is a named function with defined inputs and outputs,
explicit side-effect and evidence boundaries, sized to stay concise, and
organized for progressive disclosure.

## Commands

```
/aidd-upskill create [name]
```

Scaffolds a new skill at `.github/skills/aidd-[name]/SKILL.md` with the required
frontmatter, sections, and directory layout.

```
/aidd-upskill review [target]
```

Evaluates an existing skill against authoring criteria: function test,
required sections, size thresholds, command separation, and README quality.
Reports issues and a pass/fail verdict.

## When to use

- Creating a new skill from scratch in `.github/skills/`
- Reviewing or refactoring an existing skill for quality and consistency
- Checking whether a candidate abstraction is ready to become a named skill
- Verifying that mutating skills declare approval, stop, evidence, provider,
  and commit/push/resolve/merge behavior
