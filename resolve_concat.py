"""Compatibility entrypoint for the legacy ``resolve_concat.py`` command."""

from __future__ import annotations

import importlib
import sys

_canonical = importlib.import_module("framestudio_concat")

if __name__ == "__main__":
    raise SystemExit(_canonical.main())

sys.modules[__name__] = _canonical
