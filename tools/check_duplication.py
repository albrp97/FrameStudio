#!/usr/bin/env python3
"""Run jscpd and gate only duplication introduced after the approved baseline."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, cast


def _clone_identity(clone: dict[str, Any]) -> str:
    first = clone["firstFile"]
    second = clone["secondFile"]
    files = sorted((str(first["name"]), str(second["name"])))
    fragment_hash = hashlib.sha256(str(clone["fragment"]).encode("utf-8")).hexdigest()
    return "|".join((*files, fragment_hash))


def _load_report(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError(f"could not read jscpd report {path}: {error}") from error
    if not isinstance(payload, dict):
        raise RuntimeError(f"jscpd report {path} is not a JSON object")
    return cast(dict[str, Any], payload)


def _run_jscpd(
    *,
    npx: str,
    config: Path,
    report_directory: Path,
    paths: list[str],
) -> dict[str, Any]:
    report_directory.mkdir(parents=True, exist_ok=True)
    command = [
        npx,
        "--no-install",
        "jscpd",
        "--config",
        str(config),
        "--threshold",
        "100",
        "--reporters",
        "json,silent",
        "--output",
        str(report_directory),
        *paths,
    ]
    result = subprocess.run(command, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"jscpd failed with exit code {result.returncode}")
    return _load_report(report_directory / "jscpd-report.json")


def _write_baseline(path: Path, report: dict[str, Any]) -> None:
    clones = sorted({_clone_identity(clone) for clone in report.get("duplicates", [])})
    payload = {
        "version": 1,
        "tool": "jscpd",
        "findings": [],
        "clones": clones,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _read_baseline(path: Path) -> set[str]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        clones = payload["clones"]
    except (OSError, KeyError, TypeError, json.JSONDecodeError) as error:
        raise RuntimeError(f"could not read duplication baseline {path}: {error}") from error
    if not isinstance(clones, list) or not all(isinstance(clone, str) for clone in clones):
        raise RuntimeError(f"duplication baseline {path} has an invalid clones list")
    return set(clones)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run jscpd and check for duplication beyond the approved baseline."
    )
    parser.add_argument("--npx", default="npx")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--report-directory", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument(
        "--update-baseline",
        action="store_true",
        help="replace the baseline with the current jscpd findings",
    )
    parser.add_argument("paths", nargs="+")
    args = parser.parse_args()

    try:
        report = _run_jscpd(
            npx=args.npx,
            config=args.config,
            report_directory=args.report_directory,
            paths=args.paths,
        )
        if args.update_baseline:
            _write_baseline(args.baseline, report)
            print(f"Updated duplication baseline at {args.baseline}")
            return 0

        baseline = _read_baseline(args.baseline)
        current = {_clone_identity(clone) for clone in report.get("duplicates", [])}
    except RuntimeError as error:
        print(f"duplication check failed: {error}", file=sys.stderr)
        return 1

    new_clones = sorted(current - baseline)
    total = report["statistics"]["total"]
    print(
        "Duplication baseline passed: "
        f"{total['percentage']:.3f}% ({total['clones']} total clones), "
        f"{len(new_clones)} new clones."
    )
    if not new_clones:
        return 0

    print("New duplication findings:", file=sys.stderr)
    for clone in new_clones:
        print(f"  {clone}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
