# Installing the skills

Claude Code, Codex, and GitHub Copilot all consume the same Agent Skills
format this repo already uses (`skills/<name>/SKILL.md`), so there is one
canonical copy of every skill and everything else is a symlink. Nothing is
duplicated; a `git pull` updates every agent at once.

## In this repo (committed symlinks)

Each tool discovers project skills in its own directory, so the repo carries
two symlinks to the canonical `skills/`:

| Symlink                     | Served agents                                    |
| --------------------------- | ------------------------------------------------ |
| `.claude/skills -> ../skills` | Claude Code, and Copilot (it reads `.claude/skills` automatically) |
| `.codex/skills -> ../skills`  | Codex (it only reads `.codex` paths; symlinks are supported) |

Open this repo in any of the three tools and the skills are available with
no install step. `.agents/skills` (the emerging cross-agent location) is
deliberately absent: Copilot already finds `.claude/skills`, and a second
discovery path risks double-loading.

## In every project (user-level install)

To use the skills from *any* project, symlink them into each agent's
personal skills directory:

```bash
task install:skills                    # all three agents
task install:skills AGENTS=claude      # or a subset
task uninstall:skills                  # remove our symlinks, nothing else
```

This links each `skills/<name>` into `~/.claude/skills/`, `~/.codex/skills/`
and `~/.copilot/skills/`, one symlink per skill, so they coexist with skills
from other sources. The installer never touches entries it didn't create:
anything that isn't a symlink into this clone is skipped with a warning, and
uninstall removes only links pointing here.

## Caveats

- **Windows**: git creates the committed symlinks only with
  `core.symlinks=true` and Developer Mode (or admin) enabled; otherwise they
  check out as plain text files. WSL works out of the box.
- **Moved clone**: re-run `task install:skills` after moving the clone —
  it re-points stale links automatically.
