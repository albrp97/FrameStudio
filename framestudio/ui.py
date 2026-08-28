from __future__ import annotations

import math


def format_duration(seconds: float) -> str:
    if not math.isfinite(float(seconds)) or seconds < 0:
        raise ValueError("Duration must be a finite non-negative number")
    total_seconds = int(seconds)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds_value = divmod(remainder, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{seconds_value:02d}"
    return f"{minutes:02d}:{seconds_value:02d}"
