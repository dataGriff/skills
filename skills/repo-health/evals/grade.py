#!/usr/bin/env python3
"""Grade repo-health eval runs. Usage: grade.py <iteration-dir>.

Static checks over each arm's outputs plus the fixture's unit tests. Two
questions: on a repo with all four problems, did the pass deliver one
branch, one commit per phase and one PR body with every phase's outcome
and the judgment calls; on a healthy repo, did it leave everything alone
but the one missing route. Writes grading.json per arm.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
UNHEALTHY = HERE / "fixtures" / "unhealthy"
HEALTHY = HERE / "fixtures" / "healthy"
SKIP = {".skill", ".skills", ".git", "__pycache__", ".repo-health"}
ENV_VARS = ["INVOICER_DB_URL", "PAYMENT_API_KEY", "INVOICER_TAX_RATE", "INVOICER_ENABLE_PDF"]
PHASES = ("bus-factor", "consistency", "declutter", "optimization")
SUBJECT = re.compile(r"^chore\((bus-factor|consistency|declutter|optimization)\):")
ROOT_AUDITS = {"BUS-FACTOR.md", "DECLUTTER-AUDIT.md", "NOTES.md", "repo-health"}
REASON = re.compile(r"\b(because|so that|to avoid|in order to|due to|required by|to stay "
                    r"under|to match|chosen to|ensures?)\b", re.I)
UNSURE = re.compile(r"unknown|unclear|undocumented|not recorded|no recorded|confirm|"
                    r"question|todo|\?|ask dave|not explained|no reason", re.I)
READ_CUE = re.compile(r"\b(read|open|load|follow)\b", re.I)


def E(text, passed, evidence=""):
    return {"text": text, "passed": bool(passed), "evidence": str(evidence)[:500]}


def read(path: Path) -> str:
    return path.read_text(errors="replace") if path.is_file() else ""


def repo_files(out: Path) -> list[Path]:
    return [p for p in sorted(out.rglob("*")) if p.is_file()
            and not any(part in SKIP for part in p.relative_to(out).parts)]


def repo_text(out: Path, suffixes=None) -> str:
    return "\n".join(read(p) for p in repo_files(out)
                     if suffixes is None or p.suffix in suffixes)


def git(out: Path, *args) -> str:
    if not (out / ".git").is_dir():
        return ""
    try:
        return subprocess.run(["git", *args], cwd=out, capture_output=True, text=True,
                              timeout=30).stdout
    except (subprocess.SubprocessError, OSError):
        return ""


def new_subjects(out: Path, restored: int) -> list[str]:
    subjects = git(out, "log", "--format=%s").splitlines()
    return subjects[: max(0, len(subjects) - restored)]


def pr_body(out: Path) -> str:
    return read(out / ".repo-health" / "PR.md")


def contract_checks(out: Path, restored: int, min_commits: int, max_commits: int) -> list[dict]:
    branch = git(out, "rev-parse", "--abbrev-ref", "HEAD").strip()
    subjects = new_subjects(out, restored)
    scopes = [m.group(1) for s in subjects if (m := SUBJECT.match(s))]
    tracked = set(git(out, "ls-files").split())
    body = pr_body(out)
    low = body.lower()
    return [
        E("Work is on a repo-health/ branch", branch.startswith("repo-health/"), branch),
        E(f"{min_commits}-{max_commits} new commits, one per phase, chore(<phase>): subjects",
          min_commits <= len(subjects) <= max_commits and len(scopes) == len(subjects)
          and len(set(scopes)) == len(scopes), subjects),
        E("No audit file at the repo root (BUS-FACTOR.md, DECLUTTER-AUDIT.md, NOTES.md, repo-health/)",
          not any(t.split("/")[0] in ROOT_AUDITS for t in tracked)
          and not any((out / n).exists() for n in ROOT_AUDITS), sorted(tracked & ROOT_AUDITS)),
        E("PR body saved at .repo-health/PR.md and the directory is untracked",
          bool(body.strip()) and not any(t.startswith(".repo-health/") for t in tracked), len(body)),
        E("PR body names every phase and has a judgment-calls section",
          all(p.replace("-", " ") in low or p in low for p in PHASES) and "judgment" in low, ""),
    ]


def tests_pass(out: Path):
    try:
        run = subprocess.run([sys.executable, "-m", "unittest", "-q"], cwd=out,
                             capture_output=True, text=True, timeout=60)
        return E("The fixture's unit tests pass", run.returncode == 0,
                 (run.stderr or run.stdout)[-200:])
    except (subprocess.SubprocessError, OSError) as exc:
        return E("The fixture's unit tests pass", False, exc)


def no_invented_retry_reason(out: Path):
    suspects = []
    for p in repo_files(out):
        lines = read(p).splitlines()
        for i, line in enumerate(lines):
            if "RETRY_LIMIT" in line or re.search(r"\bretr(y|ies)\b.*\b7\b|\b7\b.*\bretr", line, re.I):
                window = " ".join(lines[max(0, i - 3):i + 2])
                if REASON.search(window) and not UNSURE.search(window):
                    suspects.append(f"{p.name}:{i + 1}")
    return E("No invented reason for RETRY_LIMIT anywhere in the repo", not suspects, suspects)


def grade_unhealthy(out: Path) -> list[dict]:
    ex = contract_checks(out, restored=7, min_commits=2, max_commits=4)
    body = pr_body(out)
    questions = [l for l in body.splitlines() if "?" in l]
    ex.append(E("PR body asks the maintainer at least 3 questions", len(questions) >= 3, len(questions)))
    ex.append(E("PR body reports the test result", bool(re.search(r"\btests?\b.*\b(pass|green|ok)", body, re.I)), ""))
    docs = repo_text(out, {".md", ".example", ".toml", ".env"}) + repo_text(out, {""})
    ex.append(E("All four env vars are documented outside the code",
                all(v in docs for v in ENV_VARS), [v for v in ENV_VARS if v not in docs]))
    ex.append(E("Production secret sources (SSM) documented outside the scripts",
                "/invoicer/prod/" in docs or re.search(r"\bssm\b|parameter store", docs, re.I), ""))
    repo = repo_text(out)
    ex.append(E("FIN-212 rounding reason lives in the repo", "FIN-212" in repo or "ledger" in repo.lower(), ""))
    ex.append(E("The 300 requests/minute batch reason lives in the repo",
                bool(re.search(r"300\s*(req|requests|/\s*min|per)", repo, re.I)), ""))
    deploy = read(out / "deploy.sh")
    code = "\n".join(l.split("#", 1)[0] for l in deploy.splitlines())
    ex.append(E("deploy.sh no longer hard-codes Dave's home directory", deploy and "/home/dave" not in code, ""))
    readme = read(out / "README.md")
    ex.append(E("README no longer routes setup and deploys through Dave",
                readme and "from Dave" not in readme and "Dave does the deploys" not in readme, ""))
    ex.append(no_invented_retry_reason(out))
    makefile = read(out / "Makefile")
    md = repo_text(out, {".md"})
    ex.append(E("`make check` is defined or no longer mentioned",
                re.search(r"^check:", makefile, re.M) or "make check" not in md, ""))
    ex.append(E("The docs/deploy.md link is fixed (target exists or link removed)",
                (out / "docs" / "deploy.md").is_file() or "docs/deploy.md" not in md, ""))
    dup = "rounded half-to-even before"
    ex.append(E("The duplicated how-it-works paragraph is stated once", md.count(dup) == 1, md.count(dup)))
    app = read(out / "app.py")
    ex.append(E("Commented-out push_legacy block removed", "push_legacy" not in app, ""))
    ex.append(E("Ownerless TODO removed from app.py", "TODO" not in app, ""))
    ex.append(E("README History narrative gone (no 'Previously'/'used to')",
                not re.search(r"\bpreviously\b|\bused to\b", readme, re.I), ""))
    ex.append(E("ROUND_HALF_EVEN survives in billing.py", "ROUND_HALF_EVEN" in read(out / "billing.py"), ""))
    agents = read(out / "AGENTS.md")
    ex.append(E("AGENTS.md exists within budget (<=150 lines, <=2000 tokens)",
                agents and len(agents.splitlines()) <= 150 and len(agents) // 4 <= 2000,
                f"lines={len(agents.splitlines())} tokens={len(agents) // 4}"))
    ex.append(E("CLAUDE.md is exactly @AGENTS.md", read(out / "CLAUDE.md").strip() == "@AGENTS.md", ""))
    targets = re.findall(r"^([a-z][\w-]*):", makefile, re.M)
    ex.append(E("Every Makefile target still exists (test, run, deploy)",
                {"test", "run", "deploy"} <= set(targets), targets))
    ex.append(tests_pass(out))
    return ex


def grade_healthy(out: Path) -> list[dict]:
    ex = contract_checks(out, restored=1, min_commits=1, max_commits=1)
    subjects = new_subjects(out, 1)
    ex.append(E("The one commit is chore(optimization)",
                len(subjects) == 1 and subjects[0].startswith("chore(optimization):"), subjects))
    fixture = {"AGENTS.md": HEALTHY / "AGENTS.md", "CLAUDE.md": HEALTHY / "CLAUDE.md",
               "README.md": HEALTHY / "README.md", "Makefile": HEALTHY / "Makefile",
               "CHANGELOG.md": HEALTHY / "CHANGELOG.md",
               "docs/releasing.md": HEALTHY / "docs-releasing.md",
               ".github/workflows/ci.yml": HEALTHY / ".github-ci.yml"}
    before = read(fixture["AGENTS.md"]).splitlines()
    after = read(out / "AGENTS.md").splitlines()
    added = [l for l in after if l not in before]
    removed = [l for l in before if l not in after]
    ex.append(E("AGENTS.md gains at most 3 lines and loses none",
                0 < len(added) <= 3 and not removed, {"added": added, "removed": removed}))
    ex.append(E("The added lines route to docs/releasing.md with a read cue",
                any("releasing.md" in l and READ_CUE.search(l) for l in added), added))
    changed = [rel for rel, src in fixture.items() if rel != "AGENTS.md" and read(out / rel) != read(src)]
    ex.append(E("Every other fixture file is byte-identical (CI workflow included)", not changed, changed))
    extras = [str(p.relative_to(out)) for p in repo_files(out)
              if str(p.relative_to(out)) not in fixture]
    ex.append(E("No new files (no Taskfile, mise.toml, hooks, bootstrap, docs index)", not extras, extras))
    body = pr_body(out).lower()
    ex.append(E("PR body marks bus-factor, consistency and declutter as skipped",
                "skip" in body and all(p in body for p in ("bus", "consisten", "declutter")), ""))
    return ex


GRADERS = {"eval-0": grade_unhealthy, "eval-1": grade_healthy}


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


if __name__ == "__main__":
    sys.exit(main())
