#!/usr/bin/env python3
"""Grade repo-optimization eval runs. Usage: grade.py <iteration-dir>.

Expects <iteration-dir>/eval-*/{with_skill,without_skill}/outputs/ as laid
out by scripts/eval_skills.py (run via `task eval:skills NAME=repo-optimization`).
Every check is static: it inspects the files the arm wrote, never runs
them. Two families of check:

- structure: for the README-only fixture, the build outcome (CLAUDE.md ==
  @AGENTS.md, an AGENTS.md that carries the universal rules within budget,
  explicit conditional routes, no index for a repo this small), the
  Taskfile as the single home for scattered commands, thin CI, hooks, a
  sandbox bootstrap; for the fat-CLAUDE.md fixture, whether the arm chose
  the cheaper routes-only outcome (kept the content that fit, routed the
  runbook explicitly, kept pnpm scripts as the command home);
- preservation: distinctive facts from the fixture docs survive somewhere
  the new layout routes to, the rules most tasks need sit in AGENTS.md
  itself, and the always-loaded cost went down;
- downstream: for each follow-up task run in the before / after-baseline /
  after-skill states of the fixture, whether the answer follows the repo's
  own rules (the runner records turns, tokens and reads per run).

Writes grading.json per arm (and per downstream run) and prints summaries.
"""
import json
import re
import sys
from pathlib import Path

import yaml

# AGENTS.md is the working layer: it carries what most tasks need, up to
# the point where rule count starts to hurt instruction-following (the
# skill's ~150 lines / ~2000 tokens).
AGENTS_MAX_LINES = 150
AGENTS_MAX_TOKENS = 2000
# Below this much agent-relevant documentation everything fits in
# AGENTS.md and a routing hop costs more than it saves.
FANOUT_THRESHOLD_TOKENS = 2000
MD_LINK = re.compile(r"\]\(([^)\s#]+)\)")
# A doc reference is a markdown link or a bare path (`docs/ci.md`); both
# count as routes when they sit on a line that names a trigger and says
# read. Lines inside code fences (layout trees) are not routes.
DOC_LINK = re.compile(r"(?<![\w/])((?:\.{1,2}/)?[\w.-]+(?:/[\w.-]+)*\.md)\b")
# A route is followed only when it names its trigger and says "read".
READ_CUE = re.compile(r"\b(read|open|load|follow)\b", re.I)
# "For <situation>, read X" is trigger-first too; "read X for details" is not.
TRIGGER_CUE = re.compile(r"\b(before|when|if|whenever|unless|first|any task)\b|^\W*for\b", re.I)


def E(text, passed, evidence):
    return {"text": text, "passed": bool(passed), "evidence": str(evidence)[:500]}


def read(path: Path) -> str:
    return path.read_text(errors="replace") if path.is_file() else ""


def tokens(text: str) -> int:
    return len(text) // 4


def load_yaml(path: Path):
    try:
        return yaml.safe_load(read(path)) or {}
    except Exception as exc:  # noqa: BLE001
        return {"__parse_error__": str(exc)}


def all_docs_text(out: Path) -> str:
    """Everything an agent could be routed to: entry files plus docs/**."""
    parts = [read(out / "AGENTS.md"), read(out / "README.md"), read(out / "CLAUDE.md")]
    docs = out / "docs"
    if docs.is_dir():
        parts += [read(p) for p in sorted(docs.rglob("*.md"))]
    return "\n".join(parts)


BLOCK_START = re.compile(r"^\s*(#|\||[-*+]\s|\d+[.)]\s|>)")


def prose_lines(text: str):
    """Logical lines outside fenced code blocks: a wrapped paragraph or
    bullet is one line, so a trigger on the first physical line and the
    read cue on the next still count as one route."""
    fenced, current = False, None
    for line in text.splitlines():
        if line.strip().startswith("```"):
            fenced = not fenced
            continue
        if fenced:
            continue
        if not line.strip():
            if current is not None:
                yield current
            current = None
        elif current is None or BLOCK_START.match(line):
            if current is not None:
                yield current
            current = line.strip()
        else:
            current += " " + line.strip()
    if current is not None:
        yield current


