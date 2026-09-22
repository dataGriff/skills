# Prose: shorter without losing a fact

## Rules

1. **Lead with the rule, then the reason.** "Never edit a merged migration;
   write a new one — replay depends on it." not "Because replay depends on
   the migration history, it is important that…"
2. **Cut throat-clearing.** "It is worth noting", "please note", "as you
   may know", "basically", "in order to", "needless to say", "first of all"
   carry nothing. Delete the phrase; the sentence still stands.
3. **One idea per sentence, about 20 words.** Split at "and", "which", "so".
4. **Imperative for instructions.** "Run `make test`." not "You will want to
   run `make test`."
5. **Tables for parallel facts.** Commands, env vars, targets, ports: a
   table is scanned, prose is read.
6. **Keep every fact.** Before rewriting a section, list its commands,
   paths, numbers, names and rules. After, check each is still there. A
   shorter doc that lost `PORT=8080` is a worse doc.
7. **Do not add.** Rewriting is not the moment to document something new;
   that is a separate change.

## Worked example

Before (12 lines):

> In order to get started you will simply need Python 3.12 and Postgres 16.
> Basically the steps are as follows. First of all, create a virtual
> environment, and then install the package in editable mode with the
> development extras, which will just pull in everything you need:
>
> ```bash
> python -m venv .venv && source .venv/bin/activate
> pip install -e ".[dev]"
> cp .env.example .env
> ```
>
> Please note that you should then fill in `DATABASE_URL` in `.env`. Never
> commit `.env`; secrets come from Vault.

Fact list: Python 3.12, Postgres 16, the three commands, `DATABASE_URL`,
never commit `.env`, secrets from Vault.

After (4 lines plus the block):

> Requires Python 3.12 and Postgres 16.
>
> ```bash
> python -m venv .venv && source .venv/bin/activate
> pip install -e ".[dev]"
> cp .env.example .env   # then set DATABASE_URL
> ```
>
> Never commit `.env`; secrets come from Vault.

Every fact survives; the hedges did not.

## When a section should be deleted rather than rewritten

- It is history (see the `history` category): move the gist to the commit
  body or `CHANGELOG.md`.
- It duplicates another doc: replace with a route line.
- Nobody needs it now: delete, and say so in the commit body.
