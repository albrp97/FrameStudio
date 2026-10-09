from __future__ import annotations

from .cli_types import CLI_EXIT_INVALID, CliError
from .model import ABSOLUTE_TIMING_MODE, SCHEMA_VERSION, Project, ProjectValidationError


def ensure_absolute_track_editing(
    project: Project,
    *,
    confirmed: bool,
) -> bool:
    """Require and, when confirmed, perform legacy-to-absolute conversion."""
    if (
        project.schema_version == SCHEMA_VERSION
        and project.timeline.timing_mode == ABSOLUTE_TIMING_MODE
    ):
        return False
    if not confirmed:
        raise CliError(
            "legacy_conversion_required",
            ("Explicit confirmation is required to convert legacy timing to synchronized tracks"),
            exit_code=CLI_EXIT_INVALID,
            details={
                "required_flag": "--confirm-legacy-conversion",
                "timing_mode": project.timeline.timing_mode,
            },
        )
    try:
        project.convert_to_synchronized(confirm=True)
    except ProjectValidationError as error:
        raise CliError(
            "invalid_operation",
            str(error),
            exit_code=CLI_EXIT_INVALID,
        ) from error
    return True


def track_error_details(project: Project, track_id: str | None = None) -> dict[str, object]:
    details: dict[str, object] = {
        "track_ids": list(project.timeline.track_ids),
    }
    if track_id is not None:
        details["track_id"] = track_id
    return details
