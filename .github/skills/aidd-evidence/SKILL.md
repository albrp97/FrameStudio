---
name: aidd-evidence
description: Maintain an append-only delivery evidence record for an active phase, feature, or ticket. Use during baseline, implementation, verification, review, and PR readiness.
---

import ../lifecycle-interface.md

# Delivery Evidence

```sudolang
Lifecycle {
  profile = evidenceMutation
}
```

Maintain the active ticket's evidence record independently from the global
changelog. The record must make a delivery claim reproducible: identify the
context, requirement or protected flow, action taken, expected result, observed
result, status, artifacts, failures, fixes, blockers, and accepted warnings.

Read `.github/aidd-config.yml` when present. Repository-specific configuration
overrides these defaults; an empty configured command means the command must be
discovered from manifests, scripts, CI, contribution guidance, or the user.
It does not mean that the check passed or is optional.

Apply [../development-mode.md](../development-mode.md) when deciding which
validation gate and owner apply to the active context.

## Evidence schema

Load [schema](./references/schema.md) when initializing or validating evidence
records and entries.

## Storage

Resolve the record path in this order:

1. `delivery.evidence.path` and `delivery.evidence.filename` from
   `.github/aidd-config.yml`;
2. the active ticket's declared evidence path;
3. `evidence/<ticket-slug>.md` as the documented fallback.

Use the active ticket, feature, and phase identifiers in the record header.
Keep the record append-only during execution: correct an earlier entry by
adding a superseding entry, not by erasing the history. Retain the record for
the duration configured by `delivery.evidence.retention`.

## Process

### Initialize

1. Load the active phase, feature, and ticket contract.
2. Resolve the configured record path and create the parent directory only when
   the caller authorized artifact creation.
3. Record repository, branch, base revision, relevant configuration, and the
   intended scope without copying secrets.
4. Add the acceptance requirements and protected regression flows that the
   record will cover.

### Append

For every baseline, unit/regression test, smoke check, fixture or acquisition
check, contract/integration check, migration/deployment check, security or
quality check, automated functionality test, static-analysis run, quality gate,
review finding, commit, push, or PR check:

1. Link the result to a requirement or protected flow.
2. Record the exact command or repeatable steps, expected behavior, observed
   behavior, outcome, and artifact paths.
   For `automatedFunctionality` and `automaticValidation`, also record `testId`, executable command or
   script, supported system boundary, assertions, and persisted or external
   effects. A human or agent narrative without an executable test is not this
   category. Technical categories are agent-owned; `userValidation` records
   only the user's functional observation and result. `automaticValidation`
   records an agent-run functionality charter in automatic development mode and
   must never be presented as user confirmation. In automatic mode, every
   validation entry, including planning, technical, static-analysis, review,
   remote, delivery, and lifecycle checks, must carry the exact configured
   Rubber Duck profile: `rubber-duck`, `gpt-5.6-luna`, high reasoning, and
   `all-validation`. The deterministic command or analyzer remains the source
   of raw results; Rubber Duck owns the validation decision.
3. Record failures, fixes, blockers, and accepted warnings explicitly.
4. Mark unavailable capabilities as `blocked` or `skippedWithReason`; never
   convert unavailable coverage into `passed`.
5. Redact credentials, tokens, cookies, private keys, sensitive test data, and
   secret-bearing command arguments before persisting the entry.

For planning evidence, record the artifact ID, parent links, review decision,
coverage result, unresolved questions, and the next permitted planning layer.
Planning evidence cannot make a child ready when its parent is missing,
blocked, or awaiting approval.

### Summarize

The final readiness summary must list:

- requirements and protected flows with their latest evidence;
- the latest automated functionality test for every acceptance outcome,
  including command, test identifier, boundary, assertions, result, and
  artifacts;
- the latest static-analysis run, tool availability, local/PR parity, new
  findings, existing findings, and remediation status;
- agent-run smoke, baseline, regression, contract, integration, migration,
  deployment, security, static-analysis, and quality-check results;
- the functionality-only user-validation handoff and user response in guided
  mode, or the agent-owned automatic-validation result in automatic mode;
- the automatic validation profile and its availability for every automatic
  validation entry and readiness decision;
- the latest commit ID, source branch, upstream/remote publication result, and
  PR state when delivery operations have started;
- passed, passed-with-concerns, failed, blocked, and skipped checks;
- unresolved blockers and accepted warnings;
- artifact paths and coverage gaps;
- whether the configured readiness gates are satisfied.

Do not declare delivery ready when a required result is missing, non-terminal,
or only inferred from another check.

## Boundaries

```sudolang
Constraints {
  Evidence is not a changelog and must not replace /aidd-log
  Never persist credentials or claim redaction was performed without applying it
  Never overwrite an earlier result to hide a failure
  Never report a check as passed without command or step evidence
  Never silently skip a configured required gate
  Never mark automated functionality as passed from a unit test, source
    inspection, human script, or agent narration
  Never use `userValidation` evidence for smoke, baseline, unit, regression,
      fixture, acquisition, contract, integration, migration, deployment,
      security, static-analysis, formatter, lint, type-check, build, or other
      technical checks
  Never ask the user to run an agent-owned technical check
  Never mark a ticket ready when the required automated functionality result is
    missing, failed, blocked, or not mapped to its acceptance outcome
  Never mark a guided ticket ready or closed while required user-validation
    evidence is missing, failed, or blocked
  Never mark an automatic ticket ready or closed while required
    automaticValidation evidence is missing, failed, or blocked
  Never mark an automatic validation entry or readiness decision as terminal
    without the exact configured Rubber Duck `gpt-5.6-luna` high-reasoning
    profile
  Never use another model, validator, or fallback profile for automatic
    validation
  Never mark static-analysis parity or required analyzer coverage as passed
    without terminal evidence
  Never use a changelog entry as planning or delivery evidence
  Never mark planning coverage complete when scope, capability, phase, feature,
  or ticket links are missing
  Do not modify source code while recording evidence
  Never record agent-run validation as `userValidation`
  If context, path, or gate policy is ambiguous, report the blocker explicitly
}
```

## Commands

```sudolang
Commands {
  /evidence init [ticket] - create or prepare the active ticket evidence record
  /evidence append [ticket] - append one baseline, test, flow, gate, review, or PR result
  /evidence summarize [ticket] - produce the readiness summary without changing source code
}
```
