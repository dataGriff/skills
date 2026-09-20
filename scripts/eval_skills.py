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

Downstream stage (optional, per eval): after both arms, evals.json may list
"downstream" tasks - small follow-up jobs run in three states of the same
fixture (before = original docs, after-baseline = the baseline arm's output,
after-skill = the skill arm's output) - to measure whether the repo the
skill produces is actually cheaper to work in: turns, tokens, reads before
the first write, and rule adherence per state.
    task eval:downstream NAME=x ITERATION=<stamp>   # rerun only that stage

Requires the `claude` CLI. Deliberately NOT part of `task ci`: eval runs
are slow, cost tokens, and are non-deterministic — see docs/skills.md for
when to run them.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"
EVAL_ROOT = REPO_ROOT / ".evals"
RUN_TIMEOUT_SECONDS = 900
DOWNSTREAM_WORKERS = 4
DOWNSTREAM_STATES = ("before", "after-baseline", "after-skill")
WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}

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


DOWNSTREAM_PROMPT = """Execute this task in the current working directory, a repository snapshot:
- Task: {prompt}
- Work only from what this repository tells you; do not read files outside \
the current directory.
"""


def run_claude(
    prompt: str,
    cwd: Path,
    model: str | None = None,
    add_dir: Path | None = None,
    allowed_tools: list[str] | None = None,
    stream: bool = False,
) -> dict:
    """Run one headless session. With stream=True the per-message event
    stream is parsed so the tool calls made before the first file write
    (how much orientation the repo demanded) are recorded as well."""
    cmd = ["claude", "-p", prompt, "--permission-mode", "acceptEdits"]
    cmd += ["--output-format", "stream-json", "--verbose"] if stream else ["--output-format", "json"]
    if model:
        cmd += ["--model", model]
    if add_dir:
        # The with-skill prompt tells the model to read files under
        # add_dir (the skill directory); some models otherwise refuse to
        # read outside cwd even under acceptEdits.
        cmd += ["--add-dir", str(add_dir)]
    if allowed_tools:
        # acceptEdits auto-approves file edits but not shell commands. An
        # eval whose task is to drive a CLI declares the commands it needs
        # in evals.json ("allowed_tools"); without this both arms stall
        # asking for approval and burn turns producing nothing.
        cmd += ["--allowedTools", *allowed_tools]
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
        if stream:
            payload, tool_calls = None, []
            for line in result.stdout.splitlines():
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if event.get("type") == "assistant":
                    for block in (event.get("message") or {}).get("content") or []:
                        if block.get("type") == "tool_use":
                            tool_calls.append(block.get("name"))
                elif event.get("type") == "result":
                    payload = event
            info["tool_calls"] = len(tool_calls)
            info["reads_before_first_write"] = next(
                (i for i, n in enumerate(tool_calls) if n in WRITE_TOOLS), len(tool_calls)
            )
            info["tool_call_names"] = tool_calls
            if payload is None:
                raise json.JSONDecodeError("no result event", result.stdout[-100:], 0)
        else:
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


def run_downstream(
    ev: dict, eval_dir: Path, fixtures: Path, scratch: Path,
    model: str | None, allowed_tools: list[str], repeats: int,
) -> None:
    """Run the eval's downstream tasks in each state of the fixture repo.

    The question is not "did the skill restructure well" but "is the
    restructured repo cheaper to work in": every task runs against the
    original docs (before), the baseline arm's output (after-baseline) and
    the skill arm's output (after-skill), and the grader scores adherence
    to the repo's own rules in each. Runs are independent, so they go
    through a small worker pool."""
    tasks = ev.get("downstream") or []
    if not tasks:
        return
    sources = {
        "before": None,
        "after-baseline": eval_dir / "without_skill" / "outputs",
        "after-skill": eval_dir / "with_skill" / "outputs",
    }
    jobs = [
        (state, sources[state], task, rep)
        for state in DOWNSTREAM_STATES
        for task in tasks
        for rep in range(1, repeats + 1)
    ]

    def run_job(job):
        state, src, task, rep = job
        rel = Path("downstream") / state / task["id"] / f"rep-{rep}"
        work = scratch / eval_dir.name / rel / "outputs"
        work.mkdir(parents=True, exist_ok=True)
        if src is None:
            for fixture in ev.get("files", []):
                shutil.copy(fixtures / fixture, work / Path(fixture).name)
        else:
            # The arm's own artefacts (.skill copy, NOTES.md) are not part
            # of the repo a later agent would see.
            shutil.copytree(src, work, dirs_exist_ok=True,
                            ignore=shutil.ignore_patterns(".skill", "NOTES.md"))
        info = run_claude(DOWNSTREAM_PROMPT.format(prompt=task["prompt"]), work,
                          model, None, allowed_tools, stream=True)
        final = eval_dir / rel / "outputs"
        final.parent.mkdir(parents=True, exist_ok=True)
        if final.exists():
            shutil.rmtree(final)
        shutil.move(str(work), str(final))
        (eval_dir / rel / "run.json").write_text(json.dumps(info, indent=2))
        return f"{state}/{task['id']}/rep-{rep}", info

    print(f"  {eval_dir.name}/downstream: {len(jobs)} runs "
          f"({len(DOWNSTREAM_STATES)} states x {len(tasks)} tasks x {repeats}) ...", flush=True)
    with ThreadPoolExecutor(max_workers=DOWNSTREAM_WORKERS) as pool:
        for label, info in pool.map(run_job, jobs):
            print(f"    {label}: {info['duration_seconds']}s, {info.get('num_turns')} turns, "
                  f"{info.get('reads_before_first_write')} reads before first write "
                  f"(exit {info['exit_code']})", flush=True)


