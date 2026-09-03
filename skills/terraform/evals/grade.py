#!/usr/bin/env python3
"""Grade terraform eval runs. Usage: grade.py <iteration-dir>.

Expects <iteration-dir>/eval-*/{with_skill,without_skill}/outputs/ as laid
out by scripts/eval_skills.py (run via `task eval:skills NAME=terraform`).
Writes grading.json per arm and prints a pass/total summary.

Checks are structural (regex over HCL) plus `terraform fmt -check` when the
terraform binary is on PATH — `terraform validate` needs provider downloads,
which sandboxed runners may not have, so it is deliberately not asserted.
"""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path


def sh(*args, cwd=None):
    try:
        r = subprocess.run(args, capture_output=True, text=True, timeout=120, cwd=cwd)
    except FileNotFoundError:
        # A missing tool must fail the check with evidence, not crash the
        # grader and leave every arm unscored.
        return 127, f"{args[0]}: not installed"
    return r.returncode, (r.stdout + r.stderr)[-600:]


def E(text, passed, evidence):
    return {"text": text, "passed": bool(passed), "evidence": str(evidence)[:500]}


def tf_files(root: Path, exclude_dirs=(".skill", ".terraform")):
    return [
        p for p in sorted(root.rglob("*.tf"))
        if not any(part in exclude_dirs for part in p.parts)
    ]


def read_all(files):
    return "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in files)


def blocks(text, kind):
    """Top-level `kind "name" { ... }` blocks as (name, body) via brace counting."""
    out = []
    for m in re.finditer(rf'^{kind}\s+"([^"]+)"[^{{]*{{', text, re.M):
        depth, i = 1, m.end()
        while i < len(text) and depth:
            depth += {"{": 1, "}": -1}.get(text[i], 0)
            i += 1
        out.append((m.group(1), text[m.end():i - 1]))
    return out


def fmt_clean(root: Path):
    if not tf_files(root):
        return False, "no .tf files"
    code, out = sh("terraform", "fmt", "-check", "-diff", cwd=root)
    return code == 0, out or "clean"


def grade_author_module(out):
    ex = []
    files = tf_files(out)
    if not files:
        return [E(".tf files produced", False, "no .tf files in outputs")]
    text = read_all(files)

    ex.append(E("terraform fmt -check clean", *fmt_clean(out)))
    ex.append(E("required_version constraint declared",
                re.search(r"required_version\s*=", text), "grep required_version"))
    prov = re.search(r"required_providers\s*{", text)
    pinned = re.search(r'source\s*=\s*"hashicorp/aws"', text) and re.search(
        r'version\s*=\s*"[~>=!<\s]*\d', text)
    ex.append(E("aws provider pinned via required_providers (source + version)",
                prov and pinned, f"block={bool(prov)} pinned={bool(pinned)}"))
    ex.append(E("no provider block inside the module (reusable-module rule)",
                not re.search(r'^provider\s+"', text, re.M), "grep ^provider"))

    variables = blocks(text, "variable")
    undocumented = [n for n, b in variables
                    if not (re.search(r"\btype\s*=", b) and re.search(r"\bdescription\s*=", b))]
    ex.append(E("every variable has a type and a description",
                variables and not undocumented, f"missing on: {undocumented}"))
    env = next((b for n, b in variables if n == "environment"), "")
    ex.append(E("environment input validated against dev/test/prod",
                "validation" in env and all(v in env for v in ("dev", "test", "prod")),
                env[:200] or "no environment variable"))
    ex.append(E("bucket guarded with lifecycle prevent_destroy",
                re.search(r"prevent_destroy\s*=\s*true", text), "grep prevent_destroy"))
    outputs = blocks(text, "output")
    described = [n for n, b in outputs if re.search(r"\bdescription\s*=", b)]
    has_arn = any("arn" in n for n, _ in outputs)
    ex.append(E("outputs expose bucket name and ARN, with descriptions",
                len(outputs) >= 2 and has_arn and len(described) == len(outputs),
                f"outputs={[n for n, _ in outputs]} described={described}"))
    return ex


