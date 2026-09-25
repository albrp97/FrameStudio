# Delivery Evidence: TICKET-105

- Phase: `PHASE-004` - Combining Mixed-Source Footage
- Feature: `FEAT-011` - Arrange and Edit a Mixed-Source Timeline
- Ticket: `TICKET-105` - Randomize Multi-Clip Add Order
- Status: `verifying`
- Branch: `ticket/randomize-multi-clip-add-order`
- Base revision: `06a1a8d433aec26dff53b6bdcb1dcd7372eeb1fd`
- Change control: `CHG-011`
- Planning chain: `OBJ-001 -> SCOPE-001 -> CAP-002/CAP-003/CAP-007/CAP-012 -> PHASE-004 -> FEAT-011 -> TICKET-105`

## RAND-BASELINE-001

- Requirement/flow: GUI, CLI, and compatibility concat paths must apply the
  same multi-clip ordering rule without reordering existing clips.
- Observed: Before the fix, the editor GUI and CLI project-add paths did not
  use the existing concat randomization behavior.
- Status: `passed` as a source-inspection baseline.

## RAND-IMPLEMENT-001

- Requirement/flow: Multi-video import/add batches are randomized, single
  additions remain in place, source identity stays aligned with timeline
  blocks, and existing timeline content remains first.
- Implementation: `framestudio/timeline_order.py` provides the shared helper.
  GUI source loading, CLI import/add, and `framestudio concat` use it. If a
  multi-item shuffle returns the original order, the helper rotates the batch
  to ensure the result differs.
- Documentation: `README.md` documents the behavior for GUI and CLI users.
- Status: `passed`.

## RAND-FUNCTIONAL-001

- Command:
  ```sh
  .venv/bin/python -m unittest \
    tests.test_editor_randomized_clip_add \
    tests.test_concat.ConcatTests.test_multiple_videos_are_shuffled_onto_the_timeline \
    tests.test_concat.ConcatTests.test_multiple_video_shuffle_never_keeps_the_original_order
  ```
- Expected: GUI append and CLI add randomize only new multi-item batches;
  helper and concat paths preserve all items and never leave a multi-item
  batch in its original order.
- Observed: Four focused regression and functionality tests passed.
- Full suite: `make quality PYTHON=.venv/bin/python` passed 489 tests.
- Status: `passed`.

## RAND-USER-001

- Requirement/flow: Confirm randomized batch order and unchanged existing
  timeline state in the target GTK editor and CLI workflow.
- Status: `blocked` pending user validation.
- Setup: Open a saved project with one existing clip and prepare three
  additional videos with distinct visible content.
- Steps: Add all three videos in one GUI batch; inspect order; add a single
  video; save and reopen; repeat a multi-video add with the CLI.
- Expected: Only the newly added multi-video batch is randomized. Existing
  clips and edits stay unchanged, a single clip appends at the end, and
  save/reopen preserves the produced order.
- Failure paths: Existing clips move; a batch remains in the input order;
  source/block identities mismatch; project state is lost; or source media
  changes.
- Cleanup: Remove only temporary project/output files created for the test.
- Evidence response: Return `PASS`, `FAIL`, or `BLOCKED`, observed order, and
  window-only screenshot paths.
- Local/PR parity: `unavailable`; the workflow's Python runtime differs from
  local Python 3.14.7 and PR checks have not run.

## RAND-USER-RESPONSE-001

- User response: `PASS` to the combined validation handoff. The user stated
  they tested the behavior and declined to provide screenshot paths or notes.
- Evidence received: No before/after window-only screenshots, observed clip
  order, or saved/reopened project paths were supplied.
- Status: `passedWithConcerns` for the user's response; the configured UI
  evidence requirement remains blocked, so TICKET-105 stays `verifying`.
