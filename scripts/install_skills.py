#!/usr/bin/env python3
"""Symlink this repo's skills into the user-level skill directories of
Claude Code, Codex, and Copilot, so one clone serves all three agents in
every project.

Each agent reads personal skills from its own home directory:

    Claude Code   ~/.claude/skills/
    Codex         ~/.codex/skills/
    Copilot CLI   ~/.copilot/skills/

All three consume the same SKILL.md format, so instead of copying we create
one symlink per skill (``~/.claude/skills/<name> -> <repo>/skills/<name>``).
A ``git pull`` in the clone updates every agent at once, and skills from
other sources can coexist alongside ours.

Safety rules:
- never touch an entry we didn't create: anything that is not a symlink
  into this repo's ``skills/`` is skipped with a warning;
- ``--uninstall`` removes only symlinks that point into this repo.

Run via ``task install:skills`` / ``task uninstall:skills``.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"

AGENT_DIRS = {
    "claude": Path.home() / ".claude" / "skills",
    "codex": Path.home() / ".codex" / "skills",
    "copilot": Path.home() / ".copilot" / "skills",
}


def repo_skills() -> list[Path]:
    return sorted(
        d for d in SKILLS_DIR.iterdir() if d.is_dir() and (d / "SKILL.md").is_file()
    )


def points_into_repo(link: Path) -> bool:
    try:
        return link.is_symlink() and link.resolve().is_relative_to(SKILLS_DIR)
    except OSError:
        return False


def install(agents: list[str]) -> int:
    warnings = 0
    for agent in agents:
        target_dir = AGENT_DIRS[agent]
        target_dir.mkdir(parents=True, exist_ok=True)
        for skill in repo_skills():
            link = target_dir / skill.name
            if points_into_repo(link):
                link.unlink()  # re-link in case the clone moved
            elif link.exists() or link.is_symlink():
                print(f"WARN  {link}: exists and is not ours - skipped")
                warnings += 1
                continue
            link.symlink_to(skill)
            print(f"ok    {link} -> {skill}")
    return warnings


def uninstall(agents: list[str]) -> int:
    for agent in agents:
        target_dir = AGENT_DIRS[agent]
        if not target_dir.is_dir():
            continue
        for link in sorted(target_dir.iterdir()):
            if points_into_repo(link):
                link.unlink()
                print(f"removed  {link}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--uninstall", action="store_true")
    parser.add_argument(
        "--agents",
        default=",".join(AGENT_DIRS),
        help=f"comma-separated subset of: {', '.join(AGENT_DIRS)}",
    )
    args = parser.parse_args()

    agents = [a.strip() for a in args.agents.split(",") if a.strip()]
    unknown = [a for a in agents if a not in AGENT_DIRS]
    if unknown:
        print(f"unknown agent(s): {', '.join(unknown)}", file=sys.stderr)
        return 1

    if args.uninstall:
        return uninstall(agents)
    warnings = install(agents)
    if warnings:
        print(f"\n{warnings} entr{'y' if warnings == 1 else 'ies'} skipped (see WARN above)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
