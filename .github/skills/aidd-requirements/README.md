# aidd-requirements

Writes functional requirements and verification mappings for user stories,
features, and tickets using a standardized "Given X, should Y" format.

## Why

Vague requirements lead to scope creep and missing features. A consistent format forces clarity about the situation and expected behavior,
while explicit success, failure, authorization, persistence, integration,
retry, error, protected-behavior, and evidence coverage reduces gaps.

## Usage

Invoke `/aidd-requirements` with the user story, feature, or ticket. Each requirement
follows this template:

```
Given <situation>, should <job to do>
```

Requirements focus on the job the user wants to accomplish and the benefit they
achieve — no specific UI elements or interactions. Map each requirement to
strongest available evidence and identify unresolved decisions.

## When to use

- Drafting requirements for a new user story
- Specifying acceptance criteria
- Reviewing whether existing requirements are complete and testable
