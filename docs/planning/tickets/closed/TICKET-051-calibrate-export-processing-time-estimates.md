# TICKET-051 - Calibrate Export Processing-Time Estimates

**Ticket ID:** TICKET-051
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-007
**Feature:** FEAT-021
**Capability links:** CAP-005, CAP-011, CAP-012
**Status:** complete
**Closure:** user-approved on 2026-08-26 after implementation, testing,
review, and acceptance of the calibrated export estimates; unavailable remote
and target-specific checks remain recorded as accepted warnings.
**Horizon:** future
**Priority:** 4
**Owner:** repository planning; maintainer identity is not recorded
**Approval:** user-authorized on 2026-08-24 to create the PHASE-007 planning
set; implementation requires the approved parent policy and configured
ticket-execution approval
**Provider:** auto; base and target branches are not configured in
`.github/aidd-config.yml`
**Source paths:** `docs/planning/features/closed/FEAT-021-planning-export-destination-and-estimates.md`,
`docs/planning/tickets/closed/TICKET-048-define-target-fps-selection-and-enhancement-scope.md`,
`framestudio/export_process.py`, `framestudio_fps.py`, `framestudio_concat.py`,
`FPS-ENHANCEMENT-RESEARCH.md`, `benchmarks/`, `.github/aidd-config.yml`
**Dependencies:** TICKET-048; measured local interpolation and export
throughput; source duration and frame-rate probes; existing progress metrics
**Risks:** hardware and source complexity can make a single point estimate
misleading, cold-start costs can be omitted, and an estimate can be mistaken
for a guarantee
**Affected surfaces:** estimator domain logic, benchmark calibration data,
export planning payloads, GUI estimate display, CLI diagnostics, tests, and
evidence
**Evidence path:** `evidence/phase-007-export-planning.md`
**Protected behaviors:** progress remains truthful, existing exports do not
depend on the estimate, and no sensitive paths or runtime secrets are stored
in calibration artifacts
**Last updated:** 2026-08-26
**Path history:** created at
`tickets/open/TICKET-051-calibrate-export-processing-time-estimates.md` ->
`tickets/closed/TICKET-051-calibrate-export-processing-time-estimates.md`

## Outcome

The export planner reports a transparent, locally calibrated estimate for
interpolation, rendering/encoding, verification, and total processing time.

## Scope

- Calculate expected source and output frames from rational rates and edited
  duration.
- Account for input-file count, target FPS, enhancement state, eligible
  enhancement duration, interpolation profile, decode/compose work, delivery
  encode, and final verification.
- Use measured local throughput for the supported workstation and a
  conservative fallback range when no matching calibration exists.
- Expose stage estimates, total estimate, assumptions, confidence, and
  uncertainty rather than false precision.
- Add self-contained tests using synthetic calibration samples and recorded
  local benchmark values. For the documented 60-second and 90-second local
  enhancement samples, the initial total estimate should be within plus or
  minus 30 percent of observed wall time; otherwise the estimate must be
  labeled low confidence and the discrepancy recorded.

### Initial estimator model to test

The first implementation should keep stage estimates separate while modeling
the current streamed pipeline as:

```text
source_frames = sum(source_duration * source_fps)
target_frames = sum(source_frames * target_fps / source_fps)
preflight = fixed_startup + per_input * input_count
interpolation = eligible_target_frames / calibrated_interpolation_fps
delivery = target_frames / calibrated_delivery_fps
verification = fixed_verify + output_duration / calibrated_probe_rate
total = preflight + max(interpolation, delivery) + verification
```

Frame values must use the approved rational rounding rules rather than the
floating-point shorthand shown above. The `max` models interpolation and
delivery encoding overlapping in the current streaming path; a future staged
route must use its measured sequential behavior instead. Missing or
mismatched calibration profiles must return a range with low confidence.

As a reproducible calibration check, the provisional local profiles use
`preflight = 0.5 + 0.5 * input_count`, `verification = 0.5 +
output_duration / 60`, 130 output frames/second for the integrated RVE path,
and 55 output frames/second for the `vs-rife` fallback. Against the recorded
integrated 30-second and 90-second samples, this produces:

| Profile and workload | Estimated | Observed | Relative error |
|---|---:|---:|---:|
| RVE, one 30-second input | 15.86 s | 15.07 s | +5.3% |
| RVE, three 30-second inputs | 45.58 s | 38.06 s | +19.8% |
| `vs-rife`, one 30-second input | 34.76 s | 34.48 s | +0.8% |
| `vs-rife`, three 30-second inputs | 102.27 s | 97.92 s | +4.4% |

These values are calibration evidence, not universal constants. The isolated
60-second RVE render is not mixed into this check because the research report
identifies it as a different diagnostic path from the integrated workflow.

## Explicit non-goals

- Guaranteeing performance on other hardware.
- Starting a benchmark or export automatically from the planner.
- Replacing measured progress with predicted values.
- Adding telemetry or remote performance collection.

## Observable requirements

- Given the same inputs and calibration profile, the estimator should return
  byte-stable component values and a total.
- Given enhancement disabled, interpolation time should be zero and the
  existing render route should still be represented.
- Given more eligible frames or a higher target rate, estimated interpolation
  work should not decrease.
- Given no calibration profile, the planner should show a range and low
  confidence rather than a success-shaped precise claim.
- Given the recorded local benchmark samples, the documented tolerance and
  discrepancy behavior should be testable.

## Commands and quality gates

- `python3 -m unittest discover -s tests`
- `make check`
- `make quality PYTHON=.venv/bin/python`
- Run the documented disposable-media calibration samples

## Functionality flows

- Estimate ordinary and enhanced exports for short, 60-second, and 90-second
  edited durations.
- Vary input count, source FPS, target FPS, enhancement toggle, composition
  requirement, and backend profile.
- Compare predicted components with observed wall-clock stage timings and
  record error and confidence.

## User validation before closure

Review the estimate panel for a disposable project, compare its prediction
with an actual short export, and confirm the stage labels and uncertainty are
understandable. Return `PASS`, `FAIL`, or `CHANGES` with any observed error.

## Definition of done

- The estimator formula and calibration assumptions are documented.
- Automated tests cover monotonicity, disabled enhancement, missing profiles,
  and the local benchmark tolerance.
- The UI/CLI can show estimates without implying a universal guarantee.

## Closure

TICKET-051 was closed on 2026-08-26 after the user confirmed the completed
ticket set was approved, accepted, and tested.
