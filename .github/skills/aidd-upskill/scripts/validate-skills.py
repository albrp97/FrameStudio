#!/usr/bin/env python3

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


MAX_BODY_LINES = 200
ACTIVATION_PATTERN = re.compile(
    r"\b(use when|use for|use during|whenever|before|after)\b",
    re.I,
)
EXECUTION_PATTERN = re.compile(
    r"^## (Process|Steps|Execute)\s*$|"
    r"^## .*(?:=>|\bprocess\b|\bsteps\b|\bexecute\b).*$|"
    r"^[A-Za-z][A-Za-z0-9]*(?:\([^)]*\))?\s*(?:=>[^{]+)?\{",
    re.M,
)
CONTRACT_IMPORTS = (
    "../lifecycle-interface.md",
    "../planning-skill-interface.md",
    "../workflow-interface.md",
)
MARKDOWN_LINK_PATTERN = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


@dataclass(frozen=True)
class Finding:
    path: Path
    check: str
    message: str


def frontmatter(text: str) -> tuple[dict[str, str], int]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, 0
    try:
        end = lines[1:].index("---") + 1
    except ValueError:
        return {}, 0

    result: dict[str, str] = {}
    for line in lines[1:end]:
        if ":" in line and not line.startswith((" ", "\t")):
            key, value = line.split(":", 1)
            result[key.strip()] = value.strip()
    return result, end + 1


def validate_links(path: Path) -> list[Finding]:
    findings: list[Finding] = []
    text = path.read_text(encoding="utf-8")
    for target in MARKDOWN_LINK_PATTERN.findall(text):
        if target.startswith(("http://", "https://", "#", "$")):
            continue
        relative_target = target.split("#", 1)[0]
        if relative_target and not (path.parent / relative_target).resolve().exists():
            findings.append(Finding(path, "link", f"missing reference target: {target}"))
    return findings


def validate_skill(path: Path) -> list[Finding]:
    text = path.read_text(encoding="utf-8")
    metadata, body_start = frontmatter(text)
    findings: list[Finding] = []
    expected_name = path.parent.name

    if metadata.get("name") != expected_name:
        findings.append(Finding(path, "frontmatter", "name must match the skill directory"))

    description = metadata.get("description", "")
    if not description:
        findings.append(Finding(path, "frontmatter", "description is required"))
    elif description != ">" and not ACTIVATION_PATTERN.search(description):
        findings.append(Finding(path, "discovery", "description needs an activation condition"))

    if not re.search(r"(?m)^#\s+\S", text):
        findings.append(Finding(path, "structure", "top-level title is required"))

    if not EXECUTION_PATTERN.search(text):
        findings.append(Finding(path, "structure", "clear process, execute section, or function pipeline is required"))

    if not any(contract in text for contract in CONTRACT_IMPORTS):
        findings.append(Finding(path, "contract", "shared lifecycle, planning, or domain contract import is required"))
    if "../lifecycle-interface.md" in text and not re.search(r"\bLifecycle\s*\{", text):
        findings.append(Finding(path, "contract", "lifecycle import requires a local Lifecycle profile declaration"))
    if "../planning-skill-interface.md" in text and not re.search(r"\bPlanningSkill\s*\{", text):
        findings.append(Finding(path, "contract", "planning import requires a local PlanningSkill declaration"))
    if "../lifecycle-interface.md" in text:
        profile_match = re.search(r"\bprofile\s*=\s*([A-Za-z][A-Za-z0-9]*)", text)
        interface = (path.parent / "../lifecycle-interface.md").resolve().read_text(encoding="utf-8")
        profiles = set(re.findall(r"(?m)^  ([A-Za-z][A-Za-z0-9]*) \{$", interface))
        if not profile_match or profile_match.group(1) not in profiles:
            findings.append(Finding(path, "contract", "Lifecycle must select a defined shared profile"))

    body_lines = len(text.splitlines()[body_start:])
    if body_lines > MAX_BODY_LINES and not re.search(r"(?m)^import\s+|references/", text):
        findings.append(
            Finding(
                path,
                "size",
                f"{body_lines} lines exceeds {MAX_BODY_LINES} without progressive disclosure",
            )
        )

    readme = path.parent / "README.md"
    if not readme.exists():
        findings.append(Finding(path, "readme", "README.md is required"))
    else:
        readme_text = readme.read_text(encoding="utf-8")
        if not re.search(r"(?m)^#\s+\S", readme_text):
            findings.append(Finding(readme, "readme", "top-level title is required"))
        exposes_command = "Commands {" in text or re.search(r"/aidd-[a-z0-9-]+", text)
        if exposes_command and not re.search(r"/[a-z][a-z0-9-]*", readme_text):
            findings.append(Finding(readme, "readme", "at least one command example is required"))
        if not exposes_command and "## Usage" not in readme_text:
            findings.append(Finding(readme, "readme", "domain README requires a Usage section"))

    for markdown_path in path.parent.rglob("*.md"):
        findings.extend(validate_links(markdown_path))

    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("target", nargs="?", default=".github/skills")
    args = parser.parse_args()
    target = Path(args.target)
    if target.is_file():
        skills = [target]
    elif (target / "SKILL.md").exists():
        skills = [target / "SKILL.md"]
    else:
        skills = sorted(target.glob("*/SKILL.md"))
    findings = [finding for skill in skills for finding in validate_skill(skill)]

    for finding in findings:
        print(f"{finding.path}: {finding.check}: {finding.message}")

    print(f"Validated {len(skills)} skills; findings: {len(findings)}")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
