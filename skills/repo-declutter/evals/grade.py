#!/usr/bin/env python3
"""Grade repo-declutter eval runs. Usage: grade.py <iteration-dir>.

Static checks over each arm's outputs, plus one subprocess (the fixture's
own unit tests) for the code fixture. Two questions per fixture: did the
noise go, and did the signal stay. Writes grading.json per arm and per
downstream run, prints pass/total summaries.
"""
import ast
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIXTURES = HERE / "fixtures"

HEDGE = re.compile(
    r"\b(it is worth noting|basically|in order to|please note|needless to say|"
    r"as you may know|generally speaking|first of all)\b", re.I)
CHANGELOG_HEADING = re.compile(
    r"^#{1,6}\s*(change ?log|history|what'?s new|release notes|migration (notes|diary)|"
    r"how we got here)", re.I | re.M)
COMMENTED_CODE = re.compile(
    r"^\s*#\s*(?:(def |class |return |if |for |while |import |from |elif |else:|try:|except)|"
    r"(?!.*\([A-Z]{2,}-\d+\)\s*$)(?=.*[=(\[{;])(?:\S+\s+){0,7}\S*[:)\]};0-9'\"]\s*$)")
SKIP = {".skill", ".git", "__pycache__"}


def E(text, passed, evidence):
    return {"text": text, "passed": bool(passed), "evidence": str(evidence)[:500]}


def read(path: Path) -> str:
    return path.read_text(errors="replace") if path.is_file() else ""


def tokens(text: str) -> int:
    return len(text) // 4


def docs_in(out: Path) -> list[Path]:
    return [p for p in sorted(out.rglob("*.md"))
            if not any(part in SKIP for part in p.parts)
            and p.name not in ("DECLUTTER-AUDIT.md", "NOTES.md", "ANSWER.md")]


def git_bodies(out: Path) -> str:
    if not (out / ".git").is_dir():
        return ""
    try:
        return subprocess.run(["git", "log", "--format=%B"], cwd=out, capture_output=True,
                              text=True, timeout=30).stdout
    except (subprocess.SubprocessError, OSError):
        return ""


def git_subjects(out: Path) -> list[str]:
    if not (out / ".git").is_dir():
        return []
    try:
        return subprocess.run(["git", "log", "--format=%s"], cwd=out, capture_output=True,
                              text=True, timeout=30).stdout.splitlines()
    except (subprocess.SubprocessError, OSError):
        return []


def audit_checks(out: Path, min_rows: int, min_categories: int = 3):
    audit = read(out / "DECLUTTER-AUDIT.md")
    header = audit.lower()
    columns = ["what", "why", "action", "git"]
    has_where = ("where" in header) or ("file" in header) or ("location" in header)
    rows = [l for l in audit.splitlines() if l.startswith("|") and not re.match(r"^\|\s*-", l)]
    rows = [r for r in rows if not re.search(r"\|\s*#?\s*\|\s*(file|where|location)", r, re.I)]
    categories = {m.lower() for r in rows
                  for m in re.findall(r"\b(prose|history|comment|code-clarity)\b", r, re.I)}
    return [
        E("DECLUTTER-AUDIT.md exists with what / where / why / action / git-holds columns",
          audit and has_where and all(c in header for c in columns),
          f"len={len(audit)} missing={[c for c in columns if c not in header]} where={has_where}"),
        E(f"Audit is a real inventory: >= {min_rows} finding rows across >= {min_categories} categories",
          len(rows) >= min_rows and len(categories) >= min_categories,
          f"rows={len(rows)} categories={sorted(categories)}"),
        E("Audit lists what was deliberately kept (a protected/kept section)",
          bool(re.search(r"protected|kept|left in place", audit, re.I)), ""),
    ]


