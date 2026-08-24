# FEAT-015 - Selecting Tested Delivery Routes

**Feature ID:** FEAT-015
**Parent links:** OBJ-001, SCOPE-001, PHASE-005
**Capability links:** CAP-005, CAP-012
**Status:** complete
**Closure:** user-approved on 2026-08-22 after TICKET-034 and TICKET-035
passed implementation, automated, real-media, review, user-validation, and
local delivery gates; remote checks remain unavailable and are recorded as an
accepted warning.
**Horizon:** future
**Priority:** 2
**Owner:** repository planning and implementation in the active worktree
**Approval:** user-authorized on 2026-08-22 to implement and close the
approved PHASE-005 ticket set after validation
**Source paths:** `vision.md`, `docs/specs/project-scope.md`,
`docs/specs/capability-map.md`,
`docs/specs/future-product-direction.md`,
`docs/planning/phases/open/PHASE-005-balancing-sources-and-delivering-consistent-media.md`,
`docs/specs/phase-002-export-policy.md`, `.github/aidd-config.yml`
**Dependencies:** PHASE-004A complete; PHASE-004 fixed 1920x1080 output and
established render profile; source-level audio policy from FEAT-014
**Risks:** codec and hardware behavior varies by workstation, audio changes
can invalidate stream copy, and a fast command can still produce unsafe media
**Affected surfaces:** delivery benchmarks, export planning, FFmpeg execution,
output verification, progress reporting, GUI, CLI, and documentation
**Evidence path:** `evidence/phase-005-delivery-profiles.md`
**Planned tickets:** TICKET-034, TICKET-035
**Last updated:** 2026-08-22
**Path history:** `features/open/FEAT-015-selecting-tested-delivery-routes.md`
-> `features/closed/FEAT-015-selecting-tested-delivery-routes.md`

## Outcome

The editor selects the fastest valid delivery route for each mixed-source edit
while keeping the fixed 1920x1080 canvas, established render profile, output
verification, and source-safe publication guarantees.

## Scope

- Benchmark and document practical preview, intermediate, and final
  codec/container profiles on the target workstation.
- Define when source-level audio changes, mixed inputs, incompatible streams,
  or fixed-canvas composition require decoding and re-encoding.
- Route eligible edits through the fast path and all other edits through a
  validated fallback.
- Preserve temporary partial files, progress reporting, post-write
  verification, cleanup, and atomic publication.

## Explicit non-goals

- Choosing a different delivery profile solely because an input codec differs.
- Universal hardware or codec guarantees outside the supported workstation.
- Triplicate composition, visual transforms, or 60 FPS enhancement.
- Publishing output before verification or overwriting source media.

## Observable requirements

- Given candidate delivery paths on the target workstation, the project
  should record measured speed, quality, compatibility, and fallback evidence.
- Given an edit with source-level audio changes, the exporter should report why
  stream copy is unavailable and select a verified render route.
- Given mixed sources or incompatible streams, the exporter should retain the
  fixed 1920x1080 output authority and established render profile.
- Given an encode, validation, or publication failure, source media and the
  last valid output should remain intact.

## Validation intent

- Benchmark representative source codecs, dimensions, frame rates, channels,
  and audio levels using disposable local media.
- Compare fast and fallback route decisions and verify output metadata,
  duration, streams, playability, and source preservation.
- Record workstation-specific limitations without presenting them as universal
  product guarantees.

## Protected behavior

Existing eligible one-source stream-copy behavior, fixed-canvas scaling,
progress fields, output verification, partial cleanup, atomic publication,
project persistence, and CLI JSON contracts remain unchanged unless the
approved source-level audio policy requires a documented fallback.

## Definition of done

- Delivery profiles and routing boundaries are documented with measured
  evidence.
- Audio-aware and mixed-source exports choose safe, explainable routes.
- Output verification and source safety remain enforced.
- Automated, real-media, GUI/CLI, and user-validation evidence covers the
  feature outcome.

## Closure

TICKET-034 and TICKET-035 satisfy the tested delivery-route outcome. The
reviewed local delivery checkpoint is
`6aebb26121eb7e4088b4c3678b670038116be2be`; remote checks remain unavailable.
