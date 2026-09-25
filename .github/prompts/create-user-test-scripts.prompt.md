---
name: Create User Test Scripts
description: Derive human-run and agent-run user test scripts from journeys, phases, epics, tickets, or release candidates.
---

You have to create user-testing scripts for `${FEATURE_OR_RELEASE}` from the best available planning artifacts.

## Outcome

Produce executable user-testing scripts that prove usability or workflow correctness, not just implementation correctness.

## Required outputs

- human-run test script in `docs/planning/user-tests/`
- agent-run test script in `docs/planning/user-tests/` when practical

## Operating rules

1. Start from the user journey, ticket, phase, or release objective.
2. Write tests in user language, not implementation language.
3. Include expected result and evidence to capture for each step.
4. Prefer the smallest script that still proves the important workflow.

## Required workflow

### 1. Identify the source artifact

- journey
- epic
- phase
- ticket
- release candidate

### 2. Extract the critical user path

- happy path
- important failure path if relevant
- observable outcome that matters

### 3. Write the scripts

For each script include:

- purpose
- prerequisites
- ordered steps
- expected result per step
- evidence to capture

## Report

Provide:

1. created script paths
2. source artifact used
3. important paths covered
4. any missing information that limits script quality
