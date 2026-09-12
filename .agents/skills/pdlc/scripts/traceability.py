#!/usr/bin/env python3
"""Report requirement-to-capability/task coverage for tontine-core.

Usage:
    uv run python .agents/skills/pdlc/scripts/traceability.py docs/planning

The script is stdlib-only and uses the package-wide requirements register plus
capability/task frontmatter. It reports gaps without modifying planning records.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REQUIREMENT_ID = re.compile(r"\b(?:FR|NFR)-[A-Z]+-\d{3}\b")
SKIP_NAMES = {"README.md", "STATUS.md", "requirements.md", "CITATIONS.md"}


def frontmatter_block(text: str) -> str:
    """Return the leading frontmatter block, if present."""
    match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    return match.group(1) if match else ""


def requirement_ids(text: str) -> set[str]:
    """Extract stable requirement identifiers from text."""
    return set(REQUIREMENT_ID.findall(text))


def planning_records(root: Path) -> list[tuple[Path, set[str]]]:
    """Read requirement references from capability and task frontmatter."""
    records: list[tuple[Path, set[str]]] = []
    for directory in (root / "capabilities", root / "tasks"):
        for path in sorted(directory.glob("*.md")):
            if path.name in SKIP_NAMES:
                continue
            references = requirement_ids(frontmatter_block(path.read_text(encoding="utf-8")))
            records.append((path, references))
    return records


def main(root_name: str = "docs/planning") -> int:
    """Print traceability findings and return a process status."""
    root = Path(root_name)
    register = root / "requirements.md"
    defined = requirement_ids(register.read_text(encoding="utf-8")) if register.exists() else set()
    records = planning_records(root)
    referenced: set[str] = set()
    owners: dict[str, list[Path]] = {}

    for path, references in records:
        referenced |= references
        for requirement in references:
            owners.setdefault(requirement, []).append(path)

    uncovered = sorted(defined - referenced)
    undefined = sorted(referenced - defined)

    print("== Package Traceability ==")
    print(f"Requirements defined: {len(defined)}")
    print(f"Requirements referenced: {len(referenced & defined)}")
    print(f"Uncovered requirements: {len(uncovered)}")
    if uncovered:
        print("  " + ", ".join(uncovered))

    print(f"Undefined references: {len(undefined)}")
    if undefined:
        print("  " + ", ".join(undefined))

    print("\nCoverage by requirement:")
    for requirement in sorted(defined):
        paths = owners.get(requirement, [])
        if paths:
            labels = ", ".join(str(path.relative_to(root.parent)) for path in paths)
            print(f"  {requirement}: {labels}")
        else:
            print(f"  {requirement}: UNCOVERED")

    return 1 if uncovered or undefined else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "docs/planning"))