def grade_docs(out: Path):
    ex = audit_checks(out, min_rows=8, min_categories=2)  # docs: prose + history
    docs = docs_in(out)
    changelog = out / "CHANGELOG.md"
    body_docs = [p for p in docs if p != changelog]
    text = "\n".join(read(p) for p in body_docs)
    protected = ["see LICENSE", "Vault", "UUIDv7", "ADR-3", "make test", "PORT=8080", "ruff",
                 "alembic upgrade head", "la-<ticket>-<slug>", "72 characters"]
    kept = [s for s in protected if s.lower() in text.lower()]
    ex.append(E(f"Every protected fact and rule survives in the docs (>= {len(protected) - 1}/{len(protected)})",
                len(kept) >= len(protected) - 1, f"lost={[s for s in protected if s not in kept]}"))
    history = ["Previously we used Flask", "as of v2", "Migration diary", "How we got here",
               "event-sourced"]
    left = [h for h in history if h.lower() in text.lower()]
    ex.append(E("History and narrative are out of README/docs (Flask era, v2 switch, migration "
                "diary, 'how we got here')", not left, f"still_in_docs={left}"))
    archive = git_bodies(out) + read(changelog) + read(out / "DECLUTTER-AUDIT.md")
    gist = ["Flask", "FastAPI", "migration"]
    ex.append(E("The removed history is preserved somewhere durable: commit bodies, CHANGELOG.md "
                "or the audit (Flask -> FastAPI gist present)",
                all(g.lower() in archive.lower() for g in gist),
                f"archive_len={len(archive)} missing={[g for g in gist if g.lower() not in archive.lower()]}"))
    ex.append(E("No changelog-style heading remains inside a non-changelog doc",
                not any(CHANGELOG_HEADING.search(read(p)) for p in body_docs),
                f"in={[p.name for p in body_docs if CHANGELOG_HEADING.search(read(p))]}"))
    hedges = sum(len(HEDGE.findall(read(p))) for p in body_docs)
    ex.append(E("Hedging phrases are gone (<= 1 left; the fixture seeds over 30)",
                hedges <= 1, f"hedges={hedges}"))
    original_readme = tokens(read(FIXTURES / "docs-heavy" / "README.md"))
    original_total = sum(tokens(read(p)) for p in (FIXTURES / "docs-heavy").glob("*.md"))
    readme_now = tokens(read(out / "README.md"))
    total_now = sum(tokens(read(p)) for p in body_docs)
    ex.append(E("README is at most 60% of its original size and the docs total shrank",
                0 < readme_now <= 0.6 * original_readme and total_now < original_total,
                f"readme {original_readme}->{readme_now} total {original_total}->{total_now}"))
    subjects = git_subjects(out)
    cats = {m.lower() for s in subjects
            for m in re.findall(r"\b(prose|history|docs|comment|code-clarity)\b", s, re.I)}
    ex.append(E("Changes land as separate commits per category (>= 3 category-named subjects; "
                "vacuous pass when no git repo was created)",
                not subjects or len(cats) >= 3, f"subjects={subjects[:6]}"))
    return ex


def ast_shape(source: str) -> dict:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return {"error": 1}
    counts = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.If, ast.For, ast.While, ast.Compare, ast.BinOp)):
            counts[type(node).__name__] = counts.get(type(node).__name__, 0) + 1
    return counts


