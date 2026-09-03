#!/usr/bin/env python3
"""Grade cucumber-js-automation eval runs. Usage: grade.py <iteration-dir>.

Expects <iteration-dir>/eval-*/{with_skill,without_skill}/outputs/ as laid
out by scripts/eval_skills.py (run via `task eval:skills
NAME=cucumber-js-automation`). Behavioural check: actually runs the
produced cucumber-js suite; the rest are structural checks on the glue
code (imports, World state, feature content).
"""
import json
import re
import subprocess
import sys
from pathlib import Path

FIXTURES = Path(__file__).resolve().parent / "fixtures"
STEP_SOURCE_SUFFIXES = (".js", ".mjs", ".cjs", ".ts")
RUN_TIMEOUT_SECONDS = 180


def E(text, passed, evidence):
    return {"text": text, "passed": bool(passed), "evidence": str(evidence)[:500]}


def project_files(out, suffixes):
    """Source files in the output tree, skipping installed dependencies
    and the with-skill arm's local skill copy."""
    return [
        p for p in sorted(out.rglob("*"))
        if p.is_file() and p.suffix in suffixes
        and "node_modules" not in p.parts and ".skill" not in p.parts
    ]


def step_files(out):
    """Files that register cucumber-js step definitions."""
    found = []
    for path in project_files(out, STEP_SOURCE_SUFFIXES):
        text = path.read_text(encoding="utf-8", errors="replace")
        if "@cucumber/cucumber" in text and re.search(r"\b(Given|When|Then)\s*\(", text):
            found.append((path, text))
    return found

def run_suite(out):
    """Run the produced suite with its own installed cucumber-js."""
    runners = [
        p for p in out.rglob("node_modules/.bin/cucumber-js")
        if ".skill" not in p.parts
    ]
    if not runners:
        return False, "no node_modules/.bin/cucumber-js — suite was never installed/run"
    runner = min(runners, key=lambda p: len(p.parts))
    try:
        result = subprocess.run(
            [str(runner)], cwd=runner.parents[2], capture_output=True,
            text=True, timeout=RUN_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return False, f"timed out after {RUN_TIMEOUT_SECONDS}s"
    tail = (result.stdout + result.stderr)[-300:]
    return result.returncode == 0, f"exit {result.returncode}: {tail}"


def grade_glue(ex, out):
    """Checks shared by both evals: dependency, bindings, World, green run."""
    pkgs = [p for p in project_files(out, (".json",))
            if p.name == "package.json"]
    dep = any("@cucumber/cucumber" in p.read_text(encoding="utf-8", errors="replace")
              for p in pkgs)
    ex.append(E("package.json depends on @cucumber/cucumber", dep,
                f"package.json files={[str(p.relative_to(out)) for p in pkgs]}"))
    steps = step_files(out)
    ex.append(E("step definitions import Given/When/Then from @cucumber/cucumber",
                bool(steps), f"files={[str(p.relative_to(out)) for p, _ in steps]}"))
    uses_world = [str(p.relative_to(out)) for p, t in steps if re.search(r"\bthis\.", t)]
    ex.append(E("steps keep scenario state on the World (this.*), not globals",
                bool(uses_world), f"files using this.*={uses_world}"))
    arrow_steps = [
        str(p.relative_to(out)) for p, t in steps
        if re.search(r"\b(Given|When|Then)\s*\(\s*[^,\n]+,\s*(?:\{[^}]*\}\s*,\s*)?"
                     r"(?:async\s*)?\([^)]*\)\s*=>", t)
    ]
    ex.append(E("no arrow-function step callbacks (they cannot bind this)",
                not arrow_steps, f"arrow steps in={arrow_steps}"))
    passed, evidence = run_suite(out)
    ex.append(E("the produced suite passes under cucumber-js", passed, evidence))
    return steps


def grade_implement_steps(out):
    ex = []
    grade_glue(ex, out)
    original = (FIXTURES / "account-withdrawal.feature").read_text(encoding="utf-8")
    # Moving the spec into the conventional features/ directory is fine —
    # only its content is contractual.
    produced = [p for p in project_files(out, (".feature",))
                if p.name == "account-withdrawal.feature"]
    unchanged = any(p.read_text(encoding="utf-8").split() == original.split()
                    for p in produced)
    ex.append(E("account-withdrawal.feature left unchanged (it is the spec)",
                unchanged, "missing" if not produced else "diff vs fixture"))
    return ex


def grade_spec_and_steps(out):
    ex = []
    grade_glue(ex, out)
    features = [p for p in project_files(out, (".feature",))]
    text = "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in features)
    n_scenarios = len(re.findall(r"^\s*(Scenario|Example)( Outline| Template)?:",
                                 text, re.M))
    ex.append(E("wrote a feature file with at least 3 scenarios",
                "Feature:" in text and n_scenarios >= 3,
                f"features={[str(p.relative_to(out)) for p in features]} "
                f"scenarios={n_scenarios}"))
    low = text.lower()
    covered = [w for w in ("discount", "deliver") if w in low]
    ex.append(E("scenarios cover both the discount and the delivery rules",
                len(covered) == 2, f"covered={covered}"))
    jargon = sorted(set(m.group(0) for m in re.finditer(
        r"\bcart\.js\b|\bmethod\b|\bfunction\b|\bpence\b|require\(", low)))
    ex.append(E("feature stays in business language (no code jargon in steps)",
                not jargon, f"found={jargon}"))
    return ex


GRADERS = {"eval-0": grade_implement_steps, "eval-1": grade_spec_and_steps}


def main():
    iteration = Path(sys.argv[1]).resolve()
    for eval_dir in sorted(iteration.glob("eval-*")):
        grader = GRADERS[eval_dir.name[:6]]
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
