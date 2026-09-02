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

## Cost discipline

A skill is paid for on every trigger, so cost is a design input. What the
`gherkin-feature-authoring` evals showed, turned into rules:

- **Unconditional loads are the cost driver, not file size.** "Start from
  the template", "read style.md before writing", "walk the checklist" each
  add a tool turn per use; three of them doubled time and tokens for no
  score change. `task check:skills` warns on that phrasing. Put the rules
  that change outcomes in SKILL.md with a short inline example, and make
  every reference opt-in with an explicit "open when …" condition.
- **Measure turns, not just tokens.** `latest-results.md` shows turns per
  arm and the with-skill/baseline token ratio. A with-skill run should sit
  within one or two turns of the baseline; more means it loaded files it
  didn't need.
- **A check both arms pass measures nothing.** The results file reports how
  many grader checks separated the arms. If none did, the delta is noise:
  either the grader needs behavioural checks, or the skill isn't earning
  its cost on that model.
- **Pin the model and record it.** `MODEL=` pins both arms; served models
  appear in the results header. Runs on different or unknown models are
  not comparable.
- **The description is paid for in every conversation.** Keep it to the
  capability and the trigger phrases.

## Validation

`task check:skills` enforces the structural rules above and
`task check:context` enforces the size budgets; both run in every commit
hook and in CI. Fix errors by moving content deeper (into `references/`),
not by deleting guidance the skill needs.

## Evals (effectiveness, not structure)

Structural checks can't tell whether a skill actually helps. For that, give
a skill an `evals/` directory (`evals.json` with realistic prompts,
optional `fixtures/` and a `grade.py`) and run:

```bash
task eval:skills NAME=my-skill   # or omit NAME for all skills with evals
```

Each prompt runs twice through headless `claude -p` — once following the
skill, once without — into the gitignored `.evals/` directory; `grade.py`
scores both arms so you can compare pass rate, and the run metadata gives
time and cost per task. The runner also refreshes the skill's
`evals/latest-results.md` — a small **committed** summary table, so a PR
that touches a skill carries its eval evidence in the diff by default:
run the evals, commit the refreshed results file with the change. The PR
template asks for the results table in the description, and CI posts each
changed skill's `latest-results.md` as a sticky PR comment — flagging skills
changed without refreshed results (see [ci.md](ci.md)). Evals
cost tokens, take minutes, and are non-deterministic, so they are
deliberately **not** part of `task ci`. Run them when:

- **creating a skill** — to prove it beats the no-skill baseline at all;
- **meaningfully editing one** — changed workflow, rewritten guidance, new
  references (typo fixes don't need a re-run);
- **the world changes underneath it** — a new version of the tool or spec
  the skill wraps (pair with re-verifying references against the live tool);
- **triggering feels off** — though description/trigger tuning needs its
  own eval type (should/shouldn't-trigger prompts), not these output evals.
