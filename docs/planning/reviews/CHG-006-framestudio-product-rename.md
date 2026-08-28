# CHG-006 - Adopt FrameStudio as the Canonical Product Identity

**Change ID:** CHG-006
**Type:** Material planning change
**Status:** approved-and-applied
**Date:** 2026-08-27
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Owner:** repository planning and implementation in the active worktree
**Approval:** User-authorized by the request to rename the project to
FrameStudio.
**Source paths:** `vision.md`, `AGENTS.md`, `README.md`,
`docs/planning/repo-map.md`, `docs/specs/project-scope.md`,
`docs/specs/cli-contract.md`, `resolve_editor/`, `resolve_editor.py`,
`resolve_media.py`, `resolve_concat.py`, `resolve_fps.py`, `install.sh`,
`Makefile`, `package.json`
**Affected IDs:** CAP-001, CAP-002, CAP-003, CAP-004, CAP-005, CAP-006,
CAP-007, CAP-008, CAP-009, CAP-010, CAP-011, CAP-012, PHASE-001,
PHASE-004A, PHASE-005, PHASE-006, PHASE-007, PHASE-008
**Evidence:** `evidence/framestudio-product-rename.md`
**Last updated:** 2026-08-28

## Request and classification

The product name `Resolve` is too closely associated with DaVinci Resolve.
The user selected **FrameStudio** as the project identity and requested a
repository-wide rename while preserving the existing scripts and workflows.

This is a material change because it affects filesystem/module names, command
names, package metadata, application identity, project-file conventions,
documentation, and operational cache identifiers. It does not change editing
semantics, media safety, export behavior, planning IDs, or the approved
product scope.

## Decision

1. Make `FrameStudio` the canonical product name, Python namespace, CLI
   identity, project-file suffix, application ID, and cache/temp naming.
2. Rename the implementation package and primary Python surfaces to
   `framestudio/`, `framestudio.py`, `framestudio_media.py`,
   `framestudio_concat.py`, and `framestudio_fps.py`.
3. Provide canonical commands `framestudio`, `framestudio-editor`,
   `framestudio-media`, `framestudio-concat`, and `framestudio-fps`.
4. Retain `resolve_editor`, `resolve_editor.py`, `resolve_media.py`,
   `resolve_concat.py`, and `resolve_fps.py` as compatibility facades that
   forward to the canonical implementation. Retain legacy command aliases and
   loadable `.resolve.json` projects.
5. Use `.framestudio.json` for newly created projects and recognize the
   legacy `.resolve.json` suffix when reopening existing projects.
6. Preserve stable planning IDs, lifecycle paths, historical evidence meaning,
   source-media safety, export verification, and existing non-product uses of
   the English word “resolve.”

## Affected-artifact inventory

| Artifact | Impact | Action |
|---|---|---|
| Python implementation package and scripts | Canonical import and execution paths change | Move to FrameStudio names and add legacy facades |
| CLI and installer commands | New canonical command names are required | Install FrameStudio commands plus legacy aliases |
| GTK application identity and process names | Product-facing runtime identity changes | Use FrameStudio identifiers |
| Project persistence and generated media names | New files should identify FrameStudio | Write new suffixes; read legacy suffixes |
| Cache, temp, and environment identifiers | Avoid new product references to Resolve | Use FrameStudio names with legacy fallback where needed |
| Tests and quality tooling | Patch/import seams must follow canonical paths | Update tests and dependency checks; cover compatibility |
| README, AGENTS, specifications, indexes, and evidence | Current documentation must be discoverable under the new name | Update active references and retain explicit migration history |
| Planning IDs and lifecycle records | Historical traceability must not change | Preserve IDs, statuses, and path history |

## Protected behavior and validation

- Existing legacy scripts, aliases, imports, and `.resolve.json` projects remain
  usable through compatibility forwarding.
- The canonical CLI and GUI continue to provide the current editor behavior.
- Source media is never overwritten, deleted, or moved by the rename.
- Existing tests, `make check`, `make contract`, and `make smoke` remain the
  primary regression gates.
- Final repository search must distinguish intentional compatibility/history
  references from stale product identifiers.

## Closure and remaining gates

The user approval authorizes this bounded rename. Implementation still requires
the configured baseline, compatibility tests, local quality checks, smoke and
contract validation, static-analysis review, user validation, and the scoped
rename commit before delivery closure. No remote check is claimed because the
repository has no configured remote.
