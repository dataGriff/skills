#!/usr/bin/env python3
"""Grade asyncapi-authoring eval runs. Usage: grade.py <iteration-dir>.

Expects <iteration-dir>/eval-*/{with_skill,without_skill}/outputs/ as laid
out by scripts/eval_skills.py (run via `task eval:skills NAME=asyncapi-authoring`).
Writes grading.json per arm and prints a pass/total summary. The
`asyncapi validate` assertion is skipped if the AsyncAPI CLI isn't on PATH.
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

SKILL_DIR = Path(__file__).resolve().parent.parent
RULESET = SKILL_DIR / "assets" / "spectral-asyncapi.yaml"


def sh(*args):
    r = subprocess.run(args, capture_output=True, text=True, timeout=180)
    return r.returncode, (r.stdout + r.stderr)[-600:]


def load(path):
    try:
        return yaml.safe_load(path.read_text()) or {}
    except Exception as e:
        return {"__parse_error__": str(e)}


def E(text, passed, evidence):
    return {"text": text, "passed": bool(passed), "evidence": str(evidence)[:500]}


def find_doc(out, preferred):
    f = out / preferred
    if f.exists():
        return f
    yams = sorted(out.glob("*.y*ml"))
    return yams[0] if yams else f


def cli_validates(ex, f):
    if shutil.which("asyncapi"):
        code, o = sh("asyncapi", "validate", str(f))
        ex.append(E("Passes `asyncapi validate`", code == 0, o))


def spectral_conventions(ex, f):
    """Score org conventions with the skill's ruleset (0 = error severity)."""
    if not shutil.which("spectral"):
        return
    r = subprocess.run(
        ["spectral", "lint", "--ruleset", str(RULESET), "-f", "json", str(f)],
        capture_output=True, text=True, timeout=180)
    try:
        results = json.loads(r.stdout or "[]")
    except json.JSONDecodeError:
        ex.append(E("No errors from the skill's Spectral governance ruleset",
                    False, r.stderr[-300:] or "spectral produced no JSON"))
        return
    # The authoring prompts name no owner, so a missing contact is honest
    # rather than wrong — don't reward a fabricated one.
    errors = [x for x in results
              if x.get("severity") == 0 and x.get("code") != "org-info-contact"]
    ex.append(E("No errors from the skill's Spectral governance ruleset",
                not errors,
                "; ".join(f"{x.get('code')}@{x.get('path')}" for x in errors[:5])
                or f"{len(results)} non-error finding(s)"))


def channel_by_address(doc, address):
    for cid, ch in (doc.get("channels") or {}).items():
        if isinstance(ch, dict) and ch.get("address") == address:
            return cid, ch
    return None, None


def op_action_for_channel(doc, channel_id):
    for op in (doc.get("operations") or {}).values():
        if not isinstance(op, dict):
            continue
        ref = (op.get("channel") or {}).get("$ref", "")
        if ref.rstrip("/").split("/")[-1] == channel_id:
            return op.get("action")
    return None


def grade_author_inventory(out):
    ex = []
    f = find_doc(out, "inventory.asyncapi.yaml")
    if not f.exists():
        return [E("inventory.asyncapi.yaml produced", False, "no yaml in outputs")]
    cli_validates(ex, f)
    doc = load(f)
    ex.append(E("Targets AsyncAPI 3.1.0", str(doc.get("asyncapi")) == "3.1.0",
                doc.get("asyncapi")))
    ex.append(E("v3 structure: root operations map, no v2 publish/subscribe keys",
                isinstance(doc.get("operations"), dict)
                and not any(isinstance(ch, dict) and ("publish" in ch or "subscribe" in ch)
                            for ch in (doc.get("channels") or {}).values()),
                list((doc.get("operations") or {}).keys())))
    orders_id, _ = channel_by_address(doc, "orders.placed.v1")
    stock_id, _ = channel_by_address(doc, "inventory.stock-level.v1")
    ex.append(E("Channels declare the two topic addresses",
                bool(orders_id and stock_id), f"orders={orders_id} stock={stock_id}"))
    ex.append(E("Consuming orders is action:receive, publishing stock is action:send",
                op_action_for_channel(doc, orders_id) == "receive"
                and op_action_for_channel(doc, stock_id) == "send",
                f"orders_op={op_action_for_channel(doc, orders_id)} "
                f"stock_op={op_action_for_channel(doc, stock_id)}"))
    s = json.dumps(doc)
    ex.append(E("Kafka bindings carry the consumer group and sku record key",
                '"kafka"' in s and "inventory-service" in s and '"key"' in s,
                "grep kafka+groupId enum+key"))
    ex.append(E("Payload constraints kept (quantity minimums as schema constraints)",
                '"minimum": 1' in s and '"minimum": 0' in s, "grep minimum 1/0"))
    spectral_conventions(ex, f)
    return ex


