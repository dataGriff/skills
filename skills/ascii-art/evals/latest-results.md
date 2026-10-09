# Eval results: ascii-art

Not yet run. The skill was authored in a sandbox without the `claude` CLI,
so `task eval:skills NAME=ascii-art` could not be executed there. Run it
(ideally with `MODEL=sonnet`) and commit the refreshed table before merging
a change that touches this skill.

What the suite measures (see `evals.json` and `grade.py`):

| Eval            | Checks                                                                                         |
|-----------------|------------------------------------------------------------------------------------------------|
| cli-banner      | rectangular frame, closed sides, block letters over 4+ rows, tagline intact, pure ASCII, <= 70 cols |
| readme-mascot   | 10-18 rows, <= 40 cols, 2:1 aspect, symmetric eyes on one row, beak, branch, no stray letters   |
| image-to-ascii  | 60 cols, aspect-correct rows, density/luminance correlation r >= 0.6, region ordering, pure ASCII |
