# TICKET-092 - Avoid Wayland Vulkan Swapchain Warnings During Editor Rendering

**Ticket ID:** TICKET-092
**Title:** Avoid the non-fatal Wayland Vulkan swapchain warning during editor rendering
**Status:** complete
**Parent feature:** FEAT-029
**Parent phase:** PHASE-008
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Capability links:** CAP-005, CAP-012
**Owner:** repository implementation in the active worktree
**Approval:** Explicitly authorized by the user's request to fix the rendering
warning shown during an active export
**Last updated:** 2026-09-07
**Affected surfaces:** `framestudio/app.py`, GTK renderer initialization,
graphics environment handling, and editor regression tests
**Risks:** changing the default GTK renderer could affect preview rendering
performance or override a user-selected renderer
**Evidence path:** `evidence/ticket-092-avoid-wayland-vulkan-swapchain-warning.md`

## Observable requirements

- Given a Wayland session with no explicit `GSK_RENDERER`, the editor should
  select the supported GTK `gl` renderer before GTK initialization so the
  known Vulkan `VK_SUBOPTIMAL_KHR` swapchain warning is not emitted during
  normal editor rendering.
- Given an explicit `GSK_RENDERER`, the editor should preserve that value and
  not override the user's renderer choice.
- Given a non-Wayland session with no explicit renderer, the editor should not
  inject a renderer setting.
- Given any renderer selection, the export media pipeline and its source-safe
  verification behavior should remain unchanged.

## Scope

- Add a small, testable graphics-environment configuration helper.
- Apply the guarded Wayland default before importing GTK in the editor process.
- Add regression coverage for Wayland, explicit-renderer, and non-Wayland cases.

## Non-goals

- Changing FFmpeg, RVE, interpolation, upscale, or export progress behavior.
- Disabling Vulkan globally or changing another process's environment.
- Overriding an explicit `GSK_RENDERER` value.

## Validation

- Focused graphics-environment regression tests.
- Existing repository test, compile, contract, smoke, and quality checks.
- Target-workstation editor smoke/render launch with the warning absent and
  explicit renderer override preserved.

## Definition of done

- The warning-producing default is avoided on Wayland without hiding unrelated
  GTK or media errors.
- Explicit renderer choices remain supported.
- Existing export and editor behavior remains covered by the repository gates.

## Implementation

`framestudio/graphics.py` now applies the supported `gl` renderer only when
the editor is running under Wayland and no `GSK_RENDERER` value was selected.
`framestudio/app.py` calls the helper before importing GTK, while explicit
renderer values and non-Wayland environments remain unchanged.

**Path history:** Created in `docs/planning/tickets/open/` on 2026-09-04.
Moved to `docs/planning/tickets/closed/` on 2026-09-07 after user
validation.
