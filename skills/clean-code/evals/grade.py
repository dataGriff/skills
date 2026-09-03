#!/usr/bin/env python3
"""Grade clean-code eval runs. Usage: grade.py <iteration-dir>.

Expects <iteration-dir>/eval-*/{with_skill,without_skill}/outputs/ as laid
out by scripts/eval_skills.py (run via `task eval:skills NAME=clean-code`).
Writes grading.json per arm and prints a pass/total summary. Structural and
behavioural checks only — generated code is executed via subprocess, never
imported into the grader process.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

FIXTURES = Path(__file__).resolve().parent / "fixtures"

REPORT_EXPECTED_STDOUT = ["o-1 208.25", "o-3 78.4", "o-5 99.96", "o-2 39.2", "5"]

BARE_EXCEPT = re.compile(r"\bexcept\s*:")
CONSTANT_ASSIGNMENT = re.compile(r"^\s*[A-Z][A-Z0-9_]*\s*=")


def E(text, passed, evidence):
    return {"text": text, "passed": bool(passed), "evidence": str(evidence)[:500]}


def run_python(args, cwd):
    try:
        r = subprocess.run([sys.executable, *args], cwd=cwd, capture_output=True,
                           text=True, timeout=60)
        return r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "timeout"


def max_indent(text):
    depth = 0
    for line in text.splitlines():
        if line.strip() and not line.lstrip().startswith("#"):
            depth = max(depth, len(line) - len(line.lstrip(" ")))
    return depth


def literal_is_named_constant(text, literal):
    """The literal appears at most once, and only on a constant-assignment line."""
    lines = [l for l in text.splitlines() if literal in l]
    return len(lines) <= 1 and all(CONSTANT_ASSIGNMENT.match(l) for l in lines)


# --- eval-0: construct-module -----------------------------------------------

INVENTORY_TEST = """
import json
import inventory

results = {}
stock = {"ABC": 10, "XYZ": 5}
lines = [{"sku": "ABC", "qty": 3}, {"sku": "ABC", "qty": 2}, {"sku": "XYZ", "qty": 5}]
out = inventory.reserve_stock(stock, lines)
results["happy_path"] = out == {"ABC": 5, "XYZ": 0}
results["input_unmutated"] = stock == {"ABC": 10, "XYZ": 5}
try:
    inventory.reserve_stock(stock, [{"sku": "NOPE", "qty": 1}])
    results["unknown_sku"] = False
except KeyError as e:
    results["unknown_sku"] = "NOPE" in str(e)
except Exception:
    results["unknown_sku"] = False
try:
    inventory.reserve_stock(stock, [{"sku": "ABC", "qty": 4}, {"sku": "XYZ", "qty": 6}])
    results["insufficient"] = False
    results["insufficient_msg"] = False
except ValueError as e:
    results["insufficient"] = stock == {"ABC": 10, "XYZ": 5}
    results["insufficient_msg"] = "XYZ" in str(e) and "6" in str(e) and "5" in str(e)
except Exception:
    results["insufficient"] = False
    results["insufficient_msg"] = False
try:
    inventory.reserve_stock(stock, [{"sku": "ABC", "qty": 6}, {"sku": "ABC", "qty": 5}])
    results["accumulated"] = False
except ValueError:
    results["accumulated"] = True
except Exception:
    results["accumulated"] = False
try:
    inventory.reserve_stock(stock, [{"sku": "ABC", "qty": 0}])
    results["invalid_qty"] = False
except ValueError:
    results["invalid_qty"] = True
except Exception:
    results["invalid_qty"] = False
