#!/usr/bin/env python3
"""Scan a repository for documentation and comment noise; print markdown tables.

Usage: audit_noise.py <repo> [--docs-only | --code-only]

Reporting only, never edits. Stdlib only. Exit 0 always: the numbers feed
the audit table in DECLUTTER-AUDIT.md; a human or agent decides what to do.
The patterns are the ones references/detection.md documents, so a hand scan
and this report agree.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

COMMENT_DENSITY_WARN = 0.30   # comment lines / code lines; above this, look closer
DOC_WARN_TOKENS = 1500        # a doc past this is worth a rewrite pass
LONG_SENTENCE_WORDS = 30

SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "dist", "build", ".skill",
             "__pycache__", ".evals", "vendor", "third_party"}
DOC_SUFFIXES = {".md", ".rst", ".txt"}
COMMENT_MARKER = {
    "#": {".py", ".rb", ".sh", ".bash", ".yaml", ".yml", ".toml", ".pl", ".r"},
    "//": {".js", ".ts", ".tsx", ".jsx", ".go", ".java", ".rs", ".c", ".h", ".cpp",
           ".cs", ".kt", ".swift", ".scala", ".dart"},
    "--": {".sql", ".lua", ".hs"},
}

HEDGE = re.compile(
    r"\b(it is worth noting|basically|in order to|please note|needless to say|"
    r"as you may know|simply|just|generally speaking|first of all)\b", re.I)
HISTORY_CUE = re.compile(
    r"\b(previously|used to|as of v?\d|we (changed|switched|migrated|moved|renamed) "
    r"(to|from|the)|no longer|originally)\b", re.I)
CHANGELOG_HEADING = re.compile(
    r"^#{1,6}\s*(change ?log|history|what'?s new|release notes|migration (notes|diary)|"
    r"how we got here)", re.I | re.M)
DATED_ENTRY = re.compile(r"^\s*[-*]\s*\d{4}-\d{2}-\d{2}", re.M)
SENTENCE_END = re.compile(r"(?<=[.!?])\s+")
# A commented line is "code" when it starts with a keyword, or is short,
# carries code punctuation and ends the way code does (not like a sentence,
# and not with a ticket reference such as "(FIN-212)").
COMMENTED_CODE = re.compile(
    r"^\s*(#|//|--)\s*(?:(def |class |return |if |for |while |import |from |"
    r"const |let |var |func |fn |elif |else:|try:|except)|"
    r"(?!.*\([A-Z]{2,}-\d+\)\s*$)(?=.*[=(\[{;])(?:\S+\s+){0,7}\S*[:)\]};0-9'\"]\s*$)")
BANNER = re.compile(r"^\s*(#|//)\s*[-=*#]{5,}")
ATTRIBUTION = re.compile(r"\b(added|modified|updated|changed|created) (by|on) \b", re.I)
TODO = re.compile(r"\b(TODO|FIXME|XXX)\b")


def files_under(root: Path):
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        yield path


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return ""


def marker_for(path: Path) -> str | None:
    for marker, suffixes in COMMENT_MARKER.items():
        if path.suffix in suffixes:
            return marker
    return None


def blocks(text: str) -> tuple[list[str], list[str]]:
    """(prose paragraphs, fenced code blocks), each whitespace-normalised.
    Duplicated paragraphs across files are the consistency checker's scan."""
    prose, fences, fenced, current = [], [], False, []
    for line in text.splitlines():
        if line.strip().startswith("```"):
            if fenced and current:
                fences.append(" ".join(current))
            elif current:
                prose.append(" ".join(current))
            current, fenced = [], not fenced
            continue
        if line.strip():
            current.append(line.strip())
        elif current and not fenced:
            prose.append(" ".join(current))
            current = []
    if current:
        (fences if fenced else prose).append(" ".join(current))
    return prose, fences


def scan_doc(path: Path, text: str, rel: str) -> dict:
    paragraphs, _ = blocks(text)
    prose = " ".join(paragraphs)
    sentences = [s for s in SENTENCE_END.split(prose) if s.strip()]
    return {
        "file": rel,
        "lines": len(text.splitlines()),
        "tokens": len(text) // 4,
        "history": sum(1 for s in sentences if HISTORY_CUE.search(s)),
        "changelog_headings": len(CHANGELOG_HEADING.findall(text)),
        "dated": len(DATED_ENTRY.findall(text)),
        "hedges": len(HEDGE.findall(prose)),
        "long": sum(1 for s in sentences if len(s.split()) > LONG_SENTENCE_WORDS),
    }


def scan_code(path: Path, text: str, marker: str, rel: str) -> dict:
    code = comments = commented_code = banners = attributions = todos = 0
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith(marker):
            comments += 1
            if COMMENTED_CODE.match(line):
                commented_code += 1
            if BANNER.match(line):
                banners += 1
            if ATTRIBUTION.search(line):
                attributions += 1
            if TODO.search(line):
                todos += 1
        else:
            code += 1
            if TODO.search(line) and marker in line:
                todos += 1
    return {
        "file": rel, "code": code, "comments": comments,
        "density": (comments / code) if code else 0.0,
        "commented_code": commented_code, "todos": todos,
        "banners": banners, "attributions": attributions,
    }


def table(rows: list[dict], columns: list[tuple[str, str]]) -> str:
    head = "| " + " | ".join(label for _, label in columns) + " |"
    rule = "|" + "|".join("---" for _ in columns) + "|"
    body = []
    for row in rows:
        cells = []
        for key, _ in columns:
            value = row[key]
            cells.append(f"{value:.2f}" if isinstance(value, float) else str(value))
        body.append("| " + " | ".join(cells) + " |")
    return "\n".join([head, rule, *body])


def main(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__.strip())
        return 0
    root = Path(argv[0]).resolve()
    docs_only, code_only = "--docs-only" in argv, "--code-only" in argv
    if not root.is_dir():
        print(f"audit_noise: {root} is not a directory", file=sys.stderr)
        return 0

    doc_rows, code_rows = [], []
    for path in files_under(root):
        rel = str(path.relative_to(root))
        text = read(path)
        if not text:
            continue
        if path.suffix in DOC_SUFFIXES and not code_only:
            doc_rows.append(scan_doc(path, text, rel))
        elif (marker := marker_for(path)) and not docs_only:
            code_rows.append(scan_code(path, text, marker, rel))

    if doc_rows:
        print(f"## Docs (warn: > {DOC_WARN_TOKENS} tokens, any history cue or changelog heading)\n")
        print(table(doc_rows, [("file", "file"), ("lines", "lines"), ("tokens", "tokens"),
                               ("history", "history cues"), ("changelog_headings", "changelog headings"),
                               ("dated", "dated entries"), ("hedges", "hedges"),
                               ("long", f"sentences > {LONG_SENTENCE_WORDS} words")]))
        print()
    if code_rows:
        print(f"## Code (warn: density > {COMMENT_DENSITY_WARN}, any commented-out code, banner or attribution)\n")
        print(table(code_rows, [("file", "file"), ("code", "code lines"), ("comments", "comment lines"),
                                ("density", "density"), ("commented_code", "commented-out code"),
                                ("todos", "TODO/FIXME"), ("banners", "banners"),
                                ("attributions", "attributions")]))
        print()
    if not doc_rows and not code_rows:
        print("audit_noise: nothing to scan.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
