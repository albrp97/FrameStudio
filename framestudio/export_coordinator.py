"""Durable coordination for independent export outputs.

The coordinator deliberately owns only batch state and publication.  Renderers
remain responsible for producing and validating a candidate file, while this
module makes each output independently resumable and keeps already-published
siblings intact after a failure or cancellation.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import shutil
import stat
import subprocess
import threading
import time
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol, TypeAlias, TypeVar
from urllib.parse import unquote, urlparse

from .audio import AUDIO_POLICY_VERSION
from .audio_compositor import AUDIO_CHANNELS, AUDIO_SAMPLE_RATE, fixed_pan_vector
from .export_process import (
    check_export_cancelled,
    make_progress_heartbeat,
    report_preparation_progress,
)
from .export_session import (
    ExportSession,
    ExportSessionError,
    ExportSessionMismatch,
    ExportSessionNotFound,
    session_root,
)
from .export_types import ExportProgressCallback
from .fps_policy import FPS_POLICY_VERSION, FrameRatePolicy, ResolvedFrameRatePolicy
from .layout_plan import DEFAULT_CANVAS, TRIPLICATE_ROLES
from .output_plan import OutputIdentity, OutputPlan, OutputRequest
from .upscale_policy import (
    UPSCALE_POLICY_VERSION,
    ResolvedUpscalePolicy,
    UpscalePolicy,
)
from .video_compositor import SourceHashCache
from .video_compositor import _sha256 as _video_file_sha256

if TYPE_CHECKING:
    from .model_project import Project

BATCH_SCHEMA_VERSION = 1
COMPOSITOR_VERSION = "t124-flexible-export-v1"
RECEIPT_SUFFIX = ".framestudio-batch-receipt.json"

JSONScalar: TypeAlias = None | bool | int | float | str
JSONValue: TypeAlias = JSONScalar | list["JSONValue"] | dict[str, "JSONValue"]
FrameRatePolicyInput: TypeAlias = (
    FrameRatePolicy | ResolvedFrameRatePolicy | Mapping[str, object] | None
)
UpscalePolicyInput: TypeAlias = UpscalePolicy | ResolvedUpscalePolicy | Mapping[str, object] | None
PlanT = TypeVar("PlanT")
PlanT_co = TypeVar("PlanT_co", covariant=True)


class SourcePlanWithExport(Protocol[PlanT_co]):
    @property
    def export_plan(self) -> PlanT_co: ...


def resolve_output_plan(
    key: str,
    source_by_key: Mapping[str, SourcePlanWithExport[PlanT_co]],
    final_by_key: Mapping[str, PlanT_co],
) -> PlanT_co | None:
    source_plan = source_by_key.get(key)
    if source_plan is not None:
        return source_plan.export_plan
    return final_by_key.get(key)


def child_resume_mode(destination: Path, requested_mode: str) -> str:
    if requested_mode == "resume" and not session_root(destination).exists():
        return "fresh"
    return requested_mode


LAYOUT_POLICY_VERSION = "layout-plan-v1"
AUDIO_COMPOSITION_VERSION = "fixed-stereo-v1"
PAN_LAW_VERSION = "equal-power-mono-linear-balance-stereo-v1"
CANVAS_POLICY_VERSION = "fixed-1920x1080-v1"
DEFAULT_POLICY_VERSIONS: dict[str, JSONValue] = {
    "fps": FPS_POLICY_VERSION,
    "upscale": UPSCALE_POLICY_VERSION,
    "layout": LAYOUT_POLICY_VERSION,
    "audio": AUDIO_COMPOSITION_VERSION,
    "pan_law": PAN_LAW_VERSION,
    "canvas": CANVAS_POLICY_VERSION,
}

_TOOL_IDENTITY_CACHE: dict[
    tuple[str, int, int, int, int, int],
    dict[str, JSONValue],
] = {}
_TOOL_IDENTITY_CACHE_LOCK = threading.Lock()


class ExportResultState(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    VERIFIED = "verified"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"


class ExportCancelled(RuntimeError):
    """Raised by a renderer or verifier when its cancellation event is set."""


def _json_value(value: object) -> JSONValue:
    if isinstance(value, Path):
        return str(value.expanduser().resolve())
    if isinstance(value, Enum):
        return _json_value(value.value)
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return _json_value(value.to_dict())
    if isinstance(value, Mapping):
        normalized: dict[str, JSONValue] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError(
                    f"Canonical JSON object keys must be strings, got {type(key).__name__}",
                )
            normalized[key] = _json_value(item)
        return {key: normalized[key] for key in sorted(normalized)}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    if isinstance(value, bool) or isinstance(value, int) or isinstance(value, str):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("Canonical JSON numbers must be finite")
        return value
    if value is None:
        return None
    raise TypeError(
        f"Unsupported canonical JSON value type: {type(value).__module__}."
        f"{type(value).__qualname__}",
    )


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        _json_value(value),
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def build_output_fingerprint(payload: object) -> str:
    """Return a stable SHA-256 fingerprint for one output's full request."""
    return hashlib.sha256(_canonical_json(payload)).hexdigest()


def _sanitized_track_label(track_id: str, index: int) -> str:
    label = re.sub(r"[^A-Za-z0-9._-]+", "-", track_id).strip("-._")
    return label or f"Track-{index + 1}"


def _source_record(
    path: Path,
    source_id: str,
    *,
    metadata: Mapping[str, object] | None = None,
    source_hash_cache: SourceHashCache | None = None,
    cancel_event: threading.Event | None = None,
    heartbeat_callback: Callable[[], None] | None = None,
) -> dict[str, JSONValue]:
    resolved = path.expanduser().resolve()
    value = resolved.stat()
    record: dict[str, JSONValue] = {
        "source_id": source_id,
        "path": str(resolved),
        "stat": {
            "size_bytes": value.st_size,
            "modified_time_ns": value.st_mtime_ns,
            "mode": stat.S_IMODE(value.st_mode),
        },
        "sha256": _video_file_sha256(
            resolved,
            source_hash_cache=source_hash_cache,
            cancel_event=cancel_event,
            heartbeat_callback=heartbeat_callback,
        ),
    }
    if metadata is not None:
        record["metadata"] = _json_value(metadata)
    return record


