# Simultaneous Tracks and Flexible Delivery

**Discovery ID:** DISC-010
**Parents:** OBJ-001, SCOPE-001, CAP-MAP-001
**Change:** CHG-012; CHG-013 supersedes the initial multi-track export restriction
**Planning depth:** crossCutting
**Horizon:** next approved extension, not the original one-source horizon
**Status:** implemented and verified in PHASE-010
**Approval:** User approved the clarified functionality contract and planning
artifact creation on 2026-10-09.
**Reviewed at:** 2026-10-09
**Confidence:** implemented GTK/CLI/media behavior with terminal source-provider evidence
**Verification:** source `981e5e2a`, Ubuntu run `38004558177`,
`../../evidence/ticket-125-phase010-functionality.md`
**Repository map:** `../planning/repo-map.md`
**Sources:** user request and clarification responses on 2026-10-09; current
`../../README.md`; `phase-002-cut-semantics.md`; `cli-contract.md`;
`future-product-direction.md`; `../../.github/aidd-config.yml`

## Objective and success signals

Make source inspection uncluttered, remove unwanted timeline blocks without
losing recovery, deliver edited files grouped by source when requested, and
arrange up to four synchronized video tracks with matching preview/export
framing and spatial stereo audio in the export.

Success is observable through filename/dimensions/FPS selection feedback,
Backspace plus Undo, one edited output per included track/source pair, collision-free
track movement, automatic 1/2/3/4-panel layouts, and measurable stereo routing.

## Approved requirements

### REQ-010-01 - Selected-video information

Given a selected segment, show only its source filename, original dimensions,
and original FPS in the information strip. Do not display audio-analysis
decisions or a list of all sources there. Selection, not the moving playhead,
owns this information. For multi-selection, use the focused/last-clicked
segment. With no focused segment, show a neutral no-selection state.
Unavailable metadata is labeled unavailable, not fabricated.

Hide routine audio analysis from this strip, not the underlying analysis or
required error/export-blocker reporting. Never copy private sample filenames
from screenshots into tests or planning.

### REQ-010-02 - Backspace removal and Undo

Given selected blocks, Backspace removes their timeline instances and shifts
later blocks left by the removed durations on each affected track only.
Other tracks keep their absolute positions. A multi-selection is one atomic
operation; intervals are half-open and removed durations are counted once.
Remaining intentional gaps are retained except for the removed durations.

Delete retains its existing excluded-block/restore behavior. Backspace can
also remove an already excluded block's occupied timeline interval. Source
media, source references, and source ranges are never deleted.

Undo restores the exact removed IDs, track assignments, positions, exclusion
state, transforms, triplicate state, and selection from the last Backspace
operation. This phase requires Backspace Undo, not a new universal edit-history
system. Prevent stale Undo from overwriting intervening edits; either integrate
with existing history or explicitly invalidate incompatible history. Persist
the edited project, not a promise of Undo across application restarts.
Keyboard shortcuts must not intercept Backspace/Delete in text-entry fields.

### REQ-010-03 - Edited source exports independently within each track

Default: export the final video only. An optional, default-off source-export
setting creates a collision-safe folder with a subfolder per included track
and one edited video per original source identity within that track.
Grouping uses stable `(track_id, source_id)`, never filenames alone.
Track 1 with A/B and Track 2 with A/C produces:

```text
Track 1/
  A.mp4
  B.mp4
Track 2/
  A.mp4
  C.mp4
```

Treat every track independently as if it were the only timeline. Within each
track/source pair, concatenate included blocks in that track's timeline order.
A source with three included blocks produces one edited file for that pair,
not three files or the untouched original. Preserve repeated/copied blocks;
the same source on different tracks produces independent files even when
its ranges or modifications are identical. Never deduplicate across tracks.

Render each pair on the full 1920x1080 canvas using existing single-timeline
framing and its individual segment zoom/offsets/triplicate modifications.
Do not bake in the simultaneous final video's split-screen slot crop.
Use only that source's normal audio with existing source-level handling;
retain its stereo characteristics without layout-based pan or other-track
mixing. Apply selected output FPS, below-50-FPS enhancement eligibility,
optional upscale, and the fastest valid verified render route.
Do not deliver excluded ranges, unused sources, or empty/excluded-only tracks.
Intentional project placement gaps and other-source intervals are not inserted
into these source-only edited reels.

When source exports are enabled, final-video export remains enabled by
default but can be switched off. Reject a request selecting neither output.
Ordinary projects retain their existing final-export behavior.

Source exports are available for one to four tracks; additional populated
tracks do not disable the option. Empty/excluded-only tracks consume no
output folder or file. An entirely empty edit or a no-output request still
fails explicitly. GUI, CLI and persisted settings express the same modes
and enumerate output results by track/source pair.

The optional final video remains the synchronized multi-track composition
defined by REQ-010-05 and REQ-010-06. Selecting source-only does not render
that composition. No additional combined-per-track export or synchronized
source-layer mode is included.

Verify each requested file before atomic publication. If one output fails,
report already verified publications and failed/pending outputs explicitly.
Resume must not rerender valid completed outputs or reuse stale artifacts.
Track/source identities, output mode, standalone framing/normal-audio versus
final composition, and relevant edits/policies belong in checkpoint identity.
Track folder and source names must be sanitized, collision-safe, and cannot
overwrite originals; renaming/reordering tracks must not alias their artifacts.

