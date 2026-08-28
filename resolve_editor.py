"""Compatibility entrypoint for the legacy ``resolve_editor.py`` command."""

from __future__ import annotations

from framestudio.entrypoint import build_parser, main

__all__ = ["build_parser", "main"]


if __name__ == "__main__":
    raise SystemExit(main())
