#!/usr/bin/env python3
"""Triage a repository for the repo-health pass: which of the four phases
earn their cost. Stdlib only.

Usage: python3 scan_repo_health.py [repo] [--json]

Reimplements nothing. It imports the sibling skills' scanners from the
directory beside this skill's:

  bus-factor/scripts/scan_bus_factor.py
  repo-consistency-checker/scripts/scan_consistency.py
  repo-declutter/scripts/audit_noise.py

adds the agent-entry signals none of them compute (entry file, its size,
unrouted docs, command homes, CI), and prints one table:

  phase | signals | verdict

A verdict is a lead. "run" means the phase audits and then applies; "skip"
means the repo shows none of that phase's symptoms, so the pass leaves it
out unless the user asked for it by name. Thresholds live here, once.

Exit 2 when a sibling skill is missing: install the family with
`task install:skills GROUP=repo`.
"""
from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

# Importing the siblings must not litter their scripts/ with bytecode: a
# skills repo's checks reject bundled files nothing routes to.
sys.dont_write_bytecode = True

SKILLS_DIR = Path(__file__).resolve().parents[2]
SIBLINGS = {
    "bus_factor": SKILLS_DIR / "bus-factor" / "scripts" / "scan_bus_factor.py",
    "consistency": SKILLS_DIR / "repo-consistency-checker" / "scripts" / "scan_consistency.py",
    "noise": SKILLS_DIR / "repo-declutter" / "scripts" / "audit_noise.py",
}

# Thresholds. A phase runs on the first signal that trips.
CONCENTRATION_MIN_COMMITS = 5      # a single-holder path matters once it has history
ENTRY_MAX_TOKENS = 2000            # repo-optimization's AGENTS.md budget (chars/4)
HEDGES_MIN = 3                     # hedges in one doc before it counts as noise
HISTORY_HOMES = re.compile(r"^(CHANGELOG|CHANGES|HISTORY|RELEASES|RELEASE[-_]NOTES)", re.I)
ENTRY_FILES = ("AGENTS.md", "CLAUDE.md", ".github/copilot-instructions.md")
RUNNER_FILES = ("Makefile", "Taskfile.yml", "Taskfile.yaml", "Justfile", "justfile")
CI_GLOBS = (".github/workflows/*.yml", ".github/workflows/*.yaml", ".gitlab-ci.yml",
            ".circleci/config.yml", "azure-pipelines.yml", "bitbucket-pipelines.yml")


def load(name: str):
    path = SIBLINGS[name]
    if not path.is_file():
        print(f"scan_repo_health: {path} not found. The pass needs the whole repo family "
              "installed beside this skill: task install:skills GROUP=repo", file=sys.stderr)
        sys.exit(2)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read(path: Path) -> str:
    try:
        return path.read_text(errors="replace")
    except OSError:
        return ""


def bus_factor_signals(root: Path) -> tuple[list[str], list[str]]:
    scan = load("bus_factor")
    result = scan.scan(root, "")
    signals, notes = [], []
    if result["undocumented_env_vars"]:
        signals.append(f"{len(result['undocumented_env_vars'])} env var(s) read in code but documented nowhere")
    kinds = sorted({p["kind"] for p in result["external_pointers"]})
    if kinds:
        signals.append(f"{len(result['external_pointers'])} pointer(s) to {', '.join(kinds)}")
    if result["manual_steps"]:
        signals.append(f"{len(result['manual_steps'])} manual step(s) described in docs or scripts")
    # Absent files are context for the newcomer walk, not a symptom: most
    # healthy repos have no runbook or decision log.
    missing = [k for k, v in result["presence"].items() if v == "MISSING"]
    if missing:
        notes.append(f"absent: {', '.join(missing)}")
    c = result["concentration"]
    if c and c["authors"] > 1:
        held = [d for d in c["dirs"] if d["bus_factor"] == 1 and d["commits"] >= CONCENTRATION_MIN_COMMITS]
        if held:
            signals.append(f"{len(held)} path(s) held by one author: "
                           + ", ".join(f"{d['path']} ({d['holders'][0]})" for d in held[:3]))
    return signals, notes


def consistency_signals(root: Path) -> tuple[list[str], list[str]]:
    scan = load("consistency")
    scanner = scan.Scanner(root)
    scanner.run()
    signals, notes = [], []
    labels = {
        "broken_references": "broken reference(s)", "undefined_commands": "undefined command(s)",
        "duplicate_paragraphs": "duplicated paragraph(s)", "orphan_docs": "orphan doc(s)",
        "commented_out_code": "run(s) of commented-out code", "markers": "TODO/FIXME marker(s)",
    }
    for kind, label in labels.items():
        n = len(scanner.findings.get(kind, []))
        if n:
            signals.append(f"{n} {label}" + (" (hard)" if kind in scan.HARD else ""))
    numeric = len(scanner.findings.get("numeric_claims", []))
    if numeric:
        notes.append(f"{numeric} numeric claim(s) to verify by hand")
    return signals, notes


