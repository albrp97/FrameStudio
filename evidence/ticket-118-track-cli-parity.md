# TICKET-118 - Track CLI Parity Evidence

Parents: OBJ-001 / SCOPE-001 / PHASE-010 / FEAT-035.
Mode: automatic, authorized by CHG-014.
Profile: `rubber-duck / gpt-5.6-luna / high / all-validation`.

## Compatibility defect and integrated functionality

Parent actual-media reproduction found that existing seconds-based splitting
with `--coordinate timeline` incorrectly required synchronized conversion.
The corrected handler requires conversion only for the new tick-based
request, retaining legacy-ripple timing for the existing seconds interface.
A public-entrypoint FFmpeg regression verifies the output project, source
cuts/IDs, unchanged input-project bytes and unchanged media hashes.

New CLI operations expose stable track IDs/order, placements, active track,
gaps and durations, and delegate editing to the shared placement model.
Unknown tracks, invalid ticks, fifth-track requests and populated-track removal
emit structured nonzero errors without writing project bytes.

Parent focused run: seven tests passed in 2.101 seconds.
Combined integrated T110/T118 run: 17 tests passed in 2.414 seconds.
Ruff complexity and diff checks passed.

## Exact-profile automatic validation and bounded review

Decision source: agent `149e814f-62ee-4ea9-8469-eb2b1dc70708`, turn 4.
Recorded by: integration owner, transcribing the read-only validator.
Categories: `automaticValidation`, `review`, bounded CLI release.

Independent combined scoped run: 17 tests passed in 2.451 seconds,
zero errors or skips. Format checked 13 files, lint passed, mypy checked nine
sources and scoped diff checks passed. The validator confirmed actual public
CLI roundtrip parity, explicit conversion, legacy split compatibility,
structured atomic failures and source preservation.

Decision: **bounded CLI PASS**, not full readiness. Whole-suite/final static
analysis, remote checks, delivery and lifecycle closeout remain pending.
