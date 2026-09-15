#!/usr/bin/env python3
"""Run the authoritative governed EDPR design workflow.

This wrapper is the user-facing entry point for design/layout/plot emission.
It applies KEL intent gates before the lower-level EDPR pipeline, stamps every
report with design-governance status, and records the human user's remaining
actions at the start and after each governed stage.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = REPO_ROOT / "tools"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "runs"
AUTHORITY = "tools/run_design_workflow.py"

sys.path.insert(0, str(TOOLS_DIR))
from design_rules_v02 import extract_design_intent, validate_layout_against_intent, workflow_blockers  # noqa: E402


def _as_rel(path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _human_actions(stage: str, status: str, blockers: list[dict[str, Any]] | None = None) -> list[str]:
    blockers = blockers or []
    if stage == "start":
        return [
            "Review the EDPR/problem understanding before accepting any design, layout, or plot output.",
            "Provide missing engineering inputs when a gate reports a blocking requirement.",
            "Treat direct plotter outputs without this governance stamp as non-authoritative study visuals.",
        ]
    if status == "blocked":
        actions = [str(item.get("required_action") or item.get("message") or item.get("code")) for item in blockers]
        return [item for item in actions if item] or ["Resolve the listed blocking gates, then rerun the governed workflow."]
    if stage == "edpr_gate":
        return ["Confirm that the EDPR matches the user request and that APF/P-map intent is complete before relying on the solver output."]
    if stage == "retrieval_and_solution":
        return ["Review retrieved EDES/EDAS/EDIKB evidence, residual risks, and unsupported comparisons before accepting the recommended candidate."]
    if stage == "layout_gate":
        return ["Review the EDAS layout report and confirm that mandatory GD-ST/GD-SB/branch/shroud gates remain satisfied."]
    if stage == "plot_gate":
        return ["Review the plot, plot report, and parameter CSV sidecar; use the CSV for dimensions rather than relying on dense figure annotations."]
    return ["Review the governed report before using the result outside conceptual study work."]


def _stage(stage: str, status: str, blockers: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return {
        "stage": stage,
        "status": status,
        "blocking_gates": blockers or [],
        "human_remaining_actions": _human_actions(stage, status, blockers),
    }


def _artifact_paths(edpr_json: Path, output_dir: Path) -> dict[str, Path]:
    stem = edpr_json.stem
    return {
        "retrieval_context": output_dir / f"{stem}.retrieval_context.json",
        "solution_json": output_dir / f"{stem}.solution.json",
        "solution_md": output_dir / f"{stem}.solution.md",
        "layout": output_dir / f"{stem}.layout.json",
        "layout_report": output_dir / f"{stem}.layout.report.json",
        "plot_image": output_dir / f"{stem}.png",
        "plot_report": output_dir / f"{stem}.plot.report.json",
        "parameter_csv": output_dir / f"{stem}.parameters.csv",
        "knowloop_candidate": output_dir / f"{stem}.knowloop_candidate.json",
        "governance_report": output_dir / f"{stem}.design_governance.json",
    }


def _existing_artifacts(paths: dict[str, Path]) -> dict[str, str]:
    return {name: _as_rel(path) for name, path in paths.items() if path.exists()}


def _stamp(
    *,
    status: str,
    allowed_output: str,
    blockers: list[dict[str, Any]],
    stage_reports: list[dict[str, Any]],
    artifacts: dict[str, str],
    pipeline_returncode: int | None = None,
) -> dict[str, Any]:
    return {
        "authority": AUTHORITY,
        "status": status,
        "allowed_output": allowed_output,
        "edpr_confirmed": not any(item.get("code") == "EDPR_CONFIRMATION_REQUIRED" for item in blockers),
        "retrieval_completed": "retrieval_context" in artifacts,
        "solution_completed": "solution_json" in artifacts or "solution_md" in artifacts,
        "layout_gate_checked": any(item["stage"] == "layout_gate" for item in stage_reports),
        "plot_gate_checked": any(item["stage"] == "plot_gate" for item in stage_reports),
        "blocking_gates": blockers,
        "human_remaining_actions": stage_reports[-1]["human_remaining_actions"] if stage_reports else _human_actions("start", "pending"),
        "stage_reports": stage_reports,
        "artifacts": artifacts,
        "pipeline_returncode": pipeline_returncode,
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    os.makedirs(path.parent, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _stamp_report(path: Path, stamp: dict[str, Any]) -> None:
    if not path.exists():
        return
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return
    if isinstance(payload, dict):
        payload["design_governance"] = stamp
        _write_json(path, payload)


def _run_pipeline(edpr_json: Path, output_dir: Path, solution_format: str, plot: bool) -> int:
    command = [
        sys.executable,
        str(TOOLS_DIR / "run_edpr_pipeline.py"),
        "--edpr-json",
        str(edpr_json),
        "--output-dir",
        str(output_dir),
        "--solution-format",
        solution_format,
    ]
    if plot:
        command.append("--plot")
    completed = subprocess.run(command, cwd=str(REPO_ROOT), text=True)
    return completed.returncode


def run(args: argparse.Namespace) -> int:
    edpr_json = Path(args.edpr_json).resolve()
    output_dir = Path(args.output_dir).resolve()
    os.makedirs(output_dir, exist_ok=True)
    paths = _artifact_paths(edpr_json, output_dir)
    stage_reports = [_stage("start", "pending")]

    try:
        edpr = json.loads(edpr_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        blockers = [{"code": "EDPR_READ_FAILED", "status": "failed", "required_action": str(exc)}]
        stage_reports.append(_stage("edpr_gate", "blocked", blockers))
        stamp = _stamp(status="blocked", allowed_output="gap_report_only", blockers=blockers, stage_reports=stage_reports, artifacts={})
        _write_json(paths["governance_report"], stamp)
        print(json.dumps({"status": "blocked", "governance_report": str(paths["governance_report"]), "blocking_gates": blockers}))
        return 1

    intent = extract_design_intent(edpr)
    blockers = workflow_blockers(intent)
    if blockers:
        stage_reports.append(_stage("edpr_gate", "blocked", blockers))
        stamp = _stamp(status="blocked", allowed_output="gap_report_only", blockers=blockers, stage_reports=stage_reports, artifacts={})
        stamp["design_intent"] = intent
        _write_json(paths["governance_report"], stamp)
        print(json.dumps({"status": "blocked", "governance_report": str(paths["governance_report"]), "blocking_gates": blockers}))
        return 1

    stage_reports.append(_stage("edpr_gate", "passed"))
    returncode = _run_pipeline(edpr_json, output_dir, args.solution_format, args.plot)
    artifacts = _existing_artifacts(paths)
    solution_done = "solution_json" in artifacts or "solution_md" in artifacts
    stage_reports.append(_stage("retrieval_and_solution", "passed" if returncode == 0 and solution_done else "failed"))

    layout_blockers: list[dict[str, Any]] = []
    if paths["layout"].exists():
        try:
            layout = json.loads(paths["layout"].read_text(encoding="utf-8"))
            layout_blockers = validate_layout_against_intent(layout, intent)
        except (OSError, json.JSONDecodeError, TypeError) as exc:
            layout_blockers = [{"code": "LAYOUT_GATE_READ_FAILED", "status": "failed", "required_action": str(exc)}]
        stage_reports.append(_stage("layout_gate", "blocked" if layout_blockers else "passed", layout_blockers))
    elif args.plot or returncode != 0:
        stage_reports.append(_stage("layout_gate", "blocked", [{"code": "LAYOUT_NOT_EMITTED", "status": "failed", "required_action": "Resolve earlier workflow errors before relying on layout or plot output."}]))

    plot_blockers: list[dict[str, Any]] = []
    if args.plot:
        if paths["plot_report"].exists():
            try:
                plot_report = json.loads(paths["plot_report"].read_text(encoding="utf-8"))
                if plot_report.get("errors"):
                    plot_blockers = [{"code": "PLOT_REPORT_ERRORS", "status": "failed", "errors": plot_report.get("errors"), "required_action": "Fix the plot report errors and rerun the governed workflow."}]
            except (OSError, json.JSONDecodeError) as exc:
                plot_blockers = [{"code": "PLOT_REPORT_READ_FAILED", "status": "failed", "required_action": str(exc)}]
        else:
            plot_blockers = [{"code": "PLOT_REPORT_NOT_EMITTED", "status": "failed", "required_action": "Resolve layout or plot execution errors before accepting the visual output."}]
        stage_reports.append(_stage("plot_gate", "blocked" if plot_blockers else "passed", plot_blockers))

    all_blockers = layout_blockers + plot_blockers
    if returncode != 0 and not all_blockers:
        all_blockers = [{"code": "PIPELINE_FAILED", "status": "failed", "required_action": "Inspect the lower-level pipeline output and rerun after correction."}]
    status = "passed" if returncode == 0 and not all_blockers else "blocked"
    allowed = "design_layout_and_plot" if status == "passed" and args.plot else "design_solution" if status == "passed" else "gap_report_only"
    artifacts = _existing_artifacts(paths)
    stamp = _stamp(status=status, allowed_output=allowed, blockers=all_blockers, stage_reports=stage_reports, artifacts=artifacts, pipeline_returncode=returncode)
    stamp["design_intent"] = intent
    _write_json(paths["governance_report"], stamp)
    _stamp_report(paths["layout_report"], stamp)
    _stamp_report(paths["plot_report"], stamp)
    print(json.dumps({"status": status, "allowed_output": allowed, "governance_report": str(paths["governance_report"]), "blocking_gates": all_blockers}))
    return 0 if status == "passed" else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--edpr-json", required=True, help="Confirmed EDPR JSON file to run through governed workflow.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Directory for governed workflow outputs.")
    parser.add_argument("--solution-format", choices=("md", "json"), default="json")
    parser.add_argument("--plot", action="store_true", help="Emit governed layout, plot, plot report, and parameter CSV.")
    return run(parser.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
