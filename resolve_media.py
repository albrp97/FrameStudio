#!/usr/bin/env python3
"""Compatibility entrypoint for the legacy ``resolve_media.py`` command."""

from __future__ import annotations

import importlib
import sys

_canonical = importlib.import_module("framestudio_media")

if __name__ == "__main__":
    raise SystemExit(_canonical.main())

sys.modules[__name__] = _canonical