def doc_refs(md_path: Path, root: Path) -> list[tuple[str, Path]]:
    """(line, resolved doc path) for every existing .md the file refers to
    in prose, resolved against the file's directory or the repo root."""
    refs = []
    for line in prose_lines(read(md_path)):
        for target in DOC_LINK.findall(line):
            for base in (md_path.parent, root):
                candidate = (base / target).resolve()
                if candidate.is_file() and candidate != md_path.resolve():
                    refs.append((line, candidate))
                    break
    return refs


def soft_routes(md_path: Path, root: Path) -> list[str]:
    """Docs this file refers to without any line that names a trigger and
    says read. A passing mention next to an explicit route is fine; a doc
    whose only mentions are soft is unreachable in practice."""
    explicit, mentioned = set(), {}
    for line, doc in doc_refs(md_path, root):
        mentioned.setdefault(doc, line.strip()[:80])
        if READ_CUE.search(line) and TRIGGER_CUE.search(line):
            explicit.add(doc)
    return sorted(f"{doc.name}: {mentioned[doc]}" for doc in mentioned if doc not in explicit)


def links_resolve(out: Path, md_path: Path):
    """(all_ok, broken) for relative markdown links in one file."""
    broken = []
    for target in MD_LINK.findall(read(md_path)):
        if target.startswith(("http://", "https://", "mailto:")):
            continue
        if not (md_path.parent / target).exists():
            broken.append(target)
    return not broken, broken


def taskfile_info(out: Path):
    tf = out / "Taskfile.yml"
    if not tf.is_file():
        tf = out / "Taskfile.yaml"
    data = load_yaml(tf)
    tasks = data.get("tasks") if isinstance(data, dict) else None
    text = read(tf)
    return tf, data, (tasks if isinstance(tasks, dict) else {}), text


