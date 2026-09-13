#!/usr/bin/env python3
"""
Run the KEL v0.1 workflow wrapper for one design-query cycle.

The wrapper orchestrates existing KEL tools. It intentionally does not invent
reviews or promotions unless an explicit expert decision is supplied.
"""

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


def slugify(value: str | None) -> str:
    raw = value or "kel_cycle"
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "_", raw).strip("_").lower()
    return slug or "kel_cycle"


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=True)
        f.write("\n")


def repo_or_abs(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(REPO_ROOT))
    except ValueError:
        return str(resolved)


def run_tool(args: list[str], dry_run: bool = False) -> dict[str, Any]:
    command = [sys.executable, *args]
    if dry_run:
        return {
            "command": command,
            "returncode": None,
            "stdout": "",
            "stderr": "",
            "dry_run": True,
        }
    completed = subprocess.run(command, cwd=str(REPO_ROOT), text=True, capture_output=True)
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


def add_optional_file_arg(command: list[str], name: str, value: str | None) -> None:
    if value:
        command.extend([name, value])


def feedback_inputs(args: argparse.Namespace) -> list[tuple[str, str]]:
    items: list[tuple[str, str]] = []
    for text in args.feedback_text or []:
        items.append(("text", text))
    for path in args.feedback_file or []:
        items.append(("file", path))
    return items


def feedback_output_path(output_dir: Path, index: int, kind: str) -> Path:
    return output_dir / "feedback_records" / f"feedback_{index:02d}_{kind}.json"


def review_output_path(output_dir: Path, change_request_path: Path) -> Path:
    return output_dir / "expert_reviews" / f"{change_request_path.stem}.review.json"


def promoted_output_path(output_dir: Path, change_request_path: Path, status: str) -> Path:
    return output_dir / "promoted" / status / f"{change_request_path.stem}.json"


