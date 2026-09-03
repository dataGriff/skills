---
name: clean-code
description: >-
  Apply clean code principles when writing, refactoring, or reviewing code:
  intention-revealing names, small single-purpose functions, flat control
  flow, minimal duplication, honest error handling, comments that explain
  why, and consistency with the surrounding codebase. Use whenever you
  construct or modify code in any language, when self-reviewing a diff
  before committing, and when performing a code review or PR review. Also
  trigger when the user mentions clean code, code quality, readability,
  maintainability, refactoring, code smells, technical debt, or asks
  whether code is well written or how to improve it.
---

# Clean code

Code is read far more often than it is written, so optimise for the next
reader. These rules apply in three situations: **while constructing any
code**, **when self-reviewing your own diff before committing**, and **when
reviewing someone else's code**. The rules are the same; only the workflow
around them differs.

## Core rules

### Names reveal intent

A name should answer why something exists and what it does, so the reader
never has to open the definition to find out. `elapsed_days` beats `d`;
`is_eligible_for_refund` beats `check2`. Use pronounceable, searchable
names; encode units and meaning (`timeout_ms`, not `timeout`). One concept,
one word — don't mix `fetch`/`get`/`retrieve` for the same idea in one
codebase. If you need a comment to explain a name, change the name instead.

### Functions do one thing

A function should be describable in one short sentence without "and". Small,
single-purpose functions are easier to name, test, and reuse; a function
that mixes levels of abstraction (business rule + byte shuffling) forces the
reader to context-switch mid-thought. Keep parameter lists short — three or
more suggests some of them belong together in a type. Avoid boolean flag
parameters that switch behaviour; split into two well-named functions.

### Keep control flow flat

Deep nesting hides the happy path. Prefer guard clauses — validate and
return early — so the main logic sits at the left margin. Extract complex
conditions into named predicates (`if is_expired(token):` rather than a
three-clause boolean inline). Handle the error case first, then write the
normal case unindented.

### Duplication, and the wrong abstraction

Duplicated logic means a future fix lands in one copy and not the other.
But a bad abstraction is worse than duplication: don't merge two things
that merely look similar today. Apply the rule of three — tolerate a second
occurrence, extract on the third, when the shared shape is proven. When an
existing helper almost fits, resist adding a flag to it; that's how wrong
abstractions grow.

### Comments explain why, not what

The code says what it does; a comment earns its place only by stating what
the code cannot: a constraint, a workaround with its ticket, a non-obvious
performance or ordering requirement. Delete commented-out code — version
control remembers it. A comment that paraphrases the next line will drift
into a lie the first time the line changes.

### Handle errors honestly

Never swallow an exception or return a silent default that hides failure.
Fail fast with context: include what was being attempted and the offending
values in the error. Don't use exceptions for expected control flow, and
don't return null/None where an empty collection or a result type makes the
caller's life simpler. Validate inputs at boundaries (user input, network,
file, cross-service), not defensively on every internal call.

### Minimise state and side effects

A function that reads its inputs and returns a result is trivially testable;
one that mutates shared state is not. Keep mutation local, pass data
explicitly instead of reaching for globals, and separate queries (return a
value, change nothing) from commands (change state). Make side effects
obvious from the name — `send_invoice` may email people; `format_invoice`
must not.

### Match the codebase

Consistency beats personal taste. Follow the surrounding file's naming,
formatting, idiom, error-handling style, and comment density — even where
you'd choose differently in a green field. A locally "cleaner" style that
diverges from the codebase makes the whole harder to read. Use the
project's existing helpers and utilities before writing new ones.

### Simplicity over speculation

Build what the task needs now — no speculative parameters, config options,
abstraction layers, or "flexibility" for requirements that don't exist yet
(YAGNI). Clever one-liners lose to boring, obvious code. The cheapest code
to maintain is the code you didn't write.

### Leave it testable and tested

If code is hard to test, that's a design smell — usually hidden
dependencies or mixed responsibilities, not a testing problem. New logic
gets a test that would fail if the logic broke; bug fixes get a regression
test reproducing the bug first. Tests are code too: same naming and
readability standards, one behaviour per test.

## While constructing code

Apply the rules as you write, not as a cleanup pass afterwards:

1. Before writing, read enough neighbouring code to absorb its conventions
   and find existing helpers you should reuse.
2. Write the simplest version that solves the actual task.
3. As you go, name things for intent, extract when a function stops being
   describable in one sentence, and guard-clause the error paths.
4. Boy-scout rule, scoped: leave code you touch slightly better (a rename,
   a dead-code deletion), but don't balloon the diff with drive-by
   refactors — unrelated cleanup belongs in its own change.

## Self-review before committing

Re-read your full diff adversarially, as if reviewing a stranger's PR:

- Does every name still say what the thing now does? (Names rot during
  iteration.)
- Any leftover debug output, commented-out code, TODO without an owner,
  or unused import/variable/parameter?
- Any duplication you introduced because you didn't check for an existing
  helper?
- Are error paths handled, or only the happy path?
- Is anything in the diff unrelated to the task? Pull it out.
- Would each rule above pass? Fix violations now — they're cheapest before
  anyone else reads the code.

## Reviewing others' code

Check the same rules, and report findings usefully:

- **Prioritise by severity**: correctness and error-handling problems
  first, then design (duplication, wrong abstraction, leaky boundaries),
  then readability, then nits. Say which category a comment is in.
- **Be concrete**: point at the line, state the problem, and sketch the
  fix. "Rename `data2` to `retry_queue`" is actionable; "this is unclear"
  is not.
- **Respect the codebase over the rulebook**: don't ask an author to
  deviate from established project conventions to satisfy a general
  principle.
- **Don't demand rewrites for taste**: if the code is correct, consistent,
  and clear enough, approve. Clean code is a threshold, not a ceiling.

When you have spotted a structural problem in written or reviewed code but
can't name it or don't know the standard fix, open
[references/code-smells.md](references/code-smells.md) — a catalog of
common smells with the refactoring that resolves each.
