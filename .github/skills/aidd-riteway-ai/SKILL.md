---
name: aidd-riteway-ai
description: Write isolated Riteway AI prompt evals for multi-step agent flows and lifecycle gates. Use when creating .sudo evals or testing skills that use tools, evidence, or external APIs.
compatibility: Requires riteway >=9 with the `riteway ai` subcommand available; another repository evaluation system may be used when configured.
---

# aidd-riteway-ai

Write isolated `.sudo` prompt evals for multi-step agent skills. Read the skill
under test, its functional requirements, `.github/aidd-config.yml`, and the
relevant delivery contract before authoring assertions.

Refer to `/aidd-tdd` for assertion style and test isolation. Refer to
`/aidd-requirements` for `Given X, should Y` requirements.

## Process

1. Read the skill, commands, requirements, lifecycle states, and configured
   side effects under test.
2. Identify discrete thinking, tool, gate, and reporting steps.
3. Create one `.sudo` eval per discrete step under
   `ai-evals/<skill-name>/`.
4. Add mock-tool preambles for unit evals, assert step-1 tool calls, and supply
   prior-step output for step N > 1.
5. Derive assertions strictly from observable requirements.
6. Add small, single-condition fixtures only when needed.
7. Add lifecycle scenarios for mutating or delivery skills.
8. Run the authoring checklist and the configured evaluation command when
   available.

## Eval file structure

```sudolang
import '.github/skills/<skill-name>/SKILL.md'

userPrompt = """
<prompt sent to the agent under test>
"""

- Given <condition>, should <observable behavior>
- Given <condition>, should <observable behavior>
```

## Rules

### One step per file

Use names such as
`ai-evals/<skill-name>/step-1-<description>-test.sudo`. Do not collapse
multiple discrete actions into one overloaded prompt.

### Unit and e2e tools

Unit evals must say they are in a test environment, provide stub return values,
and instruct the agent to use mock tools instead of real APIs. Step 1 asserts
the calls the agent makes rather than pre-supplying their answers. Step N > 1
includes the previous step's output.

E2E evals use real tools only when credentials and provider configuration are
available, and use the `-e2e.test.sudo` suffix. Never persist credentials in
evals or fixtures.

### Fixtures and assertions

Keep fixtures under 20 lines with one clear bug or condition. Assertions must
use `Given X, should Y`, test distinct observable behavior, and avoid
implementation details or duplicate claims.

## Lifecycle scenarios

Every lifecycle or mutating skill should have eval coverage for the behaviors
that prevent false delivery claims:

```sudolang
LifecycleScenario {
  name
  skill
  setup
  expectedToolCalls[]
  expectedOutput[]
  forbiddenOutput[]
}
```

At minimum, cover:

- baseline not run => the agent refuses to claim baseline success;
- required gate failure => the agent stops and reports the blocker;
- scope change => unrelated work becomes follow-up work rather than silent scope expansion;
- missing evidence => readiness remains false;
- unavailable optional capability => the result is a recorded coverage gap, not a pass;
- successful terminal evidence => the readiness summary names the requirement,
  artifact, and gate.

Do not make Riteway a prerequisite for repositories that use another configured
evaluation system.

## Checklist

- [ ] One eval file per discrete step
- [ ] Unit evals include mock tools
- [ ] Step 1 asserts tool calls without pre-supplied answers
- [ ] Later steps include previous output
- [ ] E2E names use `-e2e.test.sudo`
- [ ] Fixtures are small and single-condition
- [ ] Assertions derive from requirements
- [ ] Lifecycle gates and evidence claims have refusal/stop coverage
- [ ] Credentials and sensitive data are absent

## Commands

```sudolang
Commands {
  /aidd-riteway-ai - write requirement and lifecycle evals for a skill
}
```
