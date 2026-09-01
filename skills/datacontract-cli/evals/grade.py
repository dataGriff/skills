#!/usr/bin/env python3
"""Grade datacontract-cli eval runs. Usage: grade.py <iteration-dir>.

Expects <iteration-dir>/eval-*/{with_skill,without_skill}/outputs/ as laid
out by scripts/eval_skills.py (run via `task eval:skills NAME=datacontract-cli`).
Writes grading.json per arm and prints a pass/total summary. Requires the
datacontract CLI for the lint assertions.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

import yaml

SNAKE = re.compile(r"^[a-z0-9]+(_[a-z0-9]+)*$")


def sh(*args):
    r = subprocess.run(args, capture_output=True, text=True, timeout=120)
    return r.returncode, (r.stdout + r.stderr)[-600:]


def load(path):
    try:
        return yaml.safe_load(path.read_text()) or {}
    except Exception as e:
        return {"__parse_error__": str(e)}


def E(text, passed, evidence):
    return {"text": text, "passed": bool(passed), "evidence": str(evidence)[:500]}


def grade_snowflake_ci(out):
    ex = []
    ci = out / "ci.yml"
    setup = out / "setup.md"
    text = (ci.read_text() if ci.exists() else "") + "\n" + (
        setup.read_text() if setup.exists() else "")
    text = text.replace("\\\n", " ")
    if ci.exists():
        valid = "__parse_error__" not in load(ci)
        has_lint = "datacontract lint" in text or "datacontract ci" in text
        has_test = "datacontract test" in text or "datacontract ci" in text
        ex.append(E("ci.yml valid YAML with lint + test steps", valid and has_lint and has_test,
                    f"valid={valid} lint={has_lint} test={has_test}"))
    else:
        ex.append(E("ci.yml valid YAML with lint + test steps", False, "ci.yml missing"))
    ex.append(E("Uses real key-pair env vars (DATACONTRACT_SNOWFLAKE_USERNAME + _PRIVATE_KEY*)",
                "DATACONTRACT_SNOWFLAKE_USERNAME" in text and "DATACONTRACT_SNOWFLAKE_PRIVATE_KEY" in text,
                f"found={sorted(set(re.findall(r'DATACONTRACT_SNOWFLAKE_[A-Z_]+', text)))}"))
    ex.append(E("Installs datacontract-cli with snowflake support",
                bool(re.search(r"datacontract-cli\[(all|snowflake)", text)),
                "grep datacontract-cli[snowflake|all]"))
    hardcoded = re.search(r"(password|private_key)\s*[:=]\s*['\"]?[A-Za-z0-9+/]{12,}", text, re.I)
    ex.append(E("Credentials via GitHub secrets, none hardcoded",
                "secrets." in text and not hardcoded,
                f"secrets.={'secrets.' in text} hardcoded={bool(hardcoded)}"))
    bad = re.findall(r"datacontract (diff|breaking|validate)\b|export\s+--format", text)
    ex.append(E("No hallucinated commands or flags", not bad, f"suspicious={bad}"))
    return ex


def grade_ddl_pipeline(out):
    ex = []
    c = out / "shipments.odcs.yaml"
    if c.exists():
        code, o = sh("datacontract", "lint", str(c), "--all-errors")
        ex.append(E("shipments.odcs.yaml exists and lints clean", code == 0, o))
    else:
        ex.append(E("shipments.odcs.yaml exists and lints clean", False, "missing"))
    cm = out / "commands.md"
    t = (cm.read_text() if cm.exists() else "").replace("\\\n", " ")
    ex.append(E("Correct import syntax (import sql --source ... --dialect)",
                bool(re.search(r"datacontract import sql\s+--source\s+\S+.*--dialect", t, re.S)),
                t[:300]))
    ex.append(E("Subcommand export syntax, no --format flag",
                bool(re.search(r"datacontract export (dbt-models|html)\b", t)) and "--format" not in t,
                "grep export subcommands"))
    dbt = out / "dbt-models.yaml"
    html = out / "shipments.html"
    ex.append(E("dbt-models.yaml and shipments.html produced, non-empty",
                dbt.exists() and dbt.stat().st_size > 50
                and html.exists() and html.stat().st_size > 200,
                f"dbt={dbt.exists()} html={html.exists()}"))
    if c.exists():
        doc = load(c)
        s = json.dumps(doc)
        cols = {"shipment_id", "order_id", "carrier", "tracking_number", "shipped_at",
                "delivered_at", "weight_kg", "status"}
        missing = {col for col in cols if f'"{col}"' not in s}
        pk = '"shipment_id"' in s and '"primaryKey": true' in s
        ex.append(E("All 8 DDL columns present; shipment_id is primary key",
                    not missing and pk, f"missing={sorted(missing)} pk={pk}"))
    else:
        ex.append(E("All 8 DDL columns present; shipment_id is primary key", False, "no contract"))
    return ex


GRADERS = {"eval-0": grade_snowflake_ci, "eval-1": grade_ddl_pipeline}


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
