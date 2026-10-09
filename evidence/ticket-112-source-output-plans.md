# TICKET-112 - Independent Output Planning Evidence

Parents: OBJ-001 / SCOPE-001 / PHASE-010 / FEAT-034.
Requirement: DISC-010 / REQ-010-03, refined by CHG-013.
Integration branch: `phase/010-synchronized-tracks`; base `330e13b`.
Mode: automatic, authorized by CHG-014.
Validation profile: `rubber-duck / gpt-5.6-luna / high / all-validation`.

## Implementation scope

Owned paths: `framestudio/output_plan.py`, `framestudio/cli_export.py`,
`tests/test_editor_source_output_plan.py` and its functionality module.
The public boundary exposes persisted final-only/combined/source-only
selection, stable track/source requests and results, deterministic destinations
and distinct final versus standalone framing/audio identities.

This ticket plans outputs. Source rendering is explicitly unavailable until113,
and final absolute composition until123/124. Source-only planning does not
invoke the unsupported original final-project planner.

## Findings and corrections

Parent reproduction and exact-profile review returned these introduced defects
for correction rather than treating passing initial tests as readiness:

- Existing final publication was incorrectly rejected as an invalid source
  directory; inferred and explicit directory handling are now distinct.
- Previously published source outputs renamed subsequent requests; allocation
  now depends on stable plan identities, not publication state.
- Source suffixes such as MKV/WebM leaked into MP4 output names; reels now use
  the supported MP4 container extension.
- Alias-check I/O errors were silently ignored; expected missing references
  alone are tolerated, other errors are typed and redact private directory paths.
- A derived source root could already be a file; that impossible plan is rejected.
- Combined suffixless output used the final file as a directory; final/source
  roots and actual reel destinations now reject equal or overlapping file/
  directory paths in either ancestor direction.
- A colon-delimited assertion intermittently failed on `C:clip.mp4`; the
  diagnostic assertion is suffix-based and source iteration is ordered.
- Production assertions failed the repository Bandit gate; narrowed optional
  path guards now provide the same typed behavior without assertions.

## Automatic functionality and interface release

Decision source: exact-profile validator
`6a2540b0-3610-444e-b264-0f42b37bbac1`, turns0 through2.
Recorded by: integration owner, transcribing the read-only validator.
Categories: `automaticValidation`, `review`.

Command:
`.venv/bin/python -m unittest -v tests.test_editor_source_output_plan tests.test_editor_source_output_plan_functionality`.
Functionality test:
`tests.test_editor_source_output_plan_functionality.SourceOutputPlanFunctionalityTests.test_source_output_plan_roundtrip`.
Supported boundary: real generated FFmpeg media, public output planning,
versioned JSON save/reopen and public CLI planning subprocesses.

The final validator run passed15 tests in12.655 seconds, with no failures,
errors or skips. Assertions cover stable ordered track/source pairs, the same
source independently modified on multiple tracks, exclusions/gaps/empty and
unused sources, all output modes, safe sanitized MP4 names, publication-stable
paths, no final planner for source-only, explicit invalid errors and source
hash preservation.

Every unit stability probe with `PYTHONHASHSEED=1,2,5,7,19` passed14 tests.
The validator's earlier intermittent test failure and destination blocker
remain historical failed decisions, superseded by this verified correction.
Decision: **PASS**, releasing113 to consume the interface.

Parent final-delta checks also passed15 tests in11.831 seconds, the same five
hash seeds, formatting/lint, two-module mypy, corrected Bandit and diff checks.

## Aggregate checkpoint and limitations

The combined repository run passed549 tests in204.061 seconds. Its
`make quality` process subsequently exited two for Bandit B101 in the then
current planner. It is not reported as a complete quality pass. The final
planner correction and four additional regression cases were checked by the
focused command above rather than claiming an unrun553-test suite.

Final `make static-analysis churn` completed with exit zero, all existing
analyzers available,46 clones and zero new clones, unchanged baseline,
and no known audited dependency vulnerabilities. Reports are in session
`files/phase010-placement-layout-quality/`; logs include
`phase010-core-wave-quality.log`, `phase010-core-bandit-corrected.log`
and `phase010-core-final-static.log`.

Local CI command configuration is unchanged. Remote Ubuntu execution,
rendering acceptance, publication and lifecycle closeout remain unverified.
