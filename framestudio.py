#!/usr/bin/env python3
"""Launch FrameStudio, the focused local video editor."""

from __future__ import annotations

from framestudio.entrypoint import build_parser, main

__all__ = ["build_parser", "main"]


if __name__ == "__main__":
    raise SystemExit(main())
