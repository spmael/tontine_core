#!/usr/bin/env python3
"""Generate the reverse ADR citation index for tontine-core.

Planning capabilities and tasks may cite ADR files through an ``adr_refs``
frontmatter field. This script generates the reverse index so an ADR shows which
package work depends on it.

Usage:
    uv run python .agents/skills/pdlc/scripts/adr_index.py
"""

from __future__ import annotations

import re
from pathlib import Path


def frontmatter_block(text: str) -> str:
    """Return the leading frontmatter block, if present."""
    match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    return match.group(1) if match else ""


def list_field(frontmatter: str, key: str) -> list[str]:
    """Read an inline or indented YAML list field from frontmatter."""
    match = re.search(rf"^{re.escape(key)}:\s*(\[.*?\])?\s*$", frontmatter, re.MULTILINE)
    if not match:
        return []
    if match.group(1):
        return [item.strip().strip("'\"") for item in match.group(1)[1:-1].split(",") if item.strip()]

    values: list[str] = []
    for line in frontmatter[match.end() :].splitlines():
        if line.startswith("  - "):
            values.append(line[4:].strip())
        elif not line.strip() or line.startswith(" "):
            continue
        else:
            break
    return values


def planning_name(frontmatter: str, path: Path) -> str:
    """Return the stable capability or task ID."""
    match = re.search(r"^id:\s*(\S+)", frontmatter, re.MULTILINE)
    return match.group(1) if match else path.stem


def main(
    planning_root_name: str = "docs/planning",
    adr_root_name: str = "docs/architecture/adr",
) -> int:
    """Generate CITATIONS.md and return a process status."""
    planning_root = Path(planning_root_name)
    adr_root = Path(adr_root_name)
    citations: dict[str, list[tuple[str, Path]]] = {}

    for directory in (planning_root / "capabilities", planning_root / "tasks"):
        for path in sorted(directory.glob("*.md")):
            frontmatter = frontmatter_block(path.read_text(encoding="utf-8"))
            for reference in list_field(frontmatter, "adr_refs"):
                citations.setdefault(Path(reference).stem, []).append(
                    (planning_name(frontmatter, path), path)
                )

    adr_files = sorted({*adr_root.glob("ADR-*.md"), *adr_root.glob("adr_*.md")})
    output = [
        "# ADR Citation Index (generated)",
        "",
        "_Reverse index of package capability and task citations. Regenerate with "
        "`uv run python .claude/skills/pdlc/scripts/adr_index.py`; do not hand-edit._",
        "",
    ]
    cited = 0
    for adr in adr_files:
        references = sorted(citations.get(adr.stem, []))
        output.extend([f"## {adr.stem}", ""])
        if references:
            cited += 1
            for name, path in references:
                relative = path.relative_to(planning_root.parent)
                output.append(f"- [{name}](../../{relative.as_posix()})")
        else:
            output.append("_No capability or task currently cites this ADR._")
        output.append("")

    output.insert(4, f"**{cited} of {len(adr_files)} ADRs are cited by planning records.**\n")
    output_path = adr_root / "CITATIONS.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(output) + "\n", encoding="utf-8")
    print(f"wrote {output_path} ({len(adr_files)} ADRs, {cited} cited)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
