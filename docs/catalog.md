# Skill catalog

Seventeen skills in five families. You do not run them by hand: an agent
picks a skill when your request matches its description, so ask for the
outcome ("write an OpenAPI spec for orders", "Dave is leaving, what do we
need from him?"). Most tasks need one skill. Families exist because some
work runs through several in order, and so you can install only what
you use.

## Using a skill

- **Ask for the outcome.** The trigger is the description; the phrases in
  the "Use when" column below are the ones that match.
- **Name it to force it.** "Use the bus-factor skill on this repo", or
  `/bus-factor` in Claude Code. Do this when two skills could fit, or
  when a skill did not trigger.
- **Give it a scope.** A path, a PR or a diff instead of "the repo": the
  audit skills cost tokens in proportion to what they read.
- **Follow the hand-offs.** Each skill names its neighbours ("Missing
  knowledge is bus-factor's job"); when it says to, run the next one.

## Install only what you use

Every installed skill's name and description load into every
conversation, whether or not it triggers. Install the families you work
in:

```bash
task install:skills GROUP=repo            # one family
task install:skills GROUP=api,data        # several
task install:skills SKILLS=bus-factor     # single skills; combines with GROUP
```

The Claude Code plugin (`/plugin install datagriff-skills@datagriff`)
installs everything. [install.md](install.md) covers agents and
uninstalling.

## API design and testing — `GROUP=api`

| Skill | Use when |
|---|---|
| `openapi-authoring` | writing, reviewing or upgrading a REST API spec (OpenAPI/Swagger) |
| `asyncapi-authoring` | describing events, topics or queues (AsyncAPI), or migrating 2.x to 3.x |
| `microcks` | you need a mock API, fake endpoints or sample events, or to check a running implementation conforms to its spec |
| `api-security` | reviewing or designing an API against the OWASP API Top 10, or fixing an auth bug |

In order: write the spec (OpenAPI or AsyncAPI) with examples, mock it with
`microcks` so consumers can start, contract-test the implementation with
`microcks` against the same examples, and review its security before
release. Each step works alone on an existing
spec.

## Data contracts — `GROUP=data`

| Skill | Use when |
|---|---|
| `odcs-authoring` | writing or reviewing a data contract (ODCS YAML): schema, quality rules, SLAs |
| `datacontract-cli` | linting, testing data against, exporting or importing a contract with the `datacontract` CLI |

In order: write the contract, then enforce it: test real data against it
and wire the checks into CI.

## Requirements and BDD — `GROUP=bdd`

| Skill | Use when |
|---|---|
| `requirements-to-gherkin` | a vague idea, story or meeting notes need turning into testable requirements, or you need questions for stakeholders |
| `gherkin-feature-authoring` | writing or reviewing `.feature` files |
| `cucumber-js-automation` | making Gherkin scenarios run in a JavaScript or TypeScript project |

In order: pin down the requirements, write them as scenarios, automate
the scenarios. Start at whichever step you already have the input for.

## Repo health — `GROUP=repo`

| Skill | Use when |
|---|---|
| `repo-health` | the whole repo needs putting right in one pass: adopting it, before a handover, a periodic tidy |
| `bus-factor` | knowledge lives in people's heads, someone is leaving, or newcomers get stuck |
| `repo-consistency-checker` | docs, comments or config may no longer match the code, or a fact is stated twice |
| `repo-declutter` | docs or comments are true but too long, or carry history that belongs in git |
| `repo-optimization` | making a repo cheap for agents: AGENTS.md, routes into docs/, one task runner, CI checks |

The four single skills each answer one question: is knowledge
**missing**, is what's written **true and said once**, is it **longer than
it needs to be**, can an agent **find it cheaply**. For a full pass
(adopting a repo, before a handover) run `repo-health`: it triages with
one scan, then runs the four in that order, because each step changes
what the next one sees, skipping the phases the repo does not need, and
hands back one branch and one draft PR. You do not need the full pass to
keep a repo in shape; run one skill on a small scope when something
happens:

| When | Run | On |
|---|---|---|
| someone leaves, or a newcomer keeps getting stuck | `bus-factor` | their areas, or the stage they stall at |
| after a refactor, rename or removal; before a release | `repo-consistency-checker` | the files the change touched |
| a doc has grown or reads badly | `repo-declutter` | that doc |
| agents ignore the rules, or the entry file is over budget | `repo-optimization` | the entry file and its routes |

What these skills set up (budget checks, hooks, pinned tools, tests named
for rules) keeps the standard between runs.

## Planning and writing — `GROUP=practice`

| Skill | Use when |
|---|---|
| `goldratt-4-questions` | deciding whether to adopt a technology, or why an adopted one is not paying off |
| `work-breakdown` | a piece of work or a PR is too big and needs slicing into shippable units |
| `orwell-prose` | prose outside a repo (an essay, email or article) is wordy or reads as AI-written |

These are independent. A common chain: decide with
`goldratt-4-questions`, slice the work with `work-breakdown`, and edit
the write-up with `orwell-prose`.
