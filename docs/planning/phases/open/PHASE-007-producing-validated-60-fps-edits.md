# PHASE-007 - Producing Validated 60 FPS Edits

**Phase ID:** PHASE-007  
**Parent links:** OBJ-001, SCOPE-001  
**Capability links:** CAP-005, CAP-011, CAP-012  
**Sequence:** 7  
**Status:** confirmed  
**Horizon:** future  
**Owner:** repository planning; maintainer identity is not recorded  
**Approval:** user-approved on 2026-08-21 before feature generation  
**Source paths:** `vision.md`, `docs/specs/project-scope.md`,
`docs/specs/capability-map.md`, `docs/planning/phases.md`,
`docs/planning/repo-map.md`, `.github/aidd-config.yml`  
**Migration source:** `docs/planning/phases.md`, inline section
`PHASE-007 - Producing Validated 60 FPS Edits`; migrated on 2026-08-21 with
the phase content preserved.  
**Affected surfaces:** FPS policy, interpolation backend, timing/audio
preservation, artifact checks, project settings, CLI, renderer, and
target-workstation benchmarks  

## Outcome

The user can optionally enhance an edit to 60 FPS through a
validated motion-interpolation path while preserving timing, audio, scene
cuts, and output integrity.

### Included

- Enable an explicit 60 FPS output option.
- Select a tested motion-interpolation backend, model, precision, and local
  GPU/CPU fallback.
- Preserve exact target timing, audio synchronization, scene-cut behavior,
  and expected frame count.
- Define whether enhancement applies to the whole project, an input, or
  selected segments.
- Detect or gate known visual artifacts before accepting output.
- Expose the selected FPS policy and evidence through the project and CLI.
- Keep the existing RIFE/RVE research and local hardware findings as
  evidence, not universal guarantees.

### Explicit non-goals

- Treating frame duplication or simple blending as equivalent to motion
  interpolation.
- Unvalidated pure TensorRT paths known to produce artifacts on the target
  setup.
- Diffusion-based interpolation as the default workflow.
- Supporting hardware or operating systems outside the project constraint.

### Entry conditions

- PHASE-004 defines the timing model for mixed sources.
- PHASE-005 defines audio and delivery output behavior.
- If enhancement is segment-selectable, PHASE-006 defines segment/link
  semantics sufficiently for timing boundaries.
- A representative benchmark set and artifact-check procedure are available.
- The selected backend passes a raw-frame and encoded-output correctness
  smoke test on the target workstation.

### Exit conditions

- A source/edit can be enhanced to 60 FPS with exact approved frame count and
  timing.
- Audio remains synchronized and scene cuts are handled according to policy.
- Known artifact checks pass, or the output is explicitly blocked/falls back.
- GPU/CPU behavior, model/precision, speed, and quality evidence is
  documented for the target workstation.
- Project and CLI settings reproduce the same enhancement decision.
- Existing non-enhanced exports and scripts remain unaffected.

### Dependencies and risks

- Depends on timing, audio, output, and optional segment semantics.
- Interpolation may hallucinate motion or fail at occlusions and hard cuts.
- GPU/runtime upgrades can invalidate cached engines or introduce artifacts.
- Enhancement can be substantially slower than stream-copy or normal export.

### Validation and evidence

- Rational frame-count and timing unit tests.
- Backend raw-frame artifact smoke tests.
- Encoded output frame-count, metadata, audio-sync, and playability tests.
- Representative target-workstation visual comparison and benchmark
  evidence.
- Explicit records for unavailable backends or blocked artifact gates.
