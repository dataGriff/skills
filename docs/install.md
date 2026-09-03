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
task install:skills                    # all skills, all three agents
task install:skills AGENTS=claude      # or a subset of agents
task install:skills SKILLS=odcs-authoring,datacontract-cli   # or of skills
task uninstall:skills                  # remove our symlinks, nothing else
task uninstall:skills SKILLS=api-mocking-microcks            # just one
```

Prefer `SKILLS=` subsets on machines that only need one group of skills:
every installed skill's name + description is loaded into every
conversation, whether or not the skill triggers, so installing less costs
less in every session.

This links each `skills/<name>` into `~/.claude/skills/`, `~/.codex/skills/`
and `~/.copilot/skills/`, one symlink per skill, so they coexist with skills
from other sources. The installer never touches entries it didn't create:
anything that isn't a symlink into this clone is skipped with a warning, and
uninstall removes only links pointing here.

## Claude Code without cloning (plugin marketplace)

`.claude-plugin/marketplace.json` makes this repo a Claude Code plugin
marketplace whose single plugin is the repo itself (`source: "./"` with
`strict: false`), so the canonical `skills/` directory doubles as the
plugin's skills directory — still no duplication, and a new skill ships
in the plugin with no manifest edit. Users install straight from GitHub:

```
/plugin marketplace add dataGriff/skills
/plugin install datagriff-skills@datagriff
```

Updates arrive with `/plugin marketplace update datagriff`. This route is
Claude-only — Codex and Copilot have no marketplace equivalent, so they use
the symlink installs above. After editing the manifest, check it with
`claude plugin validate .`.

## Caveats

- **Windows**: git creates the committed symlinks only with
  `core.symlinks=true` and Developer Mode (or admin) enabled; otherwise they
  check out as plain text files. `task install:skills` also creates
  symlinks and needs the same Developer Mode (or admin) privileges, or it
  errors out per-entry instead of installing. WSL works out of the box.
- **Moved clone**: re-run `task install:skills` after moving the clone —
  it re-points stale links automatically.
