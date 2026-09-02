# Eval results: api-mocking-microcks

Last run: 20260902-204630 UTC via `task eval:skills NAME=api-mocking-microcks MODEL=sonnet` (commit this file with the skill change so the PR carries the evidence).

Models served: claude-haiku-4-5-20251001, claude-sonnet-5.

| Eval | With skill | Baseline | Turns (skill/base) | Time (skill/base) | Cost (skill/base) |
|------|-----------|----------|--------------------|-------------------|-------------------|
| json-body-dispatch | 8/8 | 6/8 | 15 / 11 | 70.1s / 137.1s | $0.28 / $0.80 |
| mock-async-signup-events | 7/7 | 7/7 | 10 / 15 | 50.2s / 194.7s | $0.21 / $0.42 |
| overlay-generated-spec | 7/7 | 4/7 | 19 / 16 | 73.6s / 216.5s | $0.33 / $0.46 |
| testcontainers-contract-wiring | 7/7 | 7/7 | 8 / 10 | 31.3s / 122.7s | $0.15 / $0.29 |

Grader checks that separated the arms: json-body-dispatch 2/8, mock-async-signup-events 0/7, overlay-generated-spec 3/7, testcontainers-contract-wiring 0/7. A check both arms always pass measures nothing; a score delta with none separating is noise.
Token cost, with skill / baseline: 0.84x. Turns above the baseline usually mean SKILL.md loads bundled files unconditionally.

Full outputs (gitignored): `.evals/api-mocking-microcks/20260902-204630/`.

Notes: this run followed hardening the skill against the failure modes the
first sharpened run exposed (JSON_BODY rule syntax, overlay steering) — the
eval loop working as intended. The baseline's misses are the silently
breaking kind: dispatcherRules missing the required `operator` with
`range[..]`-prefixed case keys (every mock call would 400), a parallel
spec copy instead of APIExamples/APIMetadata overlays, and the 150ms
delay + catalog label dropped. The with-skill arm was also cheaper and
2-4x faster than baseline on every task — conditional reference loads mean
the skill pays for itself in fewer wrong-direction turns.
