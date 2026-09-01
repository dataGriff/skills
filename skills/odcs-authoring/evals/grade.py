#!/usr/bin/env python3
"""Grade odcs-authoring eval runs. Usage: grade.py <iteration-dir>.

Expects <iteration-dir>/eval-*/{with_skill,without_skill}/outputs/ as laid
out by scripts/eval_skills.py (run via `task eval:skills NAME=odcs-authoring`).
Writes grading.json per arm and prints a pass/total summary. Requires the
datacontract CLI; the Spectral assertion is skipped if spectral isn't on PATH.
"""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

SKILL_DIR = Path(__file__).resolve().parent.parent
RULESET = SKILL_DIR / "assets" / "spectral-odcs.yaml"
SNAKE = re.compile(r"^[a-z0-9]+(_[a-z0-9]+)*$")


def sh(*args):
    r = subprocess.run(args, capture_output=True, text=True, timeout=120)
    return r.returncode, (r.stdout + r.stderr)[-600:]


def lint(path):
    code, out = sh("datacontract", "lint", str(path), "--all-errors")
    return code == 0, out


def load(path):
    try:
        return yaml.safe_load(path.read_text()) or {}
    except Exception as e:
        return {"__parse_error__": str(e)}


def all_names(schema):
    names = []
    def walk(props):
        for p in props or []:
            if isinstance(p, dict):
                names.append(str(p.get("name", "")))
                items = p.get("items") or {}
                walk(p.get("properties"))
                walk(items.get("properties") if isinstance(items, dict) else None)
    for obj in schema or []:
        if isinstance(obj, dict):
            names.append(str(obj.get("name", "")))
            walk(obj.get("properties"))
    return [n for n in names if n]


def E(text, passed, evidence):
    return {"text": text, "passed": bool(passed), "evidence": str(evidence)[:500]}


def grade_author_orders(out):
    ex = []
    f = out / "orders.odcs.yaml"
    if not f.exists():
        yams = [p for p in out.glob("*.y*ml")]
        f = yams[0] if yams else f
    if not f.exists():
        return [E("orders.odcs.yaml produced", False, "no yaml in outputs")]
    ok, o = lint(f)
    ex.append(E("Passes `datacontract lint`", ok, o))
    doc = load(f)
    ex.append(E("apiVersion is v3.1.0", doc.get("apiVersion") == "v3.1.0",
                doc.get("apiVersion")))
    names = all_names(doc.get("schema"))
    bad = [n for n in names if not SNAKE.match(n)]
    ex.append(E("All schema names lower_snake_case", names and not bad, f"bad={bad}"))
    s = json.dumps(doc)
    ex.append(E("Quality rule restricts order_status to the 5 valid values",
                all(v in s for v in ["pending", "paid", "shipped", "cancelled", "refunded"])
                and ("validValues" in s or "invalidValues" in s or '"sql"' in s),
                "checked validValues/invalidValues with all 5 values"))
    sla = [p for p in doc.get("slaProperties") or [] if isinstance(p, dict)]
    fresh = any(p.get("property") in ("latency", "freshness") and str(p.get("value")) == "2" for p in sla)
    ret = any(p.get("property") == "retention" and str(p.get("value")) == "5" for p in sla)
    ex.append(E("SLAs declare 2h freshness and 5y retention", fresh and ret, json.dumps(sla)[:300]))
    ex.append(E("Team owner and support channel present",
                "priya@example.com" in s and "sales-data" in s, "grep owner+channel"))
    if shutil.which("spectral"):
        code, o2 = sh("spectral", "lint", "--ruleset", str(RULESET), str(f))
        ex.append(E("Passes Spectral governance ruleset", code == 0, o2))
    return ex


def grade_review_legacy(out):
    ex = []
    f = out / "customer-profiles.odcs.yaml"
    rv = out / "review.md"
    if not f.exists():
        return [E("customer-profiles.odcs.yaml produced", False, "missing")]
    ok, o = lint(f)
    doc = load(f)
    ex.append(E("Fixed contract lints clean and declares v3.1.0",
                ok and doc.get("apiVersion") == "v3.1.0", f"lint={ok} api={doc.get('apiVersion')}"))
    s = json.dumps(doc)
    ex.append(E("Deprecated dataProduct removed and rule: replaced with metric:",
                "dataProduct" not in doc and '"rule"' not in s and '"metric"' in s,
                f"dataProduct={'dataProduct' in doc}"))
    team = doc.get("team")
    ex.append(E("team is v3.1 object form with members",
                isinstance(team, dict) and isinstance(team.get("members"), list),
                type(team).__name__))
    names = all_names(doc.get("schema"))
    bad = [n for n in names if not SNAKE.match(n)]
    ex.append(E("All names converted to snake_case", names and not bad, f"bad={bad}"))
    ex.append(E("Password removed from servers", "hunter2" not in s and
                not any("password" in (srv or {}) for srv in doc.get("servers") or []),
                "checked hunter2 + password key"))
    if rv.exists():
        r = rv.read_text().lower()
        flags = {
            "deprecated": "dataproduct" in r or "deprecated" in r,
            "casing": "snake" in r or "camel" in r or "case" in r,
            "secret": "password" in r or "secret" in r or "credential" in r,
            "team": "team" in r and ("member" in r or "object" in r or "structure" in r or "deprecated" in r),
        }
        ex.append(E("review.md flags all four planted defect classes", all(flags.values()),
                    json.dumps(flags)))
    else:
        ex.append(E("review.md flags all four planted defect classes", False, "review.md missing"))
    return ex


GRADERS = {"eval-0": grade_author_orders, "eval-1": grade_review_legacy}


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