def grade_review_legacy(out):
    ex = []
    rv = out / "review.md"
    if rv.exists():
        r = rv.read_text(encoding="utf-8", errors="replace").lower()
        flags = {
            "credentials": "access_key" in r or "credential" in r or "hardcoded key" in r,
            "secret_default": "password" in r and ("default" in r or "sensitive" in r),
            "pinning": "pin" in r or "required_providers" in r or "required_version" in r or "version constraint" in r,
            "count_fragility": "for_each" in r or ("count" in r and ("index" in r or "recreat" in r or "for_each" in r)),
            "hardcoded_ami": "ami" in r,
            "state_backend": "backend" in r or "remote state" in r or "tfstate" in r,
        }
        ex.append(E("review.md flags all six planted defect classes",
                    all(flags.values()), json.dumps(flags)))
    else:
        ex.append(E("review.md flags all six planted defect classes", False, "review.md missing"))

    fixed = out / "fixed"
    files = tf_files(fixed) if fixed.is_dir() else []
    if not files:
        return ex + [E("fixed/ configuration produced", False, "no .tf under fixed/")]
    text = read_all(files)

    ex.append(E("fixed config: terraform fmt -check clean", *fmt_clean(fixed)))
    ex.append(E("fixed config: terraform + provider versions pinned",
                re.search(r"required_providers\s*{", text)
                and re.search(r"required_version\s*=", text), "grep pins"))
    leaked = [s for s in ("AKIAIOSFODNN7EXAMPLE", "wJalrXUtnFEMI", "SuperSecret123!")
              if s in text]
    ex.append(E("no plaintext credentials or password left anywhere",
                not leaked, f"leaked={leaked}"))
    pw = next((b for n, b in blocks(text, "variable") if "password" in n), "")
    ex.append(E("db_password marked sensitive and stripped of its default",
                pw and re.search(r"sensitive\s*=\s*true", pw)
                and not re.search(r"\bdefault\s*=", pw), pw[:200] or "no password variable"))
    ex.append(E("subnets use for_each (or keyed map), not count over a list",
                "for_each" in text and not re.search(r"\bcount\s*=\s*length\(", text),
                "grep for_each / count=length"))
    # A pinned AMI is acceptable ("must keep existing" forbids replacement) —
    # but only as a visible decision: parameterised/looked up, or a literal
    # with an explanatory comment right above it.
    parameterised = 'data "aws_ami"' in text or re.search(r'variable\s+"[^"]*ami', text)
    deliberate, literal_use = True, False
    for f in files:
        lines = f.read_text(encoding="utf-8", errors="replace").splitlines()
        for i, line in enumerate(lines):
            if re.search(r'\bami\s*=\s*"ami-', line):
                literal_use = True
                if not any(l.lstrip().startswith("#") for l in lines[max(0, i - 3):i]):
                    deliberate = False
    ex.append(E("AMI handled deliberately: parameterised, looked up, or pinned with a comment",
                (parameterised and not literal_use) or (literal_use and deliberate),
                f"literal_use={literal_use} commented={deliberate} parameterised={bool(parameterised)}"))
    return ex


def grade_refactor_adopt(out):
    ex = []
    files = tf_files(out)
    if not files:
        return [E(".tf files produced", False, "no .tf files in outputs")]
    text = read_all(files)

    moved = re.search(
        r"moved\s*{[^}]*from\s*=\s*aws_s3_bucket\.data\b[^}]*to\s*=\s*aws_s3_bucket\.artifacts\b",
        text, re.S) or re.search(
        r"moved\s*{[^}]*to\s*=\s*aws_s3_bucket\.artifacts\b[^}]*from\s*=\s*aws_s3_bucket\.data\b",
        text, re.S)
    ex.append(E("rename done with a moved block (declarative, plan-reviewable)",
                moved, "grep moved{from=data,to=artifacts}"))
    ex.append(E("resource renamed to artifacts in config",
                re.search(r'resource\s+"aws_s3_bucket"\s+"artifacts"', text)
                and not re.search(r'resource\s+"aws_s3_bucket"\s+"data"', text),
                "grep resource blocks"))
    imp = re.search(
        r"import\s*{[^}]*to\s*=\s*aws_s3_bucket\.logs_archive\b[^}]*id\s*=\s*\"acme-logs-archive\"",
        text, re.S) or re.search(
        r"import\s*{[^}]*id\s*=\s*\"acme-logs-archive\"[^}]*to\s*=\s*aws_s3_bucket\.logs_archive\b",
        text, re.S)
    ex.append(E("adoption done with an import block targeting logs_archive",
                imp and re.search(r'resource\s+"aws_s3_bucket"\s+"logs_archive"', text),
                f"import_block={bool(imp)}"))
    backend = re.search(r'backend\s+"s3"\s*{([^}]*)}', text, re.S)
    body = backend.group(1) if backend else ""
    ex.append(E("s3 backend configured with the given bucket and key",
                "acme-tfstate" in body and "platform/app.tfstate" in body,
                body[:200] or "no s3 backend block"))
    ex.append(E("locking via use_lockfile, not the deprecated DynamoDB table",
                re.search(r"use_lockfile\s*=\s*true", body) and "dynamodb" not in body,
                body[:200] or "no s3 backend block"))
    ex.append(E("terraform fmt -check clean", *fmt_clean(out)))
    notes = out / "notes.md"
    if notes.exists():
        n = notes.read_text(encoding="utf-8", errors="replace").lower()
        ex.append(E("notes.md covers state migration on init and no destroy/recreate",
                    "-migrate-state" in n and ("no-op" in n or "not be destroyed" in n
                    or "without destroy" in n or "no destroy" in n or "no resources" in n
                    or "recreat" in n),
                    n[:200]))
    else:
        ex.append(E("notes.md covers state migration on init and no destroy/recreate",
                    False, "notes.md missing"))
    return ex


GRADERS = {"eval-0": grade_author_module, "eval-1": grade_review_legacy,
           "eval-2": grade_refactor_adopt}


def main():
    iteration = Path(sys.argv[1])
    if shutil.which("terraform") is None:
        print("  note: terraform not on PATH — fmt checks will fail with evidence")
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
