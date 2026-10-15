#!/usr/bin/env python3
"""Scan a repository for bus-factor risk. Stdlib only.

Usage: python3 scan_bus_factor.py [repo] [--json] [--since 2.years]

--since limits concentration to recent history (default: all of it).

Prints leads, not findings - each still needs checking against the repo:

- concentration: per file and per directory, how many authors cover half
  the commits (the bus factor of that path) and who holds it; needs git;
- undocumented env vars: names read in code that no doc, example env file
  or config template mentions;
- external pointers: lines that send the reader to a person, a chat, a
  wiki or a personal machine instead of carrying the knowledge;
- manual steps: lines describing work done by hand or on a server;
- unexplained constants: module-level numeric constants with no comment;
- presence: the files that usually carry setup, conventions and ownership.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build",
             ".tox", ".mypy_cache", ".pytest_cache", "vendor", "target", ".evals", ".skill"}
CODE_EXT = {".py", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".go", ".rb", ".java", ".kt",
            ".cs", ".rs", ".php", ".sh", ".bash", ".ps1"}
DOC_EXT = {".md", ".rst", ".txt", ".adoc"}
CONFIG_NAMES = re.compile(r"(^\.env\.(example|sample|template|dist)$|^env\.example$|"
                          r"docker-compose.*\.ya?ml$|\.ya?ml$|\.toml$|\.ini$|\.cfg$|^Makefile$|"
                          r"^Taskfile\.ya?ml$|^Justfile$|^justfile$)")

ENV_PATTERNS = [
    re.compile(r"os\.environ(?:\.get)?\s*[\[(]\s*['\"]([A-Z][A-Z0-9_]{2,})['\"]"),
    re.compile(r"os\.getenv\(\s*['\"]([A-Z][A-Z0-9_]{2,})['\"]"),
    re.compile(r"process\.env\.([A-Z][A-Z0-9_]{2,})"),
    re.compile(r"process\.env\[\s*['\"]([A-Z][A-Z0-9_]{2,})['\"]"),
    re.compile(r"ENV(?:\.fetch)?[\[(]\s*['\"]([A-Z][A-Z0-9_]{2,})['\"]"),
    re.compile(r"Getenv\(\s*\"([A-Z][A-Z0-9_]{2,})\""),
    re.compile(r"Environment\.GetEnvironmentVariable\(\s*\"([A-Z][A-Z0-9_]{2,})\""),
    re.compile(r"\$\{([A-Z][A-Z0-9_]{2,})(?::?[-?][^}]*)?\}"),
]
SHELL_BUILTIN_VARS = {"HOME", "PATH", "PWD", "USER", "SHELL", "TMPDIR", "LANG", "TERM",
                      "CI", "HOSTNAME", "OLDPWD", "BASH_SOURCE", "GITHUB_TOKEN",
                      "GITHUB_SHA", "GITHUB_REF", "GITHUB_WORKSPACE", "RUNNER_TEMP"}

EXTERNAL = [
    ("person", re.compile(r"(?i:\b(?:ask|ping|talk to|check with|contact|dm)\b)\s+"
                          r"(?:him|her|them|@?[A-Z][a-z]+)\b")),
    ("person", re.compile(r"\b(?:only|just)\s+[A-Z][a-z]+\s+(?:knows|can|has)\b")),
    ("person", re.compile(r"\b(?!(?:What|Where|How|Who|When|Why|Which|This|That|It|He|She|They)\b)"
                          r"[A-Z][a-z]+ (?:does|handles|owns|knows|runs) (?:the|all|our)\b")),
    ("chat", re.compile(r"(slack\.com|\bslack\b|#[a-z][\w-]*-(dev|team|eng|ops|help)\b|"
                        r"teams\.microsoft|discord\.(gg|com))", re.I)),
    ("wiki", re.compile(r"(atlassian\.net|confluence|notion\.so|docs\.google\.com|"
                        r"sharepoint\.com|\bthe wiki\b|quip\.com)", re.I)),
    ("machine", re.compile(r"(/Users/[a-z][\w.-]+|/home/[a-z][\w.-]+|[A-Z]:\\\\?Users\\\\?\w+)")),
]
# A bare @handle only means a person in prose; in code it is a decorator,
# a package scope or a template key.
HANDLE = re.compile(r"(?<![\w./\"'@`-])@[a-z][\w-]{2,}\b(?![/.\w-])", re.I)
MANUAL = re.compile(r"\b(manually|by hand|ssh (in)?to|on the (prod|production|build) "
                    r"(box|server|machine)|copy (it|the file) (to|onto)|remember to)\b", re.I)
AUTHOR_MARK = "@@author@@"
CONSTANT = re.compile(r"^([A-Z][A-Z0-9_]{2,})\s*(?::\s*\w+\s*)?=\s*(-?\d[\d_.]*)\s*$")

PRESENCE = {
    "readme": ["README.md", "README.rst", "README"],
    "contributing": ["CONTRIBUTING.md", "docs/CONTRIBUTING.md", ".github/CONTRIBUTING.md"],
    "agent entry": ["AGENTS.md", "CLAUDE.md"],
    "codeowners": ["CODEOWNERS", ".github/CODEOWNERS", "docs/CODEOWNERS"],
    "env example": [".env.example", ".env.sample", ".env.template", "env.example"],
    "toolchain pin": [".tool-versions", "mise.toml", ".mise.toml", ".python-version",
                      ".nvmrc", ".node-version", "rust-toolchain.toml", "go.mod",
                      ".ruby-version", "global.json"],
    "task runner": ["Taskfile.yml", "Taskfile.yaml", "Makefile", "justfile", "Justfile"],
    "ci": [".github/workflows", ".gitlab-ci.yml", "azure-pipelines.yml", ".circleci",
           "Jenkinsfile", "bitbucket-pipelines.yml"],
    "decisions": ["docs/adr", "docs/decisions", "adr", "doc/adr", "docs/architecture/decisions"],
    "runbook": ["RUNBOOK.md", "docs/runbook.md", "docs/runbooks", "OPERATIONS.md"],
    "changelog": ["CHANGELOG.md", "CHANGES.md", "HISTORY.md"],
}


def files(root: Path):
    for path in sorted(root.rglob("*")):
        if path.is_file() and not any(p in SKIP_DIRS for p in path.relative_to(root).parts):
            yield path


def read(path: Path) -> str:
    try:
        return path.read_text(errors="replace")
    except OSError:
        return ""


def git(root: Path, *args: str) -> str:
    try:
        return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True,
                              timeout=120).stdout
    except (OSError, subprocess.SubprocessError):
        return ""


def bus_factor(counts: Counter) -> tuple[int, list[str]]:
    """Fewest authors whose commits cover at least half the total."""
    total, covered, holders = sum(counts.values()), 0, []
    for author, n in counts.most_common():
        holders.append(author)
        covered += n
        if covered * 2 >= total:
            break
    return len(holders), holders


def concentration(root: Path, since: str):
    if not (root / ".git").exists():
        return None
    window = [f"--since={since}"] if since else []
    log = git(root, "log", *window, "--no-merges", "--no-renames",
              f"--format={AUTHOR_MARK}%aN", "--name-only")
    per_file: dict[str, Counter] = defaultdict(Counter)
    author = None
    for line in log.splitlines():
        if line.startswith(AUTHOR_MARK):
            author = line[len(AUTHOR_MARK):]
        elif line.strip() and author:
            per_file[line.strip()][author] += 1
    live = {f: c for f, c in per_file.items() if (root / f).exists()}
    per_dir: dict[str, Counter] = defaultdict(Counter)
    overall: Counter = Counter()
    for f, c in live.items():
        top = f.split("/", 1)[0] if "/" in f else "."
        per_dir[top].update(c)
        overall.update(c)
    single = sorted(f for f, c in live.items() if len(c) == 1)
    return {
        "authors": len(overall),
        "repo_bus_factor": bus_factor(overall)[0] if overall else 0,
        "dirs": sorted(({"path": d, "bus_factor": bus_factor(c)[0], "holders": bus_factor(c)[1],
                         "commits": sum(c.values()), "authors": len(c)}
                        for d, c in per_dir.items()), key=lambda r: (r["bus_factor"], -r["commits"])),
        "single_author_files": [{"path": f, "author": next(iter(live[f])),
                                 "commits": sum(live[f].values())} for f in single],
        "single_author_share": round(len(single) / len(live), 2) if live else 0,
    }


def scan(root: Path, since: str) -> dict:
    env_reads: dict[str, list[str]] = defaultdict(list)
    doc_text, leads, manual, constants = [], [], [], []
    for path in files(root):
        rel = str(path.relative_to(root))
        text = read(path)
        is_code = path.suffix in CODE_EXT
        is_doc = path.suffix in DOC_EXT or path.name.startswith("README")
        if is_doc or CONFIG_NAMES.search(path.name) or path.name.startswith(".env."):
            doc_text.append(text)
        if not (is_code or is_doc or CONFIG_NAMES.search(path.name)):
            continue
        lines = text.splitlines()
        fenced = False
        for i, line in enumerate(lines, 1):
            if is_doc and line.lstrip().startswith(("```", "~~~")):
                fenced = not fenced
            if is_code:
                for pat in ENV_PATTERNS:
                    for name in pat.findall(line):
                        if name not in SHELL_BUILTIN_VARS:
                            env_reads[name].append(f"{rel}:{i}")
                m = CONSTANT.match(line)
                prev = lines[i - 2].strip() if i > 1 else ""
                if m and m.group(2) not in {"0", "1"} and "#" not in line and "//" not in line \
                        and not prev.startswith(("#", "//")):
                    constants.append({"where": f"{rel}:{i}", "name": m.group(1), "value": m.group(2)})
            kinds = {kind for kind, pat in EXTERNAL if pat.search(line)}
            if is_doc and not fenced and HANDLE.search(line):
                kinds.add("person")
            kinds = sorted(kinds)
            if kinds:
                leads.append({"where": f"{rel}:{i}", "kind": ", ".join(kinds),
                              "line": line.strip()[:160]})
            if MANUAL.search(line):
                manual.append({"where": f"{rel}:{i}", "line": line.strip()[:160]})
    docs = "\n".join(doc_text)
    undocumented = [{"name": n, "read_at": sorted(set(w))[:3]}
                    for n, w in sorted(env_reads.items()) if n not in docs]
    presence = {}
    for label, candidates in PRESENCE.items():
        hit = next((c for c in candidates if (root / c).exists()), None)
        presence[label] = hit or "MISSING"
    return {
        "repo": str(root),
        "presence": presence,
        "concentration": concentration(root, since),
        "env_vars_read": len(env_reads),
        "undocumented_env_vars": undocumented,
        "external_pointers": leads,
        "manual_steps": manual,
        "unexplained_constants": constants,
    }


def table(headers: list[str], rows: list[list]) -> str:
    out = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    out += ["| " + " | ".join(str(c).replace("|", "\\|") for c in r) + " |" for r in rows]
    return "\n".join(out)


def report(r: dict) -> str:
    parts = [f"# Bus-factor scan: {r['repo']}", "", "Leads, not findings: confirm each "
             "against the repo before reporting it.", "", "## Presence", "",
             table(["area", "file"], [[k, v] for k, v in r["presence"].items()])]
    c = r["concentration"]
    parts += ["", "## Concentration", ""]
    if c is None:
        parts.append("No git history: concentration not measured.")
    else:
        parts.append(f"{c['authors']} author(s); repo bus factor {c['repo_bus_factor']}; "
                     f"{int(c['single_author_share'] * 100)}% of live files have one author.")
        parts += ["", table(["path", "bus factor", "holders", "commits", "authors"],
                            [[d["path"], d["bus_factor"], ", ".join(d["holders"]), d["commits"],
                              d["authors"]] for d in c["dirs"]])]
        if c["single_author_files"]:
            parts += ["", "Single-author files (most commits first):", "",
                      table(["file", "author", "commits"],
                            [[f["path"], f["author"], f["commits"]] for f in
                             sorted(c["single_author_files"], key=lambda f: -f["commits"])[:25]])]
    parts += ["", f"## Env vars read in code but in no doc or example ({len(r['undocumented_env_vars'])}"
              f" of {r['env_vars_read']})", ""]
    parts.append(table(["name", "read at"], [[u["name"], ", ".join(u["read_at"])]
                                             for u in r["undocumented_env_vars"]])
                 if r["undocumented_env_vars"] else "None.")
    for title, key, cols in [("External pointers", "external_pointers", ["where", "kind", "line"]),
                             ("Manual steps", "manual_steps", ["where", "line"]),
                             ("Constants with no comment", "unexplained_constants",
                              ["where", "name", "value"])]:
        rows = r[key]
        parts += ["", f"## {title} ({len(rows)})", ""]
        parts.append(table(cols, [[row[k] for k in cols] for row in rows[:40]]) if rows else "None.")
    return "\n".join(parts) + "\n"


def main(argv: list[str]) -> int:
    args = [a for a in argv if not a.startswith("--")]
    since = ""
    if "--since" in argv:
        i = argv.index("--since")
        since = argv[i + 1]
        args = [a for a in args if a != since]
    root = Path(args[0] if args else ".").resolve()
    if not root.is_dir():
        print(f"scan_bus_factor: {root} is not a directory", file=sys.stderr)
        return 2
    result = scan(root, since)
    print(json.dumps(result, indent=2) if "--json" in argv else report(result))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