def build_cycle(args: argparse.Namespace) -> dict[str, Any]:
    label = slugify(args.cycle_id or args.label or "kel_cycle")
    output_dir = Path(args.output_dir or f"runs/kel_cycle/{label}_{utc_stamp()}")
    if not args.dry_run:
        output_dir.mkdir(parents=True, exist_ok=True)

    summary: dict[str, Any] = {
        "schema": "kel-cycle-run/0.1",
        "cycle_id": args.cycle_id or f"kel:cycle:{label}:{utc_stamp()}",
        "created_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "output_dir": repo_or_abs(output_dir),
        "steps": [],
        "artifacts": {
            "experience_record": None,
            "sufficiency_report": None,
            "feedback_records": [],
            "graph_change_requests": [],
            "expert_reviews": [],
            "promoted_change_requests": [],
        },
        "notes": [],
    }

    experience_path = output_dir / "experience_record.json"
    experience_cmd = [str(KEL_TOOLS / "create_kel_experience_record.py"), "--output", str(experience_path)]
    add_optional_file_arg(experience_cmd, "--edpr-json", args.edpr_json)
    add_optional_file_arg(experience_cmd, "--context-json", args.context_json)
    add_optional_file_arg(experience_cmd, "--solution-json", args.solution_json)
    add_optional_file_arg(experience_cmd, "--solution-md", args.solution_md)
    add_optional_file_arg(experience_cmd, "--layout-report", args.layout_report)
    add_optional_file_arg(experience_cmd, "--plot-report", args.plot_report)
    add_optional_file_arg(experience_cmd, "--plot-path", args.plot_path)
    add_optional_file_arg(experience_cmd, "--knowloop-json", args.knowloop_json)
    if args.experience_id:
        experience_cmd.extend(["--experience-id", args.experience_id])
    step = run_tool(experience_cmd, args.dry_run)
    summary["steps"].append({"name": "create_experience_record", **step})
    require_success(step)
    if not args.dry_run:
        summary["artifacts"]["experience_record"] = repo_or_abs(experience_path)
        experience = load_json(experience_path)
        linked_experience_id = experience["experience_id"]
    else:
        linked_experience_id = args.experience_id or "kel:experience:dry_run"

    sufficiency_path = output_dir / "sufficiency_report.json"
    suff_cmd = [str(KEL_TOOLS / "evaluate_kg_sufficiency.py"), "--output", str(sufficiency_path), "--linked-experience-id", linked_experience_id]
    add_optional_file_arg(suff_cmd, "--edpr-json", args.edpr_json)
    add_optional_file_arg(suff_cmd, "--context-json", args.context_json)
    add_optional_file_arg(suff_cmd, "--solution-json", args.solution_json)
    add_optional_file_arg(suff_cmd, "--solution-md", args.solution_md)
    step = run_tool(suff_cmd, args.dry_run)
    summary["steps"].append({"name": "evaluate_kg_sufficiency", **step})
    require_success(step)
    if not args.dry_run:
        summary["artifacts"]["sufficiency_report"] = repo_or_abs(sufficiency_path)

    feedback_paths: list[Path] = []
    for index, (kind, value) in enumerate(feedback_inputs(args), start=1):
        feedback_path = feedback_output_path(output_dir, index, kind)
        fb_cmd = [str(KEL_TOOLS / "convert_feedback_to_pmap_apf.py"), "--output", str(feedback_path), "--linked-experience-id", linked_experience_id]
        add_optional_file_arg(fb_cmd, "--edpr-json", args.edpr_json)
        fb_cmd.extend(["--experience-json", str(experience_path)])
        if kind == "text":
            fb_cmd.extend(["--feedback-text", value])
        else:
            fb_cmd.extend(["--feedback-file", value])
        step = run_tool(fb_cmd, args.dry_run)
        summary["steps"].append({"name": f"convert_feedback_{index:02d}", **step})
        require_success(step)
        feedback_paths.append(feedback_path)
        if not args.dry_run:
            summary["artifacts"]["feedback_records"].append(repo_or_abs(feedback_path))

    gcr_paths: list[Path] = []
    if feedback_paths:
        gcr_dir = output_dir / "graph_change_requests"
        gcr_cmd = [str(KEL_TOOLS / "generate_graph_change_request.py"), *[str(path) for path in feedback_paths], "--output-dir", str(gcr_dir)]
        step = run_tool(gcr_cmd, args.dry_run)
        summary["steps"].append({"name": "generate_graph_change_requests", **step})
        require_success(step)
        if not args.dry_run:
            gcr_paths = sorted(gcr_dir.glob("*.json"))
            summary["artifacts"]["graph_change_requests"] = [repo_or_abs(path) for path in gcr_paths]

    if args.review_decision:
        if not gcr_paths and not args.dry_run:
            summary["notes"].append("Review decision supplied, but no graph change requests were generated.")
        for gcr_path in gcr_paths:
            review_path = review_output_path(output_dir, gcr_path)
            review_cmd = [
                str(KEL_TOOLS / "create_expert_review_record.py"),
                "--change-request",
                str(gcr_path),
                "--decision",
                args.review_decision,
                "--output",
                str(review_path),
            ]
            if args.reviewer:
                review_cmd.extend(["--reviewer", args.reviewer])
            if args.decision_reason:
                review_cmd.extend(["--decision-reason", args.decision_reason])
            if args.implementation_reference:
                review_cmd.extend(["--implementation-reference", args.implementation_reference])
            if args.implementation_target:
                review_cmd.extend(["--implementation-target", args.implementation_target])
            step = run_tool(review_cmd, args.dry_run)
            summary["steps"].append({"name": f"create_review_{gcr_path.stem}", **step})
            require_success(step)
            if not args.dry_run:
                summary["artifacts"]["expert_reviews"].append(repo_or_abs(review_path))

            if args.promote_status:
                promoted_path = promoted_output_path(output_dir, gcr_path, args.promote_status)
                promote_cmd = [
                    str(KEL_TOOLS / "promote_accepted_kel_change.py"),
                    "--change-request",
                    str(gcr_path),
                    "--review",
                    str(review_path),
                    "--status",
                    args.promote_status,
                    "--output",
                    str(promoted_path),
                ]
                step = run_tool(promote_cmd, args.dry_run)
                summary["steps"].append({"name": f"promote_{gcr_path.stem}", **step})
                require_success(step)
                if not args.dry_run:
                    summary["artifacts"]["promoted_change_requests"].append(repo_or_abs(promoted_path))

    summary_path = output_dir / "kel_cycle_summary.json"
    if not args.dry_run:
        write_json(summary_path, summary)
    else:
        summary["artifacts"]["summary"] = repo_or_abs(summary_path)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the KEL v0.1 workflow wrapper.")
    parser.add_argument("--label", default=None, help="Human-readable run label used in output path.")
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
    parser.add_argument("--review-decision", choices=("accepted", "rejected", "needs_evidence", "needs_revision", "implemented", "superseded"), default=None)
    parser.add_argument("--reviewer", default=None)
    parser.add_argument("--decision-reason", default=None)
    parser.add_argument("--implementation-target", default=None)
    parser.add_argument("--implementation-reference", default=None)
    parser.add_argument("--promote-status", choices=("accepted", "implemented", "rejected", "needs_evidence", "needs_revision", "superseded"), default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.solution_json and args.solution_md:
        raise SystemExit("Use either --solution-json or --solution-md, not both.")
    if args.promote_status and not args.review_decision:
        raise SystemExit("--promote-status requires --review-decision.")
    if args.review_decision and not str(args.reviewer or "").strip():
        raise SystemExit("--review-decision requires --reviewer.")
    if args.review_decision and not str(args.decision_reason or "").strip():
        raise SystemExit("--review-decision requires --decision-reason.")
    allowed_statuses = {
        "accepted": {"accepted", "implemented"},
        "implemented": {"implemented"},
        "rejected": {"rejected"},
        "needs_evidence": {"needs_evidence"},
        "needs_revision": {"needs_revision"},
        "superseded": {"superseded"},
    }
    if args.promote_status and args.promote_status not in allowed_statuses[args.review_decision]:
        raise SystemExit("--promote-status conflicts with --review-decision.")
    if args.promote_status == "implemented" and not str(args.implementation_reference or "").strip():
        raise SystemExit("--promote-status implemented requires --implementation-reference.")

    summary = build_cycle(args)
    print(json.dumps({
        "status": "dry_run" if args.dry_run else "completed",
        "cycle_id": summary["cycle_id"],
        "output_dir": summary["output_dir"],
        "artifacts": summary["artifacts"],
        "step_count": len(summary["steps"]),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
