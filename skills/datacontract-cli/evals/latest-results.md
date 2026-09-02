# Eval results: datacontract-cli

Last run: 20260902-202100 UTC via `task eval:skills NAME=datacontract-cli MODEL=claude-sonnet-5` (commit this file with the skill change so the PR carries the evidence).

Models served: claude-haiku-4-5-20251001, claude-sonnet-5.

| Eval | With skill | Baseline | Turns (skill/base) | Time (skill/base) | Cost (skill/base) |
|------|-----------|----------|--------------------|-------------------|-------------------|
| snowflake-ci-guidance | 5/5 | 5/5 | 9 / 11 | 60.9s / 172.5s | $0.21 / $0.34 |
| ddl-to-contract-pipeline | 5/5 | 5/5 | 17 / 12 | 61.5s / 52.7s | $0.25 / $0.21 |

Grader checks that separated the arms: snowflake-ci-guidance 0/5, ddl-to-contract-pipeline 0/5. A check both arms always pass measures nothing; a score delta with none separating is noise.
Token cost, with skill / baseline: 1.01x. Turns above the baseline usually mean SKILL.md loads bundled files unconditionally.

Full outputs (gitignored): `.evals/datacontract-cli/20260902-202100/`.

## Notes: cost slimming attempted and reverted (2026-09-02)

**Harness finding first.** This skill's evals had never actually run in
the `task eval:skills` harness: headless `claude -p` under `acceptEdits`
blocks every shell command, so both arms stalled asking for approval to
run even `datacontract --version`, burned 18–30 turns, and produced no
files (0/5 each). Fixed by letting `evals.json` declare
`"allowed_tools": ["Bash(datacontract *)"]`. The table above is the first
valid measurement of the committed SKILL.md on this harness.

**The skill is already lean.** Its reference pointers are conditional
(passes both layers of the load gate) and it sits at 1.01× the baseline's
tokens. The mix matters: on the Snowflake task the skill is faster and
cheaper (9 vs 11 turns, 61s vs 173s, $0.21 vs $0.34 — the baseline dug
through the installed CLI's source to find the key-pair env vars); on the
pipeline task it costs 5 more turns (17 vs 12).

**Slimming attempt, reverted.** Inlining the common credential env vars,
export/import format lists, and CI snippet (4.7k → 6.2k chars, no
mandatory loads) measured *worse* on one sample each: Snowflake 9 → 18
turns and $0.21 → $0.35, pipeline flat at 17 turns and $0.25 → $0.28,
ratio 1.01× → 1.63×, scores unchanged at 5/5 everywhere. Both runs
produced correct deliverables; the extra turns were more CLI verification
and writing, not loads. Single samples are noisy (the baseline itself
swung 11 → 9 and 12 → 16 turns between runs), but the change had no
measured upside and raised every trigger's context, so the original
SKILL.md was restored. Lesson recorded in docs/skills.md: this skill's
turns come from running the CLI, not from reference loads — slim only
what the turns prove.

**Grader signal.** 0 of 5 checks separate the arms on either eval when
the CLI is installed: the baseline verifies flags and env vars against the
tool itself. The skill's value here is time on the knowledge-heavy task
(Snowflake: ~3× faster), and it would be larger where the CLI is not
installed to consult.
