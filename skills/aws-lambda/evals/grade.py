#!/usr/bin/env python3
"""Grade aws-lambda eval runs. Usage: grade.py <iteration-dir>.

Expects <iteration-dir>/eval-*/{with_skill,without_skill}/outputs/ as laid
out by scripts/eval_skills.py (run via `task eval:skills NAME=aws-lambda`).
Writes grading.json per arm and prints a pass/total summary. All checks are
static (YAML/code inspection) — nothing talks to AWS.
"""
import json
import re
import sys
from pathlib import Path

import yaml

FIXTURES = {"legacy-handler.py", "legacy-template.yaml"}
CURRENT_PY = re.compile(r"python3\.1[2-9]")
MODULE_SCOPE_BOTO = re.compile(r"^[^\s#].*boto3\.(client|resource)\s*\(", re.M)
HANDLER_SCOPE_BOTO = re.compile(r"^[ \t]+.*boto3\.(client|resource)\s*\(", re.M)


class CfnLoader(yaml.SafeLoader):
    """SafeLoader that tolerates CloudFormation short intrinsics (!Ref etc.)."""


def _unknown_tag(loader, suffix, node):
    if isinstance(node, yaml.ScalarNode):
        return loader.construct_scalar(node)
    if isinstance(node, yaml.SequenceNode):
        return loader.construct_sequence(node)
    return loader.construct_mapping(node)


CfnLoader.add_multi_constructor("!", _unknown_tag)


def uses_powertools_batch(hsrc):
    return re.search(r"BatchProcessor|process_partial_response|batch_processor", hsrc)


def per_record_try(hsrc):
    """A try: nested inside a loop over the event's Records."""
    lines = hsrc.splitlines()
    for i, ln in enumerate(lines):
        m = re.match(r"(\s*)for\s+\w+\s+in\s+.*Records", ln)
        if not m:
            continue
        indent = len(m.group(1))
        for nxt in lines[i + 1:]:
            if nxt.strip() and (len(nxt) - len(nxt.lstrip())) <= indent:
                break
            if nxt.strip().startswith("try"):
                return True
    return False


def E(text, passed, evidence):
    return {"text": text, "passed": bool(passed), "evidence": str(evidence)[:500]}


def outputs_files(out, pattern):
    """Deliverables in outputs/, skipping fixtures and the copied .skill dir."""
    return [p for p in out.rglob(pattern)
            if ".skill" not in p.parts and p.name not in FIXTURES]


def find_template(out, preferred="template.yaml"):
    f = out / preferred
    if f.exists():
        return f
    for p in outputs_files(out, "*.y*ml"):
        if "AWS::Serverless" in p.read_text() or "AWS::Lambda" in p.read_text():
            return p
    return f


def find_handler(out, preferred):
    f = out / preferred
    if f.exists():
        return f
    pys = outputs_files(out, "*.py")
    return pys[0] if pys else f


def load_template(path):
    try:
        return yaml.load(path.read_text(), Loader=CfnLoader) or {}
    except Exception as e:
        return {"__parse_error__": str(e)}


def function_properties(doc):
    for res in (doc.get("Resources") or {}).values():
        if isinstance(res, dict) and res.get("Type") == "AWS::Serverless::Function":
            return res.get("Properties") or {}
    return {}


def grade_common(out, template, handler, ex):
    """Checks shared by both evals: template soundness + handler patterns."""
    doc = load_template(template)
    tsrc = template.read_text()
    ex.append(E("Template parses and defines a Serverless function",
                "__parse_error__" not in doc and bool(function_properties(doc)),
                doc.get("__parse_error__", "ok")))
    props = function_properties(doc)
    ex.append(E("Runtime pinned to a current Python (>= 3.12)",
                CURRENT_PY.search(str(props.get("Runtime", ""))),
                props.get("Runtime")))
    timeout = props.get("Timeout")
    ex.append(E("Timeout set explicitly above the 3s default",
                isinstance(timeout, int) and timeout > 3, f"Timeout={timeout}"))
    ex.append(E("No admin/wildcard permissions on the execution role",
                "AdministratorAccess" not in tsrc
                and not re.search(r"Action:\s*['\"]?\*", tsrc), "grep policy"))
    ex.append(E("SQS event source reports partial batch failures",
                "ReportBatchItemFailures" in tsrc, "grep FunctionResponseTypes"))
    ex.append(E("Poisoned messages drain to a DLQ (queue redrive)",
                re.search(r"RedrivePolicy|deadLetter", tsrc, re.I), "grep redrive"))
    hsrc = handler.read_text()
    ex.append(E("boto3 client/resource created at module scope, not per invoke",
                MODULE_SCOPE_BOTO.search(hsrc) and not HANDLER_SCOPE_BOTO.search(hsrc),
                "grep boto3 init scope"))
    ex.append(E("Handler returns batchItemFailures for failed records",
                ("batchItemFailures" in hsrc and "itemIdentifier" in hsrc)
                or uses_powertools_batch(hsrc), "grep partial batch response"))
    ex.append(E("Per-record error handling (try inside the record loop)",
                per_record_try(hsrc) or uses_powertools_batch(hsrc),
                "grep per-record try / Powertools batch"))
    return tsrc, hsrc


def grade_build_worker(out):
    ex = []
    template = find_template(out)
    handler = find_handler(out, Path("src/app.py"))
    if not template.exists() or not handler.exists():
        return [E("template.yaml and src/app.py produced",
                  False, f"template={template.exists()} handler={handler.exists()}")]
    tsrc, hsrc = grade_common(out, template, handler, ex)
    ex.append(E("Table name read from the environment, not hardcoded",
                re.search(r"os\.environ|getenv", hsrc), "grep env lookup"))
    ex.append(E("Message body parsed as JSON from Records[].body",
                re.search(r"json\.loads\(.*body", hsrc, re.I), "grep body parse"))
    return ex


def grade_review_legacy(out):
    ex = []
    template = find_template(out)
    handler = find_handler(out, Path("handler.py"))
    review = out / "review.md"
    if not template.exists() or not handler.exists():
        return [E("Fixed template.yaml and handler.py produced",
                  False, f"template={template.exists()} handler={handler.exists()}")]
    tsrc, hsrc = grade_common(out, template, handler, ex)
    ex.append(E("Hardcoded credential removed from the template",
                "sup3rs3cretPr0d" not in tsrc, "grep planted secret"))
    ex.append(E("Errors no longer swallowed batch-wide (no bare pass-all except)",
                not re.search(r"except\s+Exception\s*:\s*(#[^\n]*)?\n\s*pass", hsrc),
                "grep swallow-all"))
    if review.exists():
        r = review.read_text().lower()
        flags = {
            "init_scope": "cold start" in r or "module scope" in r or "init" in r
                          or "every invocation" in r or "each invocation" in r,
            "runtime": "3.8" in r or "deprecat" in r or "runtime" in r,
            "iam": "administratoraccess" in r or "least privilege" in r or "admin" in r,
            "secret": "secret" in r or "password" in r or "hardcod" in r or "credential" in r,
            "failures": "batch" in r or "dlq" in r or "dead-letter" in r
                        or "dead letter" in r or "swallow" in r or "lost" in r,
        }
        ex.append(E("review.md flags all five planted defect classes",
                    all(flags.values()), json.dumps(flags)))
    else:
        ex.append(E("review.md flags all five planted defect classes",
                    False, "review.md missing"))
    return ex


GRADERS = {"eval-0": grade_build_worker, "eval-1": grade_review_legacy}


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
