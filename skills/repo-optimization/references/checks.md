# Guardrail checks: design and skeletons

Checks exist to stop the structure regressing after you leave. Two families:

## 1. Context-size checks

Fail the build when the always-loaded layer grows. Check:

- README.md, AGENTS.md, docs/index.md against line + estimated-token
  budgets (chars/4 is a fine, dependency-free token estimate).
- `CLAUDE.md` content is exactly `@AGENTS.md`.
- Each `docs/*.md` topic file under a per-file line budget (~300).
- For skills repos: each SKILL.md under ~500 lines / ~5000 tokens.

Error messages should teach the fix: "move detail deeper into the fanout",
not just "too long".

## 2. Convention checks

Repo-specific structure rules. For a skills repo:

- every `skills/*/` has a SKILL.md with frontmatter
- frontmatter has non-empty `name` (lowercase-hyphenated, equals the
  directory name) and `description` (≤1024 chars; states capability first,
  then explicit trigger context — cues like "use when"/"whenever")
- relative paths mentioned in SKILL.md (`references/…`, `scripts/…`) exist
- no orphaned bundled files: everything under `references/`, `scripts/`,
  `assets/` is mentioned in SKILL.md or a reference doc (unrouted = invisible)
- relative markdown links inside reference docs resolve
- reference files >300 lines carry a table of contents (warning, not error)

Deterministic checks are a floor, not a certification: content freshness
belongs in a periodic job (re-verify against the live tools), and
effectiveness/triggering quality only show up in evals.

For other repos, encode whatever the docs promise: every topic doc has a
route row in docs/index.md, every Taskfile task has a `desc:`, etc. A
convention that isn't checked is a suggestion.

## Script design rules

- **Stdlib only.** Checks must run on a bare pinned python — no dependency
  install step before the pre-commit hook can run.
- **Budgets are named constants at the top of the file**, changed
  deliberately in a reviewed commit, never bypassed.
- **Warnings vs errors**: structural violations fail (exit 1); style
  suggestions warn. A check that cries wolf gets `--no-verify`'d.
- **Wire into the aggregate**: each script gets a `check:<name>` task, added
  to the `check` chain, so hooks and CI pick it up with no extra wiring.

## Skeleton

```python
#!/usr/bin/env python3
"""One-line purpose. Run via `task check:<name>`."""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MAX_LINES = 60  # budget: raise only with a reason in the commit message

def main() -> int:
    errors: list[str] = []
    # ... append "path: problem. How to fix it." strings ...
    for e in errors:
        print(f"ERROR: {e}")
    return 1 if errors else 0

if __name__ == "__main__":
    sys.exit(main())
```

Working full implementations to copy from: `scripts/check_skills.py` and
`scripts/check_context.py` in the repository this skill ships in
(github.com/dataGriff/skills).