### REQ-010-04 - One to four synchronized tracks

One global playhead/timebase drives up to four ordered video tracks. Existing
projects migrate to one equivalent track. Users add/remove empty tracks
explicitly; refuse a fifth track and refuse silently discarding a populated
track. New imports use the current active track; the original one-track
workflow stays familiar.

Moving a block between tracks preserves its source interval, identity,
duration, exclusion state, and all segment modifications. Placement supports
non-negative absolute starts and intentional gaps. Two blocks cannot occupy
overlapping time on the same track, including visible excluded blocks.
Different tracks may overlap intentionally.

Dragging into an occupied interval moves only the dragged block to the first
free interval after the collided block, skipping further collisions until the
entire dragged duration fits. Existing blocks do not move. Invalid drops
leave the project unchanged. Splitting, copying, pasting, selection, duration,
save/reopen, autosave/recovery, and CLI operations must remain coherent.

### REQ-010-05 - Dynamic sections and per-segment framing

At each half-open timeline interval, count included blocks active at that
instant, in ascending track order. Empty/excluded/inactive tracks consume no
visual slot. One active block fills the canvas; two share equal vertical
halves; three share equal vertical thirds; four occupy equal 2x2 quadrants
in row-major order. The fixed output remains 1920x1080.

Center-crop to fill each section, preserving aspect ratio. Source center maps
to section center by default: two centered objects appear at X=480 and X=1440.
Per-segment zoom and X/Y offsets remain independent and editable. Existing
triplicate composition stays inside its segment's section and creates no extra
tracks. Fixed stereo pan does not alter image position.

No active blocks means black video and silent output. Duration ends at the
last included block on any track, including leading/intermediate gaps.
Layouts update at active-set boundaries without blending across hard cuts.
Preview and render use the same timing/framing rules.

### REQ-010-06 - Silent preview and fixed export stereo pan

Preview is video-only for this horizon, including one-track projects. No
preview audio is launched. The final composed video mixes all active sources' audio, applies
existing source-level audio handling, aligns it to timeline starts/cuts, and
protects against clipping. Silent sources contribute silence.

| Active clips | Visual positions, in track order | Fixed stereo pan |
|---|---|---|
| 1 | Full canvas | 0% |
| 2 | Left, right | -25%, +25% |
| 3 | Left, center, right | -25%, 0%, +25% |
| 4 | Top-left, top-right, bottom-left, bottom-right | -25%, +25%, -50%, +50% |

Pan ranges from -100% left-only to +100% right-only, with 0% centered.
Percentages are fixed product constants, not user controls. Slot changes
update pan to match the current layout, not a permanent track number.
The implementation contract must define a tested mono/stereo/channel-layout
mapping and gain law; do not confuse this with visual panning or assert that
percentages are literal channel-volume percentages.

These slot-based pan/mix rules apply only to the simultaneous final video,
not the standalone track/source exports in REQ-010-03.

## Boundaries and protected behavior

No implementation, dependency installation, architecture replacement, commit,
push, or ticket closeout is authorized by this planning request. No transitions,
keyframes, arbitrary fifth track, standalone audio tracks, or general-purpose
undo/redo are included. Retain Linux/GTK/FFmpeg, legacy imports/projects/CLI,
atomic saves, original source bytes, verified partial-output handling,
enhancement artifact gates, exact output frame counts, cancellation/recovery,
and explicit failures.

### Subsequent execution authorization

After the final planning write, the user authorized orchestrated implementation,
review and actual UI/CLI functionality tests on 2026-10-09, using bounded
GPT-5.6 Luna agents at maximum reasoning and safe parallelism. This supersedes
the original planning-only restriction on implementation, not the product
boundaries or source protection. CHG-014 subsequently records explicit
authorization for autonomous implementation, testing and delivery without
routine questions. The repository mode is automatic. Routine approvals are
bootstrap-authorized; every validation decision uses Rubber Duck GPT-5.6
Luna high `all-validation`. Agent-run functionality is `automaticValidation`,
never a human result. Dependencies, unavailable tools, security, provider,
branch protection, remote checks and merge/lifecycle policy remain gates.

## Verification and implementation decisions

Every ticket maps its acceptance outcomes to a named planned executable
functionality test. GUI charters require a real GTK session; media charters
use generated fixtures, FFmpeg rendering/probing, pixel/audio measurements,
source hashes, failure injection, and persistence round trips as applicable.
Unit assertions alone do not satisfy acceptance.

Before execution, approve schema migration and timing/history contracts in
TICKET-115/TICKET-110, shared layout/transform ordering in TICKET-119, stereo
gain/channel mapping in TICKET-122, and multi-output session identity in
TICKET-124. These are bounded technical decisions within confirmed product
behavior, not permission to invent a dependency or silently change behavior.
No remaining product question blocked the planning write. Current execution
status is tracked in the phase/backlog rather than inferred from this contract.
DESIGN-010-115 was subsequently approved: synchronized Delete keeps absolute
time occupied, and legacy conversion explicitly confirms preserving visible
positions even when that introduces output gaps. Remaining bounded history,
layout/audio and checkpoint contracts still require their own approvals.
