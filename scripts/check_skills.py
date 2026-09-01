#!/usr/bin/env python3
"""Validate every skill in skills/ against skill best practices.

Checks (per skill):
- SKILL.md exists
- YAML frontmatter present with non-empty `name` and `description`
- `name` matches the directory name and is lowercase-hyphenated
- description states BOTH what the skill does and when to use it (heuristic:
  contains a trigger cue like "use when", "use this", "trigger", "whenever")
- description fits in the metadata budget (<= 1024 characters)
- SKILL.md body stays within the progressive-disclosure budget (<= 500 lines)
- relative file paths referenced from SKILL.md actually exist
- large reference files (> 300 lines) carry a table of contents (warning only)

Exit code 1 on any error; warnings do not fail the run.
Run via `task check:skills` — do not invoke ad hoc variants of these checks.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"

MAX_SKILL_MD_LINES = 500
MAX_DESCRIPTION_CHARS = 1024
REFERENCE_TOC_THRESHOLD_LINES = 300

TRIGGER_CUES = (
    "use when",
    "use this",
    "use it when",
    "trigger",
    "whenever",
    "when the user",
    "when a user",
    "when you",
    "when asked",
)

NAME_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
# Relative paths mentioned in SKILL.md, e.g. references/foo.md or scripts/run.py
REFERENCED_PATH_PATTERN = re.compile(
    r"(?:\]\(|`|\s)((?:references|scripts|assets)/[A-Za-z0-9_\-./]+)"
)


def parse_frontmatter(text: str) -> dict[str, str] | None:
    """Minimal YAML frontmatter parser (flat key: value pairs only)."""
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    block = text[3:end]
    fields: dict[str, str] = {}
    current_key = None
    for line in block.splitlines():
        if not line.strip():
            continue
        match = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*):\s*(.*)$", line)
        if match:
            current_key = match.group(1)
            fields[current_key] = match.group(2).strip().strip("\"'")
        elif current_key and line.startswith((" ", "\t")):
            # continuation line of a folded/multi-line value
            fields[current_key] += " " + line.strip().strip("\"'")
    return fields


def check_skill(skill_dir: Path, errors: list[str], warnings: list[str]) -> None:
    rel = skill_dir.relative_to(REPO_ROOT)
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        errors.append(f"{rel}: missing SKILL.md")
        return

    text = skill_md.read_text(encoding="utf-8")
    lines = text.splitlines()

    if len(lines) > MAX_SKILL_MD_LINES:
        errors.append(
            f"{rel}/SKILL.md: {len(lines)} lines exceeds the {MAX_SKILL_MD_LINES}-line "
            "budget. Move detail into references/ and route to it from SKILL.md."
        )

    fm = parse_frontmatter(text)
    if fm is None:
        errors.append(f"{rel}/SKILL.md: missing YAML frontmatter (--- block)")
    else:
        name = fm.get("name", "")
        description = fm.get("description", "")

        if not name:
            errors.append(f"{rel}/SKILL.md: frontmatter missing `name`")
        else:
            if not NAME_PATTERN.match(name):
                errors.append(
                    f"{rel}/SKILL.md: name '{name}' must be lowercase-hyphenated"
                )
            if name != skill_dir.name:
                errors.append(
                    f"{rel}/SKILL.md: name '{name}' does not match directory "
                    f"'{skill_dir.name}'"
                )

        if not description:
            errors.append(f"{rel}/SKILL.md: frontmatter missing `description`")
        else:
            if len(description) > MAX_DESCRIPTION_CHARS:
                errors.append(
                    f"{rel}/SKILL.md: description is {len(description)} chars "
                    f"(max {MAX_DESCRIPTION_CHARS}). It loads into every "
                    "conversation's context — keep it tight."
                )
            lowered = description.lower()
            if not any(cue in lowered for cue in TRIGGER_CUES):
                errors.append(
                    f"{rel}/SKILL.md: description says what the skill does but "
                    "not when to use it. Add explicit trigger context "
                    "(e.g. 'Use when ...') — the description is the only "
                    "triggering mechanism."
                )

    # Referenced files must exist.
    for match in REFERENCED_PATH_PATTERN.finditer(text):
        ref = match.group(1).rstrip(".")
        if not (skill_dir / ref).exists():
            errors.append(f"{rel}/SKILL.md: references '{ref}' which does not exist")

    # Large reference docs should carry a table of contents.
    refs_dir = skill_dir / "references"
    if refs_dir.is_dir():
        for ref_file in sorted(refs_dir.rglob("*.md")):
            ref_lines = ref_file.read_text(encoding="utf-8").splitlines()
            if len(ref_lines) > REFERENCE_TOC_THRESHOLD_LINES:
                head = "\n".join(ref_lines[:40]).lower()
                if "contents" not in head:
                    warnings.append(
                        f"{ref_file.relative_to(REPO_ROOT)}: {len(ref_lines)} lines "
                        "with no table of contents near the top — add one so agents "
                        "can jump instead of reading it all."
                    )


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    if not SKILLS_DIR.is_dir():
        print("check_skills: no skills/ directory found — nothing to check.")
        return 0

    skill_dirs = sorted(p for p in SKILLS_DIR.iterdir() if p.is_dir())
    if not skill_dirs:
        print("check_skills: skills/ is empty — nothing to check.")
        return 0

    for skill_dir in skill_dirs:
        check_skill(skill_dir, errors, warnings)

    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}")

    if errors:
        print(f"\ncheck_skills: {len(errors)} error(s) in {len(skill_dirs)} skill(s).")
        return 1
    print(
        f"check_skills: {len(skill_dirs)} skill(s) pass best-practice checks"
        + (f" ({len(warnings)} warning(s))." if warnings else ".")
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
