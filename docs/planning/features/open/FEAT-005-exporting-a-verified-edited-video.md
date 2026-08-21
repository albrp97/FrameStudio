# FEAT-005 - Exporting a Verified Edited Video

**Feature ID:** FEAT-005  
**Parent links:** OBJ-001, SCOPE-001, PHASE-002  
**Capability links:** CAP-005, CAP-012  
**Status:** confirmed  
**Horizon:** first  
**Owner:** repository planning; maintainer identity is not recorded  
**Approval:** user-approved on 2026-08-21 as part of PHASE-002 planning  
**Source paths:** `vision.md`, `docs/specs/project-scope.md`,
`docs/specs/capability-map.md`, `docs/planning/features.md`,
`docs/planning/phases/open/PHASE-002-cutting-and-exporting-one-source-safely.md`,
`.github/aidd-config.yml`  
**Migration source:** `docs/planning/features.md`, inline section
`FEAT-005 - Exporting a Verified Edited Video`; migrated on 2026-08-21 with
the feature content preserved.  
**Affected surfaces:** export planner, FFmpeg execution, output validation,
temporary files, atomic publication, project output state, and error handling  

## Outcome

Given a valid one-source edit, the exporter selects the fastest
valid route, reports fallback reasons, verifies the output, and never
replaces the source or last valid output after failure.

### Included

- Define stream-copy/smart-render eligibility for the approved cut semantics.
- Execute a fast path when the edit and source permit it.
- Use an explicit fallback encode when stream copy cannot satisfy the edit.
- Write through temporary/partial output and atomically publish only after
  verification.
- Verify playability, duration, stream presence, and relevant metadata.
- Surface unsupported codecs, timestamp ambiguity, command failures, and
  fallback decisions.

### Explicit non-goals

- Multiple source composition, scaling, triplicate layouts, audio
  normalization, or FPS enhancement.
- Publishing an output before validation succeeds.
- Destructive source replacement or deletion.

### Dependencies and risks

- Depends on FEAT-004 segment state and approved cut boundary semantics.
- Requires an evidence-backed FFmpeg/container/codec policy for the target
  workstation.
- Stream-copy output may be keyframe-bound; fallback encoding increases cost
  and can change timing or metadata.

### Acceptance outcomes

- Given an eligible edit, export uses or reports the configured fast path.
- Given an ineligible edit, export reports why and uses the validated
  fallback.
- Given a completed export, the output is playable and matches expected
  duration and stream requirements.
- Given an export failure, the source and last valid output remain intact.

### Evidence plan

- Unit tests for export-plan eligibility, fallback selection, and failure
  state.
- FFmpeg integration tests with generated fixtures and output probing.
- Manual target-workstation cut/export/source-preservation flow with output
  metadata and elapsed-time evidence.
