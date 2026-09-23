# Contributing

## Setup

```bash
mise install     # task and python, pinned in mise.toml
task setup       # git hooks
task --list      # every command
```

No mise (sandbox, fresh container)? `scripts/bootstrap.sh` installs `task`.

## Workflow

1. Branch from `main`.
2. New skill: `task new:skill NAME=my-skill`, then follow the conventions
   in [docs/skills.md](docs/skills.md) (frontmatter, budgets, opt-in
   references, evals).
3. `task check` runs on commit (skill best practices, context budgets,
   `cbi validate`); `task ci` on push.
4. Meaningful skill edits: run `task eval:skills NAME=<skill>` and commit
   the refreshed `evals/latest-results.md`; the PR template asks for it.
5. Open a pull request.

Where content belongs (this file, `docs/`, a skill's `references/`) is
decided by [docs/docs-style.md](docs/docs-style.md).
