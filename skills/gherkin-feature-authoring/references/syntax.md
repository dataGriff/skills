# Gherkin syntax reference

Complete construct reference for Gherkin 6+ (the syntax shared by Cucumber,
SpecFlow/Reqnroll, Behave, behat, and cucumber-js). Line-oriented: one
keyword clause per line, indentation is conventional (2 spaces per level)
but not significant.

## Contents

- [File structure](#file-structure)
- [Feature](#feature)
- [Descriptions](#descriptions)
- [Rule](#rule)
- [Scenario / Example](#scenario--example)
- [Steps: Given / When / Then / And / But / *](#steps)
- [Background](#background)
- [Scenario Outline and Examples](#scenario-outline-and-examples)
- [Data tables](#data-tables)
- [Doc strings](#doc-strings)
- [Tags](#tags)
- [Comments](#comments)
- [Language header](#language-header)
- [Escaping rules](#escaping-rules)

## File structure

One `.feature` file contains exactly one `Feature`. Inside it, in order:
optional `Background`, then any mix of `Rule`, `Scenario`, and
`Scenario Outline` blocks. A `Rule` may contain its own `Background` and its
child scenarios. Keywords end with a colon (`Feature:`, `Scenario:`) except
step keywords, which do not.

## Feature

```gherkin
Feature: Account withdrawal
```

The name should identify a capability. Everything between the `Feature:`
line and the first keyword (`Background:`, `Rule:`, `Scenario:`, or a tag
line) is the feature description.

## Descriptions

`Feature`, `Rule`, `Scenario`, `Scenario Outline`, and `Examples` can all
carry free-text descriptions: any non-keyword lines directly under the
title line. Markdown renders in most report tools. Use the feature
description for the user-story narrative ("As a… I want… so that…"),
scope notes, and links. A description cannot contain a line that *starts*
with a keyword; comments (`#`) are fine.

## Rule

```gherkin
Rule: Withdrawals must not exceed the available balance
```

Groups the scenarios illustrating one business rule (Gherkin 6+; supported
by current Cucumber implementations and Reqnroll — SpecFlow legacy and very
old runners may not parse it, so check the toolchain before using it).
A `Rule` may open with its own `Background` applying only to its scenarios.
State the rule as a declarative sentence, not a title fragment.

## Scenario / Example

```gherkin
Scenario: Withdrawal exceeding the balance
```

`Example:` is a synonym for `Scenario:` — pick one per repo and stay
consistent. A scenario is a name, an optional description, then steps.
Zero steps is valid syntax but meaningless; treat a scenario as complete
only with at least a `When` and a `Then` (pure lookup scenarios may be
Given + Then).

## Steps

```gherkin
Given Alice has an open account with a balance of £100
And she has a daily withdrawal limit of £300
When she withdraws £80
Then £80 is dispensed
But no receipt is printed
```

- `Given` — the state the world is in before the behaviour: past events,
  preconditions. Present-perfect or state phrasing ("has", "is"), not
  actions.
- `When` — the single event or action under test. One `When` per scenario;
  a second `When` means a second scenario is hiding in this one.
- `Then` — the observable outcome to assert: what the actor can see or an
  external system receives. Never an internal detail ("the row is
  inserted").
- `And` / `But` — continuation of whichever keyword came before. `But` reads
  naturally for negative assertions; the runner treats them identically.
- `*` — anonymous bullet, valid in every implementation
  (`* some ingredient`); useful for list-like Givens, rare otherwise.

Keyword choice is documentation only — runners match steps by text, not
keyword. That is precisely why the keyword must match the intent: a `Then`
that performs an action lies to the reader without failing the run.

## Background

```gherkin
Background:
  Given Alice has an open account with a balance of £100
```

Steps prepended to every scenario in scope (the feature, or the enclosing
`Rule`). Only `Given` steps (with `And`/`But`) belong here — a `When` in a
Background is behaviour every scenario silently re-runs. Keep it short
(~4 lines): readers must hold it in mind for every scenario below. Don't
use Background for technical setup the reader doesn't need to know
(clearing databases, starting services) — hide that in hooks/step
definitions. If only some scenarios need the setup, it isn't Background;
put it in those scenarios' Givens.

## Scenario Outline and Examples

```gherkin
Scenario Outline: Password rejected when too weak
  Given Riley is registering an account
  When she chooses the password "<password>"
  Then registration is rejected because "<reason>"

  Examples:
    | password  | reason               |
    | short1    | shorter than 8 chars |
    | alllowercase | no digit or capital |
```

The outline runs once per `Examples` row; `<name>` placeholders are
substituted anywhere in steps, data tables, and doc strings — including
inside quoted strings. `Scenario Template:` / `Scenarios:` are accepted
synonyms for `Scenario Outline:` / `Examples:` in some runners; prefer the
canonical pair.

- Multiple `Examples` blocks under one outline are allowed and each can be
  named, described, and tagged — the idiomatic way to separate
  `Examples: Accepted` from `Examples: Rejected`, or to tag one block
  `@slow`.
- Columns should be exactly what varies. A column with the same value in
  every row belongs in the step text.
- If the table has one row, use a plain `Scenario` instead.

## Data tables

```gherkin
Given the following account holders exist:
  | name  | balance | status |
  | Alice | 100     | open   |
  | Bob   | 0       | frozen |
```

A table directly under a step is passed to that step's definition as a
structured argument. Cells are strings; the step definition does the
typing. Conventionally row one is a header, but Gherkin itself doesn't
distinguish — vertical key/value layouts are equally valid. Use a table
when a step needs more than ~2 pieces of data or a collection; don't cram
a table's worth of facts into one long sentence.

## Doc strings

```gherkin
Given the welcome email template is
  """markdown
  Hello {name},
  Thanks for joining.
  """
```

A multi-line string argument to the step above it, delimited by `"""` or
```` ``` ````. Indentation is stripped relative to the opening delimiter.
An optional content-type annotation (`"""json`) is passed to the step
definition. Use for payloads, templates, and message bodies.

## Tags

```gherkin
@billing @smoke
Feature: Account withdrawal

  @wip
  Scenario: Withdrawal exceeding the balance
```

Tags go on the line(s) above `Feature`, `Rule`, `Scenario`,
`Scenario Outline`, and `Examples` — never on steps or `Background`. A tag
is `@` plus a name (no spaces). Scenarios inherit the tags of their feature
and rule. Runners use them for filtering (`cucumber --tags "@smoke and not
@wip"`) and hooks. Tag for selection and lifecycle; a tag no filter or hook
ever reads is noise.

## Comments

```gherkin
# TODO: add the frozen-account case once the rule is agreed
```

`#` at the start of a line (leading whitespace allowed); no inline or block
comments. A comment explaining what a scenario means is a smell — rewrite
the scenario. Reserve comments for annotations to maintainers.

## Language header

```gherkin
# language: fr
Fonctionnalité: Retrait d'argent
```

First line of the file; switches all keywords to the named language
(70+ supported — `Angenommen`/`Wenn`/`Dann`, `Soit`/`Quand`/`Alors`, …).
Default is `en` or the runner's configured default. Write in the language
the business speaks; never mix languages in one file.

## Escaping rules

- In **data table cells**: `\|` for a literal pipe, `\\` for a backslash,
  `\n` for a newline.
- In **doc strings**: a literal `"""` inside a `"""`-delimited string is
  escaped as `\"\"\"` — or just use ```` ``` ```` delimiters instead.
- In **Examples placeholders**: there is no escape for `<` `>` in steps —
  angle brackets outside a defined column name are left literal by most
  runners, but avoid the ambiguity by renaming.
