from __future__ import annotations

import math
import uuid
from dataclasses import dataclass
from typing import Any, Mapping

COMPOSITION_SCHEMA_VERSION = 1
CANVAS_WIDTH = 1920
CANVAS_HEIGHT = 1080
TRIPLICATE_SLOT_WIDTH = CANVAS_WIDTH // 3
MIN_ZOOM = 1.0
MAX_ZOOM = 8.0
MAX_OFFSET_X = CANVAS_WIDTH / 2.0
MAX_OFFSET_Y = CANVAS_HEIGHT / 2.0
TRIPLICATE_LAYOUT = "three-column"
TRIPLICATE_BACKGROUND = "black"
TRIPLICATE_ROLES = ("center", "left", "right")


def _finite_number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a finite number")
    parsed = float(value)
    if not math.isfinite(parsed):
        raise ValueError(f"{label} must be a finite number")
    return parsed


def _bounded(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


@dataclass(frozen=True)
class VisualTransform:
    """Validated focus values in fixed project-canvas pixel coordinates."""

    zoom: float = MIN_ZOOM
    offset_x: float = 0.0
    offset_y: float = 0.0
    version: int = COMPOSITION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.version != COMPOSITION_SCHEMA_VERSION:
            raise ValueError(f"Unsupported visual transform version: {self.version!r}")
        zoom = _finite_number(self.zoom, "Visual transform zoom")
        offset_x = _finite_number(self.offset_x, "Visual transform X offset")
        offset_y = _finite_number(self.offset_y, "Visual transform Y offset")
        if not MIN_ZOOM <= zoom <= MAX_ZOOM:
            raise ValueError(f"Visual transform zoom must be between {MIN_ZOOM:g} and {MAX_ZOOM:g}")
        if not -MAX_OFFSET_X <= offset_x <= MAX_OFFSET_X:
            raise ValueError(
                f"Visual transform X offset must be between {-MAX_OFFSET_X:g} and {MAX_OFFSET_X:g}"
            )
        if not -MAX_OFFSET_Y <= offset_y <= MAX_OFFSET_Y:
            raise ValueError(
                f"Visual transform Y offset must be between {-MAX_OFFSET_Y:g} and {MAX_OFFSET_Y:g}"
            )
        object.__setattr__(self, "zoom", zoom)
        object.__setattr__(self, "offset_x", offset_x)
        object.__setattr__(self, "offset_y", offset_y)

    @classmethod
    def clamped(
        cls,
        *,
        zoom: Any = MIN_ZOOM,
        offset_x: Any = 0.0,
        offset_y: Any = 0.0,
    ) -> VisualTransform:
        parsed_zoom = _finite_number(zoom, "Visual transform zoom")
        parsed_x = _finite_number(offset_x, "Visual transform X offset")
        parsed_y = _finite_number(offset_y, "Visual transform Y offset")
        return cls(
            zoom=_bounded(parsed_zoom, MIN_ZOOM, MAX_ZOOM),
            offset_x=_bounded(parsed_x, -MAX_OFFSET_X, MAX_OFFSET_X),
            offset_y=_bounded(parsed_y, -MAX_OFFSET_Y, MAX_OFFSET_Y),
        )

    @classmethod
    def from_dict(cls, value: Mapping[str, Any] | None) -> VisualTransform:
        if value is None:
            return cls()
        if not isinstance(value, Mapping):
            raise ValueError("Visual transform must be an object")
        version = value.get("version", COMPOSITION_SCHEMA_VERSION)
        if (
            isinstance(version, bool)
            or not isinstance(version, int)
            or version != COMPOSITION_SCHEMA_VERSION
        ):
            raise ValueError(f"Unsupported visual transform version: {version!r}")
        offset = value.get("offset")
        if offset is not None:
            if not isinstance(offset, Mapping):
                raise ValueError("Visual transform offset must be an object")
            offset_x = offset.get("x", value.get("offset_x", 0.0))
            offset_y = offset.get("y", value.get("offset_y", 0.0))
        else:
            offset_x = value.get("offset_x", 0.0)
            offset_y = value.get("offset_y", 0.0)
        return cls(
            zoom=value.get("zoom", MIN_ZOOM),
            offset_x=offset_x,
            offset_y=offset_y,
            version=version,
        )

    def with_values(
        self,
        *,
        zoom: Any | None = None,
        offset_x: Any | None = None,
        offset_y: Any | None = None,
    ) -> VisualTransform:
        return VisualTransform.clamped(
            zoom=self.zoom if zoom is None else zoom,
            offset_x=self.offset_x if offset_x is None else offset_x,
            offset_y=self.offset_y if offset_y is None else offset_y,
        )

    @property
    def is_default(self) -> bool:
        return self == VisualTransform()

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "zoom": self.zoom,
            "offset_x": self.offset_x,
            "offset_y": self.offset_y,
        }


@dataclass(frozen=True)
class TriplicateInstance:
    role: str

    def __post_init__(self) -> None:
        if self.role not in TRIPLICATE_ROLES:
            raise ValueError(f"Unsupported triplicate role: {self.role!r}")

    def to_dict(self) -> dict[str, str]:
        return {"role": self.role}

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> TriplicateInstance:
        if not isinstance(value, Mapping):
            raise ValueError("Triplicate instance must be an object")
        role = value.get("role")
        if not isinstance(role, str):
            raise ValueError("Triplicate instance role must be a string")
        return cls(role)


