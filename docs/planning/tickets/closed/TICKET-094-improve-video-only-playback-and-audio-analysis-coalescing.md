# TICKET-094 - Improve Video-Only Playback and Audio-Analysis Coalescing

**Ticket ID:** TICKET-094
**Title:** Keep editor playback responsive while deferring nonessential audio work
**Status:** complete
**Parent feature:** FEAT-029
**Parent phase:** PHASE-008
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Capability links:** CAP-002, CAP-005, CAP-012
**Owner:** repository implementation in the active worktree
**Approval:** Explicitly authorized by the user's request to implement the
multi-video playback and audio responsiveness improvements without waiting for
separate ticket approval
**Last updated:** 2026-09-07
**Dependencies:** TICKET-083 metadata-first project attachment; existing raw
frame playback; source-level export audio analysis and normalization
**Affected surfaces:** `framestudio/app_project.py`,
`framestudio/ffmpeg_playback.py`, `framestudio/app_playback.py`, editor
composition and playback tests, and target-workstation playback evidence
**Risks:** disabling preview audio could surprise users, stale analysis could
affect preview state, or an unnecessary backend rebuild could still interrupt
active playback
**Evidence path:** `evidence/ticket-094-improve-video-only-playback-and-audio-analysis-coalescing.md`

## Observable requirements

- Given a project with one or more sources, editor playback should default to
  video-only mode so pending or completed source audio analysis does not block
  or compete with frame playback.
- Given an audio-analysis result completes while playback is active, the
  current video backend should not be synchronously stopped and rebuilt for
  each individual source result.
- Given export requires source-level audio decisions, full analysis and
  normalization must remain available and unchanged for export validation.
- Given optional audio preview is unavailable or disabled, video playback
  should remain usable and surface only a non-fatal diagnostic when relevant.
- Given a supported audio-preview path is explicitly enabled, its channel
  layout invocation should work with the installed FFmpeg/ffplay contract.

## Scope

- Make editor preview video-only by default while preserving export-time audio
  analysis and normalization.
- Remove per-source forced video-backend refreshes from background analysis;
  coalesce or independently update optional audio preview if it remains
  exposed.
- Correct the local ffplay channel-layout argument and keep warning behavior
  explicit.
- Add focused playback and lifecycle regressions for active playback,
  multi-source analysis completion, and export audio preservation.

## Non-goals

- Replacing the raw-frame playback architecture.
- Weakening export-time audio analysis, normalization, or verification.
- Claiming universal playback performance across codecs or hardware.
- Adding a new audio-processing dependency or changing the established source
  audio policy.

## Validation

- Focused playback, composition, and audio-analysis lifecycle tests.
- Existing repository unit, compile, contract, smoke, and quality checks.
- Target-workstation multi-source playback smoke with analysis pending and
  completed, recording any environment-specific limitations.

## Definition of done

- Multi-source editor playback remains responsive without unnecessary audio
  preview work by default.
- Analysis completion no longer rebuilds active video playback per source.
- Export still requires and receives the established terminal audio decisions.
- Focused regressions and repository gates provide evidence; the ticket
  remains `verifying` until required user validation and delivery gates are
  terminal.

**Path history:** Created in `docs/planning/tickets/open/` on 2026-09-05.
Moved to `docs/planning/tickets/closed/` on 2026-09-07 after user
validation.
