#!/usr/bin/env python3
"""Grade repo-optimization eval runs. Usage: grade.py <iteration-dir>.

Expects <iteration-dir>/eval-*/{with_skill,without_skill}/outputs/ as laid
out by scripts/eval_skills.py (run via `task eval:skills NAME=repo-optimization`).
Every check is static: it inspects the files the arm wrote, never runs
them. Two families of check:

- structure: the entry shape (CLAUDE.md == @AGENTS.md, an AGENTS.md that
  carries the universal rules within budget, explicit conditional routes,
  hop depth, an index only when it pays), the Taskfile as the single home
  for commands, thin CI, hooks, a sandbox bootstrap;
- preservation: distinctive facts from the fixture docs survive somewhere
  the new layout routes to, the rules most tasks need sit in AGENTS.md
  itself, and the always-loaded cost went down.

Writes grading.json per arm and prints a pass/total summary.
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
DOC_LINK = re.compile(r"\]\(([^)\s#]+\.md)\)")
# A route is followed only when it names its trigger and says "read".
READ_CUE = re.compile(r"\b(read|open|load|follow)\b", re.I)
TRIGGER_CUE = re.compile(r"\b(before|when|if|whenever|unless|first|any task)\b", re.I)


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


def soft_routes(md_path: Path) -> list[str]:
    """Lines linking a .md doc without a trigger + read cue on the same line."""
    soft = []
    for line in read(md_path).splitlines():
        if DOC_LINK.search(line) and not (READ_CUE.search(line) and TRIGGER_CUE.search(line)):
            soft.append(line.strip()[:80])
    return soft


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
    soft = soft_routes(out / "AGENTS.md")
    index = out / "docs" / "index.md"
    if index.is_file():
        soft += soft_routes(index)
    ex.append(E("Every route in AGENTS.md and docs/index.md is explicit: the line "
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
        ex.append(E(f"No docs/index.md hop for a repo whose docs are under "
                    f"~{FANOUT_THRESHOLD_TOKENS} tokens (a single AGENTS.md is "
                    "cheaper than two Read calls)",
                    not index.is_file(),
                    f"docs/index.md exists={index.is_file()} original_docs_tokens={original_tokens}"))
    else:
        routed = [t for t in MD_LINK.findall(read(index))
                  if not t.startswith("http") and (index.parent / t).is_file()]
        # Routed docs must carry content, not just route again (max two
        # hops): a doc where most lines are links is another index.
        shallow = []
        for t in routed:
            lines = [l for l in read(index.parent / t).splitlines() if l.strip()]
            link_lines = [l for l in lines if MD_LINK.search(l)]
            if lines and len(link_lines) / len(lines) > 0.5:
                shallow.append(t)
        ex.append(E("docs/index.md routes to >= 2 topic docs, each holding content "
                    "rather than routing onward again (<= 2 hops)",
                    len(routed) >= 2 and not shallow,
                    f"routed={len(routed)} routing-only={shallow}"))

    # Always-loaded layer after the change: AGENTS.md alone (the index is
    # read only when AGENTS.md does not cover the task).
    cold = tokens(agents)
    ex.append(E(f"Always-loaded layer (AGENTS.md) <= {AGENTS_MAX_TOKENS} est. tokens "
                "and below the original always-loaded docs",
                agents and cold <= AGENTS_MAX_TOKENS and cold < original_tokens,
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


def grade_notify(out: Path):
    return common_checks(
        out, original_tokens=1871 + 196, expect_index=True,
        commands=[("tsx watch src/server.ts", "pnpm dev"),
                  ("tsx src/queue/worker.ts", "pnpm worker"),
                  ("tsup", "pnpm build"), ("mjml", "build:templates"),
                  ("vitest run", "pnpm test"), ("test:integration",),
                  ("eslint", "pnpm lint"), ("tsc --noEmit", "pnpm typecheck"),
                  ("k6", "pnpm loadtest"), ("openapi-typescript", "gen:sdk"),
                  ("test/seed/load.ts", "pnpm seed"), ("queue:pause",)],
        facts=["never log message bodies", "HMAC-SHA256", "config/limits.yaml",
               "prisma migrate reset", "src/generated", "build:templates",
               "test/factories", "queue:pause", "X-Notify-Signature",
               "notify_send_total"],
        universal=["never log message bodies", "src/generated",
                   "prisma migrate reset", "test/factories"],
        ci_forbidden=["pnpm lint", "pnpm test", "pnpm typecheck", "tsc --noEmit",
                      "setup-node", "pnpm/action-setup"],
        tool_pins=["task", "node", "pnpm"],
    )


GRADERS = {"eval-0": grade_orders, "eval-1": grade_notify}


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
            passed = sum(1 for e in expectations if e["passed"])
            (eval_dir / arm / "grading.json").write_text(json.dumps(
                {"expectations": expectations,
                 "summary": {"passed": passed, "failed": len(expectations) - passed,
                             "total": len(expectations),
                             "pass_rate": round(passed / len(expectations), 4)}},
                indent=2))
            print(f"  {eval_dir.name}/{arm}: {passed}/{len(expectations)}")


if __name__ == "__main__":
    sys.exit(main())
