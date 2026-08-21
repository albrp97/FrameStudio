#!/usr/bin/env python3
"""Check dependency boundaries and cycles within the editor package."""

from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path

PACKAGE = "resolve_editor"
PACKAGE_PATH = Path(__file__).resolve().parents[1] / PACKAGE
ADAPTERS = {
    f"{PACKAGE}.app",
    f"{PACKAGE}.cli",
}
DOMAIN_MODULES = {
    f"{PACKAGE}.{name}"
    for name in (
        "export",
        "ffmpeg_playback",
        "media",
        "model",
        "operations",
        "persistence",
        "playback",
        "timeline",
        "ui",
    )
}


def _module_names() -> set[str]:
    return {
        f"{PACKAGE}.{path.stem}" for path in PACKAGE_PATH.glob("*.py") if path.stem != "__init__"
    }


def _resolve_import(
    module_name: str,
    imported_name: str | None,
    level: int,
) -> str | None:
    if level == 0:
        return imported_name
    package_parts = module_name.split(".")[:-1]
    if level > len(package_parts):
        return None
    base = package_parts[: len(package_parts) - level + 1]
    if imported_name:
        base.append(imported_name)
    return ".".join(base)


def _internal_imports(
    module_name: str,
    tree: ast.AST,
    modules: set[str],
) -> set[str]:
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            candidates = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            imported_names = [
                node.module if node.module is not None else alias.name for alias in node.names
            ]
            candidates = []
            for imported_name in imported_names:
                resolved = _resolve_import(module_name, imported_name, node.level)
                if resolved is not None:
                    candidates.append(resolved)
        else:
            continue
        for candidate in candidates:
            if candidate in modules:
                imports.add(candidate)
    return imports


def _dependency_graph(modules: set[str]) -> dict[str, set[str]]:
    graph: dict[str, set[str]] = {}
    for module_name in sorted(modules):
        path = PACKAGE_PATH / f"{module_name.rsplit('.', 1)[-1]}.py"
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        graph[module_name] = _internal_imports(module_name, tree, modules)
    return graph


def _cycle_findings(graph: dict[str, set[str]]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    visiting: set[str] = set()
    visited: set[str] = set()
    stack: list[str] = []

    def visit(module_name: str) -> None:
        if module_name in visiting:
            start = stack.index(module_name)
            cycle = stack[start:] + [module_name]
            findings.append(
                {
                    "rule": "no-import-cycles",
                    "source": module_name,
                    "target": module_name,
                    "message": "Import cycle: " + " -> ".join(cycle),
                }
            )
            return
        if module_name in visited:
            return
        visiting.add(module_name)
        stack.append(module_name)
        for dependency in sorted(graph[module_name]):
            visit(dependency)
        stack.pop()
        visiting.remove(module_name)
        visited.add(module_name)

    for module_name in sorted(graph):
        visit(module_name)
    return findings


def _boundary_findings(graph: dict[str, set[str]]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for source in sorted(DOMAIN_MODULES):
        for target in sorted(graph.get(source, set()) & ADAPTERS):
            findings.append(
                {
                    "rule": "domain-does-not-import-adapters",
                    "source": source,
                    "target": target,
                    "message": f"{source} imports adapter module {target}",
                }
            )
    if f"{PACKAGE}.cli" in graph.get(f"{PACKAGE}.cli", set()):
        findings.append(
            {
                "rule": "cli-does-not-import-itself",
                "source": f"{PACKAGE}.cli",
                "target": f"{PACKAGE}.cli",
                "message": "CLI module must not import itself",
            }
        )
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Check editor dependency boundaries and cycles.")
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit the machine-readable report",
    )
    parser.parse_args()
    modules = _module_names()
    graph = _dependency_graph(modules)
    findings = _cycle_findings(graph) + _boundary_findings(graph)
    payload = {
        "ok": not findings,
        "tool": "repository-dependency-check",
        "version": "1",
        "scope": PACKAGE,
        "modules": sorted(modules),
        "graph": {module: sorted(dependencies) for module, dependencies in sorted(graph.items())},
        "findings": findings,
    }
    print(json.dumps(payload, ensure_ascii=True, sort_keys=True))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
