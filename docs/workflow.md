# From requirements to gated specs

The skills in this repo are not just a grab-bag: most of them chain into
one delivery pipeline. Requirements are captured as concrete examples,
converted into executable specifications, and those specifications then do
two jobs — they steer whoever implements (human or AI agent), and they run
in CI as the gate that proves the implementation honours them. This page
names the pipeline once so each skill can stay single-purpose.

## The three tracks

Each track runs the same three stages: **capture → author the spec →
gate in CI**. Which track applies depends on what the requirement
describes — behaviour, an interface, or data.

| Track     | Capture                   | Author the spec                              | Gate in CI                                        |
| --------- | ------------------------- | -------------------------------------------- | ------------------------------------------------- |
| Behaviour | `requirements-to-gherkin` | `gherkin-feature-authoring` (`.feature`)     | `cucumber-js-automation` (cucumber suite)          |
| API       | `requirements-to-gherkin` | `openapi-authoring` / `asyncapi-authoring`   | `contract-testing-microcks` / `api-mocking-microcks` |
| Data      | `requirements-to-gherkin` | `odcs-authoring` (`.odcs.yaml`)              | `datacontract-cli` (`datacontract test` / `ci`)    |

One piece of work often spans tracks: a refunds feature yields Gherkin
scenarios (behaviour), an OpenAPI change (interface), and a data-contract
change (what lands in the warehouse). `requirements-to-gherkin` captures
all of it on one discovery board — behaviour goes to Gherkin, shape and
obligation go to the matching contract skill.

## Stage by stage

1. **Capture.** `requirements-to-gherkin` turns stakeholder input into
   rules with concrete examples plus an honest open-questions list. The
   examples are the raw material for every track: scenarios, example
   payloads, example records.
2. **Author.** The authoring skills turn rules and examples into a
   reviewable, lintable artifact committed to the target repo. The spec is
   the source of truth from here on — reviews and stakeholder sign-off
   happen on the spec, not on the code.
3. **Implement against the spec.** An implementer (especially an AI agent)
   loads the spec first and works outside-in: run the gate, let the
   failures drive the code, repeat until green. A spec that seems wrong
   mid-implementation goes back to its owner (or its `# OPEN:` question)
   — it is never quietly reworded, loosened, or trimmed to make a run
   pass, because that silently rewrites the agreement the spec records.
4. **Gate.** Each gate tool exits non-zero on violation, so all three wire
   into a pipeline as required checks: the cucumber suite, `microcks test`
   (or its Testcontainers/GitHub Action forms), and `datacontract test` /
   `datacontract ci`.

## Making the specs findable and the gates binding

Specs only influence agents if agents find them, and gates only gate if
they run on every change. In a target repo (see the `repo-optimization`
skill for the surrounding structure):

- Keep specs in conventional, discoverable locations: `features/*.feature`,
  `openapi.yaml` / `asyncapi.yaml` (or `<api>.openapi.yaml`),
  `<dataset>.odcs.yaml` — and route to them from `AGENTS.md` so an agent
  reads the contracts before writing code.
- Fold every gate into the repo's single definition of green (`task ci`
  or equivalent), so hooks, CI, and humans all run the specs the same way.

## Slicing work along the specs

When delivery needs breaking down, the specs give natural seams: one
`Rule:` block (or one scenario) turned green, one endpoint of the OpenAPI
spec implemented, one object of a data contract landed. The
`work-breakdown` skill covers slicing; spec-shaped units are already
shippable, provable (the gate proves them), and pre-agreed in scope.

## Skills outside the pipeline

`repo-optimization` and `work-breakdown` are general-purpose — they
support the pipeline (discoverability, gating, slicing) but stand alone.
