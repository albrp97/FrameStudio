# FEAT-014 - Balancing Each Source Consistently

**Feature ID:** FEAT-014
**Parent links:** OBJ-001, SCOPE-001, PHASE-005
**Capability links:** CAP-008, CAP-012
**Status:** complete
**Closure:** user-approved on 2026-08-22 after TICKET-031 through TICKET-033
passed implementation, automated, real-media, review, user-validation, and
local delivery gates; remote checks remain unavailable and are recorded as an
accepted warning.
**Horizon:** future
**Priority:** 1
**Owner:** repository planning and implementation in the active worktree
**Approval:** user-authorized on 2026-08-22 to implement and close the
approved PHASE-005 ticket set after validation
**Source paths:** `vision.md`, `docs/specs/project-scope.md`,
`docs/specs/capability-map.md`,
`docs/specs/future-product-direction.md`,
`docs/planning/phases/open/PHASE-005-balancing-sources-and-delivering-consistent-media.md`,
`.github/aidd-config.yml`
**Dependencies:** PHASE-004A complete; PHASE-004 mixed-source model and
fixed-output policy; representative local audio fixtures
**Risks:** loudness measurements may not predict perceived balance, source
audio may have incompatible channels or sample rates, and failed analysis
could otherwise become a silent default
**Affected surfaces:** source audio analysis, project state, preview/export
audio handling, GUI, CLI, persistence, tests, and evidence
**Evidence path:** `evidence/phase-005-audio-policy.md`
**Planned tickets:** TICKET-031, TICKET-032, TICKET-033
**Last updated:** 2026-08-22
**Path history:** `features/open/FEAT-014-balancing-each-source-consistently.md`
-> `features/closed/FEAT-014-balancing-each-source-consistently.md`

## Outcome

Each input video receives one explicit, inspectable audio decision that is
applied consistently to every timeline segment originating from that source.

## Scope

- Define the measurement, target, gain/normalization, peak-protection, and
  fallback policy for source-level audio handling.
- Analyze each input source independently and persist its decision.
- Apply the decision across all segments of that source without recalculating
  a different automatic level per segment by default.
- Preserve expected channels, duration, useful dynamics, and explicit failure
  states.

## Explicit non-goals

- Replacing source audio with another recording.
- Per-segment automatic gain as the default behavior.
- Full mixing, mastering, equalization, noise removal, or voice isolation.
- Triplicate composition, visual transforms, or 60 FPS enhancement.

## Observable requirements

- Given a source with one or more timeline segments, the project should store
  one source-level audio decision and reuse it across those segments.
- Given sources with different levels, the editor should analyze them
  independently rather than using one project-wide or per-segment default.
- Given silence, unsupported audio, incompatible channels, or failed analysis,
  the editor should expose an explicit result and preserve a safe fallback.
- Given a saved project, reopening it should restore the same source-level
  decision without modifying the original media.

## Validation intent

- Compare deterministic measurements and decisions for generated fixtures with
  quiet, loud, clipped, silent, mono, stereo, and multi-channel audio.
- Confirm that splitting, moving, deleting, or copy/pasting segments does not
  create a new automatic source-level decision.
- Review persisted project and CLI state for source identity, decision,
  failure status, and override boundaries.

## Protected behavior

Existing segment identity, block ordering, deletion state, split inheritance,
fixed 1920x1080 output, source preservation, and safe temporary-output
behavior remain unchanged.

## Definition of done

- The source-level audio policy is documented and approved.
- Analysis and persisted decisions are deterministic and source-scoped.
- Preview/export application uses the same decision for every segment of a
  source.
- Automated, real-media, GUI/CLI, persistence, and user-validation evidence
  covers the feature outcome.

## Closure

TICKET-031 through TICKET-033 satisfy the source-level audio outcome. The
reviewed local delivery checkpoint is
`6aebb26121eb7e4088b4c3678b670038116be2be`; remote checks remain unavailable.