def grade_code(out: Path):
    ex = audit_checks(out, min_rows=6)
    src = read(out / "pricing.py")
    original = read(FIXTURES / "code" / "pricing.py")
    lines = src.splitlines()
    ex.append(E("SPDX and copyright header lines are intact at the top of pricing.py",
                len(lines) >= 2 and "SPDX-License-Identifier: MIT" in lines[0]
                and "Copyright (c) 2024 Acme Ledger" in lines[1], lines[:2]))
    ex.append(E("Constraint comments survive: FIN-212 banker's rounding and never-log card_token (SEC-7)",
                "FIN-212" in src and "card_token" in src and "SEC-7" in src,
                f"FIN={'FIN-212' in src} SEC={'SEC-7' in src}"))
    commented = [l for l in lines if COMMENTED_CODE.match(l)]
    ex.append(E("No commented-out code remains", not commented, commented[:3]))
    gone = ["=====", "added by jsmith", "modified by rlee", "# increment", "# return the",
            "TODO(2021)", "# build the line", "# cap the rate"]
    left = [g for g in gone if g in src]
    ex.append(E("Banner, attribution, restating comments and the stale TODO are gone",
                not left, f"left={left}"))
    comment_lines = lambda s: sum(1 for l in s.splitlines() if l.strip().startswith("#"))  # noqa: E731
    before, after = comment_lines(original), comment_lines(src)
    ex.append(E("Comment lines cut by at least half, with the constraint comments still present (>= 2)",
                after <= before / 2 and after >= 2, f"comments {before}->{after}"))
    papered = bool(re.search(r"def \w+\(d, r, f\)", src)) or "d = subtotal" in src
    ex.append(E("calc(d, r, f) has descriptive parameter names and the comment that explained "
                "them is gone", not papered, f"papered={papered}"))
    shape_before, shape_after = ast_shape(original), ast_shape(src)
    ex.append(E("Control flow and arithmetic unchanged (same counts of If/For/While/Compare/BinOp): "
                "rename and extract only", shape_before == shape_after,
                f"before={shape_before} after={shape_after}"))
    test_src = read(out / "test_pricing.py")
    original_tests = read(FIXTURES / "code" / "test_pricing.py")
    numbers = set(re.findall(r"\b\d+\b", original_tests))
    numbers_now = set(re.findall(r"\b\d+\b", test_src))
    ex.append(E("Tests were not weakened: every numeric assertion value from the fixture is still present",
                test_src and numbers <= numbers_now, f"missing={sorted(numbers - numbers_now)}"))
    try:
        run = subprocess.run([sys.executable, "-m", "unittest", "-q"], cwd=out,
                             capture_output=True, text=True, timeout=60)
        passed = run.returncode == 0 and "OK" in (run.stderr + run.stdout)
        tail = (run.stderr or run.stdout)[-200:]
    except (subprocess.SubprocessError, OSError) as exc:  # noqa: BLE001
        passed, tail = False, str(exc)
    ex.append(E("The fixture's unit tests pass after the change", passed, tail))
    audit = read(out / "DECLUTTER-AUDIT.md")
    rows = [l for l in audit.splitlines() if l.startswith("|") and
            re.search(r"\b(history|comment)\b", l, re.I)]
    filled = [r for r in rows if len([c for c in r.split("|") if c.strip()]) >= 6]
    ex.append(E("Audit rows for history/comment findings say what git holds (>= 6 filled cells)",
                rows and len(filled) >= max(1, len(rows) // 2), f"rows={len(rows)} filled={len(filled)}"))
    return ex


GRADERS = {"eval-0": grade_docs, "eval-1": grade_code}

DOWNSTREAM = {
    ("eval-0", "orient"): lambda out: [
        E(f"ANSWER.md includes {label}", any(k.lower() in read(out / "ANSWER.md").lower() for k in keys), "")
        for label, keys in [("the test command (make test)", ["make test"]),
                            ("the identifier rule (UUIDv7)", ["uuidv7", "uuid v7"]),
                            ("where secrets come from (Vault)", ["vault"])]
    ],
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
        grader = GRADERS.get(match.group(1)) if match else None
        if grader is None:
            continue
        for arm in ("with_skill", "without_skill"):
            out = eval_dir / arm / "outputs"
            if not out.is_dir():
                continue
            passed = write_grading(eval_dir / arm / "grading.json", grader(out))
            total = json.loads((eval_dir / arm / "grading.json").read_text())["summary"]["total"]
            print(f"  {eval_dir.name}/{arm}: {passed}/{total}")
        downstream = eval_dir / "downstream"
        if downstream.is_dir():
            totals = {}
            for run_dir in sorted(downstream.glob("*/*/rep-*")):
                state, task_id = run_dir.parts[-3], run_dir.parts[-2]
                task_grader = DOWNSTREAM.get((match.group(1), task_id))
                if task_grader is None or not (run_dir / "outputs").is_dir():
                    continue
                expectations = task_grader(run_dir / "outputs")
                passed = write_grading(run_dir / "grading.json", expectations)
                totals.setdefault(state, [0, 0])
                totals[state][0] += passed
                totals[state][1] += len(expectations)
            for state, (passed, total) in totals.items():
                print(f"  {eval_dir.name}/downstream/{state}: {passed}/{total} adherence")


if __name__ == "__main__":
    sys.exit(main())