def grade_and_summarise(skill_dir: Path, iteration: Path, stamp: str, model: str | None) -> None:
    grader = skill_dir / "evals" / "grade.py"
    if grader.is_file():
        print(f"  grading with {grader.relative_to(REPO_ROOT)}")
        subprocess.run([sys.executable, str(grader), str(iteration)], check=False)
    else:
        print(f"  no grader — compare outputs manually under {iteration}")
    write_results_summary(skill_dir, iteration, stamp, model)


def run_downstream_only(skill_dir: Path, stamp: str, model: str | None = None) -> Path | None:
    """Re-run just the downstream stage against an existing iteration's arm
    outputs, then regrade and rewrite the summary."""
    evals_file = skill_dir / "evals" / "evals.json"
    spec = json.loads(evals_file.read_text(encoding="utf-8"))
    iteration = EVAL_ROOT / skill_dir.name / stamp
    if not iteration.is_dir():
        print(f"eval_skills: {iteration.relative_to(REPO_ROOT)} not found", file=sys.stderr)
        return None
    fixtures = skill_dir / "evals" / "fixtures"
    scratch = Path(tempfile.mkdtemp(prefix=f"skill-eval-{skill_dir.name}-"))
    for ev in spec["evals"]:
        eval_dir = iteration / f"eval-{ev['id']}-{ev['name']}"
        shutil.rmtree(eval_dir / "downstream", ignore_errors=True)
        run_downstream(ev, eval_dir, fixtures, scratch, model,
                       spec.get("allowed_tools") or [], int(spec.get("downstream_repeats", 1)))
    shutil.rmtree(scratch, ignore_errors=True)
    grade_and_summarise(skill_dir, iteration, stamp, model)
    return iteration


def run_skill_evals(skill_dir: Path, model: str | None = None) -> Path | None:
    evals_file = skill_dir / "evals" / "evals.json"
    spec = json.loads(evals_file.read_text(encoding="utf-8"))
    allowed_tools = spec.get("allowed_tools") or []
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    iteration = EVAL_ROOT / skill_dir.name / stamp
    fixtures = skill_dir / "evals" / "fixtures"
    # Each arm runs in a scratch directory OUTSIDE the repo tree and is
    # moved under .evals/ afterwards. `claude -p` loads CLAUDE.md from every
    # ancestor of its working directory, so a session under .evals/ would
    # read this repo's AGENTS.md - the baseline arm then sees the very
    # conventions the skill teaches and the comparison measures nothing.
    scratch = Path(tempfile.mkdtemp(prefix=f"skill-eval-{skill_dir.name}-"))

    for ev in spec["evals"]:
        eval_dir = iteration / f"eval-{ev['id']}-{ev['name']}"
        for arm, template in (
            ("with_skill", WITH_SKILL_PROMPT),
            ("without_skill", BASELINE_PROMPT),
        ):
            final_outputs = eval_dir / arm / "outputs"
            outputs = scratch / eval_dir.name / arm / "outputs"
            outputs.mkdir(parents=True, exist_ok=True)
            for fixture in ev.get("files", []):
                shutil.copy(fixtures / fixture, outputs / Path(fixture).name)
            # Eval sessions may be sandboxed to their working directory (e.g.
            # on remote runners), so the with_skill arm gets a local copy of
            # the skill rather than a path it may not be allowed to read.
            # evals/ is excluded so the arm can't see its own grader.
            eval_skill_dir = outputs / ".skill"
            if arm == "with_skill":
                shutil.copytree(
                    skill_dir, eval_skill_dir, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("evals"),
                )
            prompt = template.format(
                skill_dir=eval_skill_dir, prompt=ev["prompt"], skills_dir=SKILLS_DIR
            )
            # Grant read access to the copy the prompt names, not the real
            # skill dir — that would re-expose evals/ (the grader).
            add_dir = eval_skill_dir if arm == "with_skill" else None
            print(f"  {eval_dir.name}/{arm} ... ", end="", flush=True)
            info = run_claude(prompt, outputs, model, add_dir, allowed_tools)
            final_outputs.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(outputs), str(final_outputs))
            (eval_dir / arm / "run.json").write_text(json.dumps(info, indent=2))
            print(f"done in {info['duration_seconds']}s (exit {info['exit_code']})")
        run_downstream(ev, eval_dir, fixtures, scratch, model, allowed_tools,
                       int(spec.get("downstream_repeats", 1)))
    shutil.rmtree(scratch, ignore_errors=True)
    grade_and_summarise(skill_dir, iteration, stamp, model)
    return iteration


