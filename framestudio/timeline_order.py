from __future__ import annotations

import random
from collections.abc import Sequence
from pathlib import Path


def randomize_clip_order(paths: Sequence[Path]) -> tuple[Path, ...]:
    ordered = tuple(paths)
    if len(ordered) <= 1:
        return ordered

    shuffled = list(ordered)
    random.shuffle(shuffled)
    if tuple(shuffled) == ordered:
        # Clip order is a UX randomization, not a security decision.
        offset = random.randrange(1, len(shuffled))  # nosec B311
        shuffled = shuffled[offset:] + shuffled[:offset]
    return tuple(shuffled)
