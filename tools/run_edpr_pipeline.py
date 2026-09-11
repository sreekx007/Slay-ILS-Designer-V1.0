#!/usr/bin/env python3
"""
Run the EDPR workflow for an existing EDPR JSON file, or prepare an LLM parser
prompt when only a natural-language problem statement is available.

Pipeline for existing EDPR JSON:
1. Validate EDPR JSON.
2. Check P-map/APF semantic completeness.
3. Retrieve EDES/EDAS/EDIKB context.
4. Produce a first-pass solution summary.
5. Emit a Knowloop candidate JSON.

Natural-language parsing remains an LLM task. This script packages the runtime
parser prompt plus the user problem so the LLM can emit EDPR JSON.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = REPO_ROOT / "tools"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "runs"


def run_command(command: list[str]) -> None:
    print("+ " + " ".join(command))
    completed = subprocess.run(command, cwd=str(REPO_ROOT), text=True)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def read_text_argument(value: str | None, path: str | None) -> str:
    if value and path:
        raise SystemExit("Use either --problem-text or --problem-file, not both.")
    if path:
        return Path(path).read_text(encoding="utf-8")
    if value:
        return value
    raise SystemExit("Provide --edpr-json for a full run, or --problem-text/--problem-file to prepare a parser prompt.")


def prepare_parser_prompt(problem_text: str, output_dir: Path) -> Path:
    runtime_prompt_path = REPO_ROOT / "knowledge" / "edpr" / "EDPR_PARSER_PROMPT_RUNTIME.md"
    manifest_path = REPO_ROOT / "framework_manifest.json"
    if not runtime_prompt_path.exists():
        raise SystemExit(f"Missing runtime prompt: {runtime_prompt_path}")

    output_dir.mkdir(parents=True, exist_ok=True)
    out = output_dir / "edpr_parser_input.prompt.md"
    prompt = runtime_prompt_path.read_text(encoding="utf-8")
    manifest_note = ""
    if manifest_path.exists():
        manifest_note = f"\nFramework manifest path: `{manifest_path.relative_to(REPO_ROOT)}`\n"

    out.write_text(
        "\n".join(
            [
                "# EDPR Parser Input",
                "",
                "Use the EDPR runtime parser prompt below to convert the user problem into valid EDPR JSON.",
                manifest_note,
                "## Runtime Parser Prompt",
                "",
                prompt,
                "",
                "## User Problem",
                "",
                problem_text.strip(),
                "",
                "## Required Output",
                "",
                "Return only EDPR JSON conforming to `schemas/EDPR_METASCHEMA.json`.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return out


def run_existing_edpr(edpr_json: Path, output_dir: Path, solution_format: str, plot: bool = False) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    context_json = output_dir / f"{edpr_json.stem}.retrieval_context.json"
    solution_ext = "json" if solution_format == "json" else "md"
    solution_path = output_dir / f"{edpr_json.stem}.solution.{solution_ext}"
    knowloop_path = output_dir / f"{edpr_json.stem}.knowloop_candidate.json"

    validator = TOOLS_DIR / "EDPR_VALIDATOR.py"
    pmap_checker = TOOLS_DIR / "check_pmap_apf.py"
    schema = REPO_ROOT / "schemas" / "EDPR_METASCHEMA.json"
    retrieve = TOOLS_DIR / "retrieve_context.py"
    solve = TOOLS_DIR / "solve_problem.py"
    knowloop = TOOLS_DIR / "generate_knowloop_candidate.py"

    for required in (validator, pmap_checker, schema, retrieve, solve, knowloop):
        if not required.exists():
            raise SystemExit(f"Missing required pipeline file: {required}")

    run_command([sys.executable, str(validator), "--schema", str(schema), str(edpr_json)])
    run_command([sys.executable, str(pmap_checker), "--strict", str(edpr_json)])
    run_command([sys.executable, str(retrieve), str(edpr_json), "--output", str(context_json)])
    run_command([sys.executable, str(solve), str(context_json), "--format", solution_format, "--output", str(solution_path)])
    knowloop_args = [
        sys.executable,
        str(knowloop),
        "--edpr-json",
        str(edpr_json),
        "--context-json",
        str(context_json),
        "--output",
        str(knowloop_path),
    ]
    if solution_format == "json":
        knowloop_args.extend(["--solution-json", str(solution_path)])
    else:
        knowloop_args.extend(["--solution-md", str(solution_path)])
    plot_failed = False
    if plot:
        structured = output_dir / f"{edpr_json.stem}.solution.json"
        if solution_format != "json":
            run_command([sys.executable, str(solve), str(context_json), "--format", "json", "--output", str(structured)])
        layout = output_dir / f"{edpr_json.stem}.layout.json"
        layout_report = output_dir / f"{edpr_json.stem}.layout.report.json"
        plot_report = output_dir / f"{edpr_json.stem}.plot.report.json"
        image = output_dir / f"{edpr_json.stem}.png"
        result = subprocess.run([sys.executable, str(TOOLS_DIR / "solution_to_layout.py"),
                                 "--solution", str(structured), "--output", str(layout),
                                 "--report", str(layout_report)], cwd=str(REPO_ROOT))
        knowloop_args.extend(["--layout-report", str(layout_report)])
        plot_failed = result.returncode != 0
        if not plot_failed:
            result = subprocess.run([sys.executable, str(TOOLS_DIR / "plot_design.py"),
                                     "--input", str(layout), "--output", str(image),
                                     "--report", str(plot_report)], cwd=str(REPO_ROOT))
            knowloop_args.extend(["--plot-report", str(plot_report)])
            plot_failed = result.returncode != 0
        if plot_failed:
            knowloop_args.extend(["--outcome-status", "failed"])
    run_command(knowloop_args)
    if plot_failed:
        raise SystemExit(1)

    print("")
    print("Pipeline complete.")
    print(f"Context package: {context_json}")
    print(f"Solution summary: {solution_path}")
    print(f"Knowloop candidate: {knowloop_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run or prepare the EDPR design pipeline.")
    parser.add_argument("--edpr-json", default=None, help="Existing EDPR JSON file to validate, retrieve, and solve.")
    parser.add_argument("--problem-text", default=None, help="Natural-language problem text to package for LLM EDPR parsing.")
    parser.add_argument("--problem-file", default=None, help="Text file containing natural-language problem text.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Directory for pipeline outputs.")
    parser.add_argument("--solution-format", choices=("md", "json"), default="md")
    parser.add_argument("--plot", action="store_true", help="Emit an EDAS study layout, plot QA and Knowloop visual feedback.")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    if args.edpr_json:
        run_existing_edpr(Path(args.edpr_json).resolve(), output_dir.resolve(), args.solution_format, args.plot)
        return 0

    problem_text = read_text_argument(args.problem_text, args.problem_file)
    prompt_path = prepare_parser_prompt(problem_text, output_dir.resolve())
    print(f"Prepared EDPR parser prompt: {prompt_path}")
    print("Next action: give this prompt to an LLM, save the returned EDPR JSON, then rerun with --edpr-json.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