def common_checks(out: Path, original_tokens: int, expect_index: bool | None,
                  commands: list[str], facts: list[str], universal: list[str],
                  ci_forbidden: list[str], tool_pins: list[str]):
    ex = []
    claude = read(out / "CLAUDE.md").strip()
    ex.append(E("CLAUDE.md is exactly '@AGENTS.md' (one shared agent entrypoint)",
                claude == "@AGENTS.md", f"CLAUDE.md={claude[:60]!r}"))

    agents = read(out / "AGENTS.md")
    n_lines, n_tok = len(agents.splitlines()), tokens(agents)
    ex.append(E(f"AGENTS.md exists within budget (<= {AGENTS_MAX_LINES} lines, "
                f"<= {AGENTS_MAX_TOKENS} est. tokens)",
                agents and n_lines <= AGENTS_MAX_LINES and n_tok <= AGENTS_MAX_TOKENS,
                f"lines={n_lines} tokens={n_tok}"))
    ex.append(E("AGENTS.md tells agents to discover commands with `task --list` "
                "and reuse existing tasks",
                "task --list" in agents, "grep 'task --list' in AGENTS.md"))
    # The rules most tasks need sit in AGENTS.md itself, not behind a hop.
    carried = [u for u in universal if u.lower() in agents.lower()]
    ex.append(E(f"AGENTS.md itself carries the rules most tasks need "
                f"(>= {len(universal) - 1}/{len(universal)} universal rules inline)",
                len(carried) >= len(universal) - 1,
                f"missing={[u for u in universal if u not in carried]}"))
    # Every route is an instruction: trigger + "read", never "see also".
    soft = soft_routes(out / "AGENTS.md", out)
    # The skill recommends docs/README.md (renders in place); index.md is
    # accepted as the same thing under an older name.
    index = next((p for p in (out / "docs" / "README.md", out / "docs" / "index.md")
                  if p.is_file()), out / "docs" / "README.md")
    if index.is_file():
        soft += soft_routes(index, out)
    ex.append(E("Every route in AGENTS.md and the docs index is explicit: the line "
                "names its trigger and says read (no bare links or 'see also')",
                agents and not soft, f"soft={soft[:4]}"))

    # Routing: every relative link from the entry files and docs resolves.
    md_files = [p for p in (out / "AGENTS.md", out / "README.md") if p.is_file()]
    if (out / "docs").is_dir():
        md_files += sorted((out / "docs").rglob("*.md"))
    broken_all = []
    for md in md_files:
        ok, broken = links_resolve(out, md)
        broken_all += [f"{md.relative_to(out)} -> {b}" for b in broken]
    ex.append(E("Every relative link in AGENTS.md/README.md/docs resolves "
                "(no routes to nowhere)", md_files and not broken_all,
                f"broken={broken_all[:5]}"))

    if expect_index is False:
        ex.append(E(f"No docs index hop for a repo whose docs are under "
                    f"~{FANOUT_THRESHOLD_TOKENS} tokens (a single AGENTS.md is "
                    "cheaper than two Read calls)",
                    not index.is_file(),
                    f"docs index exists={index.is_file()} original_docs_tokens={original_tokens}"))
    else:
        # Detail must fan out to topic docs that hold content, each reached
        # from AGENTS.md directly or via the docs index (<= 2 hops). The
        # index itself is optional: with few docs, direct routes are cheaper.
        docs_root = (out / "docs").resolve()
        routers = [p for p in (out / "AGENTS.md", index) if p.is_file()]
        routed = set()
        for r in routers:
            for _, p in doc_refs(r, out):
                if docs_root in p.parents and p != index.resolve():
                    routed.add(p)
        topic_docs = [p for p in (sorted(docs_root.rglob("*.md")) if docs_root.is_dir() else [])
                      if p.resolve() != index.resolve()]
        unrouted = [p.name for p in topic_docs if p.resolve() not in routed]
        shallow = []
        for p in routed:
            lines = [l for l in read(p).splitlines() if l.strip()]
            link_lines = [l for l in lines if MD_LINK.search(l)]
            if lines and len(link_lines) / len(lines) > 0.5:
                shallow.append(p.name)
        ex.append(E("Detail fans out to >= 2 topic docs under docs/, each routed from "
                    "AGENTS.md or the docs index and holding content rather than "
                    "routing onward again (<= 2 hops)",
                    len(routed) >= 2 and not unrouted and not shallow,
                    f"routed={len(routed)} unrouted={unrouted[:4]} routing-only={shallow}"))

    # Always-loaded layer after the change: AGENTS.md alone (the index is
    # read only when AGENTS.md does not cover the task). It must shrink
    # only when the original was over budget; a small repo's AGENTS.md
    # legitimately carries everything the README did plus the new rules.
    cold = tokens(agents)
    shrunk = cold < original_tokens if original_tokens > AGENTS_MAX_TOKENS else True
    ex.append(E(f"Always-loaded layer (AGENTS.md) <= {AGENTS_MAX_TOKENS} est. tokens, "
                "and smaller than the original when that was over budget",
                agents and cold <= AGENTS_MAX_TOKENS and shrunk,
                f"before={original_tokens} after={cold}"))

    tf, data, tasks, tf_text = taskfile_info(out)
    valid = tf.is_file() and "__parse_error__" not in data and bool(tasks)
    # Each command is a tuple of acceptable spellings (raw command, or the
    # package-script wrapper that runs it).
    present = [c for c in commands if any(alt in tf_text for alt in c)]
    ex.append(E("Taskfile.yml parses as YAML and absorbs the existing commands "
                f"(>= {len(commands) - 1}/{len(commands)} present)",
                valid and len(present) >= len(commands) - 1,
                f"valid={valid} parse={str(data.get('__parse_error__', ''))[:80]!r} "
                f"missing={[c[0] for c in commands if c not in present]}"))
    no_desc = [n for n, t in tasks.items() if not (isinstance(t, dict) and t.get("desc"))]
    ex.append(E("Taskfile has a `ci` task and every task carries a desc",
                valid and "ci" in tasks and not no_desc,
                f"ci={'ci' in tasks} without_desc={no_desc[:6]}"))

    mise = read(out / "mise.toml")
    pinned = [t for t in tool_pins if re.search(rf"^\s*{re.escape(t)}\s*=", mise, re.M)]
    ex.append(E(f"mise.toml pins the tools ({', '.join(tool_pins)})",
                len(pinned) == len(tool_pins), f"pinned={pinned}"))

    hooks = out / ".githooks"
    hook_files = [p for p in (hooks / "pre-commit", hooks / "pre-push") if p.is_file()]
    hooks_ok = len(hook_files) == 2 and all("task" in read(p) for p in hook_files)
    ex.append(E("Versioned .githooks/pre-commit and pre-push exist and delegate to task",
                hooks_ok, f"hooks={[p.name for p in hook_files]}"))

    wf_dir = out / ".github" / "workflows"
    wfs = sorted(wf_dir.glob("*.y*ml")) if wf_dir.is_dir() else []
    wf_text = "\n".join(read(p) for p in wfs)
    leaked = [c for c in ci_forbidden if c in wf_text]
    ex.append(E("CI workflow is a thin wrapper: installs via mise-action and runs "
                "`task ci`, with no check commands of its own",
                wfs and "task ci" in wf_text and "mise-action" in wf_text and not leaked,
                f"workflows={[p.name for p in wfs]} leaked={leaked}"))

    boot = next((p for p in out.rglob("bootstrap*") if p.is_file()), None)
    settings = read(out / ".claude" / "settings.json")
    ex.append(E("A bootstrap exists for environments without task (script present, "
                "named in AGENTS.md or wired as a SessionStart hook)",
                boot is not None and ("bootstrap" in agents.lower() or "SessionStart" in settings),
                f"bootstrap={boot.relative_to(out) if boot else None} "
                f"agents_mentions={'bootstrap' in agents.lower()} hook={'SessionStart' in settings}"))

    everything = all_docs_text(out)
    kept = [f for f in facts if f.lower() in everything.lower()]
    ex.append(E(f"Original rules and facts survive somewhere routed "
                f"(>= {len(facts) - 1}/{len(facts)})",
                len(kept) >= len(facts) - 1,
                f"lost={[f for f in facts if f not in kept]}"))

    notes = read(out / "NOTES.md")
    ex.append(E("NOTES.md reports before/after cold-start numbers",
                bool(re.search(r"\d", notes)) and re.search(r"before", notes, re.I)
                and re.search(r"after", notes, re.I), f"len={len(notes)}"))
    return ex


