#!/usr/bin/env python3
"""Grade api-mocking-microcks eval runs. Usage: grade.py <iteration-dir>.

Expects <iteration-dir>/eval-*/{with_skill,without_skill}/outputs/ as laid
out by scripts/eval_skills.py (run via `task eval:skills
NAME=api-mocking-microcks`). Writes grading.json per arm and prints a
pass/total summary.

Grading is static: it checks the produced specs, overlays, and test code
against the Microcks conventions that determine whether mocks actually work
(dispatcher wiring, named-example pairing, `{{ }}` templating, overlay
identity matching, Testcontainers endpoint injection). Container registries
hosting Microcks images may be unreachable in sandboxed environments, so no
live import is attempted.
"""
import json
import sys
from pathlib import Path

import yaml

FIXTURES = Path(__file__).resolve().parent / "fixtures"


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


def find_by_kind(out, kind):
    """Locate a Microcks overlay (APIExamples/APIMetadata) among the outputs."""
    for p in sorted(out.rglob("*.y*ml")):
        text = p.read_text()
        for doc in yaml.safe_load_all(text) if "---" in text else [load_yaml(p)]:
            if isinstance(doc, dict) and doc.get("kind") == kind:
                return p, doc
    return None, None


def all_doc_text(out):
    """Docs and scripts an agent might put instructions in."""
    files = [p for pat in ("*.md", "*.sh", "*.txt") for p in sorted(out.rglob(pat))]
    return "\n".join(p.read_text() for p in files).lower()


def E(text, passed, evidence):
    return {"text": text, "passed": bool(passed), "evidence": str(evidence)[:500]}


def has_generator(s):
    """True when s uses a Microcks id-generator template ({{ uuid() }},
    guid()/randomUUID() aliases, randomString())."""
    s = s.lower()
    return "{{" in s and any(g in s for g in ("guid(", "uuid(", "randomstring("))


def response_example_names(op):
    names = set()
    for resp in (op.get("responses") or {}).values():
        for media in (resp.get("content") or {}).values():
            ex = media.get("examples")
            if isinstance(ex, dict):
                names |= set(ex.keys())
    return names


def grade_json_body(out):
    ex = []
    f = find_spec(out, "lending-api.yaml", "openapi")
    if f is None:
        return [E("lending-api.yaml produced and parseable", False, "no OpenAPI yaml found")]
    doc = load_yaml(f)
    if not isinstance(doc, dict):
        return [E("lending-api.yaml produced and parseable", False, "yaml parse error")]
    info = doc.get("info") or {}
    ex.append(E("info.title 'Lending API' and version '1.0' (Microcks identity)",
                info.get("title") == "Lending API" and str(info.get("version")) == "1.0",
                f"title={info.get('title')} version={info.get('version')}"))

    post_op = next((ops.get("post") for ops in (doc.get("paths") or {}).values()
                    if isinstance(ops, dict) and "post" in ops), None) or {}
    xmo = post_op.get("x-microcks-operation") or {}
    ex.append(E("POST carries x-microcks-operation with a JSON_BODY dispatcher",
                xmo.get("dispatcher") == "JSON_BODY", f"dispatcher={xmo.get('dispatcher')}"))

    rules = xmo.get("dispatcherRules")
    try:
        rules = json.loads(rules) if isinstance(rules, str) else rules
    except json.JSONDecodeError:
        rules = None
    cases = (rules or {}).get("cases") or {}
    ex.append(E("Rules use operator 'range' on the /amount body pointer",
                isinstance(rules, dict) and rules.get("exp") == "/amount"
                and rules.get("operator") == "range",
                f"exp={rules.get('exp') if isinstance(rules, dict) else rules} "
                f"op={(rules or {}).get('operator') if isinstance(rules, dict) else ''}"))
    ex.append(E("Range cases are bare [..;..] intervals (no range() prefix) plus a default",
                "default" in cases and any(k.startswith(("[", "]")) for k in cases)
                and not any(k.lower().startswith("range") for k in cases),
                f"case keys={sorted(cases)}"))

    resp_names = response_example_names(post_op)
    ex.append(E("Every case maps to a response example that actually exists",
                bool(cases) and set(map(str, cases.values())) <= resp_names,
                f"cases->{sorted(map(str, cases.values()))} examples={sorted(resp_names)}"))
    ex.append(E("201, 202 and 422 responses all defined with examples",
                {"201", "202", "422"} <= set(map(str, (post_op.get("responses") or {})))
                and len(resp_names) >= 3, f"responses={sorted(post_op.get('responses') or {})}"))

    post_str = json.dumps(post_op, default=str)
    ex.append(E("Responses generate a fresh application id via template function",
                has_generator(post_str), "grep {{ guid()/uuid()/randomUUID() }} in POST"))
    ex.append(E("Responses echo the submitted amount via request.body templating",
                "request.body" in post_str, "grep {{ request.body/amount }} in POST"))
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
                has_generator(payloads),
                "grep {{ guid()/uuid()/randomUUID() }} in example payloads"))
    ex.append(E("Publication frequency set to 5s via x-microcks-operation",
                "x-microcks-operation" in text and "frequency" in text and "5" in text.split("frequency")[-1][:20],
                "grep x-microcks-operation frequency"))

    md_text = all_doc_text(out)
    ex.append(E("EVENTS.md runs Microcks via docker",
                "docker" in md_text and "microcks" in md_text, "grep docker+microcks"))
    ex.append(E("EVENTS.md points at the broker-free WebSocket mock endpoint",
                "ws://" in md_text or "/api/ws" in md_text or "websocket" in md_text,
                "grep ws:///api/ws/websocket"))
    return ex


