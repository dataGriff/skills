# Creating skills

Skills live in `skills/<name>/` with a required `SKILL.md`. Scaffold one with:

```bash
task new:skill NAME=my-skill
```

## Anatomy

```
skills/my-skill/
├── SKILL.md          required: frontmatter + instructions
├── references/       docs loaded into context only when needed
├── scripts/          executable helpers (can run without being read)
└── assets/           templates, fonts, icons used in output
```

## Progressive disclosure

Skills load in three levels, and the budgets exist because each level has a
different context cost:

1. **Metadata** (`name` + `description`) — in context for *every*
   conversation, so keep it ~100 words.
2. **SKILL.md body** — loaded whole when the skill triggers. Keep it under
   500 lines; route detail to `references/`.
3. **Bundled resources** — unlimited; loaded (or executed) only on demand.

## Frontmatter rules

- `name`: lowercase-hyphenated, must equal the directory name.
- `description`: the *only* triggering mechanism. State what the skill does
  AND when to use it, explicitly ("Use when the user…"). Claude tends to
  under-trigger skills, so be a little pushy: enumerate the phrases and
  situations that should trigger it. Max 1024 characters.

## Writing style

- Imperative voice. Explain *why* a rule matters instead of stacking MUSTs —
  models follow reasoning better than decrees.
- Generalise: a skill gets used across thousands of prompts, so avoid
  overfitting instructions to one example.
- If several tasks would each rewrite the same helper, bundle it once in
  `scripts/` and point to it.
- Reference files over 300 lines get a table of contents near the top.

## Validation

`task check:skills` enforces the structural rules above and
`task check:context` enforces the size budgets; both run in every commit
hook and in CI. Fix errors by moving content deeper (into `references/`),
not by deleting guidance the skill needs.
