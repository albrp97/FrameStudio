from __future__ import annotations

import os
from collections.abc import MutableMapping

DEFAULT_GTK_RENDERER = "gl"


def configure_graphics_environment(
    environment: MutableMapping[str, str] | None = None,
) -> str | None:
    values = os.environ if environment is None else environment
    if "GSK_RENDERER" in values:
        return values["GSK_RENDERER"]
    if values.get("WAYLAND_DISPLAY"):
        values["GSK_RENDERER"] = DEFAULT_GTK_RENDERER
        return DEFAULT_GTK_RENDERER
    return None


__all__ = ["DEFAULT_GTK_RENDERER", "configure_graphics_environment"]
