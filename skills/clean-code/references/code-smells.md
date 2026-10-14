# Code smells catalog

Named structural problems and the refactoring that resolves each. Open this
when a review (of your own diff or someone else's) has flagged something
that feels wrong and you need the standard name and fix. Grouped by the
kind of damage the smell does.

## Bloaters — things that have grown too large

### Long function

A function you can't summarise in one sentence, or that scrolls past a
screen. **Fix**: Extract Function — pull each coherent block into a named
helper at one level of abstraction lower. The original becomes a readable
sequence of named steps.

### Long parameter list

Four or more parameters, especially ones that always travel together.
**Fix**: Introduce Parameter Object — group the travelling companions into
a type whose name explains the grouping (`DateRange`, `RetryPolicy`). If
several parameters come from one object, pass the object.

### Large class / god object

A class that imports everything and that every change touches. **Fix**:
Extract Class — find clusters of fields and methods that change together
and move each cluster into its own type. The cluster boundaries usually
follow the reasons the class changes.

### Primitive obsession

Domain concepts passed around as bare strings/ints (`user_id: str`,
`amount: float` for money), so nothing stops you swapping arguments or
mixing currencies. **Fix**: Replace Primitive with Value Object for
concepts that carry rules (Money, EmailAddress, Duration).

## Change amplifiers — one edit fans out everywhere

### Duplicated code

The same logic in multiple places; a fix lands in one and not the others.
**Fix**: Extract Function/Method into a shared helper — but only when the
copies are the same concept, not merely the same shape today (rule of
three; see SKILL.md on the wrong abstraction).

### Shotgun surgery

One conceptual change requires edits in many files. **Fix**: Move
Function/Field to gather the scattered logic into one module that owns the
concept.

### Divergent change

One module is edited for many unrelated reasons — it owns too many
concepts. **Fix**: Split by reason-for-change (Extract Class/Module); each
resulting piece changes for one reason.

## Couplers — things that know too much about each other

### Feature envy

A method that mostly reads another object's data to compute something.
**Fix**: Move Function — put the computation where the data lives.

### Message chains

`order.customer.address.city.tax_rate()` — the caller knows the whole
object graph, and any link changing breaks it. **Fix**: Hide Delegate —
ask the nearest object for what you need (`order.tax_rate()`), or pass in
the value itself.

### Inappropriate intimacy

Two modules reach into each other's internals (private fields, undocumented
invariants). **Fix**: Move the shared logic into one owner, or define an
explicit interface between them and talk only through it.

### Global / shared mutable state

Anything can write it, so nothing can be reasoned about locally, and tests
interfere with each other. **Fix**: pass the value explicitly as a
parameter; if it's genuinely process-wide (config, clock), inject it at
construction so tests can substitute it.

## Deceivers — code that misleads the reader

### Misleading name

A function called `get_user` that also creates one; a `list_items` that
mutates. The reader trusts the name and is wrong. **Fix**: Rename to match
behaviour, or change behaviour to match the name — whichever the callers
actually rely on.

### Flag argument

`render(item, true)` — the boolean switches behaviour, and the call site is
unreadable without opening the function. **Fix**: split into two functions
named for each behaviour (`render_compact`, `render_full`).

### Comment as deodorant

A comment explaining a confusing block instead of fixing it. **Fix**:
Extract Function named after what the comment said, or rename the variables
until the comment is redundant, then delete the comment.

### Dead code and speculative generality

Unused functions, unreachable branches, hooks and parameters "for later".
Readers pay to understand code that does nothing. **Fix**: delete it;
version control remembers. Remove unused parameters and collapse
single-implementation interfaces.

## Fragile logic

### Nested conditionals

Arrow-shaped code where the happy path hides at indentation level five.
**Fix**: Replace Nested Conditional with Guard Clauses — return early on
each error/edge case; the main logic ends up unindented.

### Switch/type-check repetition

The same `if isinstance(...)` / `switch on kind` ladder appears in several
places, and each new kind means finding all of them. **Fix**: Replace
Conditional with Polymorphism — one type per kind, each owning its
behaviour — or a dispatch table keyed by kind, when full polymorphism is
overkill.

### Swallowed exception

`except: pass`, an empty catch, or logging-and-continuing when the
operation actually failed. The failure surfaces later, far from its cause.
**Fix**: handle it meaningfully, or let it propagate with added context;
catch only the specific exceptions you can actually handle.

### Magic values

Bare `86400`, `"ACTIVE"`, `0.15` in logic. The reader must guess the
meaning, and two occurrences can drift apart. **Fix**: Extract Constant
with an intent-revealing name (`SECONDS_PER_DAY`, `DEFAULT_TAX_RATE`); use
an enum where the values form a closed set.

### Temporal coupling

Methods that only work when called in an undocumented order
(`connect()` before `send()`, `init()` before anything). **Fix**: make the
prerequisite explicit — have the first step return the object the second
step needs, so the wrong order won't compile or will fail immediately with
a clear error.