def grade_orders(out: Path):
    # 886 = est. tokens of the fixture README, the only doc an agent had before.
    return common_checks(
        out, original_tokens=886, expect_index=False,
        commands=[("pytest tests/unit",), ("pytest tests/integration",),
                  ("ruff check",), ("ruff format",), ("mypy orders",),
                  ("npm run lint",), ("npm run build",),
                  ("alembic upgrade head",), ("deploy.sh",)],
        facts=["orders_status", "Decimal", "flags.yaml", "structlog",
               "DEPLOY_TOKEN", "never import"],
        universal=["Decimal", "structlog", "flags.yaml", "never import"],
        ci_forbidden=["ruff check", "mypy orders", "pytest", "npm run lint",
                      "setup-python", "setup-node"],
        tool_pins=["task", "python", "node"],
    )


def routes_only_checks(out: Path, original_tokens: int, inline_facts: list[str],
                       routed_doc_marker: str, routed_doc_trigger: str,
                       facts: list[str], commands: list[str], command_home_cues: list[str]):
    """The fixture's entry file fits the budget and is followed, so the
    cheaper path is to keep it and add routes. Grades whether the arm
    chose that path rather than a restructure."""
    ex = []
    claude = read(out / "CLAUDE.md").strip()
    agents = read(out / "AGENTS.md")
    ex.append(E("CLAUDE.md is exactly '@AGENTS.md' so Codex/Copilot share the entry "
                "(a rename plus include, not a rewrite)",
                claude == "@AGENTS.md", f"CLAUDE.md={claude[:60]!r}"))
    n_lines, n_tok = len(agents.splitlines()), tokens(agents)
    ex.append(E(f"AGENTS.md exists within budget (<= {AGENTS_MAX_TOKENS} est. tokens)",
                agents and n_tok <= AGENTS_MAX_TOKENS, f"lines={n_lines} tokens={n_tok}"))
    # Chose the cheaper path: the content that fit stayed in the entry file.
    kept = [f for f in inline_facts if f.lower() in agents.lower()]
    ex.append(E(f"Content that fit stayed in AGENTS.md rather than being fanned out "
                f"(>= {len(inline_facts) - 2}/{len(inline_facts)} entry-file facts inline)",
                len(kept) >= len(inline_facts) - 2,
                f"missing={[f for f in inline_facts if f not in kept]}"))
    docs_root = out / "docs"
    topic_docs = [p.name for p in sorted(docs_root.rglob("*.md"))
                  if p.name not in ("README.md", "index.md")] if docs_root.is_dir() else []
    ex.append(E("No fanout of content that fit: at most one topic doc under docs/ "
                "(the runbook may move there)",
                len(topic_docs) <= 1, f"topic_docs={topic_docs}"))
    # The unrouted doc is now routed, explicitly.
    runbook = next((p for p in out.rglob("*.md")
                    if routed_doc_marker in read(p) and p.name not in
                    ("AGENTS.md", "CLAUDE.md", "NOTES.md")), None)
    route_lines = []
    if runbook is not None:
        for line, doc in doc_refs(out / "AGENTS.md", out):
            if doc == runbook.resolve() and READ_CUE.search(line) and TRIGGER_CUE.search(line):
                route_lines.append(line.strip()[:80])
    ex.append(E(f"The runbook survives as its own doc and AGENTS.md routes to it "
                f"explicitly (a line naming {routed_doc_trigger} and saying read)",
                runbook is not None and bool(route_lines),
                f"runbook={runbook.relative_to(out) if runbook else None} routes={route_lines[:2]}"))
    soft = soft_routes(out / "AGENTS.md", out)
    ex.append(E("Every route in AGENTS.md is explicit (no bare links or 'see also')",
                agents and not soft, f"soft={soft[:4]}"))
    md_files = [p for p in (out / "AGENTS.md", out / "README.md") if p.is_file()]
    if docs_root.is_dir():
        md_files += sorted(docs_root.rglob("*.md"))
    broken_all = []
    for md in md_files:
        ok, broken = links_resolve(out, md)
        broken_all += [f"{md.relative_to(out)} -> {b}" for b in broken]
    ex.append(E("Every relative link in AGENTS.md/README.md/docs resolves",
                md_files and not broken_all, f"broken={broken_all[:5]}"))
    # Commands: the single existing home stays, or a Taskfile that parses wraps them.
    tf, data, tasks, tf_text = taskfile_info(out)
    if tf.is_file():
        valid = "__parse_error__" not in data and bool(tasks)
        present = [c for c in commands if any(alt in tf_text for alt in c)]
        ok = valid and len(present) >= len(commands) - 1
        why = "a Taskfile was added, so it must parse and wrap the pnpm scripts"
        evidence = f"valid={valid} missing={[c[0] for c in commands if c not in present]}"
    else:
        ok = all(c in agents for c in command_home_cues)
        why = "no Taskfile, so AGENTS.md names the pnpm scripts as the command home"
        evidence = f"cues_in_agents={[c for c in command_home_cues if c in agents]}"
    ex.append(E(f"Commands keep one discoverable home ({why})", ok, evidence))
    everything = all_docs_text(out) + read(out / "RUNBOOK.md")
    kept_all = [f for f in facts if f.lower() in everything.lower()]
    ex.append(E(f"Original rules and facts survive somewhere routed "
                f"(>= {len(facts) - 1}/{len(facts)})",
                len(kept_all) >= len(facts) - 1, f"lost={[f for f in facts if f not in kept_all]}"))
    notes = read(out / "NOTES.md")
    ex.append(E("NOTES.md reports before/after cold-start numbers and the chosen outcome",
                bool(re.search(r"\d", notes)) and re.search(r"before", notes, re.I)
                and re.search(r"after", notes, re.I), f"len={len(notes)}"))
    return ex


