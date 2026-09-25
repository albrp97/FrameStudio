# Types & Interfaces

## Types

```
type SkillName = string(
  1-64 chars,
  lowercase alphanumeric + hyphens,
  no leading/trailing/consecutive hyphens,
  must match parent directory name,
  prefix: "aidd-" (shared ecosystem skills; project- or org-specific skills are exempt),
  verb or role-based noun
)

type SkillDescription = string(
  1-1024 chars,
  describes what the skill does AND when to use it,
  precise enough for an agent to activate on description alone
)
```

## SizeMetrics

```
SizeMetrics {
  frontmatterTokens: number  // run validate-skill for current thresholds
  bodyLines: number          // run validate-skill for current thresholds
  bodyTokens: number         // run validate-skill for current thresholds
}
```

## SkillPlan

```
SkillPlan {
  name: SkillName
  purpose: SkillDescription
  alwaysApply: boolean       // preload on project init? Use sparingly.
  relatedSkills[]            // existing skills found during discovery
  bestPractices[]            // findings from research
  proposedSections[]         // planned SKILL.md structure
  optionalDirs: ["scripts" | "references" | "assets"]
  sizeEstimate: SizeMetrics
}

LifecycleContract {
  inputs: string[]
  outputs: string[]
  filesRead: string[]
  filesWritten: string[]
  sideEffects: string[]
  approvalConditions: string[]
  stopConditions: string[]
  requiredEvidence: string[]
  repositoryDependencies: string[]
  providerDependencies: string[]
  failureAndBlockerBehavior: string
  mayCommit: boolean
  mayPush: boolean
  mayResolve: boolean
  mayMerge: boolean
}

LifecycleDeclaration {
  profile: LifecycleProfile
  overrides {}
}

DomainContract {
  inputs: string[]
  outputs: string[]
  risks: string[]
  assumptions: string[]
  limitations: string[]
  expectedEvidence: string[]
  blockers: string[]
  sideEffects: []
  mayCommit: false
  mayPush: false
  mayResolve: false
  mayMerge: false
}
```

## Frontmatter

```
Frontmatter {
  name: SkillName                       // required
  description: SkillDescription         // required
  license                               // optional
  compatibility: string(1-500)          // optional, environment requirements
  metadata {}                           // optional, AIDD extensions
  allowed-tools                         // optional, space-delimited tool list
}
```

### AIDD Extensions via `metadata`

`metadata.alwaysApply: "true"` preloads the full SKILL.md on project init.
Use only for skills that apply to nearly every ticket (e.g., coding standards).
Ticket-specific skills should activate on demand, not preload.

## RequiredSections

Every generated SKILL.md body must include:

```
RequiredSections {
  "# Title"                  // skill name as heading
  executionInterface         // `## Steps`, `## Process`, `## Execute`, or a
                             // named SudoLang function/command pipeline
}
```

An imported process reference satisfies the execution-interface requirement
only when `SKILL.md` links it explicitly. A formal SudoLang function or command
pipeline satisfies the requirement when its executable entry point is clear.

## Function Test

Every skill must answer:

1. What single capability does this skill own?
2. What inputs does it require and what outputs does it produce?
3. What state may it read or change?
4. What evidence proves a successful result?
5. Which conditions require it to stop or hand off?

A skill fails when the answers are absent, contradictory, or spread across
unlinked files.
