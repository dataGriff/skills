# Guardrail checks: design and skeletons

Checks exist to stop the structure regressing after you leave. Three
families:

## 1. Context-size checks

Fail the build when the always-loaded layer grows. Check:

- AGENTS.md against ~150 lines / ~2000 estimated tokens (chars/4 is a
  fine, dependency-free estimate); README.md against ~60 / ~600;
  docs/index.md against ~100 / ~1000.
- `CLAUDE.md` content is exactly `@AGENTS.md`.
- Each `docs/*.md` topic file under a per-file line budget (~300).
- For skills repos: each SKILL.md under ~500 lines / ~5000 tokens.

Error messages should teach the fix: "move detail into a routed doc", not
just "too long".

Print a **cold-start report** on every run, pass or fail: tokens for the
always-loaded layer (AGENTS.md via CLAUDE.md) against its target, then the
fallback hop (docs/index.md) and each topic doc so the reader can see what
one specialised task costs. A budget only speaks when it trips; the report
makes a creeping cost visible in every hook and CI run, and gives the
before/after numbers the skill's verify step asks for.

## 2. Routing checks

The fanout only works if the routes are taken. Check:

- Every line in AGENTS.md or docs/index.md that links a `.md` file is an
  explicit route: it contains a read cue (`read|open|load|follow`) and a
  trigger cue (`before|when|if|whenever|unless|first|any task`). A bare
  link or "see also" fails, with a message showing the template
  ("Before you <do X>, read <doc> — <what it holds>").
- Every `docs/*.md` topic doc is linked from AGENTS.md or docs/index.md
  (unrouted = invisible).
- Relative links in AGENTS.md, README.md and docs/ resolve.

## 3. Convention checks

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

For other repos, encode whatever the docs promise: every Taskfile task has
a `desc:`, generated files are not hand-edited, etc. A convention that
isn't checked is a suggestion.

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
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
AGENTS_MAX_LINES = 150  # budget: raise only with a reason in the commit message
AGENTS_MAX_TOKENS = 2000
MD_LINK = re.compile(r"\]\(([^)\s#]+\.md)\)")
READ_CUE = re.compile(r"\b(read|open|load|follow)\b", re.I)
TRIGGER_CUE = re.compile(r"\b(before|when|if|whenever|unless|first|any task)\b", re.I)

def soft_routes(path: Path) -> list[str]:
    """Lines that link a doc without saying when to read it."""
    return [line for line in path.read_text().splitlines()
            if MD_LINK.search(line) and not (READ_CUE.search(line) and TRIGGER_CUE.search(line))]

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
