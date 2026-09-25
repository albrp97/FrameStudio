# TICKET-105 - Randomize Multi-Clip Add Order

**Ticket ID:** TICKET-105
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-004
**Feature:** FEAT-011
**Capability links:** CAP-002, CAP-003, CAP-007, CAP-012
**Status:** verifying
**Horizon:** future
**Priority:** 1
**Owner:** repository implementation in the active worktree
**Approval:** User-authorized by the request to fix multi-clip randomization,
then confirmed under CHG-011 to include the complete worktree in delivery.
**Last updated:** 2026-09-24
**Source paths:** `docs/planning/reviews/CHG-011-deliver-authorized-existing-worktree-changes.md`,
`docs/planning/features/open/FEAT-011-arranging-and-editing-a-mixed-source-timeline.md`,
`framestudio/app_project.py`, `framestudio/cli.py`,
`framestudio_concat.py`, `framestudio/timeline_order.py`,
`tests/test_editor_randomized_clip_add.py`, `tests/test_concat.py`,
`.github/aidd-config.yml`
**Dependencies:** approved mixed-source project identity and existing timeline
append behavior
**Risks:** reordering existing clips, losing source-to-block identity, or
changing one-clip add behavior
**Affected surfaces:** GUI source import/add, CLI import/add, legacy concat
ordering helper, timeline ordering, and tests
**Evidence path:** `evidence/ticket-105-randomized-clip-add-order.md`
**Protected behaviors:** existing project edits and source media remain
unchanged; single-clip additions append normally; source identity remains
aligned with timeline blocks

## Outcome

When a user imports or adds more than one video in one batch, the new clips
appear in randomized order in the timeline without disturbing clips already
in the project.

## Scope

- Use one shared randomization rule for GUI, CLI, and the legacy concat
  workflow.
- Randomize only multi-clip batches; preserve the ordinary position of a
  single imported or added clip.
- Ensure an unchanged random shuffle cannot silently leave a multi-clip batch
  in its input order.
- Preserve source-to-timeline identity and all existing project state.

## Explicit non-goals

- Reordering clips already present in a project.
- Adding random playback, transitions, or a persistent “shuffle” setting.
- Changing media probing, clip trimming, source paths, or project schema.

## Observable acceptance criteria

- Given a multi-video GUI import, the created timeline contains the same
  videos in a randomized order.
- Given an open GUI project and a multi-video add batch, existing timeline
  blocks remain first and unchanged while the new batch is randomized.
- Given CLI import or add with multiple videos, the resulting project uses
  the same random-order behavior as the GUI.
- Given a single-video import/add, no random reorder occurs.
- Given any batch, every source remains attached to the matching timeline
  block and original media bytes remain unchanged.

## Validation

- Automated functionality tests for GUI append and CLI add behavior.
- Deterministic helper tests for unchanged-shuffle and one-item behavior.
- Existing concat, project persistence, repository, and compatibility tests.
- Target-workstation GUI confirmation and window-only before/after evidence.

## User-validation plan

- **Setup:** open a project containing one existing clip and prepare at least
  three additional videos with distinct visible content.
- **Steps:** add all three in one GUI batch; inspect their order; add one
  additional video separately; save/reopen; repeat a multi-video add through
  the CLI.
- **Expected result:** only the new multi-video batch is randomized, the
  existing clip and its edits stay unchanged, a single clip appends at the
  end, and save/reopen preserves the produced order.
- **Failure paths:** existing clips move, batch order remains the input order,
  source/block identities mismatch, project state is lost, or source media
  changes.
- **Cleanup:** remove only temporary project/output files created for the
  test; do not delete source media.
- **Evidence response:** return `PASS`, `FAIL`, or `BLOCKED` with observed
  order and window-only screenshot paths.
- **Pass criteria:** GUI and CLI agree on multi-clip randomization and
  preserve existing timeline state.