@dataclass(frozen=True)
class TriplicateGroup:
    """One segment-owned three-column composition with shared focus state."""

    group_id: str
    shared_transform: VisualTransform = VisualTransform()
    enabled: bool = True
    layout: str = TRIPLICATE_LAYOUT
    background: str = TRIPLICATE_BACKGROUND
    instances: tuple[TriplicateInstance, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.group_id, str) or not self.group_id:
            raise ValueError("Triplicate group_id must be a non-empty string")
        if not isinstance(self.enabled, bool):
            raise ValueError("Triplicate enabled must be a boolean")
        if self.layout != TRIPLICATE_LAYOUT:
            raise ValueError(f"Unsupported triplicate layout: {self.layout!r}")
        if self.background != TRIPLICATE_BACKGROUND:
            raise ValueError(f"Unsupported triplicate background: {self.background!r}")
        if not isinstance(self.shared_transform, VisualTransform):
            raise ValueError("Triplicate shared transform is invalid")
        instances = self.instances
        if not instances:
            instances = tuple(TriplicateInstance(role) for role in TRIPLICATE_ROLES)
        if not isinstance(instances, tuple):
            instances = tuple(instances)
        roles = tuple(instance.role for instance in instances)
        if (
            len(instances) != len(TRIPLICATE_ROLES)
            or set(roles) != set(TRIPLICATE_ROLES)
            or len(set(roles)) != len(roles)
        ):
            raise ValueError(
                "Triplicate group must contain exactly center, left, and right instances"
            )
        if any(not isinstance(instance, TriplicateInstance) for instance in instances):
            raise ValueError("Triplicate instances are invalid")
        object.__setattr__(self, "instances", instances)

    @classmethod
    def create(
        cls,
        transform: VisualTransform | None = None,
        *,
        group_id: str | None = None,
    ) -> TriplicateGroup:
        return cls(
            group_id=group_id or uuid.uuid4().hex,
            shared_transform=VisualTransform() if transform is None else transform,
        )

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> TriplicateGroup:
        if not isinstance(value, Mapping):
            raise ValueError("Triplicate group must be an object")
        group_id = value.get("group_id")
        if not isinstance(group_id, str) or not group_id:
            raise ValueError("Triplicate group_id must be a non-empty string")
        raw_instances = value.get("instances")
        instances: tuple[TriplicateInstance, ...]
        if raw_instances is None:
            instances = ()
        elif isinstance(raw_instances, list):
            instances = tuple(TriplicateInstance.from_dict(item) for item in raw_instances)
        else:
            raise ValueError("Triplicate instances must be an array")
        return cls(
            group_id=group_id,
            shared_transform=VisualTransform.from_dict(value.get("shared_transform")),
            enabled=value.get("enabled", True),
            layout=value.get("layout", TRIPLICATE_LAYOUT),
            background=value.get("background", TRIPLICATE_BACKGROUND),
            instances=instances,
        )

    def with_transform(self, transform: VisualTransform) -> TriplicateGroup:
        return TriplicateGroup(
            group_id=self.group_id,
            shared_transform=transform,
            enabled=self.enabled,
            layout=self.layout,
            background=self.background,
            instances=self.instances,
        )

    def with_enabled(self, enabled: bool) -> TriplicateGroup:
        return TriplicateGroup(
            group_id=self.group_id,
            shared_transform=self.shared_transform,
            enabled=enabled,
            layout=self.layout,
            background=self.background,
            instances=self.instances,
        )

    def clone(self, *, new_id: bool = True) -> TriplicateGroup:
        return TriplicateGroup(
            group_id=uuid.uuid4().hex if new_id else self.group_id,
            shared_transform=self.shared_transform,
            enabled=self.enabled,
            layout=self.layout,
            background=self.background,
            instances=self.instances,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "group_id": self.group_id,
            "enabled": self.enabled,
            "layout": self.layout,
            "background": self.background,
            "shared_transform": self.shared_transform.to_dict(),
            "instances": [instance.to_dict() for instance in self.instances],
        }


def coerce_legacy_transform(state: Mapping[str, Any]) -> VisualTransform:
    """Read the pre-contract generic state shape without changing that state."""
    raw_transform = state.get("visual_transform")
    if isinstance(raw_transform, Mapping):
        return VisualTransform.from_dict(raw_transform)
    raw_transform = state.get("transform")
    if isinstance(raw_transform, Mapping):
        return VisualTransform.from_dict(raw_transform)
    raw_offset = state.get("offset")
    if "zoom" not in state and not isinstance(raw_offset, Mapping):
        return VisualTransform()
    if raw_offset is None:
        raw_offset = {}
    if not isinstance(raw_offset, Mapping):
        raise ValueError("Legacy visual transform offset must be an object")
    return VisualTransform.clamped(
        zoom=state.get("zoom", MIN_ZOOM),
        offset_x=raw_offset.get("x", 0.0),
        offset_y=raw_offset.get("y", 0.0),
    )


def segment_has_visual_modifications(segment: Any) -> bool:
    transform = getattr(segment, "visual_transform", VisualTransform())
    group = getattr(segment, "triplicate", None)
    return transform != VisualTransform() or (group is not None and bool(group.enabled))


__all__ = [
    "CANVAS_HEIGHT",
    "CANVAS_WIDTH",
    "COMPOSITION_SCHEMA_VERSION",
    "MAX_OFFSET_X",
    "MAX_OFFSET_Y",
    "MAX_ZOOM",
    "MIN_ZOOM",
    "TRIPLICATE_BACKGROUND",
    "TRIPLICATE_LAYOUT",
    "TRIPLICATE_ROLES",
    "TRIPLICATE_SLOT_WIDTH",
    "TriplicateGroup",
    "TriplicateInstance",
    "VisualTransform",
    "coerce_legacy_transform",
    "segment_has_visual_modifications",
]