def downstream_rows(iteration: Path) -> list[tuple]:
    """One row per eval x state: run count, adherence, and mean turns /
    reads-before-first-write / tokens / cost across its tasks and repeats."""
    rows = []
    for eval_dir in sorted(iteration.glob("eval-*")):
        ds = eval_dir / "downstream"
        if not ds.is_dir():
            continue
        for state in DOWNSTREAM_STATES:
            runs = sorted((ds / state).glob("*/rep-*")) if (ds / state).is_dir() else []
            if not runs:
                continue
            agg: dict[str, list[float]] = {"turns": [], "reads": [], "tokens": [], "cost": []}
            passed = total = 0
            for run_dir in runs:
                run_file, grade_file = run_dir / "run.json", run_dir / "grading.json"
                if run_file.is_file():
                    run = json.loads(run_file.read_text())
                    for key, field in (("turns", "num_turns"), ("reads", "reads_before_first_write"),
                                       ("tokens", "tokens"), ("cost", "total_cost_usd")):
                        value = run.get(field)
                        if isinstance(value, (int, float)):
                            agg[key].append(value)
                if grade_file.is_file():
                    summary = json.loads(grade_file.read_text()).get("summary", {})
                    passed += summary.get("passed", 0)
                    total += summary.get("total", 0)

            def mean(xs: list[float]) -> float | None:
                return sum(xs) / len(xs) if xs else None

            rows.append((eval_dir.name.split("-", 2)[-1], state, len(runs), passed, total,
                         mean(agg["turns"]), mean(agg["reads"]), mean(agg["tokens"]), mean(agg["cost"])))
    return rows


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
    ds_rows = downstream_rows(iteration)
    if ds_rows:
        lines += [
            "",
            "Downstream tasks - the same follow-up jobs run in the fixture repo before "
            "the restructure, after the baseline arm's restructure, and after the skill "
            "arm's (means per run; adherence = grader checks the answers passed). This "
            "is the cost the skill is meant to reduce: what a later agent pays to "
            "orient and whether it follows the repo's rules.",
            "",
            "| Eval | State | Runs | Adherence | Turns | Reads before first write | Tokens | Cost |",
            "|------|-------|------|-----------|-------|--------------------------|--------|------|",
        ]

        def fmt(value, spec: str) -> str:
            return format(value, spec) if isinstance(value, (int, float)) else "?"

        for name, state, n, passed, total, turns, reads, toks, cost in ds_rows:
            lines.append(
                f"| {name} | {state} | {n} | {passed}/{total} | {fmt(turns, '.1f')} | "
                f"{fmt(reads, '.1f')} | {fmt(toks, ',.0f')} | ${fmt(cost, '.2f')} |"
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

    argv = sys.argv[1:]
    downstream_stamp = None
    if "--downstream" in argv:
        i = argv.index("--downstream")
        downstream_stamp = argv[i + 1] if len(argv) > i + 1 else None
        argv = argv[:i] + argv[i + 2:]
    name = argv[0] if len(argv) > 0 and argv[0] else None
    model = argv[1] if len(argv) > 1 and argv[1] else None
    if downstream_stamp is not None:
        if not name:
            print("eval_skills: --downstream needs NAME and ITERATION", file=sys.stderr)
            return 1
        print(f"Downstream evals for {name}, iteration {downstream_stamp}"
              + (f" on {model}" if model else "") + ":")
        return 0 if run_downstream_only(SKILLS_DIR / name, downstream_stamp, model) else 1
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