def grade_request_reply_avro(out):
    ex = []
    f = find_doc(out, "payment-check.asyncapi.yaml")
    if not f.exists():
        return [E("payment-check.asyncapi.yaml produced", False, "no yaml in outputs")]
    cli_validates(ex, f)
    doc = load(f)
    ex.append(E("Targets AsyncAPI 3.1.0", str(doc.get("asyncapi")) == "3.1.0",
                doc.get("asyncapi")))
    req_id, _ = channel_by_address(doc, "payments.authorize.request")
    ex.append(E("Request channel declares the queue address", bool(req_id), req_id))
    reply_channels = [cid for cid, ch in (doc.get("channels") or {}).items()
                      if isinstance(ch, dict) and ch.get("address") is None]
    ex.append(E("Reply channel present with null/absent address (dynamic at runtime)",
                bool(reply_channels), f"null-address channels={reply_channels}"))
    send_op = next((op for op in (doc.get("operations") or {}).values()
                    if isinstance(op, dict) and op.get("action") == "send"
                    and (op.get("channel") or {}).get("$ref", "").endswith(str(req_id))),
                   None) or {}
    reply = send_op.get("reply") or {}
    loc = str(((reply.get("address") or {}).get("location") or ""))
    ex.append(E("Send operation carries a reply with address at $message.header#/replyTo",
                loc.startswith("$message.header") and "replyTo" in loc, loc or reply))
    s = json.dumps(doc)
    ex.append(E("Avro multi-format schemas used for both records",
                s.count("schemaFormat") >= 2 and "avro" in s.lower()
                and "PaymentAuthRequest" in s and "PaymentAuthReply" in s,
                f"schemaFormat x{s.count('schemaFormat')}"))
    ex.append(E("correlationId defined against the correlationId header",
                '"correlationId"' in s and "$message.header#/correlationId" in s,
                "grep correlationId location"))
    spectral_conventions(ex, f)
    return ex


def grade_review_legacy(out):
    ex = []
    f = find_doc(out, "notification-service.asyncapi.yaml")
    rv = out / "review.md"
    if not f.exists():
        return [E("notification-service.asyncapi.yaml produced", False, "missing")]
    cli_validates(ex, f)
    doc = load(f)
    ex.append(E("Upgraded to AsyncAPI 3.1.0", str(doc.get("asyncapi")) == "3.1.0",
                doc.get("asyncapi")))
    s = json.dumps(doc)
    servers = [srv or {} for srv in (doc.get("servers") or {}).values()]
    ex.append(E("Credentials removed and server split into host/protocol",
                "hunter2" not in s and "svc_notify" not in s
                and bool(servers)
                and all("url" not in srv and "host" in srv and "protocol" in srv
                        for srv in servers),
                "checked hunter2/svc_notify/url/host/protocol on "
                f"{len(servers)} server(s)"))
    signup_id, _ = channel_by_address(doc, "user/signedup")
    sent_id = None
    for cid, ch in (doc.get("channels") or {}).items():
        addr = (ch or {}).get("address") or ""
        if addr.startswith("notifications/email/") and addr.endswith("/sent"):
            sent_id = cid
    ex.append(E("Wire addresses preserved on v3 channels",
                bool(signup_id and sent_id), f"signup={signup_id} sent={sent_id}"))
    ex.append(E("v2 semantics correctly inverted: signedup received, email-sent sent",
                op_action_for_channel(doc, signup_id) == "receive"
                and op_action_for_channel(doc, sent_id) == "send",
                f"signup_op={op_action_for_channel(doc, signup_id)} "
                f"sent_op={op_action_for_channel(doc, sent_id)}"))
    ex.append(E("Owning contact added and v2 parameter schema dropped",
                isinstance((doc.get("info") or {}).get("contact"), dict)
                and '"schema"' not in json.dumps(
                    [(ch or {}).get("parameters") for ch in (doc.get("channels") or {}).values()]),
                "checked info.contact + parameters"))
    if rv.exists():
        r = rv.read_text().lower()
        flags = {
            "version": "2.6" in r or "3.1" in r or "version" in r,
            "secret": "password" in r or "credential" in r or "secret" in r or "hunter2" in r,
            "semantics": ("publish" in r or "subscribe" in r)
                          and ("invert" in r or "receive" in r or "send" in r or "perspective" in r),
        }
        ex.append(E("review.md flags version, secret, and publish/subscribe semantics",
                    all(flags.values()), json.dumps(flags)))
    else:
        ex.append(E("review.md flags version, secret, and publish/subscribe semantics",
                    False, "review.md missing"))
    return ex


GRADERS = {
    "eval-0": grade_author_inventory,
    "eval-1": grade_review_legacy,
    # eval-1 keeps its legacy slash addresses by design, so the Spectral
    # address-convention check applies only to the authoring evals.
    "eval-2": grade_request_reply_avro,
}


def main():
    iteration = Path(sys.argv[1])
    for eval_dir in sorted(iteration.glob("eval-*")):
        key = "-".join(eval_dir.name.split("-", 2)[:2])
        grader = GRADERS.get(key)
        if grader is None:
            print(f"  {eval_dir.name}: no grader registered for '{key}' — skipping",
                  file=sys.stderr)
            continue
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
