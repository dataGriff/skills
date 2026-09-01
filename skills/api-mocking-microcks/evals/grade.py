#!/usr/bin/env python3
"""Grade api-mocking-microcks eval runs. Usage: grade.py <iteration-dir>.

Expects <iteration-dir>/eval-*/{with_skill,without_skill}/outputs/ as laid
out by scripts/eval_skills.py (run via `task eval:skills
NAME=api-mocking-microcks`). Writes grading.json per arm and prints a
pass/total summary.

Grading is static: it checks the produced specs against the Microcks
conventions that determine whether mocks actually work (named-example
pairing, dispatcher config, `{{ }}` templating, async frequency/direction).
Container registries hosting Microcks images may be unreachable in
sandboxed environments, so no live import is attempted.
"""
import json
import sys
from pathlib import Path

import yaml


def load_yaml(path):
    try:
        return yaml.safe_load(path.read_text()) or {}
    except Exception:
        return None


def find_spec(out, preferred, root_key):
    f = out / preferred
    if f.exists():
        return f
    for p in sorted(out.glob("*.y*ml")):
        doc = load_yaml(p)
        if isinstance(doc, dict) and root_key in doc:
            return p
    return None


def E(text, passed, evidence):
    return {"text": text, "passed": bool(passed), "evidence": str(evidence)[:500]}


def example_names(node):
    """Names of the plural named-`examples` map on a parameter/media object."""
    if not isinstance(node, dict):
        return set()
    ex = node.get("examples")
    return set(ex.keys()) if isinstance(ex, dict) else set()


def grade_rest(out):
    ex = []
    f = find_spec(out, "order-api.yaml", "openapi")
    if f is None:
        return [E("order-api.yaml produced and parseable", False, "no OpenAPI yaml found")]
    doc = load_yaml(f)
    if not isinstance(doc, dict):
        return [E("order-api.yaml produced and parseable", False, "yaml parse error")]
    text = f.read_text()
    info = doc.get("info") or {}
    ex.append(E("info.title 'Order API' and version '1.0' (Microcks identity)",
                info.get("title") == "Order API" and str(info.get("version")) == "1.0",
                f"title={info.get('title')} version={info.get('version')}"))

    # GET /orders/{id}: named examples paired between path param and 200 response
    get_op = next((ops.get("get") for p, ops in (doc.get("paths") or {}).items()
                   if isinstance(ops, dict) and "get" in ops and "{" in p), None) or {}
    param_names = set()
    for prm in get_op.get("parameters") or []:
        if isinstance(prm, dict) and prm.get("in") == "path":
            param_names |= example_names(prm)
    resp200 = ((get_op.get("responses") or {}).get("200") or {}).get("content") or {}
    resp_names = set()
    for media in resp200.values():
        resp_names |= example_names(media)
    paired = param_names & resp_names
    ex.append(E("GET uses plural named `examples`, request/response paired by name (>=2)",
                len(paired) >= 2, f"param={sorted(param_names)} resp={sorted(resp_names)}"))
    ex.append(E("Both known orders present with correct data",
                all(v in text for v in ["abc123", "def456", "shipped", "pending", "45.5", "12"]),
                "grep ids/statuses/totals"))

    # 404 for ANY other id needs a FALLBACK dispatcher, not just a 404 example
    ex.append(E("FALLBACK dispatcher configured so unknown ids get the 404 example",
                "FALLBACK" in text and ("x-microcks-operation" in text or "fallback" in text),
                "grep FALLBACK/x-microcks-operation"))
    has_404 = "404" in json.dumps((get_op.get("responses") or {}), default=str)
    ex.append(E("404 response with error example defined", has_404, "responses keys"))

    # POST /orders: dynamic response via templating
    post_op = next((ops.get("post") for ops in (doc.get("paths") or {}).values()
                    if isinstance(ops, dict) and "post" in ops), None) or {}
    post_str = json.dumps(post_op, default=str)
    ex.append(E("POST response generates a fresh id via template function",
                "{{" in post_str and any(g in post_str for g in ("guid(", "uuid(", "randomString(")),
                "grep {{ guid()/uuid() }} in POST"))
    ex.append(E("POST response echoes request body fields via request.body templating",
                "request.body" in post_str, "grep {{ request.body/... }} in POST"))

    md = out / "MOCKING.md"
    md_text = md.read_text().lower() if md.exists() else ""
    ex.append(E("MOCKING.md runs Microcks via docker",
                "docker" in md_text and "microcks" in md_text, "grep docker+microcks"))
    ex.append(E("MOCKING.md curls the correct /rest/{name}/{version} mock URL",
                "rest/order%20api/1.0" in md_text or "rest/order api/1.0" in md_text,
                "grep rest/Order API/1.0"))
    return ex


