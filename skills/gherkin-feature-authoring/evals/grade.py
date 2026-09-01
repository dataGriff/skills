#!/usr/bin/env python3
"""Grade gherkin-feature-authoring eval runs. Usage: grade.py <iteration-dir>.

Expects <iteration-dir>/eval-*/{with_skill,without_skill}/outputs/ as laid
out by scripts/eval_skills.py (run via `task eval:skills
NAME=gherkin-feature-authoring`). Writes grading.json per arm and prints a
pass/total summary. Structural checks only — no gherkin parser dependency.
"""
import json
import re
import sys
from pathlib import Path

STEP_KEYWORDS = ("Given ", "When ", "Then ", "And ", "But ", "* ")
BLOCK_KEYWORDS = ("Scenario:", "Scenario Outline:", "Example:", "Scenario Template:")
UI_WORDS = re.compile(
    r"\bclick|\bbutton\b|\bbrowser\b|\bdropdown\b|\bcheckbox\b|text box|"
    r"\burl\b|\bnavigat|\bI open \"|I see the text|into the \"",
    re.I,
)


def scenarios(text):
    """Split a feature file into (name, [step lines]) blocks."""
    blocks, name, steps = [], None, []
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith(BLOCK_KEYWORDS):
            if name is not None:
                blocks.append((name, steps))
            name, steps = line.split(":", 1)[1].strip(), []
        elif line.startswith(("Background:", "Rule:")):
            if name is not None:
                blocks.append((name, steps))
            name, steps = None, []
        elif name is not None and line.startswith(STEP_KEYWORDS):
            steps.append(line)
    if name is not None:
        blocks.append((name, steps))
    return blocks


def feature_description(text):
    """Free text between the Feature: line and the first structural keyword."""
    lines = text.splitlines()
    starts = [i for i, l in enumerate(lines) if l.strip().startswith("Feature:")]
    if not starts:
        return ""
    desc = []
    for line in lines[starts[0] + 1:]:
        s = line.strip()
        if s.startswith(BLOCK_KEYWORDS + ("Background:", "Rule:", "@")):
            break
        if s and not s.startswith("#"):
            desc.append(s)
    return " ".join(desc)


def E(text, passed, evidence):
    return {"text": text, "passed": bool(passed), "evidence": str(evidence)[:500]}


def grade_structure(ex, text, min_scenarios):
    blocks = scenarios(text)
    ex.append(E(f"One Feature, >= {min_scenarios} scenarios",
                text.count("Feature:") == 1 and len(blocks) >= min_scenarios,
                f"features={text.count('Feature:')} scenarios={len(blocks)}"))
    desc = feature_description(text)
    ex.append(E("Feature carries a narrative description", len(desc) >= 30, desc[:120]))
    multi_when = [n for n, s in blocks
                  if sum(1 for l in s if l.startswith("When ")) > 1]
    ex.append(E("At most one When per scenario", not multi_when, f"multi={multi_when}"))
    no_then = [n for n, s in blocks if not any(l.startswith("Then ") for l in s)]
    ex.append(E("Every scenario asserts an outcome (has a Then)",
                not no_then, f"missing={no_then}"))
    ui = sorted(set(m.group(0).strip() for m in UI_WORDS.finditer(text)))
    ex.append(E("Declarative: no UI mechanics in steps", not ui, f"found={ui}"))
    return blocks


def grade_story_to_feature(out):
    ex = []
    f = out / "loyalty-points.feature"
    if not f.exists():
        return [E("loyalty-points.feature exists", False, "missing")]
    text = f.read_text(encoding="utf-8")
    grade_structure(ex, text, min_scenarios=4)
    low = text.lower()
    covered = [w for w in ("deliver", "ship", "discount") if w in low]
    ex.append(E("Covers delivery-fee, award-on-shipping and discount criteria",
                len(covered) == 3, f"covered={covered}"))
    ex.append(E("Concrete example data (real amounts, not only placeholders)",
                bool(re.search(r"(Given|When|Then|And|But)[^<\n]*\d", text)),
                "digit in a step outside <placeholders>"))
    return ex


def grade_review_rewrite(out):
    ex = []
    f = out / "checkout.feature"
    if not f.exists():
        return [E("checkout.feature exists", False, "missing")]
    text = f.read_text(encoding="utf-8")
    blocks = grade_structure(ex, text, min_scenarios=3)
    bad_names = [n for n, _ in blocks if re.fullmatch(r"Test ?\d+", n, re.I)]
    ex.append(E("Scenario names state the behaviour, not 'Test N'",
                blocks and not bad_names, f"bad={bad_names}"))
    ex.append(E("No technical setup (database wiping) in steps",
                "database" not in text.lower(), "grep database"))
    review = out / "review.md"
    r = review.read_text(encoding="utf-8").lower() if review.exists() else ""
    smells = {
        "ui-coupling": ("ui", "imperative", "click"),
        "one-behaviour": ("one when", "single behaviour", "single behavior",
                          "multiple when", "one behaviour", "one behavior", "split"),
        "independence": ("independen", "order", "chain", "depend"),
        "missing-then": ("then", "outcome", "assert"),
    }
    named = [k for k, cues in smells.items() if any(c in r for c in cues)]
    ex.append(E("review.md names at least 3 of the 4 planted smell classes",
                len(named) >= 3, f"named={named}"))
    return ex


GRADERS = {"eval-0": grade_story_to_feature, "eval-1": grade_review_rewrite}


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
