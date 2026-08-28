# TICKET-061 - Research Lossless Cut Preview Architecture

**Ticket ID:** TICKET-061
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-008
**Feature:** FEAT-024
**Capability links:** CAP-002, CAP-005, CAP-012
**Status:** complete
**Closure:** closed on 2026-08-26 after the revision-pinned research notes,
license boundary, and transferable preview hypotheses were recorded; the
external implementation limitations remain explicit.
**Horizon:** future
**Priority:** 1
**Owner:** repository planning; maintainer identity is not recorded
**Approval:** user-authorized on 2026-08-26 for PHASE-008 planning; execution
requires the configured preimplementation and approval gates
**Provider:** auto; base and target branches are not configured
**Last updated:** 2026-08-26
**Source paths:** `docs/planning/features/closed/FEAT-024-optimizing-cursor-driven-preview.md`,
`framestudio/app_playback.py`, `framestudio/ffmpeg_playback.py`,
`framestudio/timeline.py`, `docs/specs/future-product-direction.md`,
[Lossless Cut repository](https://github.com/mifi/lossless-cut.git),
`.github/aidd-config.yml`
**Dependencies:** target-workstation access; a disposable research location;
network access or an explicit unavailable-source record
**Risks:** external code may change, license obligations may be missed, and
patterns that work for Lossless Cut may not fit the Python/GTK/FFmpeg stack
**Affected surfaces:** preview research, benchmark design, playback
architecture notes, licensing records, and future implementation choices
**Evidence path:** `evidence/phase-008-preview-responsiveness.md`
**Path history:** `tickets/open/TICKET-061-research-lossless-cut-preview-architecture.md`
-> `tickets/closed/TICKET-061-research-lossless-cut-preview-architecture.md`
**Protected behaviors:** no production code, dependency, source media, or
legacy script is changed by this research ticket

## Outcome

The project has a revision-pinned, license-aware description of Lossless
Cut's preview and seek architecture and a shortlist of patterns worth testing
in this editor.

## Scope

- Clone the public repository into a disposable, non-committed location.
- Record the inspected revision and relevant license information.
- Trace preview frame acquisition, seeking, caching, scheduling, and UI
  update behavior from source and documented build/runtime details.
- Separate transferable concepts from code or dependencies that must not be
  copied or introduced.

## Explicit non-goals

- Vendoring, copying, or importing Lossless Cut code.
- Adding a submodule, runtime dependency, or generated checkout to the
  repository.
- Declaring a faster strategy before the benchmark tickets measure it.

## Observable requirements

- Given the public repository is available, the evidence should identify the
  revision, inspected subsystems, license, and applicable patterns.
- Given the repository or network is unavailable, the evidence should record
  the limitation and continue without a success-shaped assumption.
- Given a candidate pattern, the notes should explain its compatibility and
  risks for GTK 4/PyGObject/FFmpeg raw-frame playback.

## Definition of done

- Research notes are source-linked and revision-pinned.
- License and non-copying boundaries are explicit.
- Candidate strategies are written as benchmark hypotheses for TICKET-063.
- No external files are tracked or production behavior is changed.

## User-validation plan

- **Setup:** provide the evidence file and the recorded source revision.
- **Steps:** inspect the architecture notes, candidate shortlist, and license
  boundary; confirm the checkout is outside the repository.
- **Expected result:** the notes are understandable and actionable without
  treating external implementation details as committed design.
- **Failure paths:** unavailable source, incomplete license information, or
  untraceable claims are recorded as blockers or research gaps.
- **Cleanup:** remove the disposable checkout after evidence capture.
- **Evidence response:** return the revision, applicable patterns, and known
  limitations.
- **Pass criteria:** the research can guide benchmark design without adding
  copied code or an unapproved dependency.

## Closure

TICKET-061 was closed after the Lossless Cut revision, GPL-2.0-only license,
inspected subsystems, compatible concepts, and research limitations were
captured in the linked evidence. The disposable checkout was removed and no
runtime dependency was introduced.
