---
name: Run User Test Workflow
description: Execute user-testing scripts, capture evidence, and turn failures into actionable work.
---

You have to run the user-testing workflow for `${FEATURE_OR_RELEASE}` using the existing user-test scripts or the best available equivalent.

## Outcome

Capture whether the target workflow is usable, what evidence was observed, and what failures or follow-up work were found.

## Required outputs

- result file in `docs/planning/user-tests/results/`

## Operating rules

1. Use the real user path where practical.
2. Capture evidence, not just a pass/fail label.
3. Turn failures into explicit follow-up actions or backlog items.
4. If the exact script does not exist, state the gap clearly.

## Required workflow

### 1. Identify the script and target

- what script is being run
- what environment or artifact is being tested

### 2. Execute and observe

Capture:

- what happened
- what was expected
- screenshots, logs, or notes if available

### 3. Record outcome

Classify:

- passed
- passed with concerns
- failed
- blocked

## Report

Provide:

1. result classification
2. evidence captured
3. failures or usability concerns
4. follow-up work required