def grade_notify(out: Path):
    return routes_only_checks(
        out, original_tokens=1881 + 196,
        inline_facts=["never log message bodies", "HMAC-SHA256", "config/limits.yaml",
                      "prisma migrate reset", "src/generated", "build:templates",
                      "test/factories", "X-Notify-Signature", "notify_send_total"],
        routed_doc_marker="queue:pause", routed_doc_trigger="incidents/backlog",
        facts=["never log message bodies", "HMAC-SHA256", "config/limits.yaml",
               "prisma migrate reset", "src/generated", "build:templates",
               "test/factories", "queue:pause", "X-Notify-Signature",
               "notify_send_total"],
        commands=[("tsx watch src/server.ts", "pnpm dev"),
                  ("tsx src/queue/worker.ts", "pnpm worker"),
                  ("tsup", "pnpm build"), ("mjml", "build:templates"),
                  ("vitest run", "pnpm test"), ("test:integration",),
                  ("eslint", "pnpm lint"), ("tsc --noEmit", "pnpm typecheck"),
                  ("k6", "pnpm loadtest"), ("openapi-typescript", "gen:sdk"),
                  ("test/seed/load.ts", "pnpm seed"), ("queue:pause",)],
        command_home_cues=["pnpm lint", "pnpm typecheck", "pnpm test"],
    )


