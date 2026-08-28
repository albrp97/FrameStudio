# TICKET-054 - Implement Exact Target FPS Interpolation

**Ticket ID:** TICKET-054
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-007
**Feature:** FEAT-022
**Capability links:** CAP-005, CAP-011, CAP-012
**Status:** complete
**Closure:** user-approved on 2026-08-26 after implementation, testing,
review, and acceptance of exact target-FPS interpolation; unavailable remote
and target-specific checks remain recorded as accepted warnings.
**Horizon:** future
**Priority:** 7
**Owner:** repository planning; maintainer identity is not recorded
**Approval:** user-authorized on 2026-08-24 to create the PHASE-007 planning
set; implementation requires TICKET-048 and TICKET-053 plus configured
ticket-execution approval
**Provider:** auto; base and target branches are not configured in
`.github/aidd-config.yml`
**Source paths:** `docs/planning/features/closed/FEAT-022-running-validated-motion-interpolation.md`,
`docs/planning/tickets/closed/TICKET-048-define-target-fps-selection-and-enhancement-scope.md`,
`docs/planning/tickets/closed/TICKET-053-validate-interpolation-backend-and-artifact-gate.md`,
`framestudio_fps.py`, `framestudio_concat.py`, `framestudio/export_planning.py`,
`framestudio/export_ffmpeg.py`, `benchmarks/`, `.github/aidd-config.yml`
**Dependencies:** TICKET-048 target eligibility; TICKET-053 validated backend;
PHASE-004 mixed-source timing; existing editor export plan and partial-output
boundaries
**Risks:** rational rounding can change duration, interpolation can cross
scene or edit cuts, and per-input processing can drift from the composed
timeline
**Affected surfaces:** editor export route, interpolation adapter, frame-count
math, scene/edit-boundary handling, mixed-source timing, FFmpeg/VapourSynth
integration, tests, and evidence
**Evidence path:** `evidence/phase-007-motion-interpolation.md`
**Protected behaviors:** exact source preservation, fixed output canvas,
ordinary stream-copy/fallback exports, atomic partial files, and legacy FPS
workflow behavior
**Last updated:** 2026-08-26
**Path history:** created at
`tickets/open/TICKET-054-implement-exact-target-fps-interpolation.md` ->
`tickets/closed/TICKET-054-implement-exact-target-fps-interpolation.md`

## Outcome

An eligible edited source is interpolated to the approved target rate with
exact, reproducible timing and no synthetic frame across a forbidden cut.

## Scope

- Apply the selected validated backend to the target-eligible source ranges
  from TICKET-048.
- Use rational frame-rate and frame-count math instead of floating-point
  duration guesses.
- Produce the exact approved output frame count, including explicit final-frame
  padding or trimming where required by the backend.
- Respect hard scene cuts and edit segment boundaries according to the approved
  policy.
- Preserve source ordering and edited duration across mixed-source timelines.
- Keep interpolation separate from final delivery encoding where the validated
  workflow requires it.

## Explicit non-goals

- Audio policy or remux implementation beyond the seam needed for timing.
- New interpolation models or unvalidated hardware paths.
- Changing timeline editing semantics.
- Accepting approximate frame counts because metadata looks plausible.

## Observable requirements

- Given source frame count/rate and target rate, output frame count should
  match the approved rational calculation.
- Given a hard scene or edit cut, no forbidden synthetic frame should bridge
  the boundary.
- Given mixed-source input, each eligible range should retain its intended
  order and duration.
- Given a backend failure, no partial output should be reported as complete.
- Given enhancement disabled, this route should not be selected.

## Commands and quality gates

- `python3 -m unittest discover -s tests`
- `make check`
- `make contract`
- `make smoke`
- `make quality PYTHON=.venv/bin/python`

## Functionality flows

- Interpolate 29.97 FPS material to 60 FPS and inspect exact frame count.
- Process mixed 29.97/60 FPS sources with eligible and ineligible ranges.
- Exercise hard scene cuts, edit boundaries, cancellation, and backend failure.

## User validation before closure

Run an enhanced export from a disposable mixed-rate project, inspect target
FPS, duration, frame count, and cut boundaries, and confirm the ordinary
non-enhanced route remains unchanged. Return `PASS`, `FAIL`, or `BLOCKED`.

## Definition of done

- Exact target timing and frame-count tests pass for rational and mixed-rate
  cases.
- Cut-boundary and failure cleanup behavior is explicit and verified.
- The validated backend is used only when the approved policy enables it.

## Closure

TICKET-054 was closed on 2026-08-26 after the user confirmed the completed
ticket set was approved, accepted, and tested.
