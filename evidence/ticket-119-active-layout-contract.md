# TICKET-119 - Shared Active Layout Evidence

Parents: OBJ-001 / SCOPE-001 / PHASE-010 / FEAT-036.
Requirement: DISC-010 / REQ-010-05.
Integration branch: `phase/010-synchronized-tracks`; base `330e13b`.
Mode: automatic, authorized by CHG-014.
Validation profile: `rubber-duck / gpt-5.6-luna / high / all-validation`.

## Implementation and remediation

Owned implementation: `framestudio/layout_plan.py` and the two dedicated
layout-plan test modules. The initial candidate was returned for correction:
formatting failures, an insufficient four-track fixture, opaque state keys
incorrectly controlling exclusion, a preframed-source bypass, and lossy
dimension/SAR coercion. The corrected candidate uses canonical deletion,
rejects incompatible preparation domains and malformed geometry, and actually
exercises three and four simultaneous clips.

## Integrated raw checks

Command:
` .venv/bin/python -m unittest -v tests.test_editor_layout_plan tests.test_editor_layout_plan_functionality`

Observed: nine tests, zero failures/errors/skips, 0.636 seconds.
Changed-file Ruff formatting/lint, module mypy and `git diff --check`
also completed successfully. These are deterministic raw results, not
independent orchestrator readiness decisions.

## Automatic functionality and local interface review

Decision source: exact-profile validator agent
`2f555536-fbda-43ff-87bc-f2fee944c896`, turn 0.
Recorded by: integration owner, transcribing the read-only validator.
Categories: `automaticValidation`, `review`.
Functionality test:
`tests.test_editor_layout_plan_functionality.LayoutPlanFunctionalityTests.test_saved_four_track_project_plans_from_real_ffmpeg_sources`.
Supported boundary: real FFmpeg-generated sources, versioned project
save/reopen, and public layout planning.

The validator independently ran the command above: nine tests passed in
0.634 seconds. Assertions cover portrait/landscape/ultrawide/square geometry,
actual active counts zero through four, exact half-open boundaries, black
gaps, persistent track order, legacy compaction, triplicate partitions,
transform isolation, schema-4 round trip and unchanged source hashes.

Decision: **PASS** for scoped automatic functionality and
**PASS_WITH_LIMITATIONS** for local review. TICKET-121 and TICKET-122 are
released to consume the shared interface in disjoint worktrees.

Conditions: video rendering must probe original SAR independently rather
than infer it from the current project metadata fallback. Native,
standalone-full-canvas and final-slot preparations must remain distinct.
Absolute playback/export guards remain until their owning consumers pass.

## Remaining gates

The aggregate quality command is running, not yet classified. Decoded
preview/render equivalence belongs to120/121/125; final audio/video export
belongs to123/124. No full-suite, remote CI, commit, publication, delivery
or lifecycle closeout is claimed by this scoped review.

## Cross-file duplication remediation

The first aggregate static run failed with one new clone: the fixture hash
loop duplicated `benchmarks/restoration_benchmark.py`. The integration owner
simplified hashing of the small generated media files to
`hashlib.sha256(path.read_bytes()).hexdigest()`. No baseline was changed.
The public layout/functionality modules passed again as part of the20-test
112/119 integration run in12.327 seconds. All repository static analyzers
then completed with exit zero. A new full-quality run includes the gathered
112/116/119 implementations and corrected paired GTK fixture.
