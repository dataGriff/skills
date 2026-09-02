#!/usr/bin/env python3
"""Grade contract-testing-microcks eval runs. Usage: grade.py <iteration-dir>.

Expects <iteration-dir>/eval-*/{with_skill,without_skill}/outputs/ as laid
out by scripts/eval_skills.py (run via
`task eval:skills NAME=contract-testing-microcks`). All checks are static
(no docker, no network): they verify the run used the real Microcks
surfaces — action/CLI names, inputs, runner ids, Testcontainers API —
rather than hallucinated ones. Writes grading.json per arm and prints a
pass/total summary.
"""
import json
import re
import sys
from pathlib import Path

import yaml


def load_yaml(path):
    try:
        return yaml.safe_load(path.read_text()) or {}
    except Exception as e:
        return {"__parse_error__": str(e)}


def E(text, passed, evidence):
    return {"text": text, "passed": bool(passed), "evidence": str(evidence)[:500]}


def read(path):
    return path.read_text() if path.exists() else ""


def grade_actions_gate(out):
    ex = []
    wf = out / "contract-test.yml"
    text = read(wf) + "\n" + read(out / "setup.md")
    valid = wf.exists() and "__parse_error__" not in load_yaml(wf)
    # Real test surface: the official action or the CLI's `test` verb.
    uses_action = "microcks/test-github-action" in text
    uses_cli = bool(re.search(r"microcks(-cli)?\s+test\s", text))
    ex.append(E("Workflow is valid YAML with a real Microcks test step "
                "(test-github-action or `microcks test`)",
                valid and (uses_action or uses_cli),
                f"valid={valid} action={uses_action} cli={uses_cli}"))
    ex.append(E("Service referenced as 'Order API:1.2.0' (name:version form)",
                "Order API:1.2.0" in text, "grep 'Order API:1.2.0'"))
    ex.append(E("Uses the OPEN_API_SCHEMA runner",
                "OPEN_API_SCHEMA" in text,
                f"runners found={sorted(set(re.findall(r'[A-Z_]*SCHEMA|POSTMAN|HTTP', text)))}"))
    has_import = ("microcks/import-github-action" in text
                  or bool(re.search(r"microcks(-cli)?\s+import(-url)?\s", text)))
    ex.append(E("Imports the committed spec (import action or `microcks import`)",
                has_import, "grep import action/command"))
    creds_named = bool(re.search(r"keycloakClient(Id|Secret)", text)) or \
        bool(re.search(r"--keycloakClient(Id|Secret)", text))
    via_secrets = "secrets." in text
    hardcoded = re.search(
        r"(clientSecret|keycloakClientSecret|password)\s*[:=]\s*['\"]?[A-Za-z0-9+/-]{12,}",
        text, re.I)
    ex.append(E("Keycloak service-account creds passed by their real names, "
                "via secrets, none hardcoded",
                creds_named and via_secrets and not hardcoded,
                f"named={creds_named} secrets={via_secrets} hardcoded={bool(hardcoded)}"))
    return ex


def grade_node_testcontainers(out):
    ex = []
    tests = list(out.glob("*.test.ts")) + list(out.glob("*.test.js"))
    code = "\n".join(read(t) for t in tests)
    text = code + "\n" + read(out / "deps.md")
    pkg_mentions = sorted(set(re.findall(r"[@\w/-]*microcks[\w/-]*", text)))[:8]
    ex.append(E("Names the real npm package @microcks/microcks-testcontainers",
                "@microcks/microcks-testcontainers" in text,
                f"pkg-ish mentions={pkg_mentions}"))
    ex.append(E("Starts MicrocksContainer and loads the spec as a main artifact",
                "MicrocksContainer" in code
                and bool(re.search(r"withMainArtifacts?\(|importAsMainArtifact\(", code)),
                "grep MicrocksContainer + withMainArtifacts/importAsMainArtifact"))
    ex.append(E("Exposes the REST mock URL via getRestMockEndpoint",
                "getRestMockEndpoint" in code, "grep getRestMockEndpoint"))
    # serviceId is often assembled from constants, so require the parts
    # (name, version, a serviceId field, the app URL) rather than the literal.
    calls_test = "testEndpoint" in code and "serviceId" in code \
        and "Order API" in code and "1.2.0" in code and "localhost:3001" in code
    ex.append(E("Runs the conformance test: testEndpoint with the service's "
                "name+version as serviceId, against the app URL",
                calls_test,
                f"testEndpoint={'testEndpoint' in code} serviceId={'serviceId' in code} "
                f"name={'Order API' in code} ver={'1.2.0' in code} url={'localhost:3001' in code}"))
    runner_ids = sorted(set(re.findall(r"[A-Z][A-Z_]*SCHEMA", code)))
    ex.append(E("Uses the real OPEN_API_SCHEMA runner id (not a hallucinated variant)",
                bool(re.search(r"\bOPEN_API_SCHEMA\b", code)),
                f"runner ids found={runner_ids}"))
    ex.append(E("Asserts on the test result's success flag",
                bool(re.search(r"(testResult|result)\.success", code)),
                "grep .success assertion"))
    return ex


GRADERS = {"eval-0": grade_actions_gate, "eval-1": grade_node_testcontainers}


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
