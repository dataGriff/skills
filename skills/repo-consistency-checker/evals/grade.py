#!/usr/bin/env python3
"""Grade repo-consistency-checker eval runs. Usage: grade.py <iteration-dir>.

Expects <iteration-dir>/eval-*/{with_skill,without_skill}/outputs/ as laid
out by scripts/eval_skills.py (run via
`task eval:skills NAME=repo-consistency-checker`). Every check is static:
it reads the files an arm wrote or changed, never runs them.

- eval-0 (audit-report): does CONSISTENCY_REPORT.md find each planted
  defect in the widgets fixture, cite locations, and leave history alone?
- eval-1 (audit-and-fix): are the fixture files now consistent, with the
  redundancy gone, the pinned behaviour unchanged and CHANGELOG untouched?

Writes grading.json per arm and prints a pass/total summary.
"""
from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "widgets"
LOCATION = re.compile(r"\b[\w.-]+\.(?:py|md|yaml|toml|Makefile)[:` ]+(?:line[s]? )?\d+|\bMakefile[:` ]+(?:line[s]? )?\d+")


def E(text, passed, evidence):
    return {"text": text, "passed": bool(passed), "evidence": str(evidence)[:500]}


def read(path: Path) -> str:
    return path.read_text(errors="replace") if path.is_file() else ""


def has(text: str, *needles: str) -> bool:
    low = text.lower()
    return all(n.lower() in low for n in needles)


def any_of(text: str, *needles: str) -> bool:
    low = text.lower()
    return any(n.lower() in low for n in needles)


# ---------------------------------------------------------------- eval-0
def grade_report(out: Path):
    ex = []
    report_path = next((p for p in out.glob("*.md") if "consistency" in p.name.lower()), None)
    report = read(report_path) if report_path else ""
    ex.append(E("CONSISTENCY_REPORT.md written", bool(report), report_path))

    checks = [
        ("`make test` (README) vs Makefile target `test-unit`", has(report, "test-unit") and any_of(report, "make test`", "make test ", "`make test")),
        ("`settings.yaml` named in docs vs real `config.yaml`", has(report, "settings.yaml", "config.yaml")),
        ("port 8080 in docs vs 8000 in config.yaml", has(report, "8080", "8000")),
        ("fetch_widget docstring 'returns None' vs code raising WidgetNotFound", has(report, "widgetnotfound") and any_of(report, "returns none", "return none", "none when", "none")),
        ("retry count: comment/README say 3 vs MAX_RETRIES = 5", any_of(report, "max_retries", "retr") and has(report, "5") and any_of(report, "3", "three")),
        ("Python 3.11 (CONTRIBUTING) vs 3.12 (README, pyproject)", has(report, "3.11", "3.12")),
        ("CONTRIBUTING duplicates the README setup section", has(report, "contributing") and any_of(report, "duplicate", "repeat", "redundan", "copy", "verbatim", "same setup", "identical")),
        ("lint tool: CONTRIBUTING says ruff, Makefile runs flake8", has(report, "ruff", "flake8")),
        ("dead code: helpers.legacy_format has no callers", has(report, "legacy_format")),
        ("commented-out refresh_catalogue block", has(report, "refresh_catalogue") or any_of(report, "commented-out", "commented out")),
        ("stale TODO: 'add caching once WidgetCache exists' but WidgetCache is used", has(report, "todo") and has(report, "widgetcache")),
        ("sync_worker.py documented (README layout, ARCHITECTURE) but removed", has(report, "sync_worker")),
        ("unused config key legacy_endpoint", has(report, "legacy_endpoint")),
    ]
    for text, passed in checks:
        ex.append(E(f"finds: {text}", passed, "keyword search in report"))

    locs = LOCATION.findall(report)
    ex.append(E("findings cite file:line locations (evidence, not vibes): >= 8 citations",
                len(locs) >= 8, f"{len(locs)} citations, e.g. {locs[:3]}"))

    changelog_lines = [l for l in report.splitlines() if "changelog" in l.lower()]
    flagged_history = [l for l in changelog_lines
                       if re.search(r"\b(stale|drift|outdated|wrong|incorrect|inconsisten|contradict)", l, re.I)
                       and not re.search(r"\b(not |history|historical|record|confirms|consistent with|leave|left|intentional)", l, re.I)]
    ex.append(E("CHANGELOG entries are treated as history, not flagged as drift",
                bool(report) and not flagged_history, flagged_history[:2]))

    ex.append(E("report states coverage: what was checked and found consistent / deliberately not flagged",
                any_of(report, "coverage", "checked and found", "found consistent", "not flagged", "verified consistent", "consistent:", "what was checked", "what i checked", "also checked"),
                "keyword search"))

    originals_changed = [f.name for f in FIXTURES.iterdir() if read(out / f.name) != read(f)]
    ex.append(E("no fixture file modified (report-only task)", not originals_changed, originals_changed))
    return ex


# ---------------------------------------------------------------- eval-1
def parse_ok(path: Path):
    try:
        return ast.parse(read(path)), None
    except SyntaxError as exc:  # noqa: PERF203
        return None, str(exc)


def docstring_of(tree, name: str) -> str:
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_docstring(node) or ""
    return ""