GRADERS = {"eval-0": grade_orders, "eval-1": grade_notify}


# --- downstream tasks: does the restructured repo make later work cheaper? ---

CONVENTION_HOMES = {"AGENTS.md", "CLAUDE.md", "README.md", "RUNBOOK.md"}


def convention_files(out: Path) -> list[Path]:
    """Where a rule belongs in any state: the entry files, or a routed doc."""
    files = [out / n for n in ("AGENTS.md", "CLAUDE.md", "README.md", "RUNBOOK.md")]
    if (out / "docs").is_dir():
        files += sorted((out / "docs").rglob("*.md"))
    return [f for f in files if f.is_file()]


def ds_single_test(out: Path, selector: str, raw_checks: list[str]):
    answer = read(out / "ANSWER.md")
    # Any runner's single entrypoint counts: the point is one command that
    # is the definition of green, not which runner provides it.
    via_task = bool(re.search(r"\b(task|make|npm run|pnpm|just) (ci|check|verify|lint|test)\b", answer))
    raw_found = [c for c in raw_checks if c in answer]
    return [
        E(f"ANSWER.md names the single-test command ({selector})",
          selector in answer, answer[:160]),
        E("ANSWER.md names the pre-push checks: the repo's one entrypoint "
          "(task/make ci or check) or every raw check command",
          via_task or len(raw_found) == len(raw_checks),
          f"task={via_task} raw={raw_found}"),
    ]


def ds_add_rule(out: Path, phrases: list[str], preexisting: set[str] = frozenset()):
    """The rule lands in a file the repo already used for conventions, not
    in a new top-level file; `preexisting` lists the root .md files that
    state started with."""
    homes = [f for f in convention_files(out)] + [
        out / n for n in preexisting if (out / n).is_file() and out / n not in convention_files(out)]
    hits = [str(f.relative_to(out)) for f in homes
            if any(ph.lower() in read(f).lower() for ph in phrases)]
    new_root = [p.name for p in out.glob("*.md")
                if p.name not in CONVENTION_HOMES | {"ANSWER.md", "NOTES.md"} | set(preexisting)]
    return [E("Rule added where this repo keeps its conventions (entry file or a "
              "routed doc), not in a new top-level file",
              bool(hits) and not new_root, f"in={hits[:3]} new_root_md={new_root}")]


def ds_new_command(out: Path):
    tf, data, tasks, tf_text = taskfile_info(out)
    homes = {"Taskfile.yml": tf_text, "Makefile": read(out / "Makefile"),
             "package.json": read(out / "package.json")}
    where = [k for k, v in homes.items() if "--cov=orders" in v]
    if tf.is_file():
        ok = "Taskfile.yml" in where and "__parse_error__" not in data
        why = "Taskfile present, so it must be a task and the file must still parse"
    else:
        ok = bool(where)
        why = "no Taskfile, so Makefile or package.json"
    answer = read(out / "ANSWER.md")
    return [
        E(f"Coverage command added to the repo's runnable home ({why})", ok,
          f"found_in={where} parse={str(data.get('__parse_error__', ''))[:60]!r}"),
        E("ANSWER.md tells a contributor how to invoke it",
          bool(re.search(r"\b(task|make|npm run|pnpm)\s+\S+", answer)), answer[:120]),
    ]


def ds_new_channel(out: Path):
    answer = read(out / "ANSWER.md").lower()
    items = [
        ("a registry entry", ["registry"]),
        ("a template directory", ["template"]),
        ("an integration test", ["integration test"]),
        ("an entry in docs/channels.md", ["channels.md"]),
        ("the PII rule (never log message bodies or recipients)",
         ["message bod", "recipient"]),
        ("the retry rule (send is idempotent; retries live in the worker)",
         ["idempot", "never implement retries", "retries inside", "backoff"]),
    ]
    return [E(f"Checklist names {label}", any(k in answer for k in keys), "")
            for label, keys in items]


