#!/usr/bin/env python3
"""Roll package planning frontmatter into docs/planning/STATUS.md.

Usage:
    uv run python .agents/skills/pdlc/scripts/status.py docs/planning

The script is stdlib-only and understands tontine-core's capability/task layout.
It reports status vocabulary drift and shipped-work evidence problems rather than
silently correcting planning records.
"""

from __future__ import annotations

import datetime as dt
import re
import sys
from pathlib import Path

CANONICAL_STATUSES = {
    "backlog",
    "ready",
    "in_progress",
    "shipped",
    "partial",
    "blocked",
}
ITEM_DIRECTORIES = {"capabilities", "tasks"}
SKIP_NAMES = {"README.md", "STATUS.md", "requirements.md"}


def frontmatter(text: str) -> dict[str, str]:
    """Parse scalar values from a leading YAML frontmatter block."""
    match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return {}

    values: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if not line or line.startswith((" ", "-", "#")) or ":" not in line:
            continue
        key, _, value = line.partition(":")
        values[key.strip()] = value.strip() or "(list)"
    return values


def item_type(path: Path) -> str:
    """Return the planning item type from its parent directory."""
    return "capability" if path.parent.name == "capabilities" else "task"


def identity(values: dict[str, str], path: Path) -> str:
    """Return the stable planning identifier."""
    return values.get("id") or path.stem


def read_items(root: Path) -> list[tuple[dict[str, str], Path]]:
    """Read capability and task records with status frontmatter."""
    items: list[tuple[dict[str, str], Path]] = []
    for directory in ITEM_DIRECTORIES:
        for path in sorted((root / directory).glob("*.md")):
            if path.name in SKIP_NAMES:
                continue
            values = frontmatter(path.read_text(encoding="utf-8"))
            if values.get("status"):
                items.append((values, path))
    return sorted(items, key=lambda item: (item_type(item[1]), identity(*item)))


def shipped_evidence(values: dict[str, str], path: Path, root: Path) -> list[str]:
    """Return evidence problems for a shipped task or capability."""
    if values.get("status") != "shipped":
        return []

    problems: list[str] = []
    for field in ("started", "completed"):
        if not values.get(field) or values[field] == "null":
            problems.append(f"missing {field} date")

    text = path.read_text(encoding="utf-8")
    if "- [ ]" in text:
        problems.append("has unchecked acceptance criteria")

    if item_type(path) == "task":
        completion = root / "completions" / f"{identity(values, path)}.md"
        if not completion.exists():
            problems.append(f"missing {completion.relative_to(root)}")
    return problems


def render(root: Path, items: list[tuple[dict[str, str], Path]]) -> str:
    """Render the package status dashboard."""
    counts = {status: 0 for status in sorted(CANONICAL_STATUSES)}
    drift: list[str] = []
    evidence: list[str] = []

    for values, path in items:
        status = values.get("status", "")
        if status in counts:
            counts[status] += 1
        else:
            drift.append(f"{path.relative_to(root)}: status={status!r}")
        evidence.extend(
            f"{path.relative_to(root)}: {problem}"
            for problem in shipped_evidence(values, path, root)
        )

    lines = [
        "---",
        "kind: status_dashboard",
        f"period: {dt.date.today().isoformat()}",
        "---",
        "",
        "# Package Delivery Status",
        "",
        "_Generated from capability and task frontmatter._",
        "",
        "## Summary",
        "",
    ]
    lines.extend(f"- {status}: {counts[status]}" for status in sorted(counts))
    lines.extend(["", "## Items", "", "| Type | ID | Status | Started | Completed | Owner |", "| --- | --- | --- | --- | --- | --- |"])
    for values, path in items:
        lines.append(
            "| {type} | {id} | {status} | {started} | {completed} | {owner} |".format(
                type=item_type(path),
                id=identity(values, path),
                status=values.get("status", ""),
                started=values.get("started", ""),
                completed=values.get("completed", ""),
                owner=values.get("owner", ""),
            )
        )

    lines.extend(["", "## Evidence Checks", ""])
    if evidence:
        lines.extend(f"- {problem}" for problem in evidence)
    else:
        lines.append("- No shipped-item evidence problems detected.")

    if drift:
        lines.extend(["", "## Vocabulary Drift", ""])
        lines.extend(f"- {problem}" for problem in drift)

    return "\n".join(lines) + "\n"


def main(root_name: str = "docs/planning") -> int:
    """Generate the dashboard and return a process status."""
    root = Path(root_name)
    items = read_items(root)
    (root / "STATUS.md").write_text(render(root, items), encoding="utf-8")
    print(f"wrote {root / 'STATUS.md'} ({len(items)} items)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "docs/planning"))
