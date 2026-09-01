# Eval results: datacontract-cli

Last run: 2026-09-01 UTC, iteration 1 (run via session subagents; rerun with
`task eval:skills NAME=datacontract-cli` — commit this file with the skill
change so the PR carries the evidence).

| Eval | With skill | Baseline | Time (skill/base) | Cost (skill/base) |
|------|-----------|----------|-------------------|-------------------|
| snowflake-ci-guidance | 5/5 | 5/5 | 110.0s / 160.2s | ? / ? |
| ddl-to-contract-pipeline | 5/5 | 5/5 | 68.8s / 94.2s | ? / ? |

Notes: correctness tied because baselines verified flags and env vars
against the installed CLI's source — spending the extra ~45–50% wall clock
the skill saves. The skill's edge grows where nothing is installed to check
against (design discussions, machines without the CLI).
