# Skill Creation Process

## Pipeline

```
createSkill(userRequest) {
  gatherRequirements
    |> nameSkill
    |> think() --compact
    |> buildPlan
    |> presentPlan
    |> draftSkillMd
    |> writeSkill
    |> writeReadme
    |> validate
    |> validateLifecycleContract
    |> reportMetrics
}
```

## Steps

**gatherRequirements(userRequest)**
1. discoverRelatedSkills — search the project for SKILL.md, `.mdc`, `.md` files; read frontmatter descriptions; identify overlap or complementary skills
2. researchBestPractices — use web search to find best practices for the domain; summarize findings
3. Infer requirements from the above context. Do not ask clarifying questions or block on user input. Use a judge to evaluate completeness: yes → proceed; no → state gaps as explicit assumptions and proceed.

Infer answers to these questions from context:
- What problem does this skill solve?
- What are its inputs and outputs?
- Any technical constraints or requirements?
- Should it `alwaysApply`? (recommend yes only if it applies to nearly every ticket)

**nameSkill(topic)**
- Use verb or role-based noun form (e.g., `format-code`, `upskill`)

**buildPlan() => SkillPlan**
Produce a `SkillPlan`

**presentPlan(plan: SkillPlan)**
Show the full plan, then run a self-validating quality gate — do not await user approval:

While important issues remain {
  reviewPlan |> fix
}

**draftSkillMd(plan: SkillPlan)**
- Write frontmatter: `name` + `description` required; add `metadata.alwaysApply` if needed
- Write body with all `RequiredSections`
- If body will exceed the line threshold (run `validate-skill` to check), extract content to `references/` and use `import $referenceFile`

**writeSkill(skillMd)**
- Write to `$skillHome/${skillName}/SKILL.md`
- Create `scripts/`, `references/`, or `assets/` directories as required

**writeReadme(skillMd)**
- Write `README.md` in the skill directory
- Include: what the skill is, why it is useful, command reference with usage examples
- Exclude: implementation details, process narratives, pipeline descriptions
- Avoid tables


**validate**
```bash
/validate-skill ./path-to-skill-directory
# If skills-ref is available:
skills-ref validate ./path-to-skill-directory
```

If CLI access is unavailable, carefully emulate the validation process.

**validateLifecycleContract(skillMd)**
1. Identify whether the skill reads, writes, commits, pushes, resolves, merges,
   delegates, or changes external state.
2. For a mutating or lifecycle skill, require explicit inputs, outputs, files,
   side effects, approval conditions, stop conditions, required evidence,
   repository/provider dependencies, and failure/blocker behavior.
3. Require explicit `mayCommit`, `mayPush`, `mayResolve`, and `mayMerge` values.
4. For a domain-only skill, require the lightweight workflow interface and an
   explicit no-delivery-side-effects boundary.
5. Flag hidden commands, credential assumptions, success-shaped fallbacks, and
   readiness claims without evidence.

**reportMetrics**
Report `SizeMetrics` and any threshold warnings to the user.

## Skill Review Process

```
reviewSkill(target) {
  readSkill(target)
    |> runFunctionTest
    |> checkRequiredSections
    |> checkSizeMetrics
    |> checkCommandSeparation
    |> checkReadme
    |> checkLifecycleContract
    |> deduplicate()
    |> think() --compact
    |> reportFindings
}
```

**runFunctionTest** — apply the 5-question Function Test from SKILL.md  
**checkRequiredSections** — verify all `RequiredSections` are present  
**checkSizeMetrics** — run `validate-skill` and report warnings  
**checkCommandSeparation** — verify no command mixes thinking and side effects
**checkReadme** — verify README.md exists and contains what/why/commands; flag if it contains implementation details or process narratives
**deduplicate()** — find every instance of repeated information across SKILL.md and its references; flag each duplicate and identify where the single source of truth should live; use `think() --compact` to reason about the canonical location  
**think() --compact** — synthesize all findings into a holistic judgment before rendering the verdict (uses the RTC think() function from `aidd-please`); independently testable as a pure thinking stage  
**checkLifecycleContract** — verify that the skill's declared permissions and
side effects match its actual commands and process, including evidence and
stop behavior.

**reportFindings** — produce a per-check pass/fail table (one row per check:
runFunctionTest, checkRequiredSections, checkSizeMetrics,
checkCommandSeparation, checkReadme, checkLifecycleContract, deduplicate) with
columns for check name, result (✅/⚠️/❌), and detail; conclude with an overall
verdict.
