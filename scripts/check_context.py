#!/usr/bin/env python3
"""Enforce context-size budgets and routing rules on the files agents load first.

AGENTS.md is the working layer: it carries what most tasks need, within a
budget set by how many rules a model follows reliably, and routes the rest
to docs/ with explicit "before you X, read Y" instructions. This script
fails the build when a routing file grows past its budget, when CLAUDE.md
stops being a pure @AGENTS.md include, when a route is soft (a doc link
with no trigger or no "read"), or when a topic doc has no route at all.

Token counts are estimated as chars/4 — coarse, but stable and dependency-free.
Run via `task check:context`.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# (path, max_lines, max_estimated_tokens)
# AGENTS.md is prompt-cached, so its tokens are cheap per turn, and every
# routing hop costs a tool turn — so it carries what most tasks need. The
# ceiling is rule count, not size: past ~150 lines (40-60 rules) models
# start dropping rules, so the overflow routes to docs/.
BUDGETS: list[tuple[str, int, int]] = [
    ("README.md", 60, 600),
    ("AGENTS.md", 150, 2000),
    ("docs/README.md", 100, 1000),
]

# docs/README.md (not index.md) so the repo UI renders the map in place.
# A route is followed only when the line names its trigger and says
# "read". "See docs/ci.md" is decoration that agents skip.
ROUTING_FILES = ["AGENTS.md", "docs/README.md"]
DOC_LINK = re.compile(r"\]\(([^)\s#]+\.md)\)")
READ_CUE = re.compile(r"\b(read|open|load|follow)\b", re.I)
TRIGGER_CUE = re.compile(r"\b(before|when|if|whenever|unless|first|any task)\b", re.I)

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

# Reported every run so drift is visible before a per-file budget trips;
# only the per-file budgets above fail the build.
ALWAYS_LOADED_TARGET_TOKENS = 2000


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


def print_cold_start_report() -> None:
    """Show the token cost of orienting in this repo, layer by layer.

    Layer 0 is loaded into every session (CLAUDE.md expands to AGENTS.md)
    and should cover most tasks on its own; layer 1 is the fallback hop for
    tasks it does not cover; layer 2 lists each topic doc so the reader can
    see what one specialised task's route costs. Numbers, not pass/fail:
    the point is to make a cost change visible in the run output."""
    def tokens_of(rel: str) -> int:
        path = REPO_ROOT / rel
        return estimate_tokens(path.read_text(encoding="utf-8")) if path.is_file() else 0

    always = tokens_of("AGENTS.md")
    hop = tokens_of("docs/README.md")
    print("check_context: cold-start report (est. tokens, chars/4)")
    print(f"  always loaded  AGENTS.md (via CLAUDE.md)   {always:>6}  (target <= {ALWAYS_LOADED_TARGET_TOKENS})")
    print(f"  fallback hop   docs/README.md               {hop:>6}  (uncovered tasks only)")
    print(f"  uncovered task AGENTS.md + docs/README.md   {always + hop:>6}")
    docs_dir = REPO_ROOT / "docs"
    if docs_dir.is_dir():
        for doc in sorted(docs_dir.rglob("*.md")):
            rel = doc.relative_to(REPO_ROOT)
            if str(rel) == "docs/README.md":
                continue
            print(f"  topic doc      {str(rel):<28}{tokens_of(str(rel)):>6}")
    if always > ALWAYS_LOADED_TARGET_TOKENS:
        print(
            f"  note: AGENTS.md costs more than {ALWAYS_LOADED_TARGET_TOKENS} tokens on "
            "every task; move the content serving the fewest tasks into a routed doc."
        )


def check_routes(errors: list[str]) -> None:
    """Every doc link in a routing file is an explicit route, every topic
    doc has one, and every relative link resolves."""
    routed: set[Path] = set()
    for rel in ROUTING_FILES:
        path = REPO_ROOT / rel
        if not path.is_file():
            continue  # reported by the budget loop
        for line in path.read_text(encoding="utf-8").splitlines():
            targets = DOC_LINK.findall(line)
            if not targets:
                continue
            for target in targets:
                routed.add((path.parent / target).resolve())
            if not (READ_CUE.search(line) and TRIGGER_CUE.search(line)):
                errors.append(
                    f"{rel}: soft route \"{line.strip()[:70]}\". A route agents follow "
                    "names its trigger and says read: 'Before you <do X>, read "
                    "<doc> - <what it holds>'."
                )
    docs_dir = REPO_ROOT / "docs"
    if docs_dir.is_dir():
        for doc in sorted(docs_dir.rglob("*.md")):
            if doc.name == "README.md" or doc.resolve() in routed:
                continue
            errors.append(
                f"{doc.relative_to(REPO_ROOT)}: no route from AGENTS.md or "
                "docs/README.md. An unrouted doc is invisible to agents - add a "
                "'when you ..., read ...' row."
            )
    for md in [REPO_ROOT / "AGENTS.md", REPO_ROOT / "README.md"] + (
        sorted(docs_dir.rglob("*.md")) if docs_dir.is_dir() else []
    ):
        if not md.is_file():
            continue
        for target in re.findall(r"\]\(([^)\s#]+)\)", md.read_text(encoding="utf-8")):
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            if not (md.parent / target).exists():
                errors.append(
                    f"{md.relative_to(REPO_ROOT)}: link to {target} does not "
                    "resolve - a route to nowhere."
                )


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
            if str(rel) == "docs/README.md":
                continue  # budgeted above
            n_lines = len(doc.read_text(encoding="utf-8").splitlines())
            if n_lines > DOCS_MAX_LINES:
                errors.append(
                    f"{rel}: {n_lines} lines (budget {DOCS_MAX_LINES}). Split it "
                    "and route from docs/README.md."
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

    check_routes(errors)
    print_cold_start_report()

    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        print(f"\ncheck_context: {len(errors)} error(s).")
        return 1
    print("check_context: all context-size budgets respected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
