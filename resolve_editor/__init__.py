"""Compatibility namespace forwarding legacy imports to :mod:`framestudio`."""

from __future__ import annotations

import importlib
import sys

import framestudio as _canonical

_MODULE_NAMES = (
    "app",
    "app_export",
    "app_helpers",
    "app_playback",
    "app_project",
    "app_timeline_actions",
    "app_ui",
    "audio",
    "cli",
    "cli_export",
    "cli_parser",
    "cli_payload",
    "cli_types",
    "composition",
    "composition_render",
    "entrypoint",
    "export",
    "export_delivery",
    "export_estimates",
    "export_ffmpeg",
    "export_interpolation",
    "export_naming",
    "export_panel",
    "export_planning",
    "export_process",
    "export_smart_render",
    "export_types",
    "ffmpeg_playback",
    "fps_policy",
    "interpolation",
    "interpolation_artifacts",
    "media",
    "model",
    "model_project",
    "model_timeline",
    "model_timeline_validation",
    "model_types",
    "operations",
    "performance",
    "persistence",
    "playback",
    "preview_strategy",
    "timeline",
    "timeline_geometry",
    "timeline_rendering",
    "ui",
    "upscale_policy",
)

for _module_name in _MODULE_NAMES:
    _module = importlib.import_module(f"framestudio.{_module_name}")
    globals()[_module_name] = _module
    sys.modules[f"{__name__}.{_module_name}"] = _module

for _name in _canonical.__all__:
    globals()[_name] = getattr(_canonical, _name)

__all__ = [*_canonical.__all__, *_MODULE_NAMES]
