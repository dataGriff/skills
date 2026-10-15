"""Read skill families from docs/catalog.md - the one place they are defined.

A family is a heading carrying ``GROUP=<name>`` followed by a table whose
first column holds backticked skill names. The installer uses this for
``GROUP=``; check_skills uses it to fail when a skill is in no family, so
the guide users read and the groups they install cannot drift apart.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CATALOG = REPO_ROOT / "docs" / "catalog.md"

GROUP_HEADING = re.compile(r"^#{2,4}\s.*`GROUP=([a-z0-9-]+)`")
OTHER_HEADING = re.compile(r"^#{1,4}\s")
SKILL_ROW = re.compile(r"^\|\s*`([a-z0-9-]+)`\s*\|")


def groups(path: Path = CATALOG) -> dict[str, list[str]]:
    """Map each group name to its skills, in catalog order."""
    found: dict[str, list[str]] = {}
    current = None
    if not path.is_file():
        return found
    for line in path.read_text(encoding="utf-8").splitlines():
        heading = GROUP_HEADING.match(line)
        if heading:
            current = heading.group(1)
            found.setdefault(current, [])
        elif OTHER_HEADING.match(line):
            current = None
        elif current:
            row = SKILL_ROW.match(line)
            if row:
                found[current].append(row.group(1))
    return found
