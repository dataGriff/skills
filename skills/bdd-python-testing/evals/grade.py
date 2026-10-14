#!/usr/bin/env python3
"""Grade bdd-python-testing eval runs. Usage: grade.py <iteration-dir>.

Expects <iteration-dir>/eval-*/{with_skill,without_skill}/outputs/ as laid
out by scripts/eval_skills.py (run via `task eval:skills
NAME=bdd-python-testing`). Behavioural where it matters: each arm's suite is
actually executed (pytest / behave must be installed on the grading host),
plus structural checks on the glue code. Writes grading.json per arm and
prints a pass/total summary.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"
STEP_DECORATOR = re.compile(r"@(given|when|then)\b")
PARAM_DECORATOR = re.compile(r"@(given|when|then)\([^)\n]*\{")


def E(text, passed, evidence):
    return {"text": text, "passed": bool(passed), "evidence": str(evidence)[:500]}


def run(cmd, cwd):
    try:
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=180)
        return r.returncode, (r.stdout + r.stderr)[-3000:]
    except subprocess.TimeoutExpired:
        return -1, "timeout"


def glue_sources(out, domain_file):
    """Concatenated Python written by the arm: everything except the domain
    fixture and the skill copy the runner drops in .skill/."""
    texts = []
    for p in sorted(out.rglob("*.py")):
        if ".skill" in p.parts or p.name == domain_file:
            continue
        texts.append(p.read_text(encoding="utf-8", errors="replace"))
    return "\n".join(texts)


def feature_untouched(out, fixture_name):
    """The feature file may move, but its text is the contract — some copy of
    it must survive verbatim (modulo trailing whitespace)."""
    want = normalise((FIXTURES / fixture_name).read_text(encoding="utf-8"))
    found = [p for p in out.rglob("*.feature") if ".skill" not in p.parts]
    ok = any(normalise(p.read_text(encoding="utf-8", errors="replace")) == want
             for p in found)
    return ok, [str(p.relative_to(out)) for p in found]


def normalise(text):
    return "\n".join(line.rstrip() for line in text.strip().splitlines())


def grade_pytest_bdd(out):
    ex = []
    code, log = run([sys.executable, "-m", "pytest", "-q", "--tb=line"], out)
    ex.append(E("pytest exits green", code == 0, log[-300:]))
    m = re.search(r"(\d+) passed", log)
    ex.append(E("All 5 scenarios run as tests (3 + 2 outline rows)",
                m and int(m.group(1)) >= 5, m.group(0) if m else "no pass count"))
    src = glue_sources(out, "giftcard.py")
    ex.append(E("Scenarios bound through pytest-bdd, not hand-rolled pytest",
                "pytest_bdd" in src, "grep pytest_bdd"))
    ex.append(E("Steps parameterised with parsers, values not hardcoded",
                "parsers." in src, "grep parsers."))
    n_steps = len(STEP_DECORATOR.findall(src))
    ex.append(E("One definition per phrasing (7 distinct phrasings, <= 9 "
                "step decorators)", 0 < n_steps <= 9, f"decorators={n_steps}"))
    ex.append(E("State flows via fixtures (target_fixture), not globals",
                "target_fixture" in src, "grep target_fixture"))
    ex.append(E("Refusal captured in the When and asserted on "
                "(RedemptionRefused referenced in glue)",
                "RedemptionRefused" in src, "grep RedemptionRefused"))
    ok, found = feature_untouched(out, "giftcard.feature")
    ex.append(E("Feature file text unchanged", ok, f"features={found}"))
    return ex


def grade_behave(out):
    ex = []
    code, log = run([sys.executable, "-m", "behave", "--dry-run"], out)
    ex.append(E("behave --dry-run clean: every step defined", code == 0, log[-300:]))
    code, log = run([sys.executable, "-m", "behave", "--format=progress"], out)
    ex.append(E("behave exits green", code == 0, log[-300:]))
    m = re.search(r"(\d+) scenarios? passed", log)
    ex.append(E("All 3 scenarios pass", m and int(m.group(1)) >= 3,
                m.group(0) if m else "no scenario count"))
    steps_dirs = [p for p in out.rglob("steps") if p.is_dir() and ".skill" not in p.parts]
    ex.append(E("Conventional behave tree (a steps/ directory)",
                bool(steps_dirs), f"steps={[str(p.relative_to(out)) for p in steps_dirs]}"))
    src = glue_sources(out, "booking.py")
    ex.append(E("Steps parameterised with matcher placeholders",
                bool(PARAM_DECORATOR.search(src)) or "use_step_matcher" in src,
                "placeholder in a step decorator"))
    ex.append(E("State shared via context, room table read from context.table",
                "context." in src and "context.table" in src,
                "grep context. / context.table"))
    ex.append(E("Refusal captured in the When and asserted on "
                "(BookingRefused referenced in glue)",
                "BookingRefused" in src, "grep BookingRefused"))
    ok, found = feature_untouched(out, "room_booking.feature")
    ex.append(E("Feature file text unchanged", ok, f"features={found}"))
    return ex


GRADERS = {"eval-0": grade_pytest_bdd, "eval-1": grade_behave}


def main():
    iteration = Path(sys.argv[1])
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