print(json.dumps(results))
"""

BEHAVIOUR_CHECKS = [
    ("happy_path", "Reserves correctly, accumulating duplicate SKUs"),
    ("input_unmutated", "Returns a new dict; input stock not mutated"),
    ("unknown_sku", "Unknown SKU raises KeyError naming the SKU"),
    ("insufficient", "Over-request raises ValueError, reserving nothing"),
    ("insufficient_msg", "Error message carries SKU and both quantities"),
    ("accumulated", "Accumulated duplicates checked against availability"),
    ("invalid_qty", "Non-positive qty raises ValueError"),
]


def grade_construct(out):
    ex = []
    f = out / "inventory.py"
    if not f.exists():
        return [E("inventory.py exists", False, "missing")]
    code, stdout, stderr = run_python(["-c", INVENTORY_TEST], out)
    results = {}
    if code == 0:
        try:
            results = json.loads(stdout.strip().splitlines()[-1])
        except (json.JSONDecodeError, IndexError):
            pass
    for key, text in BEHAVIOUR_CHECKS:
        ex.append(E(text, results.get(key, False),
                    results.get(key, f"harness failed: {stderr[-200:]}")))
    text = f.read_text(encoding="utf-8")
    ex.append(E("No bare except (errors not swallowed)",
                not BARE_EXCEPT.search(text), "grep 'except:'"))
    bodies = re.split(r"^def ", text, flags=re.M)[1:]
    longest = max((len(b.rstrip().splitlines()) for b in bodies), default=0)
    ex.append(E("Functions stay small (longest <= 40 lines)",
                0 < longest <= 40, f"longest={longest}"))
    single = re.findall(r"def\s+\w+\(\s*[a-z]\s*[,)]", text)
    ex.append(E("No single-letter parameter names", not single, f"found={single}"))
    return ex


# --- eval-1: refactor-legacy ------------------------------------------------

def grade_refactor(out):
    ex = []
    f = out / "order_report.py"
    if not f.exists():
        return [E("order_report.py exists", False, "missing")]
    code, stdout, stderr = run_python(["order_report.py"], out)
    got = [l.strip() for l in stdout.strip().splitlines()]
    ex.append(E("Behaviour preserved: script prints exactly the original output",
                code == 0 and got == REPORT_EXPECTED_STDOUT,
                f"exit={code} got={got} err={stderr[-150:]}"))
    text = f.read_text(encoding="utf-8")
    ex.append(E("Swallowed exception gone (no bare except)",
                not BARE_EXCEPT.search(text), "grep 'except:'"))
    ex.append(E("Commented-out code deleted", "old_proc" not in text, "grep old_proc"))
    ex.append(E("Duplicated discount/fee logic collapsed (rate literals appear "
                "at most once)", text.count("0.15") <= 1 and text.count("0.02") <= 1,
                f"0.15 x{text.count('0.15')}, 0.02 x{text.count('0.02')}"))
    named = all(literal_is_named_constant(text, lit)
                for lit in ("0.15", "0.02", "86400"))
    ex.append(E("Magic numbers replaced with named constants", named,
                "0.15/0.02/86400 only on UPPER_CASE assignment lines"))
    ex.append(E("proc/proc2 renamed to intent-revealing names",
                "def proc(" not in text and "def proc2(" not in text, "grep def proc"))
    ex.append(E("Boolean flag parameter removed", not re.search(r"\bflag\b", text),
                "grep flag"))
    ex.append(E("Nesting flattened (max indent <= 16 spaces, was 28)",
                max_indent(text) <= 16, f"max_indent={max_indent(text)}"))
    ex.append(E("No comparisons to None with != / ==",
                "!= None" not in text and "== None" not in text, "grep '!= None'"))
    ex.append(E("What-comments removed", "processes the orders" not in text,
                "grep 'processes the orders'"))
    return ex


# --- eval-2: review-code ----------------------------------------------------

# Planted defect -> cues that show the review named it. Correctness-class
# defects also feed the severity-ordering check.
DEFECTS = {
    "swallowed exception in charge()": (
        "swallow", "silent", "suppress", "except exception", "bare except",
        "hides", "ignores the error", "ignored"),
    "charge() returns True on failure": ("returns true", "return true", "reports success", "false success"),
    "get_customer creates records (misleading name / side effect)": None,  # custom
    "mutable default argument in add_line": (
        "mutable default", "default argument", "lines=[]", "shared between calls"),
    "order_total/refund_total duplication": (
        "duplicat", "identical", "copy of", "copy-paste", "copied", "same logic"),
    "magic values (0.9, 1.2, GOLD)": ("magic", "hard-coded", "hardcoded", "named constant"),
    "deep nesting in charge()": ("nest", "guard clause", "early return", "arrow"),
    "commented-out old_charge": ("commented-out", "commented out", "dead code", "old_charge"),
}
CORRECTNESS_CUES = ("swallow", "silent", "suppress", "returns true", "return true",
                    "mutable default", "hides")
STYLE_CUES = ("magic", "commented-out", "commented out", "dead code")


def first_pos(text, cues):
    hits = [text.find(c) for c in cues if c in text]
    return min(hits) if hits else None


def grade_review(out):
    ex = []
    review = out / "review.md"
    if not review.exists():
        return [E("review.md exists", False, "missing")]
    fixture = (FIXTURES / "payment_service.py").read_text(encoding="utf-8")
    written = (out / "payment_service.py")
    ex.append(E("payment_service.py left unmodified",
                written.exists() and written.read_text(encoding="utf-8") == fixture,
                "diff vs fixture"))
    r = review.read_text(encoding="utf-8").lower()
    for defect, cues in DEFECTS.items():
        if cues is None:
            found = "get_customer" in r and any(
                c in r for c in ("creat", "side effect", "mutat", "mislead", "surpris"))
        else:
            found = any(c in r for c in cues)
        ex.append(E(f"Review names: {defect}", found, "cue search in review.md"))
    c, s = first_pos(r, CORRECTNESS_CUES), first_pos(r, STYLE_CUES)
    ex.append(E("Correctness findings ranked above style findings",
                c is not None and (s is None or c < s), f"correctness@{c} style@{s}"))
    return ex


GRADERS = {"eval-0": grade_construct, "eval-1": grade_refactor, "eval-2": grade_review}


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