def ds_answer_items(out: Path, items: list[tuple[str, list[str]]]):
    """One check per fact the answer must carry; each fact lives only in
    a doc the layout has to route the agent to."""
    answer = read(out / "ANSWER.md").lower()
    return [E(f"ANSWER.md includes {label}", any(k.lower() in answer for k in keys), "")
            for label, keys in items]


DOWNSTREAM = {
    ("eval-0", "single-test"): lambda out: ds_single_test(
        out, "test_pricing.py::test_discount", ["ruff check", "mypy", "npm run lint"]),
    ("eval-0", "new-command"): ds_new_command,
    ("eval-0", "add-rule"): lambda out, pre=frozenset(): ds_add_rule(out, ["minor units"], pre),
    ("eval-0", "prod-incident"): lambda out: ds_answer_items(out, [
        ("the rollback command (deploy.sh prod --rollback or its task)", ["--rollback", "rollback"]),
        ("the DEPLOY_TOKEN requirement", ["DEPLOY_TOKEN"]),
        ("that prod deploys happen from main", ["from main", "main branch", "on main", "from `main`"]),
        ("alembic upgrade head for the out-of-date database", ["upgrade head"]),
    ]),
    ("eval-1", "single-test"): lambda out: ds_single_test(
        out, "email.test.ts", ["pnpm lint", "pnpm typecheck", "pnpm test"]),
    ("eval-1", "new-channel"): ds_new_channel,
    ("eval-1", "add-rule"): lambda out, pre=frozenset(): ds_add_rule(out, ["src/links.ts", "raw url"], pre),
    ("eval-1", "queue-backlog"): lambda out: ds_answer_items(out, [
        ("checking worker pods (kubectl get pods -l app=notify-worker)", ["notify-worker"]),
        ("the Redis memory 80% check before scaling workers", ["80"]),
        ("pausing the dominant channel with queue:pause", ["queue:pause"]),
        ("resuming with queue:resume", ["queue:resume"]),
    ]),
}


def write_grading(target: Path, expectations: list[dict]) -> int:
    passed = sum(1 for e in expectations if e["passed"])
    target.write_text(json.dumps(
        {"expectations": expectations,
         "summary": {"passed": passed, "failed": len(expectations) - passed,
                     "total": len(expectations),
                     "pass_rate": round(passed / len(expectations), 4) if expectations else 0}},
        indent=2))
    return passed


def main():
    iteration = Path(sys.argv[1])
    for eval_dir in sorted(iteration.glob("eval-*")):
        match = re.match(r"(eval-\d+)(?:-|$)", eval_dir.name)
        grader = GRADERS[match.group(1)]
        for arm in ("with_skill", "without_skill"):
            out = eval_dir / arm / "outputs"
            if not out.is_dir():
                continue
            expectations = grader(out)
            passed = write_grading(eval_dir / arm / "grading.json", expectations)
            print(f"  {eval_dir.name}/{arm}: {passed}/{len(expectations)}")
        downstream = eval_dir / "downstream"
        if downstream.is_dir():
            totals: dict[str, list[int]] = {}
            for run_dir in sorted(downstream.glob("*/*/rep-*")):
                state, task_id = run_dir.parts[-3], run_dir.parts[-2]
                task_grader = DOWNSTREAM.get((match.group(1), task_id))
                if task_grader is None or not (run_dir / "outputs").is_dir():
                    continue
                # Root files the state started with (the arm's output for the
                # after-* states) are not "new files" when a task edits them.
                source = {"after-baseline": eval_dir / "without_skill" / "outputs",
                          "after-skill": eval_dir / "with_skill" / "outputs"}.get(state)
                preexisting = frozenset(p.name for p in source.glob("*.md")) if source else frozenset()
                if task_id == "add-rule":
                    expectations = task_grader(run_dir / "outputs", preexisting)
                else:
                    expectations = task_grader(run_dir / "outputs")
                passed = write_grading(run_dir / "grading.json", expectations)
                totals.setdefault(state, [0, 0])
                totals[state][0] += passed
                totals[state][1] += len(expectations)
            for state, (passed, total) in totals.items():
                print(f"  {eval_dir.name}/downstream/{state}: {passed}/{total} adherence")


if __name__ == "__main__":
    sys.exit(main())
