#!/usr/bin/env python3
"""Grade goldratt-4-questions eval runs. Usage: grade.py <iteration-dir>.

Expects <iteration-dir>/eval-*/{with_skill,without_skill}/outputs/ as laid
out by scripts/eval_skills.py (run via `task eval:skills
NAME=goldratt-4-questions`). Writes grading.json per arm and prints a
pass/total summary. Checks are keyed to traps planted in the fixtures: a
feature-list pitch with no limitation evidence, an explicit
"no process changes, old system runs in parallel indefinitely" plan, and
a failed adoption whose old rules were never retired — the things the
four questions exist to catch.
"""
import json
import re
import sys
from pathlib import Path


def E(text, passed, evidence):
    return {"text": text, "passed": bool(passed), "evidence": str(evidence)[:500]}


def grade_proposal_review(out):
    f = out / "assessment.md"
    if not f.exists():
        return [E("assessment.md exists", False, "missing")]
    text = f.read_text(encoding="utf-8")
    ex = [E("assessment.md exists with substance", len(text) > 800, f"{len(text)} chars")]
    ex.append(E(
        "Ties value to the concrete current-state pain (nightly batch staleness, "
        "multi-week export queue) rather than accepting 'best practice' rhetoric",
        bool(re.search(r"nightly|batch|stale|24[- ]?hour", text, re.I))
        and bool(re.search(r"two to four weeks|2.4 weeks|weeks|turnaround|jira|export", text, re.I)),
        "grep batch/staleness + export-queue phrasing"))
    ex.append(E(
        "Flags the missing evidence for the limitation as an open question "
        "(how often it bites, what it costs, who suffers)",
        bool(re.search(r"how often|how much|what (does|is) (it|the|this).{0,20}cost|"
                       r"quantif|evidence|no (data|figures|numbers)|incident|"
                       r"cost of (the )?(delay|staleness|status quo)", text, re.I)),
        "grep evidence/cost probing"))
    ex.append(E(
        "Identifies existing processes as rules that would have to change or be "
        "retired (reconciliation report, Jira export queue)",
        bool(re.search(r"reconcil", text, re.I))
        and bool(re.search(r"retire|replace|remove|stop|decommission|no longer|"
                           r"go(es)? away|change", text, re.I)),
        "grep reconciliation + retirement phrasing"))
    ex.append(E(
        "Challenges 'no process changes required' / batch running in parallel "
        "indefinitely as cost without benefit",
        bool(re.search(r"parallel|safety net|no changes|keep.{0,30}(batch|jira)|"
                       r"indefinitely", text, re.I))
        and bool(re.search(r"cost without|both systems|two systems|double|red flag|"
                           r"contradict|undermine|no benefit|defeats|never.{0,20}"
                           r"(realis|realiz)|won'?t.{0,30}(value|benefit)|"
                           r"without.{0,30}(benefit|value)", text, re.I)),
        "grep parallel-plan challenge"))
    ex.append(E(
        "Distinguishes power from the feature list (names what the tech makes "
        "possible, not just connectors/dashboards/SSO)",
        bool(re.search(r"real[- ]?time|near[- ]?real|event[- ]?driven|stream|"
                       r"as (it|they) happen|self[- ]?serve|without (raising|waiting)",
                       text, re.I)),
        "grep capability phrasing"))
    ex.append(E(
        "Ends with an explicit recommendation section",
        bool(re.search(r"^#+ .*(recommend|verdict|decision|conclusion)", text, re.I | re.M)),
        "grep recommendation heading"))
    ex.append(E(
        "Recommendation is conditional or withheld, not a rubber-stamp approve "
        "of the proposal as written",
        bool(re.search(r"do(es)? not (approve|adopt)|don'?t (approve|adopt)|"
                       r"not (yet|ready|as written|approve)|defer|reject|spike|"
                       r"pilot|proof of concept|poc\b|only if|provided that|"
                       r"conditional|before (approving|adopting|committing)|"
                       r"revise|rework", text, re.I)),
        "grep conditional-verdict phrasing"))
    return ex


def grade_adoption_post_mortem(out):
    f = out / "review.md"
    if not f.exists():
        return [E("review.md exists", False, "missing")]
    text = f.read_text(encoding="utf-8")
    ex = [E("review.md exists with substance", len(text) > 800, f"{len(text)} chars")]
    ex.append(E(
        "Root cause: the old discovery channels (email / #data-help) and the "
        "old documentation home (Confluence) were never retired and compete "
        "with the catalog",
        bool(re.search(r"confluence", text, re.I))
        and bool(re.search(r"email|#?data-help|slack", text, re.I))
        and bool(re.search(r"still|parallel|compet|alongside|never (retired|stopped|"
                           r"switched)|remain", text, re.I)),
        "grep old-channels-kept phrasing"))
    ex.append(E(
        "Names that no behaviour change was ever required (population optional, "
        "nobody asked to stop or start anything)",
        bool(re.search(r"optional|nobody was asked|no ?one was asked|"
                       r"not required|voluntar|no (behaviou?r|process) change|"
                       r"asked to stop", text, re.I)),
        "grep no-behaviour-change phrasing"))
    ex.append(E(
        "Frames the outcome as paying for the tool on top of the old process "
        "(cost without benefit)",
        bool(re.search(r"cost without|paying for both|tool and the old|"
                       r"on top of|duplicat|£40k|40k|added cost|"
                       r"cost.{0,40}(no|without|little).{0,15}(benefit|value)",
                       text, re.I)),
        "grep cost-without-benefit phrasing"))
    ex.append(E(
        "Engages with whether the underlying limitation is real, using the "
        "demand evidence (25 requests/week to the platform team)",
        bool(re.search(r"25|requests? (a|per) week|demand|bottleneck|"
                       r"limitation|real problem|genuine", text, re.I)),
        "grep limitation-evidence phrasing"))
    ex.append(E(
        "Recommends a concrete renewal decision: enforce new rules (retire "
        "parallel channels, make population part of the workflow) or "
        "decommission — not more evangelism",
        bool(re.search(r"decommission|don'?t renew|do not renew|cancel|"
                       r"retire|redirect|freeze|read[- ]?only|mandat|require|"
                       r"enforce|gate|part of (the )?workflow|single (source|path)",
                       text, re.I)),
        "grep enforce-or-decommission phrasing"))
    ex.append(E(
        "Does not recommend awareness campaigns / training as the primary fix",
        not re.search(r"^#+ .*(awareness|evangeli|training|campaign|promote)",
                      text, re.I | re.M),
        "grep evangelism headings"))
    return ex


GRADERS = {"eval-0": grade_proposal_review, "eval-1": grade_adoption_post_mortem}


def main():
    iteration = Path(sys.argv[1])
    for eval_dir in sorted(iteration.glob("eval-*")):
        grader = GRADERS["-".join(eval_dir.name.split("-", 2)[:2])]
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
