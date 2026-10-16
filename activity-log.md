# Activity Log

## 2026-10-16

- :rocket: - Resumable export recovery - Per-track audio checkpoints and cached source hashes ([evidence](evidence/ticket-124-flexible-export-recovery.md))
- :bug: - Large multitrack export memory - Bounded interval composition avoids out-of-memory kills ([evidence](evidence/ticket-124-flexible-export-recovery.md))
- :bug: - UI export resume - Sessions created by the CLI resume from the editor ([evidence](evidence/ticket-124-flexible-export-recovery.md))
- :bug: - FFmpeg 6.1 audio mix - Shared audio input reuse is enabled only on FFmpeg 9 or newer; older builds use the legacy graph ([evidence](evidence/ticket-124-flexible-export-recovery.md))
- :bug: - Export progress replay - Heartbeat no longer re-sends checkpoint milestones, so resumed interpolation counts stay exact ([evidence](evidence/ticket-124-flexible-export-recovery.md))
- :wrench: - X11 pointer tests - Real-pointer snapping uses non-blocking `xdotool mousemove` instead of `--sync`, which hung under Xvfb ([evidence](evidence/ticket-124-flexible-export-recovery.md))

## 2026-10-09

- :rocket: - Synchronized editing and exports - Four tracks, ripple Undo and source reels ([evidence](evidence/ticket-125-phase010-functionality.md))

## 2026-08-21

- :rocket: - Deterministic editor CLI - Inspect, edit, export, and round-trip one-source projects ([evidence/phase-003-gui-cli-parity.md](evidence/phase-003-gui-cli-parity.md))
- :rocket: - Repository quality gates - Reproducible local and CI validation ([evidence/static-analysis-setup.md](evidence/static-analysis-setup.md))
- :rocket: - One-source cut editing - Split/delete/restore with persisted state ([evidence/split-delete-duration.md](evidence/split-delete-duration.md), [evidence/persist-cut-state-recovery.md](evidence/persist-cut-state-recovery.md))
- :rocket: - One-source editor foundation - Open and preserve source projects ([evidence](evidence/open-supported-source-project.md))
