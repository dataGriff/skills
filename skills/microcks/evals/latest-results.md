# Eval results: microcks

Last run: 20261015-064146 UTC via `task eval:skills NAME=microcks MODEL=claude-sonnet-5-5` (commit this file with the skill change so the PR carries the evidence).

Models served: claude-haiku-5-5, claude-sonnet-5-5.

| Eval | With skill | Baseline | Turns (skill/base) | Time (skill/base) | Cost (skill/base) |
|------|-----------|----------|--------------------|-------------------|-------------------|
| json-body-dispatch | 8/8 | 8/8 | 5 / 2 | 26.9s / 19.4s | $0.14 / $0.07 |
| mock-async-signup-events | 7/7 | 7/7 | 7 / 2 | 30.2s / 22.8s | $0.14 / $0.08 |
| overlay-generated-spec | 7/7 | 6/7 | 7 / 6 | 32.3s / 39.5s | $0.15 / $0.13 |
| github-actions-contract-gate | 5/5 | 5/5 | 7 / 3 | 36.4s / 37.9s | $0.15 / $0.09 |
| node-testcontainers-provider-test | 6/6 | 6/6 | 6 / 5 | 29.6s / 29.9s | $0.13 / $0.11 |

Grader checks that separated the arms: json-body-dispatch 0/8, mock-async-signup-events 0/7, overlay-generated-spec 1/7, github-actions-contract-gate 0/5, node-testcontainers-provider-test 0/6. A check both arms always pass measures nothing; a score delta with none separating is noise.
Token cost, with skill / baseline: 2.14x. Turns above the baseline usually mean SKILL.md loads bundled files unconditionally.

Full outputs (gitignored): `.evals/microcks/20261015-064146/`.

## Notes: first run after the merge (2026-10-15)

`microcks` merges `api-mocking-microcks` (evals 0-2 here) and
`contract-testing-microcks` (evals 3-4). The mocking skill's Testcontainers
eval was dropped: it duplicated eval 4 and no check in it ever separated
the arms.

- **On this model the baseline has caught up.** 33/33 against 32/33; the
  one separating check is eval 2, where the baseline's APIExamples overlay
  used the wrong identity (`Inventory API` 2.3.0, not the generated spec's
  title and version), so its examples would land on a separate API. The
  earlier separations (JSON_BODY rule syntax, the `OPENAPI_SCHEMA` runner
  hallucination) did not recur.
- **Cost: 2.14x the baseline's tokens.** The skill arm reads SKILL.md and
  then one or two conditional references before writing (5-7 turns); the
  baseline writes straight away (2-6 turns). The reads are the ones the
  skill tells it to make for these tasks, so this is the price of the
  guidance, not an unconditional load.
- **Not yet known:** whether the merge or the model change explains the
  difference from the pre-merge results (recorded on claude-sonnet-5).
