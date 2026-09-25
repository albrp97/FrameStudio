# Charter execution

## Human script

For the implementation closure handoff, include only the user's functional
purpose, setup, representative data, exact actions, visible and persisted
expectations, user-observable failure behavior, cleanup, and post-test result.
A separate usability study may collect friction and confidence; it must not be
presented as implementation proof or mixed into the functionality closure gate.

## Agent script

The agent owns technical verification and automated functionality execution.
Drive the supported real local stack and browser without using source code to
discover the UI, and invoke the executable automated functionality test when
the charter is used for implementation verification. At each step:

1. perform the action and narrate expectations and observations;
2. validate visible and persisted/external results;
3. capture configured screenshots at checkpoints, before/after states, or
   failures;
4. record duration, difficulty, status, evidence paths, and coverage gaps;
5. retry only according to the persona and configured retry policy.

If the browser, service, data, or integration capability is unavailable, mark
the flow `blocked` and record the reason. Never report an unrun flow as passed.
An agent narration without machine-checked assertions is diagnostic evidence
only and cannot satisfy the automated functionality gate. Technical-check
failures remain agent-owned blockers and must not be passed to the user as
smoke or regression instructions.

When automatic mode is selected, the agent also owns the functionality closure
charter. The Rubber Duck validator must run or inspect every validation step
using the exact configured profile. It must run the executable test, assert
visible/output and persisted/external effects, record `automaticValidation`
with the profile, and continue only after a terminal result. It must not
simulate a human response or label the entry `userValidation`.

## File locations

Use configured artifact paths when present. Portable defaults are:

- human scripts: `$projectRoot/plan/${journey-name}-human-test.md`;
- agent scripts: `$projectRoot/plan/${journey-name}-agent-test.md`;
- journey data: `$projectRoot/plan/story-map/${journey-name}.yaml`;
- evidence: `evidence/<ticket-slug>.md`.

Create files only when the caller authorizes artifact creation.
