#!/usr/bin/env python3
"""Run the KEL v0.2 cycle with atomic feedback grouping and v0.1 fallback."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
KEL_TOOLS = REPO_ROOT / "tools" / "kel"


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def slugify(value: str | None) -> str:
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "_", value or "kel_cycle").strip("_").lower()
    return slug or "kel_cycle"


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=True)
        handle.write("\n")


def repo_or_abs(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path.resolve())


def run_tool(args: list[str], dry_run: bool) -> dict[str, Any]:
    command = [sys.executable, *args]
    if dry_run:
        return {"command": command, "returncode": None, "stdout": "", "stderr": "", "dry_run": True}
    completed = subprocess.run(command, cwd=REPO_ROOT, text=True, capture_output=True)
    return {
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "dry_run": False,
    }


def require_success(step: dict[str, Any]) -> None:
    if step["returncode"] not in (0, None):
        print(step["stdout"], end="")
        print(step["stderr"], end="", file=sys.stderr)
        raise SystemExit(step["returncode"])


def add_optional(command: list[str], name: str, value: str | None) -> None:
    if value:
        command.extend([name, value])


def feedback_inputs(args: argparse.Namespace) -> list[tuple[str, str]]:
    return [("text", value) for value in args.feedback_text] + [("file", value) for value in args.feedback_file]


def record_step(summary: dict[str, Any], name: str, command: list[str], dry_run: bool) -> None:
    step = run_tool(command, dry_run)
    summary["steps"].append({"name": name, **step})
    require_success(step)


def build_cycle(args: argparse.Namespace) -> dict[str, Any]:
    label = slugify(args.cycle_id or args.label)
    output_dir = Path(args.output_dir or f"runs/kel_cycle/{label}_{utc_stamp()}")
    if not args.dry_run:
        output_dir.mkdir(parents=True, exist_ok=True)
    summary: dict[str, Any] = {
        "schema": "kel-cycle-run/0.2",
        "cycle_id": args.cycle_id or f"kel:cycle:{label}:{utc_stamp()}",
        "created_utc": utc_now(),
        "feedback_flow": "legacy_v0.1" if args.legacy_feedback_flow else "grouped_v0.2",
        "output_dir": repo_or_abs(output_dir),
        "steps": [],
        "artifacts": {
            "experience_record": None,
            "sufficiency_report": None,
            "feedback_records": [],
            "atomic_feedback_records": [],
            "feedback_groups": [],
            "graph_change_requests": [],
            "expert_reviews": [],
            "promoted_change_requests": [],
        },
        "notes": [],
    }

    experience_path = output_dir / "experience_record.json"
    command = [str(KEL_TOOLS / "create_kel_experience_record.py"), "--output", str(experience_path)]
    for name, value in (
        ("--edpr-json", args.edpr_json), ("--context-json", args.context_json),
        ("--solution-json", args.solution_json), ("--solution-md", args.solution_md),
        ("--layout-report", args.layout_report), ("--plot-report", args.plot_report),
        ("--plot-path", args.plot_path), ("--knowloop-json", args.knowloop_json),
        ("--experience-id", args.experience_id),
    ):
        add_optional(command, name, value)
    record_step(summary, "create_experience_record", command, args.dry_run)
    if args.dry_run:
        linked_experience_id = args.experience_id or "kel:experience:dry_run"
    else:
        linked_experience_id = str(load_json(experience_path)["experience_id"])
        summary["artifacts"]["experience_record"] = repo_or_abs(experience_path)

    sufficiency_path = output_dir / "sufficiency_report.json"
    command = [
        str(KEL_TOOLS / "evaluate_kg_sufficiency.py"), "--output", str(sufficiency_path),
        "--linked-experience-id", linked_experience_id,
    ]
    for name, value in (
        ("--edpr-json", args.edpr_json), ("--context-json", args.context_json),
        ("--solution-json", args.solution_json), ("--solution-md", args.solution_md),
    ):
        add_optional(command, name, value)
    record_step(summary, "evaluate_kg_sufficiency", command, args.dry_run)
    if not args.dry_run:
        summary["artifacts"]["sufficiency_report"] = repo_or_abs(sufficiency_path)

    feedback_paths: list[Path] = []
    for index, (kind, value) in enumerate(feedback_inputs(args), start=1):
        path = output_dir / "feedback_records" / f"feedback_{index:02d}_{kind}.json"
        command = [
            str(KEL_TOOLS / "convert_feedback_to_pmap_apf.py"), "--output", str(path),
            "--linked-experience-id", linked_experience_id, "--experience-json", str(experience_path),
        ]
        add_optional(command, "--edpr-json", args.edpr_json)
        command.extend(["--feedback-text" if kind == "text" else "--feedback-file", value])
        record_step(summary, f"convert_feedback_{index:02d}", command, args.dry_run)
        feedback_paths.append(path)
        if not args.dry_run:
            summary["artifacts"]["feedback_records"].append(repo_or_abs(path))

    gcr_paths: list[Path] = []
    if feedback_paths and args.legacy_feedback_flow:
        gcr_dir = output_dir / "graph_change_requests"
        command = [str(KEL_TOOLS / "generate_graph_change_request.py"), *map(str, feedback_paths), "--output-dir", str(gcr_dir)]
        record_step(summary, "generate_graph_change_requests", command, args.dry_run)
        if not args.dry_run:
            gcr_paths = sorted(gcr_dir.glob("*.json"))
    elif feedback_paths:
        atomic_dir = output_dir / "atomic_feedback_records"
        command = [str(KEL_TOOLS / "decompose_feedback.py"), *map(str, feedback_paths), "--output-dir", str(atomic_dir)]
        record_step(summary, "decompose_feedback", command, args.dry_run)
        atomic_paths = sorted(atomic_dir.glob("*.json")) if not args.dry_run else [atomic_dir / "<atomic-feedback-records>"]
        if not args.dry_run:
            summary["artifacts"]["atomic_feedback_records"] = [repo_or_abs(path) for path in atomic_paths]

        group_dir = output_dir / "feedback_groups"
        command = [str(KEL_TOOLS / "group_feedback.py"), *map(str, atomic_paths), "--output-dir", str(group_dir)]
        record_step(summary, "group_feedback", command, args.dry_run)
        group_paths = sorted(group_dir.glob("*.json")) if not args.dry_run else [group_dir / "<feedback-groups>"]
        if not args.dry_run:
            summary["artifacts"]["feedback_groups"] = [repo_or_abs(path) for path in group_paths]

        gcr_dir = output_dir / "graph_change_requests"
        command = [str(KEL_TOOLS / "generate_graph_change_request.py"), *map(str, group_paths), "--output-dir", str(gcr_dir)]
        record_step(summary, "generate_grouped_graph_change_requests", command, args.dry_run)
        if not args.dry_run:
            gcr_paths = sorted(gcr_dir.glob("*.json"))

    if not args.dry_run:
        summary["artifacts"]["graph_change_requests"] = [repo_or_abs(path) for path in gcr_paths]

    if args.review_decision:
        for gcr_path in gcr_paths:
            review_path = output_dir / "expert_reviews" / f"{gcr_path.stem}.review.json"
            command = [
                str(KEL_TOOLS / "create_expert_review_record.py"), "--change-request", str(gcr_path),
                "--decision", args.review_decision, "--reviewer", args.reviewer,
                "--decision-reason", args.decision_reason, "--output", str(review_path),
            ]
            add_optional(command, "--implementation-target", args.implementation_target)
            add_optional(command, "--implementation-reference", args.implementation_reference)
            record_step(summary, f"create_review_{gcr_path.stem}", command, args.dry_run)
            if not args.dry_run:
                summary["artifacts"]["expert_reviews"].append(repo_or_abs(review_path))
            if args.promote_status:
                promoted_path = output_dir / "promoted" / args.promote_status / f"{gcr_path.stem}.json"
                command = [
                    str(KEL_TOOLS / "promote_accepted_kel_change.py"), "--change-request", str(gcr_path),
                    "--review", str(review_path), "--status", args.promote_status, "--output", str(promoted_path),
                ]
                record_step(summary, f"promote_{gcr_path.stem}", command, args.dry_run)
                if not args.dry_run:
                    summary["artifacts"]["promoted_change_requests"].append(repo_or_abs(promoted_path))

    summary_path = output_dir / "kel_cycle_summary.json"
    if not args.dry_run:
        write_json(summary_path, summary)
    summary["artifacts"]["summary"] = repo_or_abs(summary_path)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the KEL v0.2 workflow wrapper.")
    parser.add_argument("--label", default=None)
    parser.add_argument("--cycle-id", default=None)
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--edpr-json", default=None)
    parser.add_argument("--context-json", default=None)
    parser.add_argument("--solution-json", default=None)
    parser.add_argument("--solution-md", default=None)
    parser.add_argument("--layout-report", default=None)
    parser.add_argument("--plot-report", default=None)
    parser.add_argument("--plot-path", default=None)
    parser.add_argument("--knowloop-json", default=None)
    parser.add_argument("--experience-id", default=None)
    parser.add_argument("--feedback-text", action="append", default=[])
    parser.add_argument("--feedback-file", action="append", default=[])
    parser.add_argument("--legacy-feedback-flow", action="store_true")
    parser.add_argument("--review-decision", choices=("accepted", "rejected", "needs_evidence", "needs_revision", "implemented", "superseded"))
    parser.add_argument("--reviewer", default=None)
    parser.add_argument("--decision-reason", default=None)
    parser.add_argument("--implementation-target", default=None)
    parser.add_argument("--implementation-reference", default=None)
    parser.add_argument("--promote-status", choices=("accepted", "implemented", "rejected", "needs_evidence", "needs_revision", "superseded"))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.solution_json and args.solution_md:
        parser.error("Use either --solution-json or --solution-md, not both")
    if args.review_decision and not args.reviewer:
        parser.error("--review-decision requires --reviewer")
    if args.review_decision and not args.decision_reason:
        parser.error("--review-decision requires --decision-reason")
    if args.promote_status and not args.review_decision:
        parser.error("--promote-status requires --review-decision")
    allowed_statuses = {
        "accepted": {"accepted", "implemented"},
        "implemented": {"implemented"},
        "rejected": {"rejected"},
        "needs_evidence": {"needs_evidence"},
        "needs_revision": {"needs_revision"},
        "superseded": {"superseded"},
    }
    if args.promote_status and args.promote_status not in allowed_statuses[args.review_decision]:
        parser.error("--promote-status conflicts with --review-decision")
    if args.promote_status == "implemented" and not args.implementation_reference:
        parser.error("--promote-status implemented requires --implementation-reference")
    summary = build_cycle(args)
    print(json.dumps({
        "status": "dry_run" if args.dry_run else "complete",
        "step_count": len(summary["steps"]),
        "feedback_flow": summary["feedback_flow"],
        "summary": summary["artifacts"]["summary"],
        "steps": summary["steps"] if args.dry_run else None,
    }, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
