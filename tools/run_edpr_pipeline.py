#!/usr/bin/env python3
"""
Run the EDPR workflow for an existing EDPR JSON file, or prepare an LLM parser
prompt when only a natural-language problem statement is available.

Pipeline for existing EDPR JSON:
1. Validate EDPR JSON.
2. Retrieve EDES/EDAS/EDIKB context.
3. Produce a first-pass solution summary.

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
    manifest_path = REPO_ROOT / "framework_manifest_v0_2.json"
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


def run_existing_edpr(edpr_json: Path, output_dir: Path, solution_format: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    context_json = output_dir / f"{edpr_json.stem}.retrieval_context.json"
    solution_ext = "json" if solution_format == "json" else "md"
    solution_path = output_dir / f"{edpr_json.stem}.solution.{solution_ext}"

    validator = TOOLS_DIR / "EDPR_VALIDATOR.py"
    schema = REPO_ROOT / "schemas" / "EDPR_METASCHEMA.json"
    retrieve = TOOLS_DIR / "retrieve_context.py"
    solve = TOOLS_DIR / "solve_problem.py"

    for required in (validator, schema, retrieve, solve):
        if not required.exists():
            raise SystemExit(f"Missing required pipeline file: {required}")

    run_command([sys.executable, str(validator), "--schema", str(schema), str(edpr_json)])
    run_command([sys.executable, str(retrieve), str(edpr_json), "--output", str(context_json)])
    run_command([sys.executable, str(solve), str(context_json), "--format", solution_format, "--output", str(solution_path)])

    print("")
    print("Pipeline complete.")
    print(f"Context package: {context_json}")
    print(f"Solution summary: {solution_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run or prepare the EDPR design pipeline.")
    parser.add_argument("--edpr-json", default=None, help="Existing EDPR JSON file to validate, retrieve, and solve.")
    parser.add_argument("--problem-text", default=None, help="Natural-language problem text to package for LLM EDPR parsing.")
    parser.add_argument("--problem-file", default=None, help="Text file containing natural-language problem text.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Directory for pipeline outputs.")
    parser.add_argument("--solution-format", choices=("md", "json"), default="md")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    if args.edpr_json:
        run_existing_edpr(Path(args.edpr_json).resolve(), output_dir.resolve(), args.solution_format)
        return 0

    problem_text = read_text_argument(args.problem_text, args.problem_file)
    prompt_path = prepare_parser_prompt(problem_text, output_dir.resolve())
    print(f"Prepared EDPR parser prompt: {prompt_path}")
    print("Next action: give this prompt to an LLM, save the returned EDPR JSON, then rerun with --edpr-json.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
