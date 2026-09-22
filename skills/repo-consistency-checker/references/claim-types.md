# Verifying claims by type

How to settle each kind of statement a repo makes about itself, and the
false positives to avoid. Open the section for the claim type in hand.

## Commands

**Claim:** "run `make test`", "`task check` runs the linters", a hook or CI
step invoking a target.

**Verify:** the target exists (Makefile target, Taskfile task, package.json
script, cargo/npm/poetry subcommand) *and* does what the sentence says —
read the target body, not just its name. A target that exists but no
longer runs the linters is drift too.

**Traps:** `pnpm test` / `npm start` are script shortcuts; `pnpm install`
is a builtin. Taskfile `includes:` namespaces (`docs:build`) live in
another file. Words like "make sure" and "the task runner" are prose, not
commands — only flag commands in code spans, fenced blocks, hooks, CI and
scripts.

## Paths and filenames

**Claim:** "config lives in `settings.yaml`", a layout tree in the README,
a link to `docs/ci.md`, a comment saying "see scripts/deploy.sh".

**Verify:** the path exists relative to the file that mentions it or to
the repo root. For layout trees, diff the tree against `ls`: missing
entries, renamed entries, and entries the tree omits are all findings
(an incomplete tree is a claim that nothing else exists).

**Traps:** placeholders (`skills/my-skill/SKILL.md`, `<name>`), paths in
other repos, paths created at runtime (`.evals/`, `dist/`) — check
`.gitignore` before calling a runtime path broken. A file that exists but
at a different depth (`src/helpers.py` vs `src/utils/helpers.py`) is the
most common real hit.

## Identifiers

**Claim:** a flag (`--strict`), env var (`APP_PORT`), config key
(`retries:`), function, class, task or job named in prose or a comment.

**Verify:** search the whole repo for the exact token. It must appear in a
definition — a function `def`, an `os.environ[...]` read, a config schema,
an argparse `add_argument` — not only in other prose. Check the spelling
and case exactly; `APP_PORT` documented but `PORT` read is drift.

**Traps:** identifiers read dynamically (`os.environ[prefix + name]`,
`getattr`), identifiers defined in a dependency rather than this repo,
generated code.

## Numbers and limits

**Claim:** "under 500 lines", "retries 3 times", "port 8080", "timeout of
30 s", "at most 1024 characters", a percentage, a page size.

**Verify:** find the constant or config value that enforces the number and
compare. The scan lists numeric claims with code lines carrying the same
number; when *no* code line carries it, the value has probably changed —
search for the identifier the sentence implies (`MAX_LINES`, `retries`,
`port`) and read the current value.

**Traps:** numbers that are examples ("for instance, 3 retries") rather
than claims; unit mismatches (30 s in docs, 30000 ms in code — consistent);
a number stated in two docs *and* a constant — that is one drift finding
plus one redundancy finding, and the fix is to keep the constant and make
the docs say "see X" or state it once.

## Versions

**Claim:** "requires Python 3.12", "tested on Node 20", "OpenAPI 3.1".

**Verify:** the pin — `pyproject.toml` `requires-python`, `.nvmrc` or
`engines`, `mise.toml`, the CI matrix, a Dockerfile base image, a lockfile.
Every pin should agree; when they don't, the doc is not the only thing
wrong.

**Traps:** a range vs a point ("3.12" in docs, ">=3.11" in the manifest is
consistent if intended); a historical version in a changelog.

## Behaviour

**Claim:** "returns None when the key is missing", "retries on 5xx",
"validates before writing", "idempotent", a docstring's Raises section.

**Verify:** read the code path and, where one exists, the test that pins
it — a test asserting the behaviour is the strongest evidence, and a test
asserting the *opposite* settles it. Trace error handling specifically:
"returns None" vs "raises", "logs and continues" vs "aborts", and default
values are the behaviours that drift most.

**Traps:** behaviour implemented in a wrapper or a decorator rather than
the function the comment sits on; behaviour that depends on config. When
the doc describes behaviour the code once had and callers still rely on
it, that is a **possible bug**, not doc drift — say so and do not rewrite
the doc to match.

## Sequences and setup steps

**Claim:** numbered install, setup or release steps.

**Verify:** each step's command or file still exists, the steps still run
in that order (step 3 must not need step 4's output), and nothing the
current setup requires is missing. Where safe, execute the sequence.

**Traps:** steps that are optional but read as required; steps for
platforms the repo no longer supports.

## Structure and architecture

**Claim:** "the API layer calls the service layer, never the repo
directly", "X publishes events consumed by Y", a diagram, a component list.

**Verify:** imports and call sites (`grep -r "from .repo import"` inside
the API package), the presence of every component the diagram names, and
the absence of paths the text forbids.

**Traps:** aspirational architecture docs — if the doc is explicitly a
target state, it is not drift, but it should say so.

## Signatures, docstrings and comments

**Claim:** parameter lists, types, return descriptions, "this function is
only called from X", a comment above a block describing what it does.

**Verify:** compare the docstring against the actual signature (names,
count, defaults, types) and the described return against every `return`.
For "only called from" claims, search for the callers. For block comments,
read the block: is every sentence still true, and is any sentence merely
the code again in English (redundancy)?

**Traps:** inherited docstrings, overloads, `**kwargs` passthroughs.

## Examples and snippets

**Claim:** a code block showing usage; a sample config; a sample request
and response.

**Verify:** the snippet parses in its language; every identifier, flag,
path and field it names exists; the shown output matches what the code
produces (run it when possible). Sample configs are a frequent source of
keys the code stopped reading.

**Traps:** deliberately abbreviated snippets (`...`); examples for a
public API where the shown consumer code is not in this repo.

## Parity claims

**Claim:** "hooks run the same checks as CI", "the Docker image and the
local setup are equivalent", "CLAUDE.md is `@AGENTS.md`".

**Verify:** both sides call the same entrypoint or contain identical
content; anything CI runs that the hook doesn't (or vice versa) is a
finding, because the claim is precisely that there is no difference.

## Generated and vendored files

Do not audit them for style, but do check two things: the generator's
input still exists and is what the doc says it is, and the generated
output is not older than its input (a stale generated file is drift
between source and artifact). Vendored code is out of scope unless a doc
claims it is patched — then verify the patch is present.
