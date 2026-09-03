#!/usr/bin/env python3
"""Enforce context-size budgets on the files agents load first.

The fanout docs style only works if the always-loaded layer stays small:
README.md and AGENTS.md route to docs/index.md, which routes onward. This
script fails the build when any routing file grows past its budget, and when
CLAUDE.md stops being a pure @AGENTS.md include.

Token counts are estimated as chars/4 — coarse, but stable and dependency-free.
Run via `task check:context`.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# (path, max_lines, max_estimated_tokens)
BUDGETS: list[tuple[str, int, int]] = [
    ("README.md", 60, 600),
    ("AGENTS.md", 60, 800),
    ("docs/index.md", 100, 1200),
]

# Every doc reachable from the fanout should individually stay readable in one
# sitting; past this an agent burns context on detail it may not need.
DOCS_MAX_LINES = 300
SKILL_MD_MAX_TOKENS = 5000

# Skill frontmatter (name + description) is injected into *every* conversation
# once the suite is installed, so the always-on cost grows linearly with skill
# count even when no skill triggers. Budget the total across the suite, not
# just each file: hitting this ceiling means tightening descriptions or
# splitting the suite into separately installable groups.
SUITE_METADATA_MAX_TOKENS = 3500


def estimate_tokens(text: str) -> int:
    return len(text) // 4


def frontmatter(text: str) -> str:
    """Return the YAML frontmatter block, without the --- fences."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return ""
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return "\n".join(lines[1:i])
    return ""


def main() -> int:
    errors: list[str] = []

    for rel_path, max_lines, max_tokens in BUDGETS:
        path = REPO_ROOT / rel_path
        if not path.is_file():
            errors.append(f"{rel_path}: missing — the fanout routing depends on it")
            continue
        text = path.read_text(encoding="utf-8")
        n_lines = len(text.splitlines())
        n_tokens = estimate_tokens(text)
        if n_lines > max_lines:
            errors.append(
                f"{rel_path}: {n_lines} lines (budget {max_lines}). This file is "
                "loaded early by every agent — move detail into docs/ and link to it."
            )
        if n_tokens > max_tokens:
            errors.append(
                f"{rel_path}: ~{n_tokens} tokens (budget {max_tokens}). Trim it; "
                "route detail deeper into the fanout."
            )

    # CLAUDE.md must stay a pure include so AGENTS.md is the single source.
    claude_md = REPO_ROOT / "CLAUDE.md"
    if not claude_md.is_file():
        errors.append("CLAUDE.md: missing — it should contain exactly '@AGENTS.md'")
    elif claude_md.read_text(encoding="utf-8").strip() != "@AGENTS.md":
        errors.append(
            "CLAUDE.md: must contain exactly '@AGENTS.md' and nothing else. "
            "Agent guidance belongs in AGENTS.md; docs belong in docs/."
        )

    # Fanned-out docs each stay digestible.
    docs_dir = REPO_ROOT / "docs"
    if docs_dir.is_dir():
        for doc in sorted(docs_dir.rglob("*.md")):
            rel = doc.relative_to(REPO_ROOT)
            if str(rel) == "docs/index.md":
                continue  # budgeted above
            n_lines = len(doc.read_text(encoding="utf-8").splitlines())
            if n_lines > DOCS_MAX_LINES:
                errors.append(
                    f"{rel}: {n_lines} lines (budget {DOCS_MAX_LINES}). Split it "
                    "and route from docs/index.md."
                )

    # SKILL.md bodies load whole when a skill triggers — keep the token cost sane.
    skills_dir = REPO_ROOT / "skills"
    if skills_dir.is_dir():
        metadata_tokens = 0
        for skill_md in sorted(skills_dir.glob("*/SKILL.md")):
            rel = skill_md.relative_to(REPO_ROOT)
            text = skill_md.read_text(encoding="utf-8")
            metadata_tokens += estimate_tokens(frontmatter(text))
            n_tokens = estimate_tokens(text)
            if n_tokens > SKILL_MD_MAX_TOKENS:
                errors.append(
                    f"{rel}: ~{n_tokens} tokens (budget {SKILL_MD_MAX_TOKENS}). "
                    "Move detail into the skill's references/ directory."
                )
        if metadata_tokens > SUITE_METADATA_MAX_TOKENS:
            errors.append(
                f"skills/*/SKILL.md frontmatter totals ~{metadata_tokens} tokens "
                f"(budget {SUITE_METADATA_MAX_TOKENS}). Every installed skill's "
                "name + description is loaded into every conversation, whether or "
                "not the skill triggers. Tighten the wordiest descriptions, or "
                "split the suite into separately installable groups "
                "(task install:skills SKILLS=...)."
            )

    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        print(f"\ncheck_context: {len(errors)} error(s).")
        return 1
    print("check_context: all context-size budgets respected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
