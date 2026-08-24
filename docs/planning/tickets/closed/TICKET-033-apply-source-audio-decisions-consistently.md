# TICKET-033 - Apply Source Audio Decisions Consistently

**Ticket ID:** TICKET-033
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-005
**Feature:** FEAT-014
**Capability links:** CAP-005, CAP-008, CAP-012
**Status:** complete
**Closure:** user-approved on 2026-08-22 after implementation, automated and
real-media verification, review, user validation, and local delivery evidence;
remote checks remain unavailable and are recorded as an accepted warning.
**Path history:** `tickets/open/TICKET-033-apply-source-audio-decisions-consistently.md`
-> `tickets/closed/TICKET-033-apply-source-audio-decisions-consistently.md`
**Horizon:** future
**Priority:** 3
**Owner:** repository planning and implementation in the active worktree
**Approval:** user-authorized on 2026-08-22 to implement all approved
PHASE-005 tickets, including source-level audio balancing, with the legacy
`resolve_concat.py` mean/median policy applied once per input source
**Provider:** auto; base and target branches are not configured in
`.github/aidd-config.yml`
**Source paths:** `docs/planning/features/open/FEAT-014-balancing-each-source-consistently.md`,
`docs/planning/tickets/open/TICKET-032-analyze-and-persist-source-audio-decisions.md`,
`docs/planning/phases/open/PHASE-005-balancing-sources-and-delivering-consistent-media.md`,
`docs/planning/tickets/closed/TICKET-024-defining-mixed-source-output-canvas-and-timing-policy.md`,
`resolve_editor/export.py`, `resolve_editor/ffmpeg_playback.py`,
`resolve_editor/operations.py`, `.github/aidd-config.yml`
**Dependencies:** TICKET-032; PHASE-004 fixed 1920x1080 output and current
timing policy; validated preview and export boundaries
**Risks:** filtering may alter duration or channel layout, preview and export
could apply different decisions, and segment-level processing could drift
from source-level intent
**Affected surfaces:** preview audio path, export filters, timing and channel
handling, progress/verification, GUI, CLI, tests, and evidence
**Evidence path:** `evidence/phase-005-audio-application.md`
**Protected behaviors:** fixed output canvas, current timing, source
preservation, atomic publication, output verification, and existing
stream-copy eligibility rules remain intact
**Last updated:** 2026-08-22

## Outcome

Preview and export apply the persisted source-level audio decision consistently
to every segment from that source while preserving duration, channels, and
failure safety.

## Scope

- Apply one source decision across all timeline occurrences of that source.
- Keep preview and final export on the same decision and fallback semantics.
- Preserve channels, sample rate, duration, synchronization, and useful
  dynamics under the approved policy.
- Report when a source decision requires decoding or prevents stream copy.
- Surface analysis failures and safe fallback behavior without success-shaped
  errors.

## Explicit non-goals

- Reanalyzing or recalculating gain independently for each segment.
- Choosing delivery codecs or containers; that belongs to FEAT-015.
- Full mixing, mastering, denoising, equalization, visual composition, or
  60 FPS enhancement.

## Observable requirements

- Given one source split into several included segments, preview and export
  should apply the same source-level decision to each segment.
- Given two sources with different decisions, each source should retain its
  own decision in the composed output.
- Given a deleted segment, its source decision should not affect edited
  duration or accidentally re-enable the segment.
- Given a decision requiring audio processing, the exporter should report the
  route change and preserve expected duration, channels, and synchronization.
- Given a failed analysis or filter operation, sources and the last valid
  output should remain intact.

## Commands and quality gates

- `python3 -m unittest discover -s tests`
- `make contract`
- `make check`
- `make smoke`
- `make quality PYTHON=.venv/bin/python`

## Functionality flows

- Preview and export a mixed-source project with different source decisions.
- Split, move, delete, restore, and copy/paste blocks from one source and
  confirm the decision remains source-scoped.
- Compare output duration, channels, synchronization, and peak evidence.

## User validation before closure

Preview and export a disposable mixed-source project containing at least two
audio levels, split one source into multiple segments, and confirm that all
segments from each source sound and measure according to that source's one
decision without changing duration or source files.

## Definition of done

- Preview and export use the same source-level decision and failure behavior.
- Audio application preserves approved timing, channels, duration, and peak
  safety.
- Route changes are explicit and verified.
- Automated, real-media, GUI/CLI, and user-listening evidence is recorded.

## Closure

Preview and export apply source-level decisions consistently in local delivery
checkpoint `6aebb26121eb7e4088b4c3678b670038116be2be`.
