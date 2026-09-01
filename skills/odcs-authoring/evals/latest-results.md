# Eval results: odcs-authoring

Last run: 2026-09-01 UTC, iteration 1 (run via session subagents; rerun with
`task eval:skills NAME=odcs-authoring` — commit this file with the skill
change so the PR carries the evidence).

| Eval | With skill | Baseline | Time (skill/base) | Cost (skill/base) |
|------|-----------|----------|-------------------|-------------------|
| author-orders-contract | 7/7 | 7/7 | 76.8s / 142.5s | ? / ? |
| review-legacy-contract | 6/6 | 5/6 | 97.2s / 240.1s | ? / ? |

Notes: the baseline's one failure kept the deprecated `dataProduct` field in
the "fixed" contract. Baselines matched on correctness mostly by
self-verifying against the installed datacontract CLI, at ~2x the wall
clock; expect a larger correctness gap where the CLI isn't available.
