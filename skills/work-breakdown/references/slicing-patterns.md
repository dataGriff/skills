# Slicing patterns

Named techniques for cutting work into units of delivery when the obvious
slices come out horizontal or the work seems atomic. Each pattern exists to
make a *smaller mergeable step* possible; pick the one that matches why the
work resists slicing.

## When slices come out horizontal

### Walking skeleton

The thinnest end-to-end path through the real architecture, deployed for
real: one request, one hard-coded response, but through the actual
service, actual pipeline, actual infrastructure. It proves the plumbing —
usually the highest-variance risk — and converts every later unit from
"integrate a new layer" into "extend a working path".

First unit for: new services, new pipelines, anything with unproven
deployment or integration.

### SPIDR — five ways to split a story

When a feature-shaped unit is too big, try each axis and keep the best cut:

- **Spike** — a time-boxed learning unit whose deliverable is an answer,
  not code. Valid unit of delivery *only* when it retires a named risk;
  its value is the reduction in uncertainty. Prefer a thin real slice if
  one would teach the same thing.
- **Paths** — split by user path: happy path first, each error/edge path
  its own unit.
- **Interfaces** — one browser, one platform, one API version first;
  others as later units.
- **Data** — one entity, one field, one file format first. "Support the
  five mandatory fields" before "support all forty".
- **Rules** — relax business rules in early units: fixed pricing before
  dynamic pricing, one currency before many.

## When the work is a refactor, migration, or rewrite

These feel atomic because the naive plan is replace-everything-then-switch.
All three patterns below work by keeping old and new alive at once so each
step merges safely.

### Branch by abstraction

For replacing a component the codebase calls directly:

1. Unit: introduce an abstraction over the old implementation; point all
   callers at it. (Proves the seam; value: replacement is now invisible to
   callers.)
2. Units: build the new implementation behind the abstraction, slice by
   capability; switch callers over incrementally — by call-site, feature
   flag, or percentage.
3. Unit: delete the old implementation and, optionally, the abstraction.
   (Value: pure reduction.)

Every unit merges to main; there is no long-lived rewrite branch.

### Parallel change (expand / migrate / contract)

For schema, API, or interface changes with independent producers and
consumers:

1. **Expand** — add the new shape alongside the old (new column, new
   endpoint version, new parameter with a default). Nothing breaks.
2. **Migrate** — move readers/writers over, one caller or one cohort per
   unit; backfill data as its own unit.
3. **Contract** — remove the old shape. Pure reduction, and its own unit
   so a problem in migration never blocks delivery of expansion.

### Strangler fig

For replacing a whole system: put a routing layer in front, then move one
capability at a time to the new system, routing switched per capability.
Each moved capability is a unit — it proves the new system handles real
traffic for that slice and reduces the old system's remaining surface.
The old system's shutdown is the final, smallest unit, not the goal that
blocks everything.

## Cross-cutting tools

### Feature flags

Flags decouple *merge* from *release*, which is what lets an incomplete
feature merge as a shippable unit. Keep flag lifetimes short: removing a
flag is itself a small unit with real value (reduction). A unit hidden
behind a flag still has to prove something — typically via internal use,
staging traffic, or a test cohort — otherwise it's inventory with extra
steps.

### Definition-of-done trimming, not quality trimming

Shrink scope, never rigor: a unit with fewer fields and full tests is a
unit; a unit with all fields and no tests is debt. If a unit only fits in
budget by skipping tests or review, the slice is wrong — cut scope with
Paths/Data/Rules instead.

## Worked example: "add multi-currency support to billing"

Naive plan: one epic branch touching schema, pricing, invoicing, UI.
Sliced with the patterns above:

1. Walking skeleton: schema + API accept a currency code, hard-wired to
   `USD` everywhere (parallel change: expand). Proves the shape reaches
   every layer.
2. Data: store and display currency on new invoices only; old rows default
   `USD` (no backfill yet). Proves display and storage paths.
3. Rules: support exactly one extra currency (`EUR`) with a fixed rate
   behind a flag. Proves conversion logic where it's cheapest.
4. Backfill historical rows (own unit — riskiest data operation isolated).
5. Migrate: dynamic rates from the provider; flag rollout by cohort.
6. Contract: remove the flag and the hard-wired defaults. Pure reduction.

Six mergeable PRs, risk retired in order, any of which could be the point
where new information changes the plan.
