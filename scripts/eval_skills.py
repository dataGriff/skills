#!/usr/bin/env python3
"""Run with/without-skill evals for skills that define them.

Usage (via the Taskfile — the canonical entrypoint):
    task eval:skills                        # every skill with an evals/evals.json
    task eval:skills NAME=x                 # one skill
    task eval:skills NAME=x MODEL=sonnet    # pin both arms to one model

MODEL is passed straight to `claude -p --model`; omit it to use the CLI's
own default. Pin it when you want a reproducible comparison on a specific
model rather than whatever the headless default happens to be.

For each eval prompt this runs two headless `claude -p` sessions — one told
to read and follow the skill, one without it — into
.evals/<skill>/<timestamp>/eval-<id>-<name>/{with_skill,without_skill}/outputs/.
If the skill ships evals/grade.py, it is run afterwards to produce
grading.json per arm and a pass/total summary; otherwise outputs are left
for human comparison.

Requires the `claude` CLI. Deliberately NOT part of `task ci`: eval runs
are slow, cost tokens, and are non-deterministic — see docs/skills.md for
when to run them.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"
EVAL_ROOT = REPO_ROOT / ".evals"
RUN_TIMEOUT_SECONDS = 900

WITH_SKILL_PROMPT = """Execute this task:
- Skill path: {skill_dir} — FIRST read the SKILL.md at that path and follow \
its instructions, loading its references/ and assets/ files as the skill directs.
- Task: {prompt}
- Save all output files in the current working directory.
"""

BASELINE_PROMPT = """Execute this task:
- Task: {prompt}
- Save all output files in the current working directory. Treat this as a \
standalone task; do not read files under {skills_dir}.
"""


def run_claude(
    prompt: str, cwd: Path, model: str | None = None, add_dir: Path | None = None
) -> dict:
    cmd = ["claude", "-p", prompt, "--permission-mode", "acceptEdits",
           "--output-format", "json"]
    if model:
        cmd += ["--model", model]
    if add_dir:
        # The with-skill prompt tells the model to read files under
        # add_dir (the skill directory); some models otherwise refuse to
        # read outside cwd even under acceptEdits.
        cmd += ["--add-dir", str(add_dir)]
    start = time.time()
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=RUN_TIMEOUT_SECONDS,
    )
    info = {
        "exit_code": result.returncode,
        "duration_seconds": round(time.time() - start, 1),
        "stderr_tail": result.stderr[-1000:],
    }
    try:  # headless JSON output carries usage/cost metadata
        payload = json.loads(result.stdout)
        info["duration_seconds"] = round(payload.get("duration_ms", 0) / 1000, 1) or info["duration_seconds"]
        info["num_turns"] = payload.get("num_turns")
        info["total_cost_usd"] = payload.get("total_cost_usd")
        # Which models actually served the run — the CLI default can change
        # between runs (e.g. after /model in an interactive session), so a
        # results table without this is not comparable across runs.
        info["models"] = sorted((payload.get("modelUsage") or {}).keys())
        usage = payload.get("usage") or {}
        info["tokens"] = sum(
            v for k, v in usage.items() if isinstance(v, (int, float)) and "tokens" in k
        ) or None
        info["result_tail"] = str(payload.get("result", ""))[-1500:]
    except (json.JSONDecodeError, TypeError):
        info["stdout_tail"] = result.stdout[-2000:]
    return info


def run_skill_evals(skill_dir: Path, model: str | None = None) -> Path | None:
    evals_file = skill_dir / "evals" / "evals.json"
    spec = json.loads(evals_file.read_text(encoding="utf-8"))
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    iteration = EVAL_ROOT / skill_dir.name / stamp
    fixtures = skill_dir / "evals" / "fixtures"

    for ev in spec["evals"]:
        eval_dir = iteration / f"eval-{ev['id']}-{ev['name']}"
        for arm, template in (
            ("with_skill", WITH_SKILL_PROMPT),
            ("without_skill", BASELINE_PROMPT),
        ):
            outputs = eval_dir / arm / "outputs"
            outputs.mkdir(parents=True, exist_ok=True)
            for fixture in ev.get("files", []):
                shutil.copy(fixtures / fixture, outputs / Path(fixture).name)
            prompt = template.format(
                skill_dir=skill_dir, prompt=ev["prompt"], skills_dir=SKILLS_DIR
            )
            add_dir = skill_dir if arm == "with_skill" else None
            print(f"  {eval_dir.name}/{arm} ... ", end="", flush=True)
            info = run_claude(prompt, outputs, model, add_dir)
            (eval_dir / arm / "run.json").write_text(json.dumps(info, indent=2))
            print(f"done in {info['duration_seconds']}s (exit {info['exit_code']})")

    grader = skill_dir / "evals" / "grade.py"
    if grader.is_file():
        print(f"  grading with {grader.relative_to(REPO_ROOT)}")
        subprocess.run([sys.executable, str(grader), str(iteration)], check=False)
    else:
        print(f"  no grader — compare outputs manually under {iteration}")
    write_results_summary(skill_dir, iteration, stamp, model)
    return iteration


def write_results_summary(
    skill_dir: Path, iteration: Path, stamp: str, model: str | None = None
) -> None:
    """Write evals/latest-results.md — committed, so eval results show up in
    the pull request diff alongside the skill change that prompted the run."""
    model_suffix = f" MODEL={model}" if model else ""
    served: set[str] = set()
    for run_file in iteration.glob("eval-*/*/run.json"):
        served.update(json.loads(run_file.read_text()).get("models") or [])
    lines = [
        f"# Eval results: {skill_dir.name}",
        "",
        f"Last run: {stamp} UTC via `task eval:skills NAME={skill_dir.name}"
        f"{model_suffix}` (commit this file with the skill change so the PR "
        "carries the evidence).",
        "",
        f"Models served: {', '.join(sorted(served)) or 'not recorded'}.",
        "",
        "| Eval | With skill | Baseline | Turns (skill/base) | Time (skill/base) | Cost (skill/base) |",
        "|------|-----------|----------|--------------------|-------------------|-------------------|",
    ]
    separating: list[str] = []
    tokens = {"with_skill": 0, "without_skill": 0}
    for eval_dir in sorted(iteration.glob("eval-*")):
        cells, expectations = {}, {}
        for arm in ("with_skill", "without_skill"):
            g, r = eval_dir / arm / "grading.json", eval_dir / arm / "run.json"
            score, turns, secs, cost = "?", "?", "?", "?"
            if g.is_file():
                graded = json.loads(g.read_text())
                s = graded.get("summary", {})
                score = f"{s.get('passed', '?')}/{s.get('total', '?')}"
                expectations[arm] = graded.get("expectations", [])
            if r.is_file():
                run = json.loads(r.read_text())
                turns = run.get("num_turns", "?")
                secs = f"{run.get('duration_seconds', '?')}s"
                usd = run.get("total_cost_usd")
                cost = f"${usd:.2f}" if isinstance(usd, (int, float)) else "?"
                tokens[arm] += run.get("tokens") or 0
            cells[arm] = (score, turns, secs, cost)
        w, b = cells.get("with_skill", ("?",) * 4), cells.get("without_skill", ("?",) * 4)
        name = eval_dir.name.split("-", 2)[-1]
        lines.append(
            f"| {name} | {w[0]} | {b[0]} | {w[1]} / {b[1]} | {w[2]} / {b[2]} | {w[3]} / {b[3]} |"
        )
        if "with_skill" in expectations and "without_skill" in expectations:
            pairs = list(zip(expectations["with_skill"], expectations["without_skill"]))
            differ = sum(1 for a, c in pairs if a.get("passed") != c.get("passed"))
            separating.append(f"{name} {differ}/{len(pairs)}")
    lines.append("")
    if separating:
        lines.append(
            "Grader checks that separated the arms: " + ", ".join(separating)
            + ". A check both arms always pass measures nothing; a score delta "
            "with none separating is noise."
        )
    if tokens["without_skill"]:
        ratio = tokens["with_skill"] / tokens["without_skill"]
        lines.append(
            f"Token cost, with skill / baseline: {ratio:.2f}x. Turns above the "
            "baseline usually mean SKILL.md loads bundled files unconditionally."
        )
    lines += ["", f"Full outputs (gitignored): `.evals/{skill_dir.name}/{stamp}/`.", ""]

    # Keep any hand-written sections (## headings) from the previous file:
    # the generated block above is regenerated every run, the notes are not.
    out = skill_dir / "evals" / "latest-results.md"
    if out.is_file():
        previous = out.read_text(encoding="utf-8").splitlines()
        first_section = next((i for i, l in enumerate(previous) if l.startswith("## ")), None)
        if first_section is not None:
            lines += previous[first_section:] + [""]
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"  summary → {out.relative_to(REPO_ROOT)}")


def main() -> int:
    if shutil.which("claude") is None:
        print(
            "eval_skills: the `claude` CLI is required to run evals "
            "(https://claude.com/claude-code). Aborting.",
            file=sys.stderr,
        )
        return 2

    name = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] else None
    model = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] else None
    if name:
        targets = [SKILLS_DIR / name]
        if not (targets[0] / "evals" / "evals.json").is_file():
            print(f"eval_skills: skills/{name}/evals/evals.json not found", file=sys.stderr)
            return 1
    else:
        targets = sorted(
            p.parent.parent for p in SKILLS_DIR.glob("*/evals/evals.json")
        )
        if not targets:
            print("eval_skills: no skill defines evals/evals.json — nothing to run.")
            return 0

    for skill_dir in targets:
        print(f"Evaluating {skill_dir.name}" + (f" on {model}" if model else "") + ":")
        run_skill_evals(skill_dir, model)
    print(f"\nResults under {EVAL_ROOT.relative_to(REPO_ROOT)}/ (gitignored).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