def _resolve_tool(path: str) -> Path | None:
    candidate = Path(path).expanduser()
    if candidate.is_file():
        return candidate.resolve()
    resolved = shutil.which(path)
    if resolved is None:
        return None
    resolved_path = Path(resolved)
    return resolved_path.resolve() if resolved_path.is_file() else None


def _tool_version(path: Path) -> dict[str, JSONValue]:
    try:
        completed = subprocess.run(
            [str(path), "--version"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as error:
        return {
            "text": None,
            "returncode": None,
            "error": type(error).__name__,
        }
    output = (completed.stdout or completed.stderr).strip()
    return {
        "text": output.splitlines()[0][:512] if output else None,
        "returncode": completed.returncode,
    }


def _tool_identity(path: str) -> dict[str, JSONValue]:
    requested = str(path)
    resolved = _resolve_tool(requested)
    if resolved is None:
        return {
            "requested": requested,
            "resolved": None,
            "available": False,
        }
    try:
        value = resolved.stat()
    except OSError as error:
        return {
            "requested": requested,
            "resolved": str(resolved),
            "available": False,
            "error": type(error).__name__,
        }
    cache_key = (
        str(resolved),
        value.st_dev,
        value.st_ino,
        value.st_size,
        value.st_mtime_ns,
        stat.S_IMODE(value.st_mode),
    )
    with _TOOL_IDENTITY_CACHE_LOCK:
        cached = _TOOL_IDENTITY_CACHE.get(cache_key)
    if cached is not None:
        return cached
    identity: dict[str, JSONValue] = {
        "requested": requested,
        "resolved": str(resolved),
        "available": True,
        "stat": {
            "device": value.st_dev,
            "inode": value.st_ino,
            "size_bytes": value.st_size,
            "modified_time_ns": value.st_mtime_ns,
            "mode": stat.S_IMODE(value.st_mode),
        },
        "sha256": _video_file_sha256(resolved),
        "version": _tool_version(resolved),
    }
    with _TOOL_IDENTITY_CACHE_LOCK:
        _TOOL_IDENTITY_CACHE[cache_key] = identity
    return identity


def build_tool_identities(
    *,
    ffmpeg_path: str = "ffmpeg",
    ffprobe_path: str = "ffprobe",
) -> dict[str, JSONValue]:
    """Resolve and fingerprint tools once for one export batch."""
    return {
        "ffmpeg": _tool_identity(ffmpeg_path),
        "ffprobe": _tool_identity(ffprobe_path),
    }


def _policy_payload(
    policy: FrameRatePolicyInput | UpscalePolicyInput,
) -> JSONValue:
    if policy is None:
        return None
    if isinstance(policy, Mapping):
        return _json_value(policy)
    return _json_value(policy.to_dict())


def _source_protection_path(value: str) -> Path | None:
    parsed = urlparse(value)
    if parsed.scheme not in {"", "file"}:
        return None
    path_value = unquote(parsed.path)
    if parsed.netloc and parsed.netloc != "localhost":
        path_value = f"//{parsed.netloc}{path_value}"
    if not path_value:
        return None
    return Path(path_value).expanduser().resolve(strict=False)


def protected_source_paths(project: Project) -> tuple[Path, ...]:
    """Return every source path and file-URI alias protected by the project."""
    protected: set[Path] = set()
    for source in tuple(project.sources or (project.source,)):
        for value in (source.path, source.uri):
            path = _source_protection_path(value)
            if path is not None:
                protected.add(path)
    return tuple(sorted(protected, key=str))


def protected_receipt_paths(
    project: Project,
    *,
    project_path: Path | str | None = None,
    planned_outputs: Sequence[Path] = (),
) -> tuple[Path, ...]:
    """Return every source, project, and planned output path for receipt safety."""
    protected = set(protected_source_paths(project))
    if project_path is not None:
        project_value = _source_protection_path(str(project_path))
        if project_value is not None:
            protected.add(project_value)
    for output in planned_outputs:
        protected.add(output.expanduser().resolve(strict=False))
    return tuple(sorted(protected, key=str))


def _same_path(left: Path, right: Path) -> bool:
    try:
        if left.exists() and right.exists() and left.samefile(right):
            return True
    except OSError:
        pass
    return left.expanduser().resolve(strict=False) == right.expanduser().resolve(strict=False)


def _ensure_not_protected(path: Path, protected_paths: Sequence[Path]) -> None:
    if any(_same_path(path, source_path) for source_path in protected_paths):
        raise ExportSessionError(
            f"Refusing to replace or remove protected source path: {path.name}",
        )


def verify_planned_output(
    plan: object,
    candidate: Path,
    *,
    ffmpeg_path: str = "ffmpeg",
    ffprobe_path: str = "ffprobe",
    cancel_event: threading.Event | None = None,
) -> dict[str, JSONValue]:
    """Re-verify a candidate against its concrete video or AV render plan."""
    from .av_compositor import AVRenderPlan, _verify_muxed_output
    from .export_delivery import verify_export_output, verify_mixed_export_output
    from .export_interpolation import probe_frame_count
    from .export_process import expected_export_frames
    from .export_types import ExportPlan
    from .media import probe_media

    def _probe_output_frame_count() -> int:
        return probe_frame_count(
            candidate,
            ffprobe_path,
            heartbeat_callback=(
                None if cancel_event is None else lambda: _raise_if_cancelled(cancel_event)
            ),
        )

    if cancel_event is not None and cancel_event.is_set():
        raise ExportCancelled("Export cancelled during output verification")
    if isinstance(plan, AVRenderPlan):
        verified = _verify_muxed_output(
            candidate,
            plan,
            ffmpeg_path=ffmpeg_path,
            ffprobe_path=ffprobe_path,
            cancel_event=cancel_event,
        )
        media = verified.output_probe
        payload: dict[str, JSONValue] = {
            "verified": True,
            "media": _json_value(media.metadata()),
            "frame_count": verified.actual_frames,
            "audio_sample_rate": verified.sample_rate,
            "audio_channels": verified.channels,
            "audio_sample_count": verified.sample_count,
        }
    elif isinstance(plan, ExportPlan):
        if plan.source_paths:
            media = verify_mixed_export_output(
                plan,
                candidate,
                ffmpeg_path=ffmpeg_path,
                ffprobe_path=ffprobe_path,
                heartbeat_callback=(
                    None if cancel_event is None else lambda: _raise_if_cancelled(cancel_event)
                ),
            )
            frame_count = _probe_output_frame_count()
        else:
            source_probe = probe_media(plan.source, ffprobe_path)
            media = verify_export_output(
                plan,
                source_probe,
                candidate,
                ffmpeg_path=ffmpeg_path,
                ffprobe_path=ffprobe_path,
                heartbeat_callback=(
                    None if cancel_event is None else lambda: _raise_if_cancelled(cancel_event)
                ),
            )
            frame_count = _probe_output_frame_count()
            expected_frames = expected_export_frames(plan, source_probe)
            if frame_count != expected_frames:
                raise ValueError(
                    f"Export frame count {frame_count} does not match expected {expected_frames}",
                )
        payload = {
            "verified": True,
            "media": _json_value(media.metadata()),
            "frame_count": frame_count,
        }
    else:
        raise TypeError(f"Unsupported output plan type: {type(plan).__name__}")
    if cancel_event is not None and cancel_event.is_set():
        raise ExportCancelled("Export cancelled during output verification")
    payload["content_sha256"] = _video_file_sha256(candidate)
    payload["published_stat"] = _json_value(_stat_payload(candidate))
    return payload


def _raise_if_cancelled(cancel_event: threading.Event) -> None:
    if cancel_event.is_set():
        raise ExportCancelled("Export cancelled during output verification")


def build_project_output_fingerprint_payload(
    project: Project,
    request: OutputRequest,
    *,
    frame_rate_policy: FrameRatePolicyInput = None,
    upscale_policy: UpscalePolicyInput = None,
    ffmpeg_path: str = "ffmpeg",
    ffprobe_path: str = "ffprobe",
    tool_identities: Mapping[str, JSONValue] | None = None,
    compositor_version: str = COMPOSITOR_VERSION,
    schema_version: str | int = BATCH_SCHEMA_VERSION,
    source_hash_cache: SourceHashCache | None = None,
    cancel_event: threading.Event | None = None,
    progress_callback: ExportProgressCallback | None = None,
) -> dict[str, JSONValue]:
    """Build the complete request payload used by app and CLI integrations."""
    sources = tuple(getattr(project, "sources", None) or (project.source,))
    source_records = []
    started = time.monotonic()
    reported = started - 1.0
    for index, source in enumerate(sources):
        check_export_cancelled(cancel_event)
        if time.monotonic() - reported >= 0.1:
            report_preparation_progress(
                progress_callback, "Fingerprinting export sources", index, len(sources), started
            )
            reported = time.monotonic()
        source_records.append(
            _source_record(
                Path(source.path),
                source.source_id,
                metadata=source.metadata,
                source_hash_cache=source_hash_cache,
                cancel_event=cancel_event,
                heartbeat_callback=make_progress_heartbeat(
                    progress_callback,
                    stage="Fingerprinting export sources",
                    total_frames=len(sources),
                    frame=index,
                    started=started,
                    percent=index * 100 / len(sources),
                ),
            )
        )
    original_timeline = project.timeline
    canonical_project = project
    if original_timeline.tracks is None:
        normalizer = getattr(project, "_legacy_v4_candidate", None)
        if not callable(normalizer):
            raise TypeError("Project does not expose the canonical legacy normalization path")
        canonical_project = normalizer()
    timeline = canonical_project.timeline
    tracks: list[dict[str, JSONValue]] = []
    blocks: list[dict[str, JSONValue]] = []
    for index, track in enumerate(tuple(timeline.tracks or ())):
        tracks.append(
            {
                "order": index,
                "track_id": track.track_id,
                "sanitized_label": _sanitized_track_label(track.track_id, index),
            }
        )
        for block_index, block in enumerate(track.blocks):
            block_value = block.to_dict(canonical_ticks=True, track_id=track.track_id)
            state = block_value.get("state", {})
            if not isinstance(state, Mapping):
                raise TypeError(f"Segment {block.segment_id} state is not a JSON object")
            copy_index = state.get("copy_index", getattr(block, "copy_index", block_index))
            repeat_index = state.get("repeat_index", getattr(block, "repeat_index", 0))
            blocks.append(
                {
                    "track_order": index,
                    "block_order": block_index,
                    "track_id": track.track_id,
                    "block_id": block.block_id or block.segment_id,
                    "source_id": block.source_id,
                    "source_start_tick": block_value.get("source_start_ticks"),
                    "source_end_tick": block_value.get("source_end_ticks"),
                    "timeline_start_tick": block_value.get("timeline_start_ticks"),
                    "timeline_end_tick": block_value.get("timeline_end_ticks"),
                    "excluded": bool(block.deleted),
                    "state": _json_value(state),
                    "copy_index": _json_value(copy_index),
                    "repeat_index": _json_value(repeat_index),
                    "transform": _json_value(block_value.get("visual_transform")),
                    "triplicate": _json_value(block_value.get("triplicate")),
                }
            )
    if not tracks:
        tracks.append(
            {
                "order": 0,
                "track_id": request.track_id or "legacy-track",
                "sanitized_label": _sanitized_track_label(
                    request.track_id or "legacy-track",
                    0,
                ),
            }
        )
    resolved_fps = _policy_payload(frame_rate_policy)
    resolved_upscale = _policy_payload(upscale_policy)
    resolved_tool_identities = (
        dict(tool_identities)
        if tool_identities is not None
        else build_tool_identities(
            ffmpeg_path=ffmpeg_path,
            ffprobe_path=ffprobe_path,
        )
    )
    timeline_payload: dict[str, JSONValue] = {
        "timing_mode": timeline.timing_mode,
        "ripple": timeline.ripple,
        "timebase": timeline.timebase,
        "frame_rate": timeline.frame_rate,
        "timeline_model_version": timeline.timeline_model_version,
        "active_track_id": timeline.active_track_id,
        "source_duration_seconds": timeline.source_duration_seconds,
        "source_durations": _json_value(timeline.source_durations or {}),
        "source_durations_ticks": _json_value(timeline.source_durations_ticks or {}),
        "editing_duration_ticks": timeline.editing_duration_ticks,
        "final_duration_ticks": timeline.final_duration_ticks,
    }
    audio_policy: dict[str, JSONValue] = {
        "analysis_version": AUDIO_POLICY_VERSION,
        "composition_version": AUDIO_COMPOSITION_VERSION,
        "sample_rate": AUDIO_SAMPLE_RATE,
        "channels": AUDIO_CHANNELS,
        "fixed_stereo": True,
        "pan_law": PAN_LAW_VERSION,
        "pan_vectors": {
            str(active_count): list(fixed_pan_vector(active_count)) for active_count in range(1, 5)
        },
        "multichannel_shared_coefficient": 0.7071067811865475,
        "multichannel_center_coefficient": 0.5,
    }
    layout_policy: dict[str, JSONValue] = {
        "version": LAYOUT_POLICY_VERSION,
        "canvas_policy": CANVAS_POLICY_VERSION,
        "canvas": {
            "x": DEFAULT_CANVAS.x,
            "y": DEFAULT_CANVAS.y,
            "width": DEFAULT_CANVAS.width,
            "height": DEFAULT_CANVAS.height,
        },
        "triplicate_roles": list(TRIPLICATE_ROLES),
    }
    return {
        "project": {
            "schema_version": canonical_project.schema_version,
            "composition_version": canonical_project.composition_version,
            "output_settings": _json_value(canonical_project.output_settings),
        },
        "sources": _json_value(source_records),
        "tracks": _json_value(tracks),
        "blocks": _json_value(blocks),
        "timeline": _json_value(timeline_payload),
        "source_audio": {
            "settings": _json_value(canonical_project.source_settings),
            "policy": audio_policy,
        },
        "layout": layout_policy,
        "render": {
            "resolved_fps": resolved_fps,
            "rve_route": _json_value(
                getattr(frame_rate_policy, "backend", None)
                or getattr(frame_rate_policy, "route", None)
            ),
            "upscale": resolved_upscale,
        },
        "output": {
            "mode": request.identity.mode,
            "selection": _json_value(request.identity.to_dict()),
            "destination": str(request.destination.expanduser().resolve()),
            "safe_naming": request.destination.name,
            "framing": request.framing,
            "audio_intent": request.audio_intent,
        },
        "tools": _json_value(resolved_tool_identities),
        "versions": {
            "compositor": compositor_version,
            "schema": schema_version,
            "timeline": getattr(timeline, "timeline_model_version", None),
            "composition": getattr(canonical_project, "composition_version", None),
            "layout": LAYOUT_POLICY_VERSION,
            "audio": AUDIO_COMPOSITION_VERSION,
            "pan_law": PAN_LAW_VERSION,
            "fixed_stereo": True,
            "canvas": CANVAS_POLICY_VERSION,
        },
    }


def _identity_key(identity: OutputIdentity) -> str:
    return json.dumps(
        identity.to_dict(),
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )


def output_identity_key(identity: OutputIdentity) -> str:
    return _identity_key(identity)


def build_output_request_maps(
    output_plan: OutputPlan,
    final_plan: PlanT | None,
) -> tuple[dict[str, PlanT], dict[str, OutputRequest]]:
    """Build the identity-keyed final plan and request maps shared by callers."""
    final_by_key: dict[str, PlanT] = {}
    if output_plan.final_request is not None and final_plan is not None:
        final_by_key[output_identity_key(output_plan.final_request.identity)] = final_plan
    request_by_key = {
        output_identity_key(request.identity): request for request in output_plan.output_requests
    }
    return final_by_key, request_by_key


def _safe_name(identity: OutputIdentity, index: int) -> str:
    raw = "-".join(
        item
        for item in (
            identity.mode,
            identity.output_kind,
            identity.track_id,
            identity.source_id,
            str(index),
        )
        if item
    )
    safe = "".join(
        character if character.isalnum() or character in "-_." else "-" for character in raw
    )
    return safe.strip(".") or f"output-{index}"


def _receipt_path(destination: Path) -> Path:
    resolved = destination.expanduser()
    return resolved.parent / f".{resolved.name}{RECEIPT_SUFFIX}"


def _stat_payload(path: Path) -> dict[str, int]:
    value = path.stat()
    return {
        "size_bytes": value.st_size,
        "modified_time_ns": value.st_mtime_ns,
        "mode": stat.S_IMODE(value.st_mode),
    }


def _error_payload(code: str, message: str) -> dict[str, str]:
    return {"code": code, "message": message}


@dataclass(frozen=True)
class ExportOutputResult:
    identity: OutputIdentity
    destination: Path
    fingerprint: str
    state: ExportResultState
    verification: dict[str, Any] | None = None
    error: dict[str, str] | None = None
    published: bool = False
    published_hash: str | None = None
    published_stat: dict[str, int] | None = None

    @property
    def verified(self) -> bool:
        return self.state in {ExportResultState.VERIFIED, ExportResultState.SKIPPED}

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "identity": self.identity.to_dict(),
            "destination": str(self.destination),
            "fingerprint": self.fingerprint,
            "state": self.state.value,
            "verified": self.verified,
            "published": self.published,
        }
        if self.verification is not None:
            payload["verification"] = _json_value(self.verification)
        if self.error is not None:
            payload["error"] = dict(self.error)
        if self.published_hash is not None:
            payload["published_hash"] = self.published_hash
        if self.published_stat is not None:
            payload["published_stat"] = dict(self.published_stat)
        return payload


@dataclass(frozen=True)
class ExportBatchResult:
    results: tuple[ExportOutputResult, ...]
    mode: str
    complete: bool
    partial_success: bool
    stale: bool = False
    error: dict[str, str] | None = None
    receipt: Path | None = None

    @property
    def verified(self) -> bool:
        return self.complete

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "complete": self.complete,
            "verified": self.complete,
            "partial_success": self.partial_success,
            "stale": self.stale,
            "error": None if self.error is None else dict(self.error),
            "receipt": None if self.receipt is None else str(self.receipt),
            "results": [result.to_dict() for result in self.results],
        }


