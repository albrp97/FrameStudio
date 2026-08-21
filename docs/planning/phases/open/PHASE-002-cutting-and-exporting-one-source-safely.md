# PHASE-002 - Cutting and Exporting One Source Safely

**Phase ID:** PHASE-002  
**Parent links:** OBJ-001, SCOPE-001  
**Capability links:** CAP-003, CAP-005, CAP-012  
**Sequence:** 2  
**Status:** confirmed  
**Horizon:** first  
**Owner:** repository planning; maintainer identity is not recorded  
**Approval:** user-approved on 2026-08-21 before feature generation  
**Source paths:** `vision.md`, `docs/specs/project-scope.md`,
`docs/specs/capability-map.md`, `docs/planning/phases.md`,
`docs/planning/repo-map.md`, `.github/aidd-config.yml`  
**Migration source:** `docs/planning/phases.md`, inline section
`PHASE-002 - Cutting and Exporting One Source Safely`; migrated on
2026-08-21 with the phase content preserved.  
**Affected surfaces:** segment model, GTK editing controls, project
persistence, export planning, FFmpeg execution, output validation, and
failure recovery  

## Outcome

The user can remove unwanted portions of one source video and
export a verified final result through the fastest valid path without changing
the source.

### Included

- Split the source at the playhead or selected timeline position.
- Represent editable segments and deletion state non-destructively.
- Delete segments and update final duration immediately.
- Show the expected final output length.
- Define exact cut semantics and document frame-accurate versus keyframe-bound
  behavior.
- Plan and execute stream-copy/smart-render when valid.
- Use an explicit validated fallback encode when the requested cut cannot use
  stream copy.
- Write temporary/partial output, verify it, and expose the final file only
  after success.
- Surface unsupported formats, timestamp ambiguity, failed commands, and
  fallback reasons.

### Explicit non-goals

- Multiple source clips, multiple tracks, mixed dimensions/frame rates, or
  triplicate composition.
- Copy/paste segments or reusable visual modifications beyond the minimum
  state model needed for future compatibility.
- Automatic per-input audio normalization and FPS enhancement.
- Destructive source deletion or overwrite.

### Entry conditions

- PHASE-001 exit evidence is complete and its project/timeline model is
  available.
- Cut boundary semantics and final-duration rules are approved.
- The export planner has a defined eligibility policy for stream copy and a
  defined fallback policy.
- Output validation checks playability, expected duration, stream presence,
  and source preservation.
- Small generated or fixture media is available for automated export tests.

### Exit conditions

- The interface can split and delete segments and keeps the final duration
  correct after repeated operations and save/reopen.
- An eligible edit uses the fast path, and an ineligible edit reports and
  uses the validated fallback.
- The resulting output is playable, has the expected duration and streams,
  and is not published before verification.
- Failed exports leave the source, project, and last valid output intact.
- Automated timeline/export tests and a real-media manual cut/export test are
  recorded.
- Existing script behavior and tests remain intact.

### Dependencies and risks

- Depends on project persistence and timeline timebase decisions from
  PHASE-001.
- Stream copy may require keyframe-bound cuts or a partial re-encode.
- Variable-frame-rate inputs and timestamp discontinuities may change exact
  duration behavior.
- A fast command can still create invalid timing, so output verification is a
  hard exit gate.

### Validation and evidence

- Unit tests for split/delete invariants, duration, undo-safe state, and
  export-plan selection.
- FFmpeg integration tests with generated fixtures where practical.
- Manual target-workstation test covering playback, split, delete, save,
  reopen, export, and source preservation.
- Output metadata, duration, playability, path, and elapsed-time evidence.
