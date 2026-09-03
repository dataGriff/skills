#!/usr/bin/env python3
"""Grade requirements-to-gherkin eval runs. Usage: grade.py <iteration-dir>.

Expects <iteration-dir>/eval-*/{with_skill,without_skill}/outputs/ as laid
out by scripts/eval_skills.py (run via `task eval:skills
NAME=requirements-to-gherkin`). Writes grading.json per arm and prints a
pass/total summary. Checks are keyed to traps planted in the eval prompts
and fixtures: a contradiction, unknowns, vague terms, and numeric
boundaries that a careful elicitor must surface rather than resolve by
guessing.
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
QUESTION_HEADING = re.compile(r"^#+ .*(question|open|unknown|clarif|to confirm|follow.?up)", re.I | re.M)


def E(text, passed, evidence):
    return {"text": text, "passed": bool(passed), "evidence": str(evidence)[:500]}


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


def questions_region(text):
    """Text from the first questions-ish heading to the end of its section."""
    m = QUESTION_HEADING.search(text)
    if not m:
        return ""
    level = m.group(0).split(" ")[0]
    rest = text[m.end():]
    nxt = re.search(rf"^{level} (?!.*(question|open|unknown|clarif))", rest, re.M | re.I)
    return rest[: nxt.start()] if nxt else rest


def grade_notes_to_gherkin(out):
    ex = []
    req = out / "requirements.md"
    feat = out / "refunds.feature"
    ex.append(E("requirements.md and refunds.feature both written",
                req.exists() and feat.exists(),
                f"req={req.exists()} feature={feat.exists()}"))
    if not (req.exists() and feat.exists()):
        return ex
    rtext = req.read_text(encoding="utf-8")
    q = questions_region(rtext)
    ex.append(E("requirements.md separates open questions under their own heading",
                len(q) > 40, f"questions region {len(q)} chars"))
    ex.append(E("The Priya/Dave contradiction (store credit vs original payment) "
                "is surfaced as a question, not silently resolved",
                bool(re.search(r"store credit|payment method", q, re.I)),
                "grep questions region"))
    ex.append(E("The unknowns nobody could answer (international/customs, "
                "goodwill override limits) land as questions",
                bool(re.search(r"international|customs", q, re.I))
                and bool(re.search(r"goodwill|override|manager", q, re.I)),
                "grep questions region"))
    ex.append(E("The vague 'quickly' is challenged (how fast, in what unit) "
                "instead of copied through as a requirement",
                bool(re.search(r"quick|how (long|fast)|hours|days|sla|working day", q, re.I)),
                "grep questions region"))

    text = feat.read_text(encoding="utf-8")
    blocks = scenarios(text)
    n_rules = len(re.findall(r"^\s*Rule:", text, re.M))
    ex.append(E("Feature file: >= 5 scenarios under >= 2 Rule: blocks",
                len(blocks) >= 5 and n_rules >= 2,
                f"scenarios={len(blocks)} rules={n_rules}"))
    multi_when = [n for n, s in blocks
                  if sum(1 for l in s if l.startswith("When ")) > 1]
    no_then = [n for n, s in blocks if not any(l.startswith("Then ") for l in s)]
    ui = sorted(set(m.group(0).strip() for m in UI_WORDS.finditer(text)))
    ex.append(E("Scenarios well-formed: one When each, every one asserts a Then, "
                "no UI mechanics",
                not multi_when and not no_then and not ui,
                f"multi_when={multi_when} no_then={no_then} ui={ui}"))
    ex.append(E("The 30-day window gets a boundary example (day 30 and/or 31 "
                "exercised)", bool(re.search(r"\b3[01]\b", text)), r"grep \b3[01]\b"))
    rejections = [n for n, s in blocks if any(
        l.startswith(("Then ", "And ", "But ")) and
        re.search(r"declin|reject|refus|not refund|no refund|store credit|told", l, re.I)
        for l in s)]
    ex.append(E("At least two scenarios show a refund being refused (window "
                "exceeded, gift card, used item…)", len(rejections) >= 2,
                f"rejections={rejections}"))
    ex.append(E("Assumptions/open points are flagged inline in the feature file, "
                "not presented as agreed",
                bool(re.search(r"^\s*#.*(open|assum|question|confirm|tbd)", text, re.I | re.M)),
                "grep # comment with open/assumed"))
    return ex


def grade_session_prep(out):
    ex = []
    f = out / "questions.md"
    if not f.exists():
        return [E("questions.md exists", False, "missing")]
    text = f.read_text(encoding="utf-8")
    n_q = text.count("?")
    ex.append(E("A real question set (>= 10 questions)", n_q >= 10, f"questions={n_q}"))
    ex.append(E("Grouped under headings, not one flat list",
                len(re.findall(r"^#{2,} ", text, re.M)) >= 3,
                f"headings={len(re.findall(r'^#{2,} ', text, re.M))}"))
    ex.append(E("Probes the 15-minute boundary: what happens at/after expiry",
                bool(re.search(r"expir|15 minutes? (is|are|pass|end|up)|runs? out|lapse", text, re.I)),
                "grep expiry phrasing"))
    ex.append(E("Probes concurrency: two shoppers wanting the last item",
                bool(re.search(r"same time|simultan|concurren|two (shopper|customer|people)|last (item|one)|someone else", text, re.I)),
                "grep concurrency phrasing"))
    ex.append(E("Probes failure/abandonment paths (checkout abandoned, payment "
                "fails, item out of stock)",
                bool(re.search(r"abandon|payment fail|fails|cancel|out of stock|close[sd]? the (tab|browser|app)", text, re.I)),
                "grep failure phrasing"))
    ex.append(E("Questions phrased as concrete scenarios, not only abstract asks",
                len(re.findall(r"what (happens|should happen)", text, re.I)) >= 3
                or bool(re.search(r"\b(Alice|Bob|a shopper (who|with))\b", text)),
                "grep 'what happens' / named actor"))
    ex.append(E("Ships a capture structure separating rules, examples and open "
                "questions for the session",
                all(re.search(w, text, re.I) for w in (r"rule", r"example", r"question")),
                "grep rule+example+question"))
    return ex


GRADERS = {"eval-0": grade_notes_to_gherkin, "eval-1": grade_session_prep}


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