def declutter_signals(root: Path) -> list[str]:
    noise = load("noise")
    signals = []
    noisy_docs, noisy_code = [], []
    for path in noise.files_under(root):
        text = noise.read(path)
        if not text:
            continue
        rel = str(path.relative_to(root))
        if path.suffix in noise.DOC_SUFFIXES:
            if HISTORY_HOMES.match(path.name):
                continue  # history belongs there; declutter moves it in, not out
            row = noise.scan_doc(path, text, rel)
            if row["history"] or row["changelog_headings"] or row["dated"]:
                noisy_docs.append(f"{rel} (history)")
            elif row["tokens"] > noise.DOC_WARN_TOKENS and row["hedges"] >= HEDGES_MIN:
                noisy_docs.append(f"{rel} ({row['tokens']} tokens, {row['hedges']} hedges)")
        elif marker := noise.marker_for(path):
            row = noise.scan_code(path, text, marker, rel)
            if row["banners"] or row["attributions"] or row["density"] > noise.COMMENT_DENSITY_WARN:
                noisy_code.append(rel)
    if noisy_docs:
        signals.append(f"{len(noisy_docs)} doc(s) carrying history or hedged prose: " + ", ".join(noisy_docs[:3]))
    if noisy_code:
        signals.append(f"{len(noisy_code)} file(s) with banners, attributions or dense comments: "
                       + ", ".join(noisy_code[:3]))
    return signals


def optimization_signals(root: Path) -> list[str]:
    signals = []
    entry = next((root / f for f in ENTRY_FILES if (root / f).is_file()), None)
    if entry is None:
        signals.append("no agent entry file (AGENTS.md or CLAUDE.md)")
        routed_text = ""
    else:
        text = read(entry)
        if text.strip() == "@AGENTS.md" and (root / "AGENTS.md").is_file():
            text = read(root / "AGENTS.md")
        tokens = len(text) // 4
        if tokens > ENTRY_MAX_TOKENS:
            signals.append(f"{entry.name} is {tokens} tokens (budget {ENTRY_MAX_TOKENS})")
        routed_text = text
        index = root / "docs" / "README.md"
        if index.is_file() and "docs/README.md" in text:
            routed_text += read(index)
    docs = root / "docs"
    if docs.is_dir():
        unrouted = [p for p in sorted(docs.rglob("*.md")) if p.name != "README.md"
                    and p.name not in routed_text and str(p.relative_to(root)) not in routed_text]
        if unrouted:
            signals.append(f"{len(unrouted)} doc(s) no entry file routes to: "
                           + ", ".join(str(p.relative_to(root)) for p in unrouted[:3]))
    homes = [f for f in RUNNER_FILES if (root / f).is_file()]
    package = root / "package.json"
    if package.is_file() and '"scripts"' in read(package):
        homes.append("package.json scripts")
    if not homes:
        homes += [d for d in ("scripts", "bin") if (root / d).is_dir() and any((root / d).iterdir())]
    if len(homes) > 1:
        signals.append(f"commands live in {len(homes)} homes: {', '.join(homes)}")
    if not any(root.glob(g) for g in CI_GLOBS):
        signals.append("no CI workflow")
    return signals


def triage(root: Path) -> list[dict]:
    bus, bus_notes = bus_factor_signals(root)
    consistency, notes = consistency_signals(root)
    phases = [
        ("bus-factor", bus, bus_notes),
        ("repo-consistency-checker", consistency, notes),
        ("repo-declutter", declutter_signals(root), []),
        ("repo-optimization", optimization_signals(root), []),
    ]
    return [{"phase": name, "signals": sig, "notes": note, "verdict": "run" if sig else "skip"}
            for name, sig, note in phases]


def table(rows: list[dict]) -> str:
    out = ["| phase | signals | verdict |", "|---|---|---|"]
    for r in rows:
        cell = "; ".join(r["signals"] + [f"note: {n}" for n in r["notes"]]) or "none"
        out.append(f"| {r['phase']} | {cell.replace('|', '/')} | {r['verdict']} |")
    return "\n".join(out)


def main(argv: list[str]) -> int:
    args = [a for a in argv if not a.startswith("--")]
    root = Path(args[0] if args else ".").resolve()
    if not root.is_dir():
        print(f"scan_repo_health: {root} is not a directory", file=sys.stderr)
        return 2
    rows = triage(root)
    if "--json" in argv:
        print(json.dumps({"repo": str(root), "phases": rows}, indent=2))
    else:
        running = [r["phase"] for r in rows if r["verdict"] == "run"]
        print(f"# Repo-health triage: {root}\n")
        print(table(rows))
        print(f"\nRun {len(running)} of 4 phases" + (f": {', '.join(running)}" if running else
              ". Nothing to do: report this table, open no branch."))
        print("Signals are leads: each phase audits before it changes anything.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
