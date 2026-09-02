#!/usr/bin/env python3
"""Aggregate eval evidence for changed skills into PR-ready markdown.

Usage (via the Taskfile — the canonical entrypoint):
    task pr:eval-summary [BASE=origin/main]

For every skill with files changed between BASE and HEAD, prints the
skill's committed evals/latest-results.md, prefixed with a warning when
the results file was not refreshed in the same diff or the skill defines
no evals at all. CI runs this on pull requests and posts the output as a
sticky PR comment; run it locally to preview what reviewers will see.
Prints nothing (exit 0) when no skill changed.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def changed_files(base: str) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", f"{base}...HEAD"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=True,
    )
    return [line for line in result.stdout.splitlines() if line]


def main() -> int:
    base = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] else "origin/main"
    try:
        files = changed_files(base)
    except subprocess.CalledProcessError as exc:
        print(
            f"pr_eval_summary: cannot diff against '{base}' "
            f"(fetch it first): {exc.stderr.strip()}",
            file=sys.stderr,
        )
        return 2

    skills = sorted(
        {
            parts[1]
            for f in files
            if (parts := f.split("/"))[0] == "skills" and len(parts) > 2
        }
    )
    if not skills:
        return 0

    print("## Eval evidence\n")
    for name in skills:
        results_rel = f"skills/{name}/evals/latest-results.md"
        results = REPO_ROOT / results_rel
        print(f"### {name}\n")
        if not results.is_file():
            print(
                f"⚠️ `skills/{name}/` changed but defines no evals — "
                "see docs/skills.md for when a skill needs them.\n"
            )
            continue
        if results_rel not in files:
            print(
                f"⚠️ Skill changed but `{results_rel}` was not refreshed in "
                f"this diff — rerun `task eval:skills NAME={name}` unless the "
                "change is typo-level (docs/skills.md says which edits need a "
                "re-run).\n"
            )
        body = results.read_text(encoding="utf-8").splitlines()
        if body and body[0].startswith("# "):
            body = body[1:]  # own heading printed above
        print("\n".join(body).strip() + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
