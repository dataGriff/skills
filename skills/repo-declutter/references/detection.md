# Detection: signals per category

The same patterns `scripts/audit_noise.py` uses, so the script's tables and
a hand scan agree. Every regex is a *signal*, not a verdict: read the
match before acting, and check the "false positive" column.

## Prose

| Signal | Pattern | False positive |
| ------ | ------- | -------------- |
| hedge | `\b(it is worth noting|basically|in order to|please note|needless to say|as you may know|simply|just|generally speaking|first of all)\b` | "just" as in "just-in-time"; quoted user text |
| long sentence | more than 30 words between sentence ends | a list rendered as a sentence; a legal sentence |
| double statement | two consecutive sentences with the same content words | an intentional summary line at the top of a section |

Before:

> It is worth noting that we have both unit and integration tests. Basically,
> `make test` runs the whole suite, and it is, needless to say, what CI runs,
> so you should run it before you push.

After:

> `make test` runs the unit and integration tests; CI runs the same target.
> Run it before you push.

## History

| Signal | Pattern | False positive |
| ------ | ------- | -------------- |
| history cue | `\b(previously|used to|as of v?\d|we (changed|switched|migrated|moved|renamed) (to|from|the)|no longer|originally)\b` | "no longer" in a rule ("tokens are no longer valid after 24 h") |
| changelog heading | `^#{1,6}\s*(change ?log|history|what'?s new|release notes|migration (notes|diary)|how we got here)` | the heading of `CHANGELOG.md` itself |
| dated entry | `^\s*[-*]\s*\d{4}-\d{2}-\d{2}` | a runbook timeline that is the procedure |

Does git already hold it?

```bash
git log -S"Flask" --oneline            # commits that added or removed the phrase
git log --follow --oneline -- docs/x.md # the file's own history
```

If those commits tell the story, delete the prose. If not, the removal
commit body carries a one-paragraph gist.

Before:

> Previously we used Flask… As of v2 we switched to FastAPI… the Flask code
> path was removed in v2.3.

After (in the doc): nothing, or one line if the present needs it:
"The HTTP layer is FastAPI." After (in the commit body): the paragraph.

## Duplicate

Normalise paragraphs (lowercase, collapse whitespace) and look for the same
text longer than ~80 characters in two files; commands in fenced blocks
count too. Keep the copy in the doc the entry file routes to; the other
becomes a route line ("Setup: read docs/setup.md").

## Comment

| Signal | Pattern | False positive |
| ------ | ------- | -------------- |
| commented-out code | starts with a keyword (`def`, `class`, `return`, `if`, `for`, `import`, `const`, `func`…), or is short (≤ 8 words), carries code punctuation (`= ( [ { ;`) and ends like code (`: ) ] } ;` a digit or a quote) rather than like a sentence or a ticket reference `(FIN-212)` | a comment quoting a command; "retry 3 times (max)" |
| banner | `^\s*(#|//)\s*[-=*#]{5,}` | a shebang or encoding line |
| attribution | `\b(added|modified|updated|changed|created) (by|on) \b` | a licence header's copyright line (protected anyway) |
| stale TODO | `\b(TODO|FIXME|XXX)\b` with a year, no ticket, or "after vN" already shipped | a TODO with a live ticket id |
| restating | the comment's content words are a subset of the next code line's identifiers ("increment count" above `count += 1`) | a comment that states a unit or invariant the code cannot |

## Code clarity

A comment that *names* what the code should have named:

- `# d = subtotal in minor units, r = rate` → rename the parameters.
- `# step 2: apply the bonus` inside a long function → extract
  `apply_bonus(...)`.
- `# returns None when the user is inactive` → the name or a type says it:
  `active_user_or_none`.

The comment goes only after the name carries it and the tests pass.
