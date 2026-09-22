#!/usr/bin/env python3
"""Mechanical consistency scan for a repository (stdlib only).

Usage:
    python3 scan_consistency.py [ROOT] [--json] [--fail-on hard|any|none]

Finds the drift and redundancy that can be detected without understanding
the code, so a human or agent can spend their reading on what cannot:

  broken_references   relative paths / markdown links (in docs and in code
                      comments) that point at files that do not exist
  undefined_commands  `task X`, `make X`, `npm run X`, `pnpm X`, `yarn X`
                      whose target is defined nowhere in the repo
  duplicate_paragraphs prose paragraphs repeated (near-)verbatim across or
                      within files - the same fact stated twice
  orphan_docs         markdown files no other file links to or names
  commented_out_code  runs of comment lines that look like code
  markers             TODO / FIXME / XXX / HACK / TBD to re-check
  numeric_claims      sentences in docs that state a number with a limit-ish
                      word, plus the code lines carrying the same number

Every hit is a lead, not a verdict: confirm it with two locations and a
quote from each before reporting it. Exit status: 1 when "hard" findings
(broken references, undefined commands) exist, unless --fail-on changes
that; --fail-on any also fails on the softer classes; --fail-on none
always exits 0.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

SKIP_DIRS = {
    ".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build",
    "target", "vendor", ".evals", ".tox", ".mypy_cache", ".pytest_cache",
    ".idea", ".vscode", "coverage", ".next", ".cache",
}
DOC_EXT = {".md", ".mdx", ".rst", ".txt"}
HASH_COMMENT_EXT = {
    ".py", ".sh", ".bash", ".zsh", ".yml", ".yaml", ".toml", ".rb", ".pl",
    ".ps1", ".cfg", ".ini", ".tf", ".r", ".jl", ".ex", ".exs",
}
SLASH_COMMENT_EXT = {
    ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".go", ".java", ".kt",
    ".kts", ".rs", ".c", ".cc", ".cpp", ".h", ".hpp", ".cs", ".swift",
    ".scala", ".php", ".dart", ".groovy", ".proto",
}
DASH_COMMENT_EXT = {".sql", ".lua", ".hs"}
HASH_COMMENT_NAMES = {"Makefile", "Taskfile.yml", "Taskfile.yaml", "Dockerfile", "Justfile"}
# Files whose whole content is commands (hooks, CI, task runners): every
# `task X` in them is a real invocation, not prose.
COMMAND_FILE_HINTS = (".githooks/", ".github/workflows/", "Taskfile", "Makefile", ".sh", "Justfile")
MAX_FILE_BYTES = 1_000_000

MD_LINK = re.compile(r"\]\(([^)\s#]+)(?:#[^)\s]*)?\)")
# path-like token: at least one slash, a final extension, no URL scheme
PATH_TOKEN = re.compile(
    r"(?<![\w/.:@$-])((?:\.{0,2}/)?(?:[A-Za-z0-9_.\-]+/)+[A-Za-z0-9_.\-]+\.[A-Za-z0-9]{1,8})(?![\w/])"
)
PLACEHOLDER = re.compile(
    r"(^|/)(my|your|our|some|example|foo|bar|baz|xxx|todo|name|placeholder|"
    r"skill-name|project|package|module|feature)[-_./]|<|>|\{|\}|\*|\$",
    re.I,
)
MIME_PREFIXES = {"application", "text", "image", "audio", "video", "multipart", "message", "font", "model"}
# "e.g. scripts/run.py" is an illustration, not a claim that the file exists
EXAMPLE_CUE = re.compile(r"(e\.g\.|for example|for instance|such as|like)\s*[`\"'(]*$", re.I)
PLACEHOLDER_NAME = re.compile(r"^(?:[A-Z][A-Z_-]*|x|name|target|script|foo|bar)$")
RUNTIME_HINT = re.compile(r"(^|/)(\.evals|dist|build|node_modules|coverage|\.venv|target|out)/")
INLINE_CODE = re.compile(r"`([^`\n]+)`")
# a bare filename named in a code span or at the start of a fenced line
# ("config lives in `settings.yaml`", a layout tree): claim that it exists
BARE_FILENAME = re.compile(
    r"^\.?[A-Za-z0-9_\-]+\.(py|js|jsx|ts|tsx|mjs|cjs|go|rs|java|kt|rb|php|cs|swift|"
    r"yaml|yml|json|toml|ini|cfg|md|rst|txt|sh|bash|sql|proto|graphql|lock|"
    r"csv|xml|html|css|scss|tf|dockerfile|feature)$",
    re.I,
)
FENCE = re.compile(r"^\s*(```|~~~)")

TASK_CMD = re.compile(r"(?<![\w/.-])task\s+([a-z][\w:.-]+)")
MAKE_CMD = re.compile(r"(?<![\w/.-])make\s+([a-z][\w.-]*)")
NPM_RUN_CMD = re.compile(r"(?<![\w/.-])(?:npm|pnpm|yarn|bun)\s+run\s+([\w:.-]+)")
NPM_SHORTCUT = re.compile(r"(?<![\w/.-])(?:npm|pnpm|yarn|bun)\s+(test|start|build|lint|dev)\b")
PM_DIRECT = re.compile(r"(?<![\w/.-])(?:pnpm|yarn|bun)\s+([a-z][\w:.-]*)")
PM_BUILTINS = {
    "install", "i", "add", "remove", "rm", "update", "up", "upgrade", "dlx",
    "exec", "link", "unlink", "publish", "pack", "outdated", "audit", "list",
    "ls", "why", "store", "setup", "create", "init", "import", "rebuild",
    "prune", "fetch", "patch", "deploy", "env", "config", "run", "help",
    "cache", "workspace", "workspaces", "global", "set", "get", "bin", "x",
    "info", "login", "logout", "version", "licenses", "self-update", "dedupe",
}
TASK_STOPWORDS = {
    "runner", "at", "hand", "definition", "definitions", "list", "name",
    "names", "file", "files", "is", "in", "to", "for", "that", "the", "and",
    "or", "with", "which", "you", "it", "does", "do", "has", "exists", "per",
    "from", "as", "by", "a", "an", "of", "on", "if", "when", "was", "are",
    "into", "already", "only", "also", "not", "can", "will", "should",
    "must", "may", "than", "then", "so", "but", "each", "every", "any",
    "this", "these", "those", "there", "here", "such", "like", "via",
    "before", "after", "itself", "its", "id", "ids", "queue", "queues",
    "runners", "binary", "version", "command", "commands", "graph", "output",
}
MAKE_STOPWORDS = {
    "sure", "it", "the", "a", "an", "this", "that", "them", "use", "changes",
    "your", "our", "any", "no", "one", "each", "sense", "up", "all", "these",
    "those", "him", "her", "us", "me", "you", "things", "way", "room",
    "progress", "is", "of", "and", "or", "in", "for", "to", "as",
}

MARKER = re.compile(r"\b(TODO|FIXME|XXX|HACK|TBD)\b")
NUMERIC_CLAIM = re.compile(
    r"\b(max(imum)?|min(imum)?|at most|at least|under|over|up to|limit|budget|"
    r"default|retries|retry|retried|times|timeout|port|second|seconds|minute|"
    r"minutes|hour|hours|ms|MB|KB|GB|line|lines|token|tokens|character|characters|"
    r"char|chars|byte|bytes|percent|%|item|items|entry|entries|row|rows|"
    r"worker|workers|thread|threads|connection|connections|attempt|attempts|"
    r"requires|version)\b",
    re.I,
)
NUMBER = re.compile(r"(?<![\w.])(\d+(?:\.\d+)?)(?![\w.]|\.\d)")
SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")
NUMBER_WORDS = {
    "zero": "0",
    "one": "1",
    "once": "1",
    "two": "2",
    "twice": "2",
}

CODEISH_START = re.compile(
    r"^(def |class |return\b|import |from \S+ import|if \(|if .*:$|for .*:$|"
    r"while .*:$|const |let |var |function\b|export |fn |pub |func |package |"
    r"else\b|try\b|except\b|catch\b|elif |switch\b|case .*:|print\(|"
    r"console\.|self\.|this\.|@\w+|#include|using |namespace |struct |enum |"
    r"impl |raise |throw |await |async |yield |assert |with .*:$|finally:|"
    r"lambda |del |global |nonlocal |pass$|break$|continue$|\"\"\"|\'\'\'|"
    r"[A-Za-z_][\w.]*\s*=\s*\S|[A-Za-z_][\w.]*\([^)]*\)\s*;?$)"
)
CODEISH_END = re.compile(r"[;{}()\]]\s*$|\)\s*:\s*$|\"\"\"$")
PROSE_HINT = re.compile(r"^[A-Z][a-z]+(\s+[a-z']+){4,}[.:]?$")
DUP_MIN_CHARS = 120
NEAR_DUP_JACCARD = 0.7
# a code line that could enforce a documented number: assignment / config value
ENFORCING_LINE = re.compile(r"(=|:)\s*[\"']?\d+(\.\d+)?[\"']?\s*(,|;|$|#|//)|\(\s*\d+\s*\)|\{\d+\}")
NUMERIC_PROXIMITY_WORDS = 3


def run_git_ls(root: Path) -> list[Path] | None:
    try:
        out = subprocess.run(
            ["git", "-C", str(root), "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
            check=True, capture_output=True, text=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        return None
    paths = []
    for rel in out.split("\0"):
        if not rel:
            continue
        p = root / rel
        if p.is_file() and not any(part in SKIP_DIRS for part in Path(rel).parts):
            paths.append(p)
    return paths


def walk(root: Path) -> list[Path]:
    paths = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for name in sorted(filenames):
            paths.append(Path(dirpath) / name)
    return paths


def read_text(path: Path) -> str | None:
    try:
        if path.stat().st_size > MAX_FILE_BYTES:
            return None
        data = path.read_bytes()
    except OSError:
        return None
    if b"\0" in data[:8000]:
        return None
    return data.decode("utf-8", errors="replace")


def comment_marker(path: Path) -> str | None:
    if path.name in HASH_COMMENT_NAMES or path.suffix in HASH_COMMENT_EXT:
        return "#"
    if path.suffix in SLASH_COMMENT_EXT:
        return "//"
    if path.suffix in DASH_COMMENT_EXT:
        return "--"
    return None


def is_doc(path: Path) -> bool:
    return path.suffix.lower() in DOC_EXT


def is_command_file(rel: str) -> bool:
    return any(h in rel for h in COMMAND_FILE_HINTS)


def comment_lines(text: str, marker: str) -> list[tuple[int, str]]:
    """(line number, comment body) for lines that are wholly comments."""
    out = []
    for i, line in enumerate(text.splitlines(), 1):
        s = line.strip()
        if s.startswith(marker) and not s.startswith(marker + "!"):
            body = s[len(marker):].strip()
            out.append((i, body))
    return out


def doc_segments(text: str) -> tuple[list[tuple[int, str]], list[tuple[int, str]]]:
    """Split a markdown file into (prose lines, code-context lines).

    Code context = fenced block lines plus inline code spans; commands are
    only looked for there, so "make sure" in prose is never a command."""
    prose, code = [], []
    in_fence = False
    for i, line in enumerate(text.splitlines(), 1):
        if FENCE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            code.append((i, line))
        else:
            prose.append((i, line))
            for m in INLINE_CODE.finditer(line):
                code.append((i, m.group(1)))
    return prose, code


class Scanner:
    def __init__(self, root: Path):
        self.root = root
        self.files = run_git_ls(root) or walk(root)
        self.texts: dict[Path, str] = {}
        for p in self.files:
            t = read_text(p)
            if t is not None:
                self.texts[p] = t
        self.existing = {p.resolve() for p in self.files}
        self.existing_dirs = {d for p in self.existing for d in p.parents}
        self.basenames: dict[str, set[Path]] = defaultdict(set)
        for p in self.existing:
            self.basenames[p.name].add(p)
        self.findings: dict[str, list[dict]] = defaultdict(list)
        self.referenced_files: set[Path] = set()

    def rel(self, p: Path) -> str:
        try:
            return p.resolve().relative_to(self.root.resolve()).as_posix()
        except ValueError:
            return str(p)

    def add(self, kind: str, path: Path, line: int, message: str, **extra):
        self.findings[kind].append({"file": self.rel(path), "line": line, "message": message, **extra})

    # -- references -----------------------------------------------------
    def resolve(self, base: Path, target: str) -> Path | None:
        candidates = [base.parent / target, self.root / re.sub(r"^(\./)+", "", target)]
        for c in candidates:
            try:
                rc = c.resolve()
            except OSError:
                continue
            if rc in self.existing or rc in self.existing_dirs or rc.exists():
                return rc
        return None

    def suffix_match(self, target: str) -> str | None:
        """A repo file whose path ends with the target (found at another depth)."""
        parts = Path(re.sub(r"^(\./)+", "", target)).parts
        for p in self.existing:
            if p.parts[-len(parts):] == parts:
                return self.rel(p)
        return None

    def check_reference(self, path: Path, line: int, target: str, via: str, before: str = ""):
        target = target.strip().rstrip(".,;:)")
        if not target or target.startswith(("http://", "https://", "mailto:", "/", "#")):
            return
        if "://" in target or "@" in target:
            return
        if PLACEHOLDER.search(target):
            return
        clean = re.sub(r"^(\./)+", "", target)
        first = clean.split("/")[0]
        if first in MIME_PREFIXES:
            return  # media type (application/vnd.x), not a path
        if "." in first and not first.startswith(".") and not (self.root / first).exists():
            return  # looks like a domain (example.com/x.html)
        if EXAMPLE_CUE.search(before[-24:]):
            return  # illustrative ("e.g. scripts/run.py")
        resolved = self.resolve(path, target)
        if resolved is not None:
            self.referenced_files.add(resolved)
            return
        note = ""
        if RUNTIME_HINT.search(target):
            note = " (gitignored/runtime path? check before flagging)"
        elif (hit := self.suffix_match(target)) is not None:
            note = f" (a file with that suffix exists at {hit})"
        self.add("broken_references", path, line, f"{via} `{target}` does not exist{note}", target=target)

    def check_bare_filename(self, path: Path, line: int, token: str, before: str):
        token = token.strip().rstrip(".,;:")
        if not BARE_FILENAME.match(token) or PLACEHOLDER.search(token) or EXAMPLE_CUE.search(before[-24:]):
            return
        if token in self.basenames:
            self.referenced_files.update(self.basenames[token])
            return
        self.add("broken_references", path, line, f"names `{token}` but no file with that name exists", target=token)

    def scan_bare_filenames(self):
        for path, text in self.texts.items():
            if not is_doc(path):
                continue
            in_fence = False
            for lineno, line in enumerate(text.splitlines(), 1):
                if FENCE.match(line):
                    in_fence = not in_fence
                    continue
                if in_fence:
                    first = line.strip().split(" ")[0] if line.strip() else ""
                    self.check_bare_filename(path, lineno, first, "")
                else:
                    for m in INLINE_CODE.finditer(line):
                        self.check_bare_filename(path, lineno, m.group(1), line[: m.start()])

    def scan_references(self):
        for path, text in self.texts.items():
            lines_to_scan: list[tuple[int, str]] = []
            if is_doc(path):
                lines_to_scan = list(enumerate(text.splitlines(), 1))
            else:
                marker = comment_marker(path)
                if marker:
                    lines_to_scan = comment_lines(text, marker)
            for lineno, line in lines_to_scan:
                for m in MD_LINK.finditer(line):
                    self.check_reference(path, lineno, m.group(1), "link to")
                stripped = MD_LINK.sub("]", line)
                for m in PATH_TOKEN.finditer(stripped):
                    self.check_reference(path, lineno, m.group(1), "reference to", stripped[: m.start()])

    # -- commands -------------------------------------------------------
    def collect_targets(self) -> dict[str, set[str]]:
        targets: dict[str, set[str]] = {
            "task": set(),
            "task_includes": set(),
            "make": set(),
            "npm": set(),
        }
        has: dict[str, bool] = {"task": False, "make": False, "npm": False}
        for path, text in self.texts.items():
            if path.name in ("Taskfile.yml", "Taskfile.yaml"):
                has["task"] = True
                in_tasks = False
                in_includes = False
                tasks_section_indent = None
                includes_section_indent = None
                task_indent = None
                include_indent = None
                for line in text.splitlines():
                    current_indent = len(line) - len(line.lstrip()) if line.strip() else None
                    mt = re.match(r"^(\s*)tasks:\s*$", line)
                    if mt:
                        in_tasks = True
                        tasks_section_indent = len(mt.group(1))
                        task_indent = None
                        continue
                    mi = re.match(r"^(\s*)includes:\s*$", line)
                    if mi:
                        in_includes = True
                        includes_section_indent = len(mi.group(1))
                        include_indent = None
                        continue
                    if in_tasks and line.strip() and current_indent is not None and current_indent <= tasks_section_indent:
                        in_tasks = False
                        tasks_section_indent = None
                        task_indent = None
                    if in_includes and line.strip() and current_indent is not None and current_indent <= includes_section_indent:
                        in_includes = False
                        includes_section_indent = None
                        include_indent = None
                    m = re.match(r"^(\s+)([A-Za-z0-9_:.\-]+):", line)
                    if in_tasks and m:
                        indent = len(m.group(1))
                        task_indent = indent if task_indent is None else task_indent
                        if indent == task_indent:
                            targets["task"].add(m.group(2))
                    if in_includes:
                        list_item = re.match(r"^(\s*)-\s+([A-Za-z0-9_:.\-]+):", line)
                        if list_item:
                            indent = len(list_item.group(1))
                            if indent > includes_section_indent:
                                include_indent = indent if include_indent is None else include_indent
                                if indent == include_indent:
                                    targets["task_includes"].add(list_item.group(2))
                        elif m:
                            indent = len(m.group(1))
                            if indent > includes_section_indent:
                                include_indent = indent if include_indent is None else include_indent
                                if indent == include_indent:
                                    targets["task_includes"].add(m.group(2))
            elif path.name in ("Makefile", "GNUmakefile", "makefile") or path.suffix == ".mk":
                has["make"] = True
                for line in text.splitlines():
                    m = re.match(r"^([A-Za-z0-9_.\-/ ]+?)\s*:(?![=:])", line)
                    if m and not line.startswith(("\t", ".", "#")):
                        for t in m.group(1).split():
                            targets["make"].add(t)
            elif path.name == "package.json":
                has["npm"] = True
                try:
                    scripts = json.loads(text).get("scripts", {})
                    if isinstance(scripts, dict):
                        targets["npm"].update(scripts)
                except (json.JSONDecodeError, AttributeError):
                    pass
        self.has_runner = has
        return targets

    def scan_commands(self):
        targets = self.collect_targets()
        for path, text in self.texts.items():
            rel = self.rel(path)
            if is_doc(path):
                _, lines = doc_segments(text)
            elif is_command_file(rel):
                lines = list(enumerate(text.splitlines(), 1))
            else:
                marker = comment_marker(path)
                lines = comment_lines(text, marker) if marker else []
            for lineno, line in lines:
                for m in TASK_CMD.finditer(line):
                    name = m.group(1).rstrip(":.")
                    if name in TASK_STOPWORDS or name in targets["task"] or PLACEHOLDER_NAME.match(name):
                        continue
                    if ":" in name and name.split(":", 1)[0] in targets["task_includes"]:
                        continue
                    if not self.has_runner["task"]:
                        msg = f"`task {name}` but no Taskfile.yml in the repo"
                    else:
                        msg = f"`task {name}` is not defined in any Taskfile"
                    self.add("undefined_commands", path, lineno, msg, command=f"task {name}")
                for m in MAKE_CMD.finditer(line):
                    name = m.group(1).rstrip(".")
                    if name in MAKE_STOPWORDS or name in targets["make"] or PLACEHOLDER_NAME.match(name):
                        continue
                    if not self.has_runner["make"]:
                        msg = f"`make {name}` but no Makefile in the repo"
                    else:
                        msg = f"`make {name}` is not a target in any Makefile"
                    self.add("undefined_commands", path, lineno, msg, command=f"make {name}")
                names = [m.group(1) for m in NPM_RUN_CMD.finditer(line)]
                names += [m.group(1) for m in NPM_SHORTCUT.finditer(line)]
                names += [
                    m.group(1) for m in PM_DIRECT.finditer(line)
                    if m.group(1) not in PM_BUILTINS and m.group(1) not in ("test", "start", "build", "lint", "dev")
                ]
                for name in names:
                    if name in targets["npm"] or name.startswith("-") or PLACEHOLDER_NAME.match(name):
                        continue
                    if not self.has_runner["npm"]:
                        continue  # no package.json: `pnpm foo` may be a bin, not a script
                    self.add(
                        "undefined_commands", path, lineno,
                        f"script `{name}` is not in any package.json scripts", command=name,
                    )

    # -- duplicate paragraphs -------------------------------------------
    @staticmethod
    def normalise(par: str) -> str:
        par = re.sub(r"[`*_#>|]", "", par)
        par = re.sub(r"^\s*(?:[-+]|\d+[.)])\s+", "", par, flags=re.M)
        return re.sub(r"\s+", " ", par).strip().lower()

    def scan_duplicates(self):
        paragraphs: list[tuple[Path, int, str]] = []
        for path, text in self.texts.items():
            if not is_doc(path):
                continue
            start, buf = None, []
            for i, line in enumerate(text.splitlines() + [""], 1):
                if line.strip():
                    if start is None:
                        start = i
                    buf.append(line)
                elif buf:
                    norm = self.normalise("\n".join(buf))
                    if len(norm) >= DUP_MIN_CHARS:
                        paragraphs.append((path, start, norm))
                    start, buf = None, []
        shingles = []
        index: dict[str, list[int]] = defaultdict(list)
        for idx, (_, _, norm) in enumerate(paragraphs):
            words = norm.split()
            sh = {" ".join(words[i:i + 3]) for i in range(max(1, len(words) - 2))}
            shingles.append(sh)
            for s in sh:
                index[s].append(idx)
        seen: set[int] = set()
        for i, (pa, la, na) in enumerate(paragraphs):
            if i in seen:
                continue
            counts: dict[int, int] = defaultdict(int)
            for s in shingles[i]:
                for j in index[s]:
                    if j > i:
                        counts[j] += 1
            matches = []
            for j, shared in counts.items():
                union = len(shingles[i] | shingles[j])
                jacc = shared / union if union else 0
                if jacc >= NEAR_DUP_JACCARD:
                    matches.append((j, jacc))
            if not matches:
                continue
            others = []
            for j, jacc in sorted(matches):
                seen.add(j)
                pb, lb, nb = paragraphs[j]
                kind = "identical" if na == nb else f"{int(jacc * 100)}%"
                others.append(f"{self.rel(pb)}:{lb} ({kind})")
            self.add(
                "duplicate_paragraphs", pa, la,
                f"\"{na[:60]}…\" is repeated at {', '.join(others)}",
                others=others,
            )

    # -- orphan docs ----------------------------------------------------
    def scan_orphans(self):
        root_names = {"readme.md", "agents.md", "claude.md", "contributing.md", "changelog.md",
                      "license.md", "code_of_conduct.md", "security.md", "skill.md"}
        # any mention of a doc's path or bare name anywhere counts as a link
        all_text = "\n".join(self.texts.values())
        for path in self.texts:
            if path.suffix.lower() not in (".md", ".mdx", ".rst"):
                continue
            rel = self.rel(path)
            if path.name.lower() in root_names or "/.github/" in f"/{rel}" or "/evals/" in f"/{rel}":
                continue
            if path.resolve() in self.referenced_files:
                continue
            others = all_text.replace(self.texts[path], "")
            if rel in others or path.name in others:
                continue
            self.add("orphan_docs", path, 1, "no other file links to or names this doc")

    # -- commented-out code ---------------------------------------------
    def scan_commented_code(self):
        for path, text in self.texts.items():
            marker = comment_marker(path)
            if not marker or path.suffix in (".yml", ".yaml", ".toml", ".cfg", ".ini", ".md"):
                continue
            lines = text.splitlines()
            run: list[tuple[int, str]] = []

            def flush():
                if len(run) >= 3:
                    codeish = sum(
                        1 for _, b in run
                        if (CODEISH_START.match(b) or CODEISH_END.search(b)) and not PROSE_HINT.match(b)
                    )
                    if codeish * 3 >= len(run) * 2:
                        self.add(
                            "commented_out_code", path, run[0][0],
                            f"{len(run)} consecutive comment lines look like code: `{run[0][1][:60]}`",
                        )
                run.clear()

            for i, line in enumerate(lines, 1):
                s = line.strip()
                if s.startswith(marker) and not s.startswith(marker + "!"):
                    body = s[len(marker):].strip()
                    if body and not re.fullmatch(r"[-=*#~_ ]{3,}", body) and not re.search(
                        r"copyright|licen[cs]e|noqa|type:|pylint|eslint|prettier", body, re.I
                    ):
                        run.append((i, body))
                        continue
                flush()
            flush()

    # -- markers --------------------------------------------------------
    def scan_markers(self):
        for path, text in self.texts.items():
            if is_doc(path):
                lines = list(enumerate(text.splitlines(), 1))
            else:
                marker = comment_marker(path)
                lines = comment_lines(text, marker) if marker else []
            for lineno, line in lines:
                m = MARKER.search(line)
                if m:
                    self.add("markers", path, lineno, line.strip()[:120], marker=m.group(1))

    # -- numeric claims -------------------------------------------------
    @staticmethod
    def claim_numbers(sentence: str) -> list[str]:
        """Numbers close to a limit-ish word. Dotted numbers are versions -
        the Version claim type covers those by reading."""
        words = sentence.split()
        out = []
        for idx, w in enumerate(words):
            m = NUMBER.search(w)
            n = None
            if m and "." not in m.group(1):
                n = m.group(1)
            else:
                token = re.sub(r"^[^A-Za-z0-9]+|[^A-Za-z0-9]+$", "", w).lower()
                n = NUMBER_WORDS.get(token)
            if n is None:
                continue
            window = " ".join(words[max(0, idx - NUMERIC_PROXIMITY_WORDS): idx + NUMERIC_PROXIMITY_WORDS + 1])
            if NUMERIC_CLAIM.search(window):
                out.append(n)
        return out

    def scan_numeric_claims(self):
        code_lines: dict[str, list[str]] = defaultdict(list)
        keyword_lines: list[str] = []  # enforcing lines, for keyword lookups
        for path, text in self.texts.items():
            if is_doc(path):
                continue
            rel = self.rel(path)
            for i, line in enumerate(text.splitlines(), 1):
                if not ENFORCING_LINE.search(line):
                    continue
                if len(keyword_lines) < 5000:
                    keyword_lines.append(f"{rel}:{i}: {line.strip()[:80]}")
                for n in NUMBER.findall(line):
                    if len(code_lines[n]) < 200:
                        code_lines[n].append(f"{rel}:{i}: {line.strip()[:80]}")
        for path, text in self.texts.items():
            if not is_doc(path):
                continue
            prose, _ = doc_segments(text)
            for lineno, line in prose:
                for sentence in SENTENCE_SPLIT.split(line):
                    if re.match(r"^\s*(\d+[.)]|#)", sentence):
                        continue  # list numbering / headings
                    nums = self.claim_numbers(sentence)
                    if not nums:
                        continue
                    hits = []
                    for n in nums:
                        hits += code_lines.get(n, [])[:3]
                    related = []
                    for kw in {m.group(0).lower() for m in NUMERIC_CLAIM.finditer(sentence)}:
                        if len(kw) < 3:
                            continue
                        for cl in keyword_lines:
                            if re.search(rf"\b{re.escape(kw)}\w*\b", cl, re.I) and cl not in hits and cl not in related:
                                related.append(cl)
                            if len(related) >= 3:
                                break
                    self.add(
                        "numeric_claims", path, lineno, sentence.strip()[:140],
                        numbers=nums, code_lines_with_same_number=hits, related_settings=related,
                    )

    def run(self):
        self.scan_references()
        self.scan_bare_filenames()
        self.scan_commands()
        self.scan_duplicates()
        self.scan_orphans()
        self.scan_commented_code()
        self.scan_markers()
        self.scan_numeric_claims()
        for items in self.findings.values():
            items.sort(key=lambda f: (f["file"], f["line"]))


SECTIONS = [
    ("broken_references", "Broken references (hard)"),
    ("undefined_commands", "Undefined commands (hard)"),
    ("duplicate_paragraphs", "Duplicate paragraphs"),
    ("orphan_docs", "Orphan docs"),
    ("commented_out_code", "Commented-out code"),
    ("markers", "TODO / FIXME markers"),
    ("numeric_claims", "Numeric claims to verify"),
]
HARD = {"broken_references", "undefined_commands"}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root", nargs="?", default=".", help="repository root (default: .)")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--fail-on", choices=["hard", "any", "none"], default="hard")
    ap.add_argument("--max", type=int, default=40, help="max lines printed per section (text mode)")
    args = ap.parse_args()
    root = Path(args.root)
    if not root.is_dir():
        print(f"scan_consistency: {root} is not a directory", file=sys.stderr)
        return 2

    sc = Scanner(root)
    sc.run()

    if args.json:
        print(json.dumps({k: sc.findings.get(k, []) for k, _ in SECTIONS}, indent=2))
    else:
        print(f"scan_consistency: {len(sc.texts)} text files under {root.resolve()}\n")
        for key, title in SECTIONS:
            items = sc.findings.get(key, [])
            print(f"## {title}: {len(items)}")
            for f in items[: args.max]:
                print(f"  {f['file']}:{f['line']}: {f['message']}")
                for hint in f.get("code_lines_with_same_number", [])[:3]:
                    print(f"      same number in {hint}")
                for hint in f.get("related_settings", [])[:3]:
                    print(f"      related setting: {hint}")
                if key == "numeric_claims" and not f.get("code_lines_with_same_number"):
                    print("      no code line carries this number — likely changed; find the constant")
            if len(items) > args.max:
                print(f"  … {len(items) - args.max} more (use --json or --max)")
            print()
        print("Leads, not verdicts: confirm each with two locations and a quote from each.")

    if args.fail_on == "none":
        return 0
    keys = HARD if args.fail_on == "hard" else {k for k, _ in SECTIONS}
    return 1 if any(sc.findings.get(k) for k in keys) else 0


if __name__ == "__main__":
    sys.exit(main())
