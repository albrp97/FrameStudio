# TICKET-088 - Add Numbered Staged Console Export Progress

**Ticket ID:** TICKET-088
**Title:** Add numbered staged console export progress
**Status:** complete
**Parent feature:** FEAT-029
**Parent phase:** PHASE-008
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Capability links:** CAP-005, CAP-012
**Owner:** repository implementation in the active worktree
**Approval:** Explicitly authorized by the 2026-08-28 user request; no
additional ticket approval is required before implementation
**Last updated:** 2026-09-07
**Dependencies:** existing `ExportProgress` events; CLI JSON Lines contract;
  GTK export worker; TICKET-087 enhanced-export stages
**Affected surfaces:** `framestudio/export_console.py`,
`framestudio/cli_export.py`, `framestudio/cli.py`,
`framestudio/cli_parser.py`, `framestudio/app_export.py`,
`docs/specs/cli-contract.md`, README, console-progress tests
**Risks:** human output could corrupt stdout automation, duplicate lines for
  frame-level events, or omit meaningful concatenation and verification work
**Evidence path:** `evidence/ticket-088-staged-export-progress.md`

## Scope

- Map export events to stable numbered stages: preparation,
  rendering/enhancement, concatenation/composition, verification, and
  publication.
- Emit concise human-readable progress with elapsed time and useful progress
  detail to stderr for interactive terminal use.
- Provide an explicit force option for redirected stderr without changing the
  default non-TTY machine behavior.
- Use the same stage vocabulary for GTK exports launched from a terminal.
- Preserve valid JSON Lines events and existing stdout/error contracts for CLI
  automation.

## Non-goals

- Replacing structured progress events, adding a second machine-readable
  protocol, or changing export stage semantics.
- Printing sensitive full paths, media metadata, credentials, or per-frame
  noise.

## Acceptance criteria

- Given an interactive export, stderr shows numbered stage progress including
  concatenation/composition, verification, and publication.
- Given redirected stderr without the force option, stdout remains unchanged
  and no human progress contaminates machine-readable output.
- Given `--human-progress`, human progress is emitted even when stderr is not
  a TTY while JSON Lines remains valid on stdout.
- Given frame-level or dynamic raw stage names, output is throttled and mapped
  to the stable stage rather than producing one line per frame.
- Given a GTK export launched from a terminal, the same numbered stages are
  visible without changing GUI export behavior.

## Verification

- Add reporter, TTY/non-TTY, force-option, stage-mapping, throttling, and CLI
  contract regressions.
- Exercise a CLI and GTK export and record the visible stage sequence alongside
  parsed JSON Lines output.
- Run existing CLI, export, compile, smoke, and configured quality checks.

## Protected behavior

The existing JSON Lines contract, structured errors, export result semantics,
GUI progress behavior, source preservation, and atomic publication remain
unchanged.

## Path history

Created in `docs/planning/tickets/open/` on 2026-08-28.
Moved to `docs/planning/tickets/closed/` on 2026-09-07 after user
validation.
