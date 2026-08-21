# PHASE-005 - Balancing Sources and Delivering Consistent Media

**Phase ID:** PHASE-005  
**Parent links:** OBJ-001, SCOPE-001  
**Capability links:** CAP-005, CAP-008, CAP-012  
**Sequence:** 5  
**Status:** confirmed  
**Horizon:** future  
**Owner:** repository planning; maintainer identity is not recorded  
**Approval:** user-approved on 2026-08-21 before feature generation  
**Source paths:** `vision.md`, `docs/specs/project-scope.md`,
`docs/specs/capability-map.md`, `docs/planning/phases.md`,
`docs/planning/repo-map.md`, `.github/aidd-config.yml`  
**Migration source:** `docs/planning/phases.md`, inline section
`PHASE-005 - Balancing Sources and Delivering Consistent Media`; migrated on
2026-08-21 with the phase content preserved.  
**Affected surfaces:** source-level audio analysis, gain/normalization,
preview and output profiles, smart-render planning, fallback encoding,
project state, GUI, and CLI  

## Outcome

The editor produces consistent mixed-source audio and delivery
media using tested policies that are applied per input source rather than
silently recalculated per segment.

### Included

- Analyze each input video's audio independently.
- Apply a source-level automatic gain/normalization decision across that
  source's timeline segments.
- Protect peaks, preserve useful dynamics, and expose the applied decision.
- Define channel, sample-rate, silence, unsupported-audio, and failed-analysis
  behavior.
- Establish evidence-based preview, intermediate, and final codec/container
  profiles for the target workstation.
- Expand smart-render and fallback planning for audio changes, composition,
  mixed inputs, and incompatible streams.
- Keep output verification and source-safe temporary handling.

### Explicit non-goals

- Replacing the user's source audio with a different recording.
- Per-segment automatic gain changes as the default behavior.
- A universal codec policy for hardware outside the supported workstation.
- 60 FPS enhancement.

### Entry conditions

- PHASE-004 has a stable mixed-source model and representative test media.
- Audio target, peak, channel, and measurement policy is approved.
- Listening and measurement evidence can be gathered without committing
  private media.
- Candidate codecs and containers can be benchmarked on the target machine.

### Exit conditions

- Each source receives an explicit audio decision that remains stable across
  its segments unless manually overridden.
- Output avoids clipping under the approved policy and preserves expected
  channels/duration.
- Codec/container profiles are documented with measured speed, quality,
  compatibility, and fallback evidence.
- Mixed-media exports are verified and source-safe.
- GUI, CLI, and project-file state expose the same source-level audio and
  delivery decisions.

### Dependencies and risks

- Depends on mixed-source timing and output-canvas behavior.
- Loudness statistics may not predict perceived balance for every recording.
- Hardware encoders and codec support can vary with local driver/runtime
  versions.

### Validation and evidence

- Audio analysis and gain-policy unit tests.
- Generated fixtures for clipping, silence, channel layouts, and mixed levels.
- Measured output metadata and peak/loudness evidence.
- Manual listening and playback evidence on representative local media.
- Render benchmark evidence for the target workstation.
