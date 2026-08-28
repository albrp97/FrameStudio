# TICKET-032 - Analyze and Persist Source Audio Decisions

**Ticket ID:** TICKET-032
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-005
**Feature:** FEAT-014
**Capability links:** CAP-008, CAP-012
**Status:** complete
**Closure:** user-approved on 2026-08-22 after implementation, automated and
real-media verification, review, user validation, and local delivery evidence;
remote checks remain unavailable and are recorded as an accepted warning.
**Path history:** `tickets/open/TICKET-032-analyze-and-persist-source-audio-decisions.md`
-> `tickets/closed/TICKET-032-analyze-and-persist-source-audio-decisions.md`
**Horizon:** future
**Priority:** 2
**Owner:** repository planning and implementation in the active worktree
**Approval:** user-authorized on 2026-08-22 to implement all approved
PHASE-005 tickets, including source-level audio balancing, with the legacy
`framestudio_concat.py` mean/median policy applied once per input source
**Provider:** auto; base and target branches are not configured in
`.github/aidd-config.yml`
**Source paths:** `docs/planning/features/open/FEAT-014-balancing-each-source-consistently.md`,
`docs/planning/tickets/open/TICKET-031-define-source-level-audio-policy.md`,
`docs/planning/phases/open/PHASE-005-balancing-sources-and-delivering-consistent-media.md`,
`docs/specs/capability-map.md`, `framestudio/model.py`,
`framestudio/media.py`, `framestudio/persistence.py`,
`.github/aidd-config.yml`
**Dependencies:** TICKET-031 approved policy; PHASE-004 mixed-source source
identity and project persistence; representative audio fixtures
**Risks:** decisions could be accidentally stored per segment, analysis
results could become stale after source replacement, and an error path could
silently substitute a successful-looking default
**Affected surfaces:** source model, audio analysis service, project schema,
persistence, source relinking, CLI inspection, tests, and evidence
**Evidence path:** `evidence/phase-005-source-audio-decisions.md`
**Protected behaviors:** existing project schema compatibility, source
preservation, source identity, segment ordering, deletion state, and
structured CLI errors remain unchanged
**Last updated:** 2026-08-22

## Outcome

Each imported source can be analyzed once under the approved policy and its
explicit audio decision can be persisted and recovered without creating
segment-specific automatic levels.

## Scope

- Analyze the audio streams of each input source independently.
- Store measurement metadata, decision, policy version, status, diagnostics,
  and any approved override boundary at source scope.
- Define stale-result behavior when a source is relinked or its media changes.
- Preserve deterministic serialization and migration behavior.
- Expose enough state for later preview, export, GUI, and CLI work without
  implementing those consumers here.

## Explicit non-goals

- Applying gain or normalization during preview or export.
- Per-segment analysis or automatic level recalculation after split.
- New audio algorithms beyond the approved TICKET-031 policy.
- Triplicate composition, visual transforms, or 60 FPS enhancement.

## Observable requirements

- Given a source with multiple timeline segments, analysis should produce one
  source-level decision referenced by all of those segments.
- Given two sources with different audio, analysis should produce independent
  decisions and diagnostics.
- Given silence, unsupported audio, or an analysis failure, persisted state
  should record the explicit status and safe fallback rather than a false
  success.
- Given a save/reopen round trip, measurements, decision, policy version,
  source identity, and failure status should remain equivalent.
- Given a source relink or changed media identity, stale analysis should be
  detected according to the approved policy.

## Commands and quality gates

- `python3 -m unittest discover -s tests`
- `make check`
- `make contract`
- `make quality PYTHON=.venv/bin/python`

## Functionality flows

- Import representative sources, analyze them, and inspect source-scoped
  decisions.
- Split one source into several segments and confirm no new automatic
  decision is created.
- Save, reopen, and relink a project while checking explicit stale/failure
  behavior.

## User validation before closure

Open a disposable mixed-source project with different audio levels, inspect
the source-level decisions, split and reorder segments, save/reopen the
project, and confirm that each source keeps one recoverable decision.

## Definition of done

- Source analysis and persistence are deterministic and covered by tests.
- Source identity, decision status, policy version, and diagnostics survive
  project round trips.
- Per-segment automatic gain is not introduced.
- The evidence record covers success, silence, unsupported audio, failure, and
  stale-source cases.

## Closure

Source-scoped analysis and persistence are complete in local delivery
checkpoint `6aebb26121eb7e4088b4c3678b670038116be2be`.
