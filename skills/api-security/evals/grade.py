#!/usr/bin/env python3
"""Grade api-security eval runs. Usage: grade.py <iteration-dir>.

Expects <iteration-dir>/eval-*/{with_skill,without_skill}/outputs/ as laid
out by scripts/eval_skills.py (run via `task eval:skills NAME=api-security`).
Writes grading.json per arm and prints a pass/total summary. Checks are
static: regexes over the review report, and ast-scoped checks over the
fixed fixture — no network or app execution.
"""
import ast
import json
import re
import sys
from pathlib import Path

FIXTURE = "vulnerable-orders-api.py"
JWT_SECRET = "super-secret-jwt-key-2019"
ADMIN_KEY = "ak_admin_9f8a7b6c5d4e"


def E(text, passed, evidence):
    return {"text": text, "passed": bool(passed), "evidence": str(evidence)[:500]}


def func_src(tree, source, name):
    """Source of top-level function `name`, '' if the model removed/renamed it."""
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return ast.get_source_segment(source, node) or ""
    return ""


def grade_review(out):
    ex = []
    report = out / "security-review.md"
    if not report.exists():
        candidates = [p for p in out.glob("*.md") if p.name != FIXTURE]
        report = candidates[0] if candidates else report
    if not report.exists():
        return [E("security-review.md produced", False, "no report in outputs")]
    r = report.read_text().lower()
    code = (out / FIXTURE).read_text() if (out / FIXTURE).exists() else ""
    ex.append(E("Application code left unmodified", JWT_SECRET in code and
                'options={"verify_signature": False}' in code, "fixture diff check"))

    def flag(text, *patterns):
        hits = {p: bool(re.search(p, r)) for p in patterns}
        ex.append(E(text, all(hits.values()), json.dumps(hits)))

    flag("Flags unverified JWT signature",
         r"verify_signature|unverified|without verif|signature[^.]{0,60}not verif|forge")
    flag("Flags BOLA on GET /orders/{id}",
         r"bola|idor|object[- ]level|ownership|owner|other users", r"order")
    flag("Flags mass assignment / role escalation via PATCH /users/me",
         r"mass[- ]assignment|(role[^.]{0,80}(escalat|admin|privilege))|(privilege[^.]{0,80}role)")
    flag("Flags SQL/column-name injection in the profile UPDATE",
         r"injection")
    flag("Flags password_hash (and similar) exposure in user responses",
         r"password.hash")
    flag("Flags SSRF in the webhook test endpoint",
         r"ssrf|169\.254|server[- ]side request|metadata|internal (service|network|host)")
    flag("Flags unbounded ?limit= (resource consumption)",
         r"limit[^.]{0,120}(cap|unbounded|maximum|no (server|upper)|abuse|large)|unbounded[^.]{0,60}limit")
    flag("Flags admin API key in the query string",
         r"api.?key[^.]{0,120}(query|url|logs?)|query[^.]{0,80}api.?key")
    flag("Flags hardcoded secrets in source",
         r"hard[- ]?cod")
    flag("Flags CORS wildcard combined with credentials",
         r"cors|allow-origin")
    flag("Flags stack trace / traceback leakage in errors",
         r"traceback|stack.?trace")
    ex.append(E("Ranks by severity (critical and high tiers present)",
                "critical" in r and "high" in r, "grep severity words"))
    cats = len(re.findall(r"\bapi(?:\s?|-)(10|[1-9])\b|owasp", r))
    ex.append(E("Findings labeled with OWASP API Top 10 categories",
                cats >= 5, f"category refs={cats}"))
    ex.append(E("Closes with what was checked and found sound",
                bool(re.search(r"(checked|reviewed|verified|tested)[^\n]{0,80}"
                               r"(sound|no (issue|finding|vulnerabilit))|found sound|"
                               r"not vulnerable|correctly (scoped|implemented|enforced)", r)),
                "grep sound-closing"))
    lines = re.findall(r"\.py:\d+|line \d+", r)
    ex.append(E("Cites concrete locations (>= 5 file:line references)",
                len(lines) >= 5, f"refs={len(lines)}"))
    return ex


def grade_fix(out):
    f = out / FIXTURE
    if not f.exists():
        return [E(f"{FIXTURE} still present", False, "file missing")]
    src = f.read_text()
    try:
        tree = ast.parse(src)
    except SyntaxError as err:
        return [E("Fixed file parses as Python", False, str(err))]
    ex = [E("Fixed file parses as Python", True, "ast.parse ok")]

    ex.append(E("JWT signature verification enabled with pinned algorithms",
                not re.search(r"verify_signature[\"']?\s*:\s*False", src)
                and "algorithms" in src, "grep verify_signature/algorithms"))
    ex.append(E("Token issuer/audience validated",
                re.search(r"\baudience\s*=|[\"']aud[\"']", src)
                and re.search(r"\bissuer\s*=|[\"']iss[\"']", src), "grep issuer/audience"))
    ex.append(E("Hardcoded JWT secret gone; config from env or JWKS",
                JWT_SECRET not in src
                and re.search(r"environ|getenv|jwks|PyJWKClient", src, re.I),
                "grep planted secret / env"))
    get_order = func_src(tree, src, "get_order")
    ex.append(E("get_order scoped to the calling user (BOLA fixed)",
                bool(re.search(r"user_id|g\.user|[\"']sub[\"']", get_order)),
                get_order[:300] or "get_order not found"))
    update = func_src(tree, src, "update_profile")
    # The allowlist may be a module-level constant, so gather every literal
    # string collection the function can see: literals inside it, plus
    # module-level assignments whose name it references.
    def str_collections(node):
        for n in ast.walk(node):
            if isinstance(n, (ast.Set, ast.List, ast.Tuple)):
                vals = [e.value for e in n.elts
                        if isinstance(e, ast.Constant) and isinstance(e.value, str)]
                if vals:
                    yield vals
    used = {n.id for fn in ast.walk(tree)
            if isinstance(fn, ast.FunctionDef) and fn.name == "update_profile"
            for n in ast.walk(fn) if isinstance(n, ast.Name)}
    pools = [v for fn in ast.walk(tree)
             if isinstance(fn, ast.FunctionDef) and fn.name == "update_profile"
             for v in str_collections(fn)]
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id in used for t in node.targets):
            pools.extend(str_collections(node))
    allowlists = [p for p in pools if ("email" in p or "name" in p)]
    # Column-name interpolation is fine once names are gated by the
    # allowlist, so the check is the gate itself: an explicit field set
    # visible to the function, with role not assignable through it.
    ex.append(E("Profile update binds an explicit field allowlist (no role)",
                update != "" and allowlists
                and all("role" not in p for p in allowlists),
                f"allowlists={allowlists}" if update else "update_profile not found"))
    get_user = func_src(tree, src, "get_user")
    ex.append(E("Sensitive fields no longer returned from get_user",
                get_user != "" and "password_hash" not in get_user
                and "stripe_customer_id" not in get_user,
                get_user[:300] or "get_user not found"))
    ex.append(E("Admin key: constant-time compare, not in the query string",
                "compare_digest" in src and ADMIN_KEY not in src
                and not re.search(r"args\.get\(\s*[\"']api_key", src),
                "grep compare_digest / planted key / args.get"))
    return ex


GRADERS = {"eval-0": grade_review, "eval-1": grade_fix}


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