def grade_fix(out: Path):
    ex = []
    readme, contrib = read(out / "README.md"), read(out / "CONTRIBUTING.md")
    arch, changelog = read(out / "ARCHITECTURE.md"), read(out / "CHANGELOG.md")
    makefile, config = read(out / "Makefile"), read(out / "config.yaml")
    app, helpers, tests = read(out / "app.py"), read(out / "helpers.py"), read(out / "test_app.py")
    docs = readme + contrib + arch

    has_test_target = re.search(r"^test\s*:", makefile, re.M) is not None
    bare_make_test = re.search(r"make test(?![-\w])", docs) is not None
    ex.append(E("README's test command matches a real Makefile target",
                (not bare_make_test) or has_test_target,
                f"bare 'make test' in docs={bare_make_test}, Makefile has test:={has_test_target}"))

    ex.append(E("docs name config.yaml, not the non-existent settings.yaml",
                "settings.yaml" not in docs or (out / "settings.yaml").is_file(),
                "grep settings.yaml"))

    port = re.search(r"^port:\s*(\d+)", config, re.M)
    port = port.group(1) if port else None
    doc_ports = set(re.findall(r"port(?: is| of|:)? (\d{4})|(\d{4}) (?:is taken|by default)", docs))
    doc_ports = {a or b for a, b in doc_ports}
    ex.append(E("port stated in docs equals the port in config.yaml",
                port is not None and (not doc_ports or doc_ports == {port}),
                f"config port={port} doc ports={doc_ports}"))

    tree, err = parse_ok(out / "app.py")
    ds = docstring_of(tree, "fetch_widget") if tree else ""
    ex.append(E("fetch_widget docstring no longer claims it returns None for a missing id",
                tree is not None and "none" not in ds.lower() and "raise" in app and "WidgetNotFound" in app,
                f"docstring={ds[:120]!r} err={err}"))

    retry_comment = re.search(r"#[^\n]*retr[^\n]*", app)
    comment_txt = retry_comment.group(0) if retry_comment else ""
    comment_ok = not re.search(r"\b(3|three)\b", comment_txt) or "5" in comment_txt
    readme_ok = not re.search(r"retried (three|3) times|(three|3) (retries|times)", readme, re.I)
    ex.append(E("retry count consistent: comment and README agree with MAX_RETRIES = 5",
                comment_ok and readme_ok and re.search(r"MAX_RETRIES\s*=\s*5", app),
                f"comment={comment_txt!r}"))

    ex.append(E("Python version consistent: no 3.11 left in README/CONTRIBUTING (pyproject pins >=3.12)",
                "3.11" not in docs and "3.12" in read(out / "pyproject.toml"), "grep 3.11"))

    dup_sentence = "adjust the port"
    dup_setup = "create a virtualenv and install the dev tools"
    n_dup = docs.lower().count(dup_sentence) + docs.lower().count(dup_setup)
    ex.append(E("CONTRIBUTING no longer repeats the README setup section (each setup sentence at most once)",
                n_dup <= 2 and not (dup_setup in readme.lower() and dup_setup in contrib.lower()),
                f"occurrences={n_dup}"))

    lint_tool_doc = "ruff" in contrib.lower()
    lint_tool_make = "ruff" in makefile.lower()
    ex.append(E("lint tool consistent between CONTRIBUTING and Makefile",
                lint_tool_doc == lint_tool_make and ("flake8" in makefile.lower() or lint_tool_make),
                f"contrib ruff={lint_tool_doc} makefile ruff={lint_tool_make}"))

    ex.append(E("dead helpers.legacy_format removed", "legacy_format" not in helpers, "grep helpers.py"))
    ex.append(E("commented-out refresh_catalogue block removed", "refresh_catalogue" not in app, "grep app.py"))
    ex.append(E("stale 'TODO: add caching' removed", "TODO: add caching" not in app, "grep app.py"))

    md_current = "\n".join(read(p) for p in out.glob("*.md") if p.name.lower() not in ("changelog.md", "notes.md"))
    ex.append(E("sync_worker no longer described as current (README layout, ARCHITECTURE)",
                "sync_worker" not in md_current, "grep *.md minus CHANGELOG/NOTES"))
    ex.append(E("unused legacy_endpoint removed from config.yaml and current docs",
                "legacy_endpoint" not in config and "legacy_endpoint" not in md_current, "grep"))

    ex.append(E("CHANGELOG.md untouched (history is not drift)",
                changelog == read(FIXTURES / "CHANGELOG.md"), "byte compare with fixture"))

    parse_errors = [f for f in ("app.py", "helpers.py", "test_app.py") if parse_ok(out / f)[0] is None]
    ex.append(E("app.py, helpers.py, test_app.py still parse and the tests still pin MAX_RETRIES == 5",
                not parse_errors and "MAX_RETRIES == 5" in tests and "WidgetNotFound" in tests,
                f"parse errors={parse_errors}"))

    notes = read(out / "NOTES.md")
    named = {f.name for f in FIXTURES.iterdir() if f.name in notes}
    ex.append(E("NOTES.md lists the changes with the files that disagreed (>= 5 fixture files named)",
                len(named) >= 5, sorted(named)))
    return ex


GRADERS = {"eval-0": grade_report, "eval-1": grade_fix}


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
