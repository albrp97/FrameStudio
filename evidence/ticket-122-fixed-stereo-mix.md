# TICKET-122 - Fixed Stereo Mix Evidence

Parents: OBJ-001 / SCOPE-001 / PHASE-010 / FEAT-037.
Mode: automatic, authorized by CHG-014.
Profile: `rubber-duck / gpt-5.6-luna / high / all-validation`.

## Integrated implementation and review corrections

The compositor consumes T119 active intervals and persistent slot order.
It applies fixed pan vectors, mono equal-power mapping, stereo balance without
crossfeed and the reviewed 5.1/5.1(side) matrices. Persisted source gain is
applied once and included in safety bounds. Silent/absent audio keeps its
visual slot. Shared cumulative 48 kHz boundaries determine exact sample counts.

Parent review corrected protection of unused/excluded original source paths,
unnecessary limiting of safe centered or sole-panned audio, rejection of legal
zero-sample microtick intervals, and persisted policy/fingerprint/gain handling.
The source-decision helper now uses the actual SourceReference type.

Initial corrected integrated run: 15 tests passed in 2.928 seconds,
including generated PCM/FFmpeg functionality, four-slot stereo identity,
surround markers, missing audio, gaps, unity peak verification, persistence
and source preservation. Ruff and mypy passed.

## Exact-profile automatic validation and remediation

Decision source: agent `2f555536-fbda-43ff-87bc-f2fee944c896`, turns 1 and 2.
Recorded by: integration owner, transcribing the read-only validator.
Categories: `automaticValidation`, `review`, bounded audio release.

Independent run: 15 tests passed in 2.970 seconds.
Decision: **bounded audio seam PASS** for T123, which must also wait for T121.

The validator identified malformed ready peak measurements becoming unknown
instead of failing before rendering. Parent corrected missing/bool/nonnumeric/
non-finite and out-of-range peak rejection. The regression asserts no FFmpeg
launch or partial, unchanged destination bytes and unchanged source bytes.
Parent combined audio run: 16 tests passed in 3.087 seconds, format/lint/mypy
and diff checks passed.

The exact-profile validator independently ran the new malformed-measurement
regression: one test passed in 0.045 seconds. Decision:
**PASS_RECONFIRMED**, previous finding resolved, bounded T123 audio release
retained. No final A/V export readiness was claimed.

## Cross-file quality and limitations

The complete parent duplication gate found one new repeated ready-settings
fixture. The functionality helper now delegates to the existing unit factory,
preserving its default sample count and overrides. Combined T110/T122 checks
passed 26 tests in 3.612 seconds, four fixture files passed format/lint, and
configured duplication passed with 46 clones, 1.259% and zero new clones.
The approved baseline was not changed. Exact-profile fixture-only confirmation
is pending.

Whole-PCM verification currently captures the decoded PCM in memory. No
bounded-memory optimization or large-project resource threshold is claimed.
Full-suite/final aggregate static analysis, combined A/V verification,
remote checks, delivery and lifecycle closeout remain pending.

Terminal fixture confirmation: exact-profile validator
`2f555536-fbda-43ff-87bc-f2fee944c896`, turn 4, classified the terminal fixture
and configured duplication correction **PASS**. The bounded T122 release
remains valid. The log is in the session `files` directory, not a repository
`files` directory. No original suite rerun, T121 review or final A/V readiness
was claimed by that decision.
