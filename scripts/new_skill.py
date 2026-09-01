#!/usr/bin/env python3
"""Scaffold a new skill under skills/<name>/.

Usage (via the Taskfile — the canonical entrypoint):
    task new:skill NAME=my-skill

Creates skills/<name>/SKILL.md with valid frontmatter plus an empty
references/ directory, ready to pass `task check`after the description
placeholders are filled in.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

TEMPLATE = """\
---
name: {name}
description: >-
  TODO - one or two sentences on what this skill does, then explicit trigger
  context. Use when TODO (name the user phrases and situations that should
  trigger this skill).
---

# {title}

TODO: imperative instructions for the agent. Keep this file under 500 lines;
put deep detail in references/ and tell the reader exactly when to open each
file.

## Workflow

1. TODO
2. TODO

## References

- `references/` — add focused docs here and route to them from this section.
"""


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: task new:skill NAME=my-skill", file=sys.stderr)
        return 2

    name = sys.argv[1]
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name):
        print(
            f"new_skill: '{name}' must be lowercase-hyphenated (e.g. pdf-tools)",
            file=sys.stderr,
        )
        return 2

    skill_dir = REPO_ROOT / "skills" / name
    if skill_dir.exists():
        print(f"new_skill: skills/{name}/ already exists", file=sys.stderr)
        return 1

    (skill_dir / "references").mkdir(parents=True)
    (skill_dir / "references" / ".gitkeep").touch()
    title = name.replace("-", " ").title()
    (skill_dir / "SKILL.md").write_text(
        TEMPLATE.format(name=name, title=title), encoding="utf-8"
    )

    print(f"Created skills/{name}/SKILL.md")
    print("Next: fill in the description TODOs, then run `task check`.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
