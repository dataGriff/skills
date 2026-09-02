# Eval results: asyncapi-authoring

Last run: 20260902-204657 UTC via `task eval:skills NAME=asyncapi-authoring MODEL=claude-sonnet-5` (commit this file with the skill change so the PR carries the evidence).

Models served: claude-haiku-4-5-20251001, claude-sonnet-5.

| Eval | With skill | Baseline | Turns (skill/base) | Time (skill/base) | Cost (skill/base) |
|------|-----------|----------|--------------------|-------------------|-------------------|
| author-inventory-asyncapi | 8/8 | 5/8 | 8 / 7 | 31.6s / 40.1s | $0.17 / $0.14 |
| review-legacy-asyncapi | 7/7 | 7/7 | 10 / 13 | 81.3s / 132.6s | $0.27 / $0.33 |
| author-request-reply-avro | 7/8 | 7/8 | 10 / 7 | 73.5s / 72.3s | $0.28 / $0.20 |

Grader checks that separated the arms: author-inventory-asyncapi 3/8, review-legacy-asyncapi 0/7, author-request-reply-avro 2/8. A check both arms always pass measures nothing; a score delta with none separating is noise.
Token cost, with skill / baseline: 1.02x. Turns above the baseline usually mean SKILL.md loads bundled files unconditionally.

Full outputs (gitignored): `.evals/asyncapi-authoring/20260902-204657/`.

## Notes (2026-09-02, pinned Sonnet, post-slimming)

- **The gap the strong-executor benchmark hid is real on Sonnet.** The
  baseline shipped `asyncapi: 3.0.0` on *both* authoring evals (no
  validator rescue this run) and produced a malformed Kafka operation
  binding; the with-skill arm wrote 3.1.0 first-try everywhere and won
  author-inventory 8/8 vs 5/8 with 3 separating checks.
- **The with-skill arm's one miss** (author-request-reply 7/8): an invalid
  AMQP channel binding (`is:` shape) — AMQP binding syntax is
  reference-routed, not inline. The baseline failed a different check
  (stale version), so 2 checks separated the arms in opposite directions.
- **Slimming worked.** Token ratio 1.02x (was 1.21–1.35x on the pre-slim
  strong-executor runs) with turns at or below baseline on two of three
  evals; the review eval is now faster *and* cheaper than baseline.
- **Prior benchmark** (pre-slim SKILL.md, session-model subagents, 3 runs
  per arm): with skill 69/69, baseline 68/69 — that executor saturated
  the graders; 5 of 6 baseline authoring runs initially wrote 3.0.0 and
  were rescued only by running the CLI. Single Sonnet runs are noisy;
  treat one-run deltas as directional.