def grade_async(out):
    ex = []
    f = find_spec(out, "user-signedup-api.yaml", "asyncapi")
    if f is None:
        return [E("user-signedup-api.yaml produced and parseable", False, "no AsyncAPI yaml found")]
    doc = load_yaml(f)
    if not isinstance(doc, dict):
        return [E("user-signedup-api.yaml produced and parseable", False, "yaml parse error")]
    text = f.read_text()
    ver = str(doc.get("asyncapi", ""))
    info = doc.get("info") or {}
    ex.append(E("Valid AsyncAPI doc with exact title/version identity",
                ver[:1] in ("2", "3") and info.get("title") == "User Signedup API"
                and str(info.get("version")) == "0.1.0",
                f"asyncapi={ver} title={info.get('title')} version={info.get('version')}"))

    chan = next((c for name, c in (doc.get("channels") or {}).items()
                 if "signedup" in name.replace("/", "").replace("-", "")), None)
    if ver.startswith("2"):
        emitting = isinstance(chan, dict) and "subscribe" in chan
        evidence = f"channel keys={sorted(chan.keys()) if isinstance(chan, dict) else None}"
    else:
        emitting = any(isinstance(o, dict) and o.get("action") == "send"
                       for o in (doc.get("operations") or {}).values())
        evidence = "looked for operations with action: send"
    ex.append(E("user/signedup channel mocked in the emitting direction "
                "(2.x subscribe / 3.x send)", chan is not None and emitting, evidence))

    # two named examples with conformant payloads
    def walk_examples(node):
        found = []
        if isinstance(node, dict):
            exs = node.get("examples")
            if isinstance(exs, list):
                found += [e for e in exs if isinstance(e, dict) and "payload" in e]
            for v in node.values():
                found += walk_examples(v)
        elif isinstance(node, list):
            for v in node:
                found += walk_examples(v)
        return found
    msgs = walk_examples(doc)
    tiers = {str((m.get("payload") or {}).get("tier")) for m in msgs}
    ex.append(E("Two named example messages with distinct users",
                len(msgs) >= 2 and len({json.dumps(m.get("payload"), default=str) for m in msgs}) >= 2
                and sum(1 for m in msgs if m.get("name")) >= 2,
                f"{len(msgs)} examples, tiers={tiers}"))
    payloads = json.dumps([m.get("payload") for m in msgs], default=str)
    ex.append(E("Example ids templated so every publication differs",
                "{{" in payloads and any(g in payloads for g in ("guid(", "uuid(", "randomString(")),
                "grep {{ guid() }} in example payloads"))
    ex.append(E("Publication frequency set to 5s via x-microcks-operation",
                "x-microcks-operation" in text and "frequency" in text and "5" in text.split("frequency")[-1][:20],
                "grep x-microcks-operation frequency"))

    md = out / "EVENTS.md"
    md_text = md.read_text().lower() if md.exists() else ""
    ex.append(E("EVENTS.md runs Microcks via docker",
                "docker" in md_text and "microcks" in md_text, "grep docker+microcks"))
    ex.append(E("EVENTS.md points at the broker-free WebSocket mock endpoint",
                "ws://" in md_text or "/api/ws" in md_text or "websocket" in md_text,
                "grep ws:///api/ws/websocket"))
    return ex


GRADERS = {"eval-0": grade_rest, "eval-1": grade_async}


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
