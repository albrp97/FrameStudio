# Development mode contract

All lifecycle skills resolve the selected development mode from
`delivery.development.mode` in `.github/aidd-config.yml`. The value is
`guided` or `automatic`; a missing value defaults to `guided`. If `vision.md`
or `AGENTS.md` records a different selected value, report a configuration
conflict before mutating the repository.

After resolving the mode, merge the selected
`delivery.mode_overrides.<mode>` policy over the base approval, version-control,
gate, and static-analysis settings. This prevents guided-only
`require_user_validation` or approval flags from remaining active in automatic
mode while preserving branch, provider, credential, security, remote-check,
and merge-protection gates.

## Explicit user delivery directives

The selected mode controls normal autonomous behavior. It does not overrule an
explicit current user instruction to commit, stage and commit, push, or commit
and push current work.

Resolve `delivery.version_control.user_directive_override` after the normal
mode policy. When it is enabled and required evidence, review, validation,
approval, lifecycle state, or branch conventions are incomplete:

1. inspect the exact requested scope and list the missing, failed, stale, or
   bypassed gates in one concise warning;
2. ask for confirmation once when the user has not already acknowledged the
   warning or explicitly said to proceed despite missing gates;
3. after confirmation, perform the requested commit or push instead of
   returning a workflow blocker;
4. record every bypassed gate as `userDirectiveOverride`, never as passed
   evidence;
5. keep ticket readiness and lifecycle closeout separate, because committing
   or pushing under override does not make missing validation pass.

An explicit request to "commit everything", "stage and commit everything", or
"commit and push everything" authorizes staging all current repository changes,
including untracked files, after showing the path list and checking for secrets.
It does not authorize secret exposure, history rewriting, force push, deletion,
or another destructive operation unless that exact operation is separately
requested.

Workflow gates are advisory under a confirmed explicit directive. Actual
inability remains blocking: missing credentials, a missing remote, provider or
branch-protection rejection, unresolved Git state that prevents the operation,
or a secret-bearing path that cannot safely be included. Attempt the requested
non-destructive operation when possible and report an external rejection from
observed output rather than predicting it from repository policy.

## Mode semantics

### Guided

Guided development preserves the normal interactive workflow:

- ask for configured planning, execution, next-ticket, delivery, and
  functionality-validation approvals;
- present the functionality-only user-validation handoff after all
  agent-owned technical checks and automated functionality tests;
- keep the ticket in `verifying` until the user's terminal functionality
  result is recorded as `userValidation` evidence;
- continue only after the configured user response or approval is available.

### Automatic

Automatic development is authorized when the user selects `automatic` during
project bootstrap and approves the foundational bootstrap write. From the
verified bootstrap handoff onward:

1. do not ask another user question or wait for a user response;
2. treat routine planning, execution, next-ticket, and delivery approvals as
   bootstrap-authorized agent decisions, and record the decision and evidence;
3. use repository evidence, confirmed project context, configured defaults,
   and the smallest safe assumption for routine choices;
4. run repository mapping, objective/scope discovery, capability mapping,
   phase/feature/ticket planning, planning review, backlog grooming, ticket
   execution, TDD or the strongest applicable evidence method, technical
   verification, automated functionality testing, deterministic review and
   remediation, and configured delivery operations in order;
5. after each terminal ticket, continue with the next ready ticket, then the
   next feature and phase, until the configured objective is complete;
6. update every planning record, index, evidence record, status, lifecycle
   path, and phase-feedback artifact through real verified file operations.

Automatic mode must never claim that a user performed a validation. It runs an
agent-owned functionality charter and records the result as
`automaticValidation`, while `userValidation` remains reserved for a human
response. The automatic validation must use an executable functionality test
that crosses the supported system boundary and asserts observable output plus
relevant persisted or external state.

Configured remote, provider, security, credential, branch-protection, merge,
or unavailable-tool requirements remain real gates. Automatic mode does not
bypass them. If one cannot be satisfied without a user decision or external
capability, stop with a precise `blocked` result and report the required
decision or capability; do not ask a follow-up question.

### Automatic validation executor

Automatic mode resolves `delivery.development.automatic_validation` and
requires this exact profile for every validation decision:

```sudolang
AutomaticValidationProfile {
  validator: rubber-duck
  model: gpt-5.6-luna
  reasoningEffort: high
  scope: all-validation
}
```

This applies to planning-artifact verification, baseline and technical checks,
automated functionality, `automaticValidation`, static analysis, review and
remediation verification, remote checks, delivery gates, and lifecycle
closeout. Deterministic commands and analyzers still produce the authoritative
raw results; the Rubber Duck validator must orchestrate, inspect, and classify
those results. No other model, validator, or silent fallback may produce an
automatic validation pass.

If the configured profile is missing, unavailable, or does not match exactly,
automatic validation is `blocked`. Record the profile and its availability in
evidence before any automatic pass or readiness claim.

## Mode resolution

```sudolang
resolveDevelopmentMode(context) {
  configMode = context.delivery.development.mode ?? guided
  projectMode = context.vision.developmentMode ?? context.agents.developmentMode

  if projectMode exists and projectMode != configMode:
    return blocked("development mode conflict")

  return configMode
}

resolveModePolicy(context) {
  mode = resolveDevelopmentMode(context)
  base = context.delivery
  modeOverrides = context.delivery.mode_overrides ?? {}
  override = modeOverrides[mode] ?? {}
  return mergeModePolicy(base, override)
}

resolveAutomaticValidationProfile(context) {
  if context.developmentMode != automatic:
    return null

  profile = context.delivery.development.automatic_validation
  if profile.validator != rubber-duck ||
     profile.model != gpt-5.6-luna ||
     profile.reasoning_effort != high ||
     profile.scope != all-validation:
    return blocked("required Rubber Duck gpt-5.6-luna high validator unavailable or mismatched")

  capability = findRuntimeValidatorCapability(
    context.validatorCapabilities,
    profile.validator,
    profile.model,
    profile.reasoning_effort,
    profile.scope
  )
  if capability is missing or capability.available != true:
    return blocked("required Rubber Duck gpt-5.6-luna high validator unavailable or mismatched")

  return profile
}
```

The machine-readable source of truth is `.github/aidd-config.yml`.
`vision.md` and project-specific `AGENTS.md` mirror the selected value and
identify that configuration key as authoritative.

## Automatic completion gate

```sudolang
automaticTicketGate(ticket, evidence) {
  automaticValidationProfileTerminal
  technicalEvidenceTerminal
  automatedFunctionalityTerminalForEveryAcceptanceOutcome
  automaticValidationTerminalForEveryFunctionalityOutcome
  staticAnalysisAndReviewTerminal
  noUnresolvedBlockers
}
```

When the automatic ticket gate passes, route directly to the configured
commit, push, PR, merge, or local-closeout operation. After closeout, select
the next ready ticket in the active phase. A phase can close only after all
required features and tickets satisfy their terminal gates.

## Response behavior

The workflow still emits the single `NextAction` contract required by the
repository instructions. In automatic mode that action is an internal
continuation route, not a question, approval request, or user handoff. At
completion, report the terminal result and any external blocker plainly.