def grade_overlay(out):
    ex = []
    spec = out / "inventory-api-generated.yaml"
    fixture = FIXTURES / "inventory-api-generated.yaml"
    ex.append(E("Generated spec left byte-identical",
                spec.exists() and spec.read_bytes() == fixture.read_bytes(),
                "compared against fixture"))

    # Mock content, wherever it landed (canonical overlay or not).
    extra = "\n".join(p.read_text() for p in sorted(out.rglob("*.y*ml"))
                      if p.name != "inventory-api-generated.yaml")
    ex.append(E("All three item exchanges present with the requested data",
                all(v in extra for v in
                    ("WIDGET-1", "GADGET-7", "MISSING-0", "Widget", "Gadget", "42")),
                "grep skus/names/stock in extra yamls"))
    ex.append(E("Reservation response has a templated id and echoes the request body",
                has_generator(extra) and "request.body" in extra,
                "grep generator + request.body"))
    ex.append(E("150ms delay and domain=inventory label configured somewhere",
                "150" in extra and "domain" in extra and "inventory" in extra,
                "grep 150/domain/inventory"))

    # The canonical mechanism: overlay artifacts, not a parallel spec copy.
    _, exdoc = find_by_kind(out, "APIExamples")
    meta = (exdoc or {}).get("metadata") or {}
    ex.append(E("Uses an APIExamples overlay with identity matching the spec",
                exdoc is not None
                and str(exdoc.get("apiVersion", "")).startswith("mocks.microcks.io")
                and meta.get("name") == "Inventory API" and str(meta.get("version")) == "2.3.0",
                "no kind: APIExamples yaml found" if exdoc is None
                else f"name={meta.get('name')} version={meta.get('version')}"))
    _, mdoc = find_by_kind(out, "APIMetadata")
    mmeta = (mdoc or {}).get("metadata") or {}
    mstr = json.dumps(mdoc, default=str)
    ex.append(E("Uses an APIMetadata overlay for the delay and label",
                mdoc is not None and mmeta.get("name") == "Inventory API"
                and "150" in mstr and (mmeta.get("labels") or {}).get("domain") == "inventory",
                "no kind: APIMetadata yaml found" if mdoc is None
                else f"labels={mmeta.get('labels')} grep 150"))

    doc_text = all_doc_text(out)
    ex.append(E("Import instructions load spec as main, overlays as secondary",
                ("mainartifact=true" in doc_text.replace('"', "").replace("'", "")
                 or ":true" in doc_text)
                and ("mainartifact=false" in doc_text.replace('"', "").replace("'", "")
                     or ":false" in doc_text),
                "grep mainArtifact=true/false or cli :true/:false"))
    return ex


def grade_testcontainers(out):
    ex = []
    test = out / "order-client.integration.test.ts"
    if not test.exists():
        test = next((p for p in sorted(out.rglob("*.ts")) + sorted(out.rglob("*.js"))
                     if "microcks" in p.read_text().lower()), None)
    if test is None:
        return [E("Integration test file produced", False, "no test file using microcks found")]
    code = test.read_text()
    ex.append(E("Uses the @microcks/microcks-testcontainers module",
                "microcks-testcontainers" in code and "MicrocksContainer" in code,
                "grep import + MicrocksContainer"))
    ex.append(E("Imports order-api.yaml into the container as a main artifact",
                "withMainArtifact" in code and "order-api.yaml" in code,
                "grep withMainArtifacts(order-api.yaml)"))
    ex.append(E("Derives the mock base URL via getRestMockEndpoint('Order API','1.0')",
                "getRestMockEndpoint" in code and "Order API" in code and "1.0" in code,
                "grep getRestMockEndpoint"))
    ex.append(E("OrderClient exercised against both known orders",
                "OrderClient" in code and "abc123" in code and "def456" in code
                and "shipped" in code and "pending" in code,
                "grep client + order assertions"))
    ex.append(E("Contract test uses testEndpoint with the OPEN_API_SCHEMA runner",
                "testEndpoint" in code and "OPEN_API_SCHEMA" in code
                and any(sut in code for sut in
                        ("localhost:3000", "host.testcontainers.internal",
                         "host.docker.internal")),
                "grep testEndpoint + runner + SUT url"))
    ex.append(E("No hand-built mock URLs (no /rest/... or fixed Microcks port)",
                "rest/order" not in code.lower().replace(" ", "").replace("+", "")
                and "8585" not in code and "localhost:8080" not in code,
                "grep hardcoded rest paths/ports"))
    md_text = all_doc_text(out)
    ex.append(E("README-TESTS.md covers installing the Testcontainers module",
                "microcks-testcontainers" in md_text, "grep install command"))
    return ex


GRADERS = {
    "eval-0": grade_json_body,
    "eval-1": grade_async,
    "eval-2": grade_overlay,
    "eval-3": grade_testcontainers,
}


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
