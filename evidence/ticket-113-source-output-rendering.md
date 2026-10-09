# TICKET-113 - Independent Edited Source Rendering Evidence

Parents: OBJ-001 / SCOPE-001 / PHASE-010 / FEAT-034.
Requirement: DISC-010 / REQ-010-03 / CHG-013.
Mode: automatic under CHG-014.
Required profile: `rubber-duck / gpt-5.6-luna / high / all-validation`.
Branch: `phase/010-synchronized-tracks`; base `330e13b`.

## Integrated route and corrected failure boundaries

The source renderer projects each stable (track_id, source_id) request onto
the existing verified one-source export route. It compacts retained cuts and
copies, carries block transforms/triplicate and source audio settings, and
does not bake synchronized placement gaps, slot framing or layout pan into
independent reels. Source-only CLI routing does not start a final compositor.
Combined synchronized final rendering remains explicitly guarded until
TICKET-123/124.

Parent review rejected the first candidate's incomplete original-source
guards, silent cleanup errors, incorrect combined partial-success aggregation
and verification after requested-destination publication. The corrected
candidate protects every registered original and path alias before planning
and execution, including altered request/export-plan destinations. Existing
delivery verifies an isolated hidden staging output, then source snapshots
and media probing complete before atomic replacement of the requested path.
Failed verification preserves an existing requested output. Cleanup failures
are reported as failed results, not silently discarded.

Partial success now accounts for all requested final/source results. Typed
OutputIdentity and ExportSessionInfo replace untyped properties. Source
resume/discard routes use the isolated execution destination. Whole
multi-output resume/invalidation remains owned by TICKET-124.

## Raw technical and automated functionality

Command:
`.venv/bin/python -m unittest -v tests.test_editor_source_outputs tests.test_editor_source_outputs_functionality tests.test_editor_cli_export`.
Observed: 26 tests passed in 55.739 seconds.
Artifact: session `files/phase010-root-source-outputs.log`.
This includes eleven focused source regressions, two public CLI/real-FFmpeg
functionality scenarios and thirteen protected CLI-export regressions.

Actual functionality selectors:
- `SourceOutputFunctionalityTests.test_public_source_only_render_produces_stable_verified_reels`
- `SourceOutputFunctionalityTests.test_public_source_only_failure_reports_partial_success_and_no_failed_publish`

Generated sources exercise stereo channels, multiple resolutions and integer
rates 12/24/30, four tracks and six independent reels. Assertions cover stable
pair identities, retained order/copies/edits, compact durations, target
FPS/canvas, full-canvas decoded video, source-specific stereo without slot pan,
all-original hashes and no final output. An injected output failure proves
five verified outputs and one unpublished failure with truthful partial
success. Unit regressions cover protected aliases, planner replacement,
existing-destination preservation, cleanup errors and mixed final/reel success.

Actual AI execution and the charter's 29.97/59.94 source-rate scenarios were
not forced by these two functionality cases. They are not claimed passed from
integer-rate tests or mocked eligibility decisions.

Four owned files passed Ruff format/lint; all 63 configured implementation
sources passed mypy. The integrated dependency check passed.

## Cross-file fixture correction

The configured root duplication scan caught one clone with the existing
TICKET-112 functionality factory. Parent extracted its unchanged probed-source
reference helper and reused it from TICKET-113, without changing media
generation or source data. Combined T112/T113 actual functionality then passed
three tests in 47.822 seconds, and both fixture modules passed Ruff.
Artifact: session `files/phase010-root-source-shared-fixture.log`.

The repeated configured duplication scan reports 49 clones, 1.228% and
three new clones, all in the still-pending T117 fixture scope. The T113 clone
is resolved; the baseline is unchanged. This is not a whole-quality PASS.
Artifact: session `files/phase010-source-fixture-duplication.log`.

## Pending exact-profile decision

Validator `6a2540b0-3610-444e-b264-0f42b37bbac1` is reviewing the integrated
source-render seam and directly related shared fixture. TICKET-114 is not
released from raw results alone. No delivery or lifecycle completion is
claimed.

## Terminal bounded automatic validation: PASS

Validator `6a2540b0-3610-444e-b264-0f42b37bbac1`, turn 3, applied the exact
required profile and released the T113 source-render consumer seam to T114.
It independently ran both public CLI/real-media cases: two passed in
36.861 seconds, plus eight focused safety regressions in 0.055 seconds.
Its directly related planner/fixture checks also passed. Scoped mypy, Ruff
and diff checks passed.

The decision found no blockers in the corrected source-render interface:
source/copy/transform isolation, verified staging, protected originals,
existing-destination preservation, truthful cleanup/partial success and
source-only routing were accepted. This is an interface release, not complete
ticket/phase/remote-CI readiness. The original worker is additionally closing
the explicit fractional-rate/actual-AI charter gap with a narrow real-media
case in its isolated worktree. That outcome is not inferred from this bounded
PASS, and T113 remains open/verifying.

## Real fractional-rate RVE charter

Added executable selector:
`SourceOutputFunctionalityTests.test_fractional_rve_source_outputs_use_real_backend_and_reuse_high_rate_source`.
The actual configured rve-4.26/TensorRT runtime validated. Generated
30000/1001 and 60000/1001 inputs produced two verified 1920x1080,
60000/1001, 36-frame stereo reels. Progress asserts interpolation for only
the low-rate source. Output probing, decoded color/tone ownership and
unchanged original hashes are asserted.

The high-rate reel uses ordinary non-enhanced decoding because audio
normalization prevents stream copy. This proves interpolation exclusion, not
zero-cost stream-copy reuse. Upscale is disabled in this narrow charter;
actual restoration is separately exercised by T121, not inferred here.

Parent reused the existing constant-source generator for fractional rates
and configurable duration, removing a copied generator while preserving the
previous 1.2-second defaults. The complete three-case real functionality
module passed in 54.344 seconds with no skips, then native Ruff formatting
and lint passed. Artifact:
session `files/phase010-root-source-rve-functionality.log`.

The configured shared duplication gate subsequently found two new
intra-module source-fixture/assertion clones and six video-test clones,
alongside the existing three GTK clones. Original workers are correcting
their owned test fixtures only, preserving functionality. The unchanged
baseline is not expanded. Fresh exact-profile classification of the added
AI charter/fixture delta is pending.

## Accepted fractional-RVE and fixture delta

Validator `6a2540b0-3610-444e-b264-0f42b37bbac1`, turn 6, returned
**bounded PASS** under `gpt-5.6-luna / high / all-validation`.
The three actual source-output functionality cases passed with zero skips,
including validated RVE enhancement of `30000/1001` and non-interpolation
of `60000/1001`. Shared fixture extraction preserved assertions.
Production and CLI interfaces remain unchanged and released. This does not
release T114 production, T125, aggregate quality or remote delivery.