RenderOutput = Callable[[OutputRequest, Path, threading.Event], Path]
VerifyOutput = Callable[[OutputRequest, Path, threading.Event], Mapping[str, Any] | None]


class ExportCoordinator:
    """Coordinate independent output rendering, verification, and publication."""

    def __init__(
        self,
        output_requests: Sequence[OutputRequest],
        session_destination: Path,
        output_fingerprints: Mapping[str, str],
        render_output: RenderOutput,
        verify_output: VerifyOutput,
        publication_lock: threading.Lock,
        *,
        on_published: Callable[[OutputRequest, Path], None] | None = None,
        tool_versions: Mapping[str, JSONValue] | None = None,
        schema_version: str | int = BATCH_SCHEMA_VERSION,
        compositor_version: str = COMPOSITOR_VERSION,
        protected_source_paths: Sequence[Path] = (),
        protected_receipt_paths: Sequence[Path] = (),
        policy_versions: Mapping[str, JSONValue] | None = None,
    ) -> None:
        self.output_requests = tuple(output_requests)
        self.session_destination = Path(session_destination).expanduser()
        self.output_fingerprints = dict(output_fingerprints)
        self.render_output = render_output
        self.verify_output = verify_output
        self.publication_lock = publication_lock
        self.on_published = on_published
        self.tool_versions = dict(tool_versions or {})
        self.schema_version = schema_version
        self.compositor_version = compositor_version
        self.policy_versions = dict(policy_versions or DEFAULT_POLICY_VERSIONS)
        self.protected_source_paths = tuple(
            path.expanduser().resolve(strict=False) for path in protected_source_paths
        )
        self.protected_receipt_paths = tuple(
            dict.fromkeys(
                (
                    *self.protected_source_paths,
                    *(path.expanduser().resolve(strict=False) for path in protected_receipt_paths),
                ),
            ),
        )
        self._validate_requests_and_fingerprints()

    def _all_protected_paths(
        self,
        planned_outputs: Iterable[Path] = (),
    ) -> tuple[Path, ...]:
        return tuple(
            dict.fromkeys(
                (
                    *self.protected_receipt_paths,
                    *(path.expanduser().resolve(strict=False) for path in planned_outputs),
                ),
            ),
        )

    @staticmethod
    def _receipt_artifact_paths(destination: Path) -> tuple[Path, Path]:
        receipt = _receipt_path(destination)
        return receipt, receipt.with_name(f".{receipt.name}.tmp")

    def _validate_requests_and_fingerprints(self) -> None:
        identities: set[str] = set()
        destinations: set[Path] = set()
        expected: set[str] = set()
        for request in self.output_requests:
            if not isinstance(request, OutputRequest):
                raise ValueError("output_requests must contain OutputRequest values")
            identity_key = _identity_key(request.identity)
            if identity_key in identities:
                raise ValueError(f"Duplicate output identity: {identity_key}")
            identities.add(identity_key)
            destination = request.destination.expanduser().resolve()
            if destination in destinations:
                raise ValueError(f"Duplicate output destination: {destination}")
            _ensure_not_protected(destination, self.protected_source_paths)
            destinations.add(destination)
            expected.add(identity_key)
        actual = set(self.output_fingerprints)
        missing = expected - actual
        extra = actual - expected
        if missing or extra:
            detail: list[str] = []
            if missing:
                detail.append(f"missing fingerprint entries: {sorted(missing)}")
            if extra:
                detail.append(f"extra fingerprint entries: {sorted(extra)}")
            raise ValueError("; ".join(detail))
        if not self.output_requests:
            raise ValueError("At least one output request is required")
        receipt, temporary = self._receipt_artifact_paths(self.session_destination)
        protected = self._all_protected_paths(destinations)
        _ensure_not_protected(receipt, protected)
        _ensure_not_protected(temporary, protected)

    def _batch_request(self) -> dict[str, Any]:
        return {
            "batch_schema_version": BATCH_SCHEMA_VERSION,
            "schema_version": self.schema_version,
            "compositor_version": self.compositor_version,
            "session_destination": self.session_destination,
            "outputs": [
                {
                    "identity": request.identity.to_dict(),
                    "destination": request.destination,
                    "fingerprint": self.output_fingerprints[_identity_key(request.identity)],
                }
                for request in self.output_requests
            ],
            "tools": self.tool_versions,
            "policy_versions": self.policy_versions,
        }

    def _initial_results(self) -> dict[str, ExportOutputResult]:
        return {
            _identity_key(request.identity): ExportOutputResult(
                identity=request.identity,
                destination=request.destination,
                fingerprint=self.output_fingerprints[_identity_key(request.identity)],
                state=ExportResultState.PENDING,
            )
            for request in self.output_requests
        }

    def _load_receipt(self) -> dict[str, Any] | None:
        path = _receipt_path(self.session_destination)
        _ensure_not_protected(path, self._all_protected_paths(self._planned_destinations()))
        try:
            if not path.is_file() or path.is_symlink():
                return None
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            return None
        return value if isinstance(value, dict) else None

    def _receipt_matches_request(self, receipt: Mapping[str, Any]) -> bool:
        if receipt.get("receipt_schema_version") != BATCH_SCHEMA_VERSION:
            return False
        if receipt.get("schema_version") != self.schema_version:
            return False
        if receipt.get("compositor_version") != self.compositor_version:
            return False
        if receipt.get("policy_versions") != _json_value(self.policy_versions):
            return False
        try:
            if receipt.get("tools") != _json_value(self.tool_versions):
                return False
            if receipt.get("batch_fingerprint") != build_output_fingerprint(
                self._batch_request(),
            ):
                return False
        except (TypeError, ValueError):
            return False
        requested = {
            item["identity_key"]: {
                "identity": item["identity"],
                "destination": item["destination"],
                "fingerprint": item["fingerprint"],
            }
            for item in self._request_records()
        }
        records = receipt.get("outputs")
        if not isinstance(records, list):
            return False
        received = {
            str(item.get("identity_key")): {
                "identity": item.get("identity"),
                "destination": item.get("destination"),
                "fingerprint": item.get("fingerprint"),
            }
            for item in records
            if isinstance(item, Mapping)
        }
        return requested == received

    def _request_records(self) -> list[dict[str, Any]]:
        return [
            {
                "identity_key": _identity_key(request.identity),
                "identity": request.identity.to_dict(),
                "destination": str(request.destination.expanduser().resolve()),
                "fingerprint": self.output_fingerprints[_identity_key(request.identity)],
            }
            for request in self.output_requests
        ]

    def _planned_destinations(self) -> tuple[Path, ...]:
        return tuple(request.destination for request in self.output_requests)

    def _candidate_path(self, session: ExportSession, index: int, request: OutputRequest) -> Path:
        directory = session.root / "candidates"
        directory.mkdir(parents=True, exist_ok=True)
        return directory / f"{_safe_name(request.identity, index)}{request.destination.suffix}"

    @staticmethod
    def _published_result(
        request: OutputRequest,
        fingerprint: str,
        verification: Mapping[str, Any] | None,
        published_hash: str | None,
        published_stat: dict[str, int] | None,
    ) -> ExportOutputResult:
        return ExportOutputResult(
            identity=request.identity,
            destination=request.destination,
            fingerprint=fingerprint,
            state=ExportResultState.VERIFIED,
            verification=dict(verification or {}),
            published=True,
            published_hash=published_hash,
            published_stat=published_stat,
        )

    @staticmethod
    def _cancelled_result(
        request: OutputRequest,
        fingerprint: str,
        error: ExportCancelled,
    ) -> ExportOutputResult:
        return ExportOutputResult(
            identity=request.identity,
            destination=request.destination,
            fingerprint=fingerprint,
            state=ExportResultState.CANCELLED,
            error=_error_payload("cancelled", str(error)),
        )

    def _retain_published_failure(
        self,
        *,
        results: dict[str, ExportOutputResult],
        request: OutputRequest,
        fingerprint: str,
        verification: Mapping[str, Any] | None,
        published_hash: str | None,
        published_stat: dict[str, int] | None,
        published_result: ExportOutputResult | None,
        error: BaseException,
        code: str,
        cancel_event: threading.Event,
    ) -> dict[str, str]:
        key = _identity_key(request.identity)
        results[key] = published_result or self._published_result(
            request,
            fingerprint,
            verification,
            published_hash,
            published_stat,
        )
        if code == "cancelled":
            cancel_event.set()
        return _error_payload(code, str(error))

    def _retain_published_context_failure(
        self,
        results: dict[str, ExportOutputResult],
        context: tuple[
            OutputRequest,
            str,
            Mapping[str, Any] | None,
            str | None,
            dict[str, int] | None,
            ExportOutputResult | None,
        ],
        error: BaseException,
        code: str,
        cancel_event: threading.Event,
    ) -> dict[str, str]:
        (
            request,
            fingerprint,
            verification,
            published_hash,
            published_stat,
            published_result,
        ) = context
        return self._retain_published_failure(
            results=results,
            request=request,
            fingerprint=fingerprint,
            verification=verification,
            published_hash=published_hash,
            published_stat=published_stat,
            published_result=published_result,
            error=error,
            code=code,
            cancel_event=cancel_event,
        )

    def _record_unpublished_cancellation(
        self,
        *,
        session: ExportSession,
        results: dict[str, ExportOutputResult],
        request: OutputRequest,
        fingerprint: str,
        candidate: Path,
        mode: str,
        error: ExportCancelled,
    ) -> None:
        results[_identity_key(request.identity)] = self._cancelled_result(
            request,
            fingerprint,
            error,
        )
        candidate.unlink(missing_ok=True)
        self._save_batch_manifest(session, results, mode=mode)

    def _save_batch_manifest(
        self,
        session: ExportSession,
        results: Mapping[str, ExportOutputResult],
        *,
        mode: str,
        error: dict[str, str] | None = None,
    ) -> None:
        session.manifest["batch"] = {
            "schema_version": BATCH_SCHEMA_VERSION,
            "mode": mode,
            "outputs": self._request_records(),
            "tools": self.tool_versions,
            "compositor_version": self.compositor_version,
            "policy_versions": self.policy_versions,
        }
        session.manifest["outputs"] = {key: result.to_dict() for key, result in results.items()}
        session.manifest["batch_error"] = None if error is None else dict(error)
        session._save_manifest()

    def _write_receipt(
        self,
        results: Mapping[str, ExportOutputResult],
    ) -> Path:
        receipt = _receipt_path(self.session_destination)
        _, temporary = self._receipt_artifact_paths(self.session_destination)
        protected = self._all_protected_paths(self._planned_destinations())
        _ensure_not_protected(receipt, protected)
        _ensure_not_protected(temporary, protected)
        if receipt.is_symlink() or temporary.is_symlink():
            raise ExportSessionError("Batch receipt paths must not be symbolic links")
        receipt.parent.mkdir(parents=True, exist_ok=True)
        records: list[dict[str, Any]] = []
        for request in self.output_requests:
            key = _identity_key(request.identity)
            result = results[key]
            destination = request.destination.expanduser()
            published_hash = result.published_hash or _video_file_sha256(destination)
            published_stat = result.published_stat or _stat_payload(destination)
            records.append(
                {
                    "identity_key": key,
                    "identity": request.identity.to_dict(),
                    "destination": str(destination.resolve()),
                    "fingerprint": result.fingerprint,
                    "state": result.state.value,
                    "published_hash": published_hash,
                    "published_stat": published_stat,
                    "media_verification": _json_value(result.verification or {}),
                }
            )
        payload = {
            "receipt_schema_version": BATCH_SCHEMA_VERSION,
            "batch_fingerprint": build_output_fingerprint(self._batch_request()),
            "session_destination": str(self.session_destination.resolve()),
            "compositor_version": self.compositor_version,
            "schema_version": self.schema_version,
            "tools": _json_value(self.tool_versions),
            "policy_versions": _json_value(self.policy_versions),
            "outputs": records,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        try:
            with temporary.open("w", encoding="utf-8") as stream:
                json.dump(payload, stream, ensure_ascii=True, indent=2, sort_keys=True)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, receipt)
            directory_fd = os.open(receipt.parent, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        except OSError:
            temporary.unlink(missing_ok=True)
            raise
        return receipt

    def _discard_receipt(self) -> bool:
        return discard_batch_receipt(
            self.session_destination,
            protected_source_paths=self._all_protected_paths(self._planned_destinations()),
        )

    def _result_from_record(
        self,
        request: OutputRequest,
        record: Mapping[str, Any],
    ) -> ExportOutputResult:
        raw_state = record.get("state")
        try:
            state = ExportResultState(raw_state)
        except ValueError:
            state = ExportResultState.PENDING
        if state not in {ExportResultState.VERIFIED, ExportResultState.SKIPPED}:
            state = ExportResultState.PENDING
        return ExportOutputResult(
            identity=request.identity,
            destination=request.destination,
            fingerprint=self.output_fingerprints[_identity_key(request.identity)],
            state=state,
            verification=(
                dict(record["verification"])
                if isinstance(record.get("verification"), Mapping)
                else None
            ),
            published=bool(record.get("published", False)),
            published_hash=(
                record.get("published_hash")
                if isinstance(record.get("published_hash"), str)
                else None
            ),
            published_stat=(
                dict(record["published_stat"])
                if isinstance(record.get("published_stat"), Mapping)
                else None
            ),
        )

    def _apply_resume_records(
        self,
        session: ExportSession,
        results: dict[str, ExportOutputResult],
        *,
        receipt: Mapping[str, Any] | None,
        cancel_event: threading.Event,
    ) -> None:
        stored: Mapping[str, Any] = {}
        if isinstance(session.manifest.get("outputs"), Mapping):
            stored = session.manifest["outputs"]
        elif receipt is not None and isinstance(receipt.get("outputs"), list):
            stored = {
                str(record.get("identity_key")): record
                for record in receipt["outputs"]
                if isinstance(record, Mapping)
            }
        for request in self.output_requests:
            key = _identity_key(request.identity)
            record = stored.get(key)
            if not isinstance(record, Mapping):
                continue
            if record.get("fingerprint") != results[key].fingerprint:
                continue
            if record.get("state") not in {
                ExportResultState.VERIFIED.value,
                ExportResultState.SKIPPED.value,
            }:
                continue
            destination = request.destination.expanduser()
            if (
                not destination.is_file()
                or destination.is_symlink()
                or not isinstance(record.get("published_hash"), str)
                or not isinstance(record.get("published_stat"), Mapping)
            ):
                continue
            try:
                if _video_file_sha256(destination) != record["published_hash"]:
                    continue
                if _stat_payload(destination) != dict(record["published_stat"]):
                    continue
            except OSError:
                continue
            try:
                verification = self.verify_output(
                    request,
                    destination,
                    cancel_event,
                )
            except (ExportCancelled, OSError, RuntimeError, ValueError):
                continue
            results[key] = ExportOutputResult(
                identity=request.identity,
                destination=request.destination,
                fingerprint=results[key].fingerprint,
                state=ExportResultState.SKIPPED,
                verification=dict(verification or {}),
                published=True,
                published_hash=record["published_hash"],
                published_stat=dict(record["published_stat"]),
            )

    def _stale_result(
        self,
        results: Mapping[str, ExportOutputResult],
        *,
        mode: str,
        message: str,
    ) -> ExportBatchResult:
        error = _error_payload("stale_session", message)
        return ExportBatchResult(
            results=tuple(
                ExportOutputResult(
                    identity=result.identity,
                    destination=result.destination,
                    fingerprint=result.fingerprint,
                    state=ExportResultState.PENDING,
                    error=error,
                )
                for result in results.values()
            ),
            mode=mode,
            complete=False,
            partial_success=False,
            stale=True,
            error=error,
        )

    def run(
        self,
        *,
        mode: str = "fresh",
        cancel_event: threading.Event | None = None,
    ) -> ExportBatchResult:
        if mode not in {"fresh", "resume", "restart"}:
            raise ValueError(f"Unsupported export coordinator mode: {mode}")
        event = cancel_event or threading.Event()
        results = self._initial_results()
        request = self._batch_request()
        receipt = self._load_receipt()
        if mode == "resume" and receipt is not None and not self._receipt_matches_request(receipt):
            return self._stale_result(
                results,
                mode=mode,
                message="Export receipt does not match the current output requests",
            )
        try:
            session = ExportSession.open(
                self.session_destination,
                request,
                ("batch",),
                mode=(
                    "fresh"
                    if mode == "resume"
                    and receipt is not None
                    and not session_root(self.session_destination).exists()
                    else mode
                ),
            )
        except (ExportSessionMismatch, ExportSessionNotFound) as error:
            return self._stale_result(results, mode=mode, message=str(error))
        except ExportSessionError as error:
            failure = _error_payload("session_error", str(error))
            return ExportBatchResult(
                results=tuple(
                    ExportOutputResult(
                        identity=result.identity,
                        destination=result.destination,
                        fingerprint=result.fingerprint,
                        state=ExportResultState.PENDING,
                        error=failure,
                    )
                    for result in results.values()
                ),
                mode=mode,
                complete=False,
                partial_success=False,
                error=failure,
            )

        try:
            if mode == "resume":
                self._apply_resume_records(
                    session,
                    results,
                    receipt=receipt,
                    cancel_event=event,
                )
            self._save_batch_manifest(session, results, mode=mode)
            bookkeeping_error: dict[str, str] | None = None
            for index, output_request in enumerate(self.output_requests):
                key = _identity_key(output_request.identity)
                current = results[key]
                if current.state == ExportResultState.SKIPPED:
                    continue
                if event.is_set():
                    break
                results[key] = ExportOutputResult(
                    identity=output_request.identity,
                    destination=output_request.destination,
                    fingerprint=current.fingerprint,
                    state=ExportResultState.RUNNING,
                )
                self._save_batch_manifest(session, results, mode=mode)
                candidate = self._candidate_path(session, index, output_request)
                candidate.unlink(missing_ok=True)
                published_result: ExportOutputResult | None = None
                publication_committed = False
                verification: Mapping[str, Any] | None = None
                published_hash: str | None = None
                published_stat: dict[str, int] | None = None
                failure_context = (
                    output_request,
                    current.fingerprint,
                    verification,
                    published_hash,
                    published_stat,
                    published_result,
                )

                try:
                    rendered = self.render_output(output_request, candidate, event)
                    if rendered.expanduser().resolve() != candidate.expanduser().resolve():
                        raise RuntimeError("Renderer returned an unexpected candidate path")
                    if event.is_set():
                        raise ExportCancelled("Export cancelled during rendering")
                    verification = self.verify_output(output_request, candidate, event)
                    if event.is_set():
                        raise ExportCancelled("Export cancelled during verification")
                    output_request.destination.parent.mkdir(parents=True, exist_ok=True)
                    with self.publication_lock:
                        if event.is_set():
                            raise ExportCancelled("Export cancelled before publication")
                        os.replace(candidate, output_request.destination)
                        publication_committed = True
                        try:
                            published_hash = _video_file_sha256(output_request.destination)
                            published_stat = _stat_payload(output_request.destination)
                        except (OSError, RuntimeError, ValueError, TypeError) as error:
                            bookkeeping_error = _error_payload("bookkeeping", str(error))
                    published_result = self._published_result(
                        output_request,
                        current.fingerprint,
                        verification,
                        published_hash,
                        published_stat,
                    )
                    failure_context = (
                        output_request,
                        current.fingerprint,
                        verification,
                        published_hash,
                        published_stat,
                        published_result,
                    )
                    results[key] = published_result
                    try:
                        self._save_batch_manifest(session, results, mode=mode)
                        if bookkeeping_error is not None:
                            break
                        if self.on_published is not None:
                            self.on_published(output_request, output_request.destination)
                    except ExportCancelled as error:
                        bookkeeping_error = self._retain_published_context_failure(
                            results, failure_context, error, "cancelled", event
                        )
                        break
                    except (OSError, RuntimeError, ValueError, TypeError) as error:
                        bookkeeping_error = self._retain_published_context_failure(
                            results, failure_context, error, "bookkeeping", event
                        )
                        break
                except ExportCancelled as error:
                    if publication_committed:
                        bookkeeping_error = self._retain_published_context_failure(
                            results, failure_context, error, "cancelled", event
                        )
                        break
                    self._record_unpublished_cancellation(
                        session=session,
                        results=results,
                        request=output_request,
                        fingerprint=current.fingerprint,
                        candidate=candidate,
                        mode=mode,
                        error=error,
                    )
                    break
                except (OSError, RuntimeError, ValueError, TypeError) as error:
                    if publication_committed:
                        bookkeeping_error = self._retain_published_context_failure(
                            results, failure_context, error, "bookkeeping", event
                        )
                        break
                    if event.is_set():
                        self._record_unpublished_cancellation(
                            session=session,
                            results=results,
                            request=output_request,
                            fingerprint=current.fingerprint,
                            candidate=candidate,
                            mode=mode,
                            error=ExportCancelled(str(error)),
                        )
                        break
                    results[key] = ExportOutputResult(
                        identity=output_request.identity,
                        destination=output_request.destination,
                        fingerprint=current.fingerprint,
                        state=ExportResultState.FAILED,
                        error=_error_payload("failed", str(error)),
                    )
                    candidate.unlink(missing_ok=True)
                    self._save_batch_manifest(session, results, mode=mode)
                    break

            complete = all(result.verified for result in results.values())
            if complete and bookkeeping_error is None:
                try:
                    receipt_path = self._write_receipt(results)
                except (OSError, ExportSessionError, TypeError, ValueError) as error:
                    bookkeeping_error = _error_payload("bookkeeping", str(error))
                else:
                    session.cleanup_after_success()
                    return ExportBatchResult(
                        results=tuple(results.values()),
                        mode=mode,
                        complete=True,
                        partial_success=False,
                        receipt=receipt_path,
                    )
            try:
                self._save_batch_manifest(
                    session,
                    results,
                    mode=mode,
                    error=bookkeeping_error,
                )
            except (OSError, RuntimeError, ValueError, TypeError):
                pass
            partial = any(result.verified for result in results.values())
            session.mark_failure(
                (
                    bookkeeping_error["message"]
                    if bookkeeping_error is not None
                    else (
                        "Export cancelled"
                        if event.is_set()
                        else "One or more outputs did not complete"
                    )
                ),
                cancelled=event.is_set(),
            )
            return ExportBatchResult(
                results=tuple(results.values()),
                mode=mode,
                complete=False,
                partial_success=partial,
                error=bookkeeping_error,
            )
        finally:
            session.close()


def discard_batch_receipt(
    destination: Path,
    *,
    protected_source_paths: Sequence[Path] = (),
) -> bool:
    """Remove only the derived batch receipt, never a source or its alias."""
    receipt = _receipt_path(Path(destination))
    temporary = receipt.with_name(f".{receipt.name}.tmp")
    normalized = tuple(path.expanduser().resolve(strict=False) for path in protected_source_paths)
    _ensure_not_protected(receipt, normalized)
    _ensure_not_protected(temporary, normalized)
    if receipt.is_symlink() or temporary.is_symlink():
        raise ExportSessionError("Batch receipt paths must not be symbolic links")
    existed = receipt.exists()
    if existed:
        receipt.unlink()
    if temporary.exists():
        temporary.unlink()
    return existed


__all__ = [
    "BATCH_SCHEMA_VERSION",
    "COMPOSITOR_VERSION",
    "ExportBatchResult",
    "ExportCancelled",
    "ExportCoordinator",
    "ExportOutputResult",
    "ExportResultState",
    "RECEIPT_SUFFIX",
    "build_output_fingerprint",
    "build_output_request_maps",
    "build_project_output_fingerprint_payload",
    "build_tool_identities",
    "discard_batch_receipt",
    "output_identity_key",
    "protected_receipt_paths",
    "protected_source_paths",
    "verify_planned_output",
]
