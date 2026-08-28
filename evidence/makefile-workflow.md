# Evidence - Makefile Workflow Maintenance

**Ticket:** repository workflow maintenance
**Scope:** Add repeatable Makefile shortcuts for existing scripts and the
one-source editor without changing product behavior.
**Method:** configuration verification and real command execution
**Evidence path:** `evidence/makefile-workflow.md`

## Requirements

- Provide discoverable commands for tests, compilation, and the editor.
- Preserve access to the existing media, concat, and FPS scripts.
- Provide a generated-media editor smoke flow that cleans up its temporary
  artifacts.
- Document the manual launch and test procedure.

## E-701 - Makefile command verification

- **Category:** functionality
- **Commands:** `make help`, `make check`, and `make smoke`.
- **Expected:** Targets execute the repository's existing Python test and
  compile commands, expose the editor workflow, and complete generated-media
  source/project smoke flows.
- **Observed:** The targets completed successfully; the smoke flow created and
  reopened a versioned project and removed its temporary fixture/project.
- **Status:** passed
- **Artifacts:** `Makefile`, `README.md`, and `AGENTS.md`.
- **Failure:** none
- **Fix:** none

## E-702 - Existing script target verification

- **Category:** regression
- **Commands:** Inspect the `media`, `concat`, `fps`, and `install` recipes
  and invoke them with the existing `ARGS` pass-through convention as needed.
- **Expected:** Existing script entry points remain directly callable without
  changing their arguments or behavior.
- **Observed:** Each target delegates to the corresponding existing script;
  no script implementation or argument contract was changed.
- **Status:** passedWithConcerns
- **Artifacts:** `Makefile`, `framestudio_media.py`, `framestudio_concat.py`,
  `framestudio_fps.py`, and `install.sh`.
- **Failure:** no full media-processing run was performed because it would
  require user media and can alter workflow outputs.
- **Fix:** none
- **Accepted warning:** Real media-processing behavior remains covered by the
  existing test suite and should be exercised with user-selected inputs.

## E-703 - Manual UI test instructions

- **Category:** documentation
- **Expected:** A user can launch the editor and exercise open, playback,
  seek, save, reopen, source preservation, and an invalid-project error path.
- **Observed:** The complete procedure is documented in the README with safe
  disposable paths and the current foundation limitations.
- **Status:** passed
- **Artifacts:** `README.md`
- **Failure:** none
- **Fix:** none

## E-704 - Final Makefile execution

- **Category:** gate
- **Commands:** `make help`, `make -n editor ARGS='--source
  /tmp/example.mp4'`, `make media ARGS='--help'`, `make concat
  ARGS='--help'`, `make fps ARGS='--help'`, `make check`, and `make smoke`.
- **Expected:** The new targets are discoverable, forward arguments, preserve
  legacy script entry points, and complete the configured local checks and
  generated-media editor flow.
- **Observed:** Help and dry-run output were correct; all legacy help targets,
  `make check`, and `make smoke` exited successfully.
- **Status:** passed
- **Artifacts:** `Makefile`, `README.md`, and this evidence record.
- **Failure:** none
- **Fix:** none

## Readiness

- **Passed:** E-701, E-703, and E-704.
- **Passed with concerns:** E-702.
- **Failed:** none.
- **Blocked:** none for Makefile automation.
- **Skipped:** destructive or user-media-dependent processing runs.
- **Coverage gap:** target-workstation visual/manual UI results still belong
  to TICKET-004 and TICKET-006.
