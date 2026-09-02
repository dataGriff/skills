#!/usr/bin/env python3
"""Grade openapi-authoring eval runs. Usage: grade.py <iteration-dir>.

Expects <iteration-dir>/eval-*/{with_skill,without_skill}/outputs/ as laid
out by scripts/eval_skills.py (run via `task eval:skills NAME=openapi-authoring`).
Writes grading.json per arm and prints a pass/total summary. Lints with the
Spectral CLI (`spectral` on PATH, else `npx -y @stoplight/spectral-cli`);
the lint assertion is skipped if neither can run.
"""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

SKILL_DIR = Path(__file__).resolve().parent.parent
RULESET = SKILL_DIR / "assets" / "spectral-openapi.yaml"
KEBAB_PATH = re.compile(r"^(/([a-z0-9]+(-[a-z0-9]+)*|\{[a-zA-Z0-9]+\}))+$")
CAMEL = re.compile(r"^[a-z][a-zA-Z0-9]*$")
METHODS = ("get", "put", "post", "delete", "options", "head", "patch", "trace")


def spectral_cmd():
    if shutil.which("spectral"):
        return ["spectral"]
    if shutil.which("npx"):
        return ["npx", "-y", "@stoplight/spectral-cli"]
    return None


def lint(path):
    cmd = spectral_cmd()
    if cmd is None:
        return None, "spectral/npx not available - lint skipped"
    r = subprocess.run(
        cmd + ["lint", "--ruleset", str(RULESET), "--fail-severity=error", str(path)],
        capture_output=True, text=True, timeout=300,
    )
    return r.returncode == 0, (r.stdout + r.stderr)[-600:]


def load(path):
    try:
        return yaml.safe_load(path.read_text()) or {}
    except Exception as e:
        return {"__parse_error__": str(e)}


def operations(doc):
    for path, item in (doc.get("paths") or {}).items():
        if isinstance(item, dict):
            for method in METHODS:
                if isinstance(item.get(method), dict):
                    yield path, method, item[method]


def E(text, passed, evidence):
    return {"text": text, "passed": bool(passed), "evidence": str(evidence)[:500]}


def find_spec(out, preferred):
    f = out / preferred
    if f.exists():
        return f
    yams = [p for p in out.glob("*.y*ml") if p.name != "legacy-customers-api.yaml"]
    return yams[0] if yams else f


def grade_common(f, ex):
    """Assertions shared by both evals: lint, 3.1, paths, operationIds, errors."""
    ok, o = lint(f)
    if ok is not None:  # omit the assertion entirely when spectral can't run
        ex.append(E("Passes Spectral governance ruleset", ok, o))
    doc = load(f)
    ex.append(E("openapi version is 3.1.x", str(doc.get("openapi", "")).startswith("3.1"),
                doc.get("openapi")))
    paths = list((doc.get("paths") or {}).keys())
    bad = [p for p in paths if not KEBAB_PATH.match(p)]
    ex.append(E("All paths kebab-case, no verbs/casing", paths and not bad, f"bad={bad}"))
    ops = list(operations(doc))
    no_id = [f"{m} {p}" for p, m, op in ops if not CAMEL.match(str(op.get("operationId", "")))]
    ex.append(E("Every operation has a camelCase operationId", ops and not no_id,
                f"missing/bad={no_id}"))
    no_default = [f"{m} {p}" for p, m, op in ops if "default" not in (op.get("responses") or {})]
    ex.append(E("Every operation declares a default error response", ops and not no_default,
                f"missing={no_default}"))
    s = json.dumps(doc)
    ex.append(E("Errors use application/problem+json", "application/problem+json" in s,
                "grep media type"))
    return doc, s


def grade_author_books(out):
    ex = []
    f = find_spec(out, "books-api.openapi.yaml")
    if not f.exists():
        return [E("books-api.openapi.yaml produced", False, "no yaml in outputs")]
    doc, s = grade_common(f, ex)
    schemes = (doc.get("components") or {}).get("securitySchemes") or {}
    bearer = any(isinstance(v, dict) and v.get("type") == "http" and v.get("scheme") == "bearer"
                 for v in schemes.values())
    ex.append(E("HTTP bearer scheme defined and applied by default",
                bearer and bool(doc.get("security")), f"schemes={list(schemes)}"))
    ex.append(E("Genre modelled as the 3-value enum",
                all(g in s for g in ["fiction", "nonfiction", "reference"]) and "enum" in s,
                "grep enum values"))
    nullable_31 = re.search(r'"type":\s*\[[^\]]*"null"', s)
    ex.append(E("discontinuedAt nullable via 3.1 type array (no `nullable:`)",
                "discontinuedAt" in s and nullable_31 and "nullable" not in s.replace("discontinuedAt", ""),
                f"type-array={bool(nullable_31)}"))
    list_ops = [op for p, m, op in operations(doc) if m == "get" and "{" not in p]
    paged = any("page" in json.dumps(op).lower() or "cursor" in json.dumps(op).lower()
                for op in list_ops)
    bare_array = any(
        mt.get("schema", {}).get("type") == "array"
        for op in list_ops
        for r in (op.get("responses") or {}).values() if isinstance(r, dict)
        for mt in (r.get("content") or {}).values() if isinstance(mt, dict))
    ex.append(E("List endpoint is paginated and not a bare top-level array",
                list_ops and paged and not bare_array, f"paged={paged} bare_array={bare_array}"))
    return ex


def grade_review_legacy(out):
    ex = []
    f = out / "customers-api.openapi.yaml"
    rv = out / "review.md"
    if not f.exists():
        return [E("customers-api.openapi.yaml produced", False, "missing")]
    doc, s = grade_common(f, ex)
    ex.append(E("3.0-only `nullable:` removed", "nullable" not in s, "grep nullable"))
    ex.append(E("Boolean exclusiveMinimum rewritten to the 3.1 numeric form",
                not re.search(r'"exclusiveMinimum":\s*(true|false)', s),
                "grep boolean exclusiveMinimum"))
    bare = [p for p in (doc.get("paths") or {}) if re.search(r"\{id\}", p)]
    ex.append(E("Path parameters resource-prefixed ({customerId}, not {id})",
                doc.get("paths") and not bare, f"bare={bare}"))
    ex.append(E("Hardcoded API key removed", "sk_live_9f8a7b6c5d4e3f2a1b0c" not in f.read_text(),
                "grep planted key"))
    if rv.exists():
        r = rv.read_text().lower()
        flags = {
            "version": "3.1" in r or "3.0" in r,
            "paths": "kebab" in r or "verb" in r or "case" in r,
            "secret": "key" in r or "secret" in r or "credential" in r,
            "errors": "operationid" in r or "error" in r or "default" in r,
        }
        ex.append(E("review.md flags all four planted defect classes", all(flags.values()),
                    json.dumps(flags)))
    else:
        ex.append(E("review.md flags all four planted defect classes", False, "review.md missing"))
    return ex


GRADERS = {"eval-0": grade_author_books, "eval-1": grade_review_legacy}


def main():
    iteration = Path(sys.argv[1])
    for eval_dir in sorted(iteration.glob("eval-*")):
        key = "-".join(eval_dir.name.split("-", 2)[:2])  # "eval-<id>"
        grader = GRADERS.get(key)
        if grader is None:
            sys.exit(f"grade.py: no grader registered for {eval_dir.name} "
                     f"(known: {sorted(GRADERS)}) — add it to GRADERS")
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
