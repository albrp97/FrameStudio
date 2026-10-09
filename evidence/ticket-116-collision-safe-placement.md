# TICKET-116 - Collision-Safe Placement Evidence

Parents: OBJ-001 / SCOPE-001 / PHASE-010 / FEAT-035.
Requirement: DISC-010 / REQ-010-04.
Integration branch: `phase/010-synchronized-tracks`; base `330e13b`.
Mode: automatic, authorized by CHG-014.
Required validation profile:
`rubber-duck / gpt-5.6-luna / high / all-validation`.

## Implementation and reproduced regression

Owned paths: `model_timeline.py`, `model_project.py`, `operations.py` under
`framestudio/`, and two dedicated track-placement test modules.
Public operations accept exact ticks and target track IDs. They preserve
existing occupancy, source ranges, modifications and atomic revision changes.

Parent reproduction found legacy import resetting revision one to zero,
rather than advancing to two. The worker reproduced the defect for legacy
v4, v2 and v3, added failing regression cases, and preserved the runtime
revision when replacing imported timelines. Save/reopen intentionally starts
a fresh runtime epoch. The owner synchronization callback now uses a typed
protocol instead of `Any`.

## Integrated raw technical and functionality results

Command:
`.venv/bin/python -m unittest -v tests.test_editor_track_placement tests.test_editor_track_placement_functionality tests.test_editor_track_migration`

Observed: 22 tests completed in 0.221 seconds with no failures, errors or
skips. Changed-file Ruff format/lint, three-source mypy and
`git diff --check` completed successfully.

Functionality test:
`tests.test_editor_track_placement_functionality.TrackPlacementFunctionalityTests.test_persisted_real_media_track_editing_round_trips_exactly`.
Supported boundary: generated FFmpeg media, public editing operations, and
versioned project save/reopen.

Assertions cover chained collisions and insufficient gaps, a long excluded
block resolving to `[7.5, 10.5)` without moving existing clips, touching
no-op/revision behavior, cross-track movement/paste, source ranges, independent
triplicate/transform copies, four-track lifecycle, fifth/populated-removal
rejection, active-track import, distinct editing/included/final durations,
persisted state and unchanged source hashes.

These are raw deterministic results. Exact-profile validator agent
`149e814f-62ee-4ea9-8469-eb2b1dc70708` owns the pending automatic functionality
and interface-release decision. Aggregate quality is running. Neither
consumer release nor delivery/lifecycle completion is claimed yet.

## Exact-profile interface and removal-contract decisions

Decision source: `149e814f-62ee-4ea9-8469-eb2b1dc70708`, turns0 and1.
Recorded by: integration owner, transcribing the read-only validator.
Profile: `rubber-duck / gpt-5.6-luna / high / all-validation`.
Categories: `automaticValidation`, `review`, `contract`.

The validator independently ran the placement and real-media test modules:
eight passed in0.236 seconds. Migration plus the persisted migration
functionality selector passed15 tests in31.288 seconds. Public split/copy/paste
wrapper probes, five-file format/lint, three-source mypy and scoped diff checks
also completed successfully.

Decision: **PASS** for the bounded116 interface; release110/117/118 with
disjoint ownership. This does not classify aggregate quality or delivery.
The validator also approved110's bounded20-receipt contract: original-state
ripple calculation, deep-copy isolation, revision plus runtime identity,
monotonic Undo commits, conservative exact-state rebasing and no cross-restart
or general-purpose history. Implementation acceptance remains separate.

## Aggregate failures and focused remediation

The first combined `make quality` run completed538 tests in182.885 seconds
with one error: the second real GTK charter registered the same D-Bus object
path. `NON_UNIQUE` alone was insufficient. This is a failed historical run,
not a pass.

Parent fixture-only remediation supplies a unique application ID from each
existing unique temporary directory before registration. Running both GTK
charters together passed two tests in2.732 seconds. Production GTK and
placement code were unchanged.

Aggregate static analysis then identified one introduced119 fixture-hash
clone against the restoration benchmark. Parent replaced the streaming loop
with SHA-256 over the small generated fixture bytes, without changing the
baseline. The complete static-analysis command subsequently exited zero.
All112/116/119 changes are now gathered for a new full-quality run; its result
is pending. Logs are in session files `phase010-placement-layout-quality.log`,
`gtk-isolated-fixture-check.log`, `phase010-placement-layout-static.log` and
`phase010-placement-layout-static-corrected.log`.
