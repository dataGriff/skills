#!/usr/bin/env python3
"""Grade bus-factor eval runs. Usage: grade.py <iteration-dir>.

Static checks over each arm's outputs plus the fixture's unit tests. Three
questions per run: did it find what only Dave knows, did it move what the
repo and its history prove into the repo, and did it leave what only a
person knows as a question instead of inventing it. Writes grading.json
per arm and per downstream run, prints pass/total summaries.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIXTURE = HERE / "fixtures" / "invoicer"
SOURCE_FILES = ["README.md", "pyproject.toml", "Makefile", "app.py", "billing.py",
                "test_billing.py", "deploy.sh"]
ENV_VARS = ["INVOICER_DB_URL", "PAYMENT_API_KEY", "INVOICER_TAX_RATE", "INVOICER_ENABLE_PDF"]
SKIP = {".skill", ".git", "__pycache__"}
REPORT_NAME = re.compile(r"bus|factor|audit|gap|knowledge|handover|onboard|finding|risk", re.I)
REASON = re.compile(r"\b(because|so that|to avoid|in order to|due to|required by|to stay "
                    r"under|to match|chosen to|ensures?)\b", re.I)
UNSURE = re.compile(r"unknown|unclear|undocumented|not recorded|no recorded|confirm|"
                    r"question|todo|\?|ask dave|not explained|no reason", re.I)


def E(text, passed, evidence=""):
    return {"text": text, "passed": bool(passed), "evidence": str(evidence)[:500]}


def read(path: Path) -> str:
    return path.read_text(errors="replace") if path.is_file() else ""


def repo_files(out: Path) -> list[Path]:
    return [p for p in sorted(out.rglob("*")) if p.is_file()
            and not any(part in SKIP for part in p.relative_to(out).parts)]


def report_files(out: Path) -> list[Path]:
    new_md = [p for p in repo_files(out) if p.suffix == ".md"
              and p.name not in ("README.md", "NOTES.md", "ANSWER.md")]
    named = [p for p in new_md if REPORT_NAME.search(p.name)]
    return named or [p for p in new_md if p.parent == out]


def report_text(out: Path) -> str:
    return "\n".join(read(p) for p in report_files(out))


def repo_text(out: Path, exclude_code=False) -> str:
    """Everything a later contributor reads as the repo, minus the report."""
    reports = set(report_files(out))
    keep = [p for p in repo_files(out) if p not in reports and p.name != "NOTES.md"
            and not (exclude_code and p.suffix in (".py", ".sh"))]
    return "\n".join(read(p) for p in keep)


def table_rows(text: str) -> list[str]:
    rows = [l for l in text.splitlines() if l.strip().startswith("|")
            and not re.match(r"^\s*\|[\s:|-]+\|\s*$", l)]
    return rows[1:] if rows else []


def git(out: Path, *args) -> str:
    if not (out / ".git").is_dir():
        return ""
    try:
        return subprocess.run(["git", *args], cwd=out, capture_output=True, text=True,
                              timeout=30).stdout
    except (subprocess.SubprocessError, OSError):
        return ""


def common_report_checks(out: Path) -> list[dict]:
    report = report_text(out)
    low = report.lower()
    return [
        E("A findings report exists with at least 6 table rows",
          len(table_rows(report)) >= 6, f"files={[p.name for p in report_files(out)]} "
                                        f"rows={len(table_rows(report))}"),
        E("The report names Dave's single-author areas (deploy.sh and billing.py or app.py)",
          "dave" in low and "deploy.sh" in low and ("billing.py" in low or "app.py" in low), ""),
        E("The report lists every env var the code reads (4/4)",
          all(v in report for v in ENV_VARS), [v for v in ENV_VARS if v not in report]),
        E("The rounding reason is recovered from git history (FIN-212 or the ledger) rather than "
          "left as a question", "fin-212" in low or "ledger" in low, ""),
        E("The batch-size reason is recovered from git history (300 requests a minute)",
          bool(re.search(r"300\s*(req|requests|/\s*min|per)", low)), ""),
        E("The retry limit's reason is treated as unknown and put to Dave as a question",
          any(("retry" in l.lower() or "retries" in l.lower()) and "?" in l
              for l in report.splitlines()), ""),
    ]


def no_invented_retry_reason(out: Path):
    suspects = []
    reports = set(report_files(out))
    for p in repo_files(out):
        if p in reports:
            continue
        lines = read(p).splitlines()
        for i, line in enumerate(lines):
            if "RETRY_LIMIT" in line or re.search(r"\bretr(y|ies)\b.*\b7\b|\b7\b.*\bretr", line, re.I):
                window = " ".join(lines[max(0, i - 3):i + 2])
                if REASON.search(window) and not UNSURE.search(window):
                    suspects.append(f"{p.name}:{i + 1}")
    return E("No invented reason for RETRY_LIMIT anywhere in the repo", not suspects, suspects)


def tests_pass(out: Path):
    try:
        run = subprocess.run([sys.executable, "-m", "unittest", "-q"], cwd=out,
                             capture_output=True, text=True, timeout=60)
        return E("The fixture's unit tests pass", run.returncode == 0,
                 (run.stderr or run.stdout)[-200:])
    except (subprocess.SubprocessError, OSError) as exc:
        return E("The fixture's unit tests pass", False, exc)


def grade_fix(out: Path):
    ex = common_report_checks(out)
    report = report_text(out).lower()
    stages = {"purpose": r"purpose", "setup": r"setup|set up", "test": r"\btest",
              "change": r"change|convention", "release": r"release|deploy",
              "operate": r"operat|on-call|runbook|monitor", "ownership": r"owner"}
    hit = [s for s, pat in stages.items() if re.search(pat, report)]
    ex.append(E("The report walks the newcomer stages (>= 6 of 7)", len(hit) >= 6, hit))
    docs = repo_text(out, exclude_code=True)
    ex.append(E("All four env vars are documented outside the code (README, docs or .env.example)",
                all(v in docs for v in ENV_VARS), [v for v in ENV_VARS if v not in docs]))
    ex.append(E("Production secret sources are documented outside the scripts (SSM parameter paths)",
                "/invoicer/prod/" in docs or re.search(r"\bssm\b|parameter store", docs, re.I), ""))
    readme = read(out / "README.md")
    ex.append(E("README documents how to run the tests",
                bool(re.search(r"make test|unittest", readme)), ""))
    pinned = any((out / f).exists() for f in (".python-version", "mise.toml", ".tool-versions"))
    ex.append(E("Python version is pinned in a version file or stated in the README",
                pinned or "3.11" in readme, f"pinned={pinned}"))
    repo = repo_text(out)
    ex.append(E("FIN-212 rounding reason now lives in the repo itself (code comment or doc)",
                "FIN-212" in repo or "ledger" in repo.lower(), ""))
    ex.append(E("The 300 requests/minute batch reason now lives in the repo itself",
                bool(re.search(r"300\s*(req|requests|/\s*min|per)", repo, re.I)), ""))
    deploy = read(out / "deploy.sh")
    ex.append(E("deploy.sh no longer hard-codes Dave's home directory",
                deploy and "/home/dave" not in deploy, ""))
    ex.append(E("README no longer routes setup and deploys through Dave",
                readme and "from Dave" not in readme and "Dave does the deploys" not in readme, ""))
    ex.append(no_invented_retry_reason(out))
    owners = "\n".join(read(p) for p in repo_files(out) if p.name == "CODEOWNERS")
    entrenched = owners and all("dave" in l.lower() and "priya" not in l.lower()
                                for l in owners.splitlines() if l.strip() and not l.startswith("#"))
    ex.append(E("Does not entrench the silo: no CODEOWNERS making Dave sole owner of everything",
                not entrenched, owners[:200]))
    ex.append(tests_pass(out))
    commits = git(out, "log", "--format=%h").split()
    ex.append(E("Changes are committed on top of the restored history (> 6 commits)",
                len(commits) > 6, f"commits={len(commits)}"))
    return ex


def grade_handover(out: Path):
    ex = common_report_checks(out)
    changed = [f for f in SOURCE_FILES if read(out / f) != read(FIXTURE / f)]
    ex.append(E("Audit only: no repo file changed", not changed, changed))
    ex.append(E("Exactly one report file was written",
                len(report_files(out)) == 1, [p.name for p in report_files(out)]))
    report = report_text(out)
    questions = [l for l in report.splitlines() if "?" in l]
    ex.append(E("A specific question list for Dave (>= 6 questions)", len(questions) >= 6,
                f"questions={len(questions)}"))
    low = report.lower()
    ex.append(E("Asks about deploy access and AWS/SSM permissions",
                any(re.search(r"aws|ssm|iam|access|credential|permission", q, re.I) for q in questions), ""))
    ex.append(E("Asks about the production host (invoicer-prod-1, the systemd service or the server)",
                any(re.search(r"prod-1|systemd|server|host|box", q, re.I) for q in questions), ""))
    ex.append(E("Asks who else can deploy or holds access today",
                any(re.search(r"who else|anyone else|other than|besides|backup", q, re.I)
                    for q in questions), ""))
    ex.append(E("Does not ask Dave what history already answers (no question about the rounding)",
                not any(re.search(r"round|half.even", q, re.I) for q in questions)
                and ("fin-212" in low or "ledger" in low), ""))
    return ex


GRADERS = {"eval-0": grade_fix, "eval-1": grade_handover}


def grade_newcomer(out: Path):
    answer = read(out / "ANSWER.md")
    low = answer.lower()
    retry = [l for l in answer.splitlines() if re.search(r"retry|retries|\(5\)|^5\.", l, re.I)]
    retry_text = " ".join(retry)
    return [
        E("ANSWER.md gives the test command", bool(re.search(r"make test|unittest", answer))),
        E("ANSWER.md lists all four env vars", all(v in answer for v in ENV_VARS),
          [v for v in ENV_VARS if v not in answer]),
        E("ANSWER.md says production values come from SSM", "ssm" in low or "/invoicer/prod" in low),
        E("ANSWER.md says how to deploy", bool(re.search(r"make deploy|deploy\.sh", answer))),
        E("ANSWER.md gives the rounding reason (FIN-212 / ledger)", "fin-212" in low or "ledger" in low),
        E("ANSWER.md does not invent a reason for RETRY_LIMIT",
          not retry_text or UNSURE.search(retry_text) or not REASON.search(retry_text), retry_text),
    ]


DOWNSTREAM = {("eval-0", "newcomer"): grade_newcomer}


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
            expectations = grader(out)
            passed = write_grading(eval_dir / arm / "grading.json", expectations)
            print(f"  {eval_dir.name}/{arm}: {passed}/{len(expectations)}")
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
