---
name: Review Security Workflow
description: Perform a focused security review of code, workflow, setup, or configuration changes.
---

You have to review `${CHANGE_OR_PR}` for high-confidence security problems relevant to the actual change.

## Outcome

Identify concrete security risks, their severity, why they matter, and what must change before the work is considered safe.

## Operating rules

1. Focus on real risk, not generic checklist noise.
2. Review the changed behavior, not just the changed files.
3. Prioritize secrets, auth/session handling, unsafe comparisons, injection risk, validation boundaries, and logging exposure.
4. If there is no meaningful security impact, say that plainly and explain why.

## Required workflow

### 1. Identify the security surface

- inputs affected
- auth or access boundaries
- data handling and logging paths
- external integrations or secrets touched

### 2. Review the change against security rules

Use the repo security rules and check:

- secret handling
- auth/session assumptions
- unsafe comparisons
- injection or unvalidated input risk
- insecure logging or error exposure
- CI or workflow secrets misuse

### 3. Decide severity and action

Classify each issue as:

- critical
- high
- medium
- low

## Report

Provide:

1. security decision
2. findings by severity
3. affected files or surfaces
4. required fixes before merge
5. why no further security action is needed if no real issues are found
