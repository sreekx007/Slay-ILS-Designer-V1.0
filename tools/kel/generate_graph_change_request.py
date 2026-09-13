#!/usr/bin/env python3
"""
Generate KEL graph change requests from KEL feedback-to-P-map/APF records.

This is a deterministic first-pass bridge from querier feedback to expert
review. It does not implement changes. It creates pending change requests with
target layer, change type, proposed action, evidence requirement, and priority.
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
VALIDATOR = REPO_ROOT / "tools" / "kel" / "validate_kel_record.py"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=True)
        f.write("\n")


def slugify(value: str | None) -> str:
    raw = value or "change"
    slug = re.sub(r"[^A-Za-z0-9_.:-]+", "_", raw).strip("_").lower()
    return slug or "change"


def short_issue(text: str, limit: int = 300) -> str:
    cleaned = " ".join(text.split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 3].rstrip() + "..."


def infer_target_and_type(feedback: dict[str, Any]) -> tuple[str, str]:
    feedback_type = str(feedback.get("feedback_type") or "")
    raw = str(feedback.get("raw_feedback_text") or "").lower()
    structured = feedback.get("structured_feedback") if isinstance(feedback.get("structured_feedback"), dict) else {}
    apf_action = str(structured.get("apf_action") or "").lower()

    if "must use repo plotter" in raw or "freehand" in raw or "workflow" in raw or "non-authoritative" in raw:
        return "KEL", "new_workflow_gate"
    if feedback_type == "answer_format_requirement":
        return "KEL", "new_output_policy"
    if feedback_type == "design_objective_requirement":
        return "EDPR", "new_design_guidance"
    if feedback_type == "default_assumption":
        if "branch connector" in raw or "ea-st" in raw:
            return "EDAS", "new_assembly_constraint"
        if "valve" in raw and ("ea-sb" in raw or "roller" in raw or "contact load" in raw):
            return "EDAS", "new_assembly_constraint"
        return "EDPR", "new_design_guidance"
    if "z-shaped" in raw or "z branch" in raw or "vertical connector" in raw:
        return "EDAS", "new_assembly_constraint"
    if "ea-st" in raw or "ea-sb" in raw or "connector" in raw or "connections" in raw:
        return "EDAS", "new_assembly_constraint"
    if "two branch valve" in raw or "two branch valves" in raw:
        return "Tools", "new_tool_capability"
    if "plot" in raw or "plotter" in raw or "drawing" in raw or "picture" in raw or "label" in raw or "scale" in raw:
        return "Plotters", "new_plotting_rule"
    if "evidence" in raw or "fea" in raw or "ml" in raw or "future" in raw:
        return "EDIKB", "future_fea_study"
    if "plot" in apf_action:
        return "Plotters", "new_plotting_rule"
    return "Docs", "new_design_guidance"


def evidence_requirement_for(target_layer: str, change_type: str, feedback: dict[str, Any]) -> str:
    raw = str(feedback.get("raw_feedback_text") or "")
    if change_type == "new_workflow_gate":
        return "Demonstrate one design query executed through EDPR/P-map/APF, retrieval, EDAS layout build, builder findings, and repository plotter output or explicit representability gap."
    if change_type == "new_output_policy":
        return "Provide before/after answer examples showing the required presentation rule and validate that KEL feedback trace remains linked."
    if change_type == "new_tool_capability":
        return "Add a buildable example and regression test showing the requested capability can be represented, built, plotted, and reported."
    if target_layer == "EDAS":
        return "Provide an EDAS layout example, successful build_ils validation, declared associations, and plotter output demonstrating the rule."
    if target_layer == "EDES":
        return "Provide the relevant EDES component parameter/constraint update, schema validation, and a component or assembly plot example."
    if target_layer == "Plotters":
        return "Provide before/after plot output, plot report, and regression coverage for labels, scale, and represented connections."
    if target_layer == "EDPR":
        return "Provide EDPR parser example input/output and P-map/APF checks showing the new objective, rule, or assumption is captured."
    if target_layer == "EDIKB":
        return "Provide traceable evidence, source case, FEA plan, or ML study parameters before promotion to behavior knowledge."
    return f"Expert review must confirm the feedback is reusable framework knowledge: {short_issue(raw, 160)}"


def proposed_change_for(target_layer: str, change_type: str, feedback: dict[str, Any]) -> str:
    raw = str(feedback.get("raw_feedback_text") or "")
    structured = feedback.get("structured_feedback") if isinstance(feedback.get("structured_feedback"), dict) else {}
    apf_action = structured.get("apf_action")
    issue = structured.get("pmap_issue") or raw
    if change_type == "new_workflow_gate":
        return "Add a KEL/LLM gate requiring EDPR/P-map/APF, EDES/EDAS/EDIKB retrieval, buildable EDAS layout JSON, builder findings, and repository plotter use before presenting design geometry."
    if "z-shaped" in raw.lower() or "z branch" in raw.lower() or "vertical connector" in raw.lower():
        return "Update EDPR/EDAS layout selection so a vertical connector maps to GD-B variant Z and an appropriate ILT-Z standard layout anchor before plotting."
    if "ea-sb" in raw.lower() and "valve" in raw.lower():
        return "Add a reusable assembly rule that inline valves needing roller/contact-load protection should trigger EA-SB protection or an explicit unresolved design assumption."
    if "ea-st" in raw.lower():
        return "Add or strengthen EDAS/plotter requirements to show GD-ST parameters, active connector slots, branch-to-top/side association, and pipe-side connection points."
    if "ea-sb" in raw.lower():
        return "Add or strengthen EDES/plotter requirements so GD-SB is drawn from EDES parameters rather than a generic protection-frame symbol."
    if "two branch valve" in raw.lower() or "two branch valves" in raw.lower():
        return "Extend branch layout representation so two distinct branch valve stations can be represented, built, plotted, and linked to branch piping connections."
    return f"Review and implement APF action `{apf_action}` for observed issue: {short_issue(str(issue), 220)}"


def build_change_request(feedback: dict[str, Any], explicit_id: str | None = None) -> dict[str, Any]:
    if feedback.get("schema") != "kel-feedback-to-pmap-apf/0.1":
        raise ValueError("Input must be a kel-feedback-to-pmap-apf/0.1 record")

    target_layer, change_type = infer_target_and_type(feedback)
    feedback_id = str(feedback.get("feedback_id") or "unlinked")
    structured = feedback.get("structured_feedback") if isinstance(feedback.get("structured_feedback"), dict) else {}
    priority = structured.get("priority") if structured.get("priority") in {"low", "medium", "high"} else "medium"
    if target_layer in {"EDAS", "Plotters", "Tools"} and change_type in {"new_assembly_constraint", "new_tool_capability"}:
        priority = "high"
    change_request_id = explicit_id or f"kel:change:{slugify(feedback_id.replace('kel:feedback:', ''))}"

    return {
        "schema": "kel-graph-change-request/0.1",
        "change_request_id": change_request_id,
        "status": "pending",
        "created_utc": utc_now(),
        "linked_experience_id": str(feedback.get("linked_experience_id") or "kel:experience:unlinked"),
        "linked_feedback_id": feedback_id,
        "target_layer": target_layer,
        "change_type": change_type,
        "problem_observed": short_issue(str(feedback.get("raw_feedback_text") or structured.get("pmap_issue") or "")),
        "proposed_change": proposed_change_for(target_layer, change_type, feedback),
        "evidence_requirement": evidence_requirement_for(target_layer, change_type, feedback),
        "priority": str(priority),
        "expert_review_ref": None,
        "implementation_ref": None,
    }


def validate_outputs(paths: list[Path]) -> None:
    if not paths or not VALIDATOR.exists():
        return
    completed = subprocess.run([sys.executable, str(VALIDATOR), *[str(path) for path in paths]], cwd=str(REPO_ROOT), text=True)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def output_path_for(feedback_path: Path, output_dir: Path) -> Path:
    stem = feedback_path.stem
    if stem.startswith("Q1_"):
        return output_dir / f"{stem.replace('Q1_', 'Q1_GCR_', 1)}.json"
    return output_dir / f"{stem}.graph_change_request.json"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate KEL graph change request JSON from KEL feedback records.")
    parser.add_argument("feedback_records", nargs="+", help="KEL feedback JSON record(s).")
    parser.add_argument("--output", "-o", default=None, help="Output file for a single feedback input.")
    parser.add_argument("--output-dir", default="knowledge/kel/graph_change_requests/pending", help="Output directory for one or more records.")
    parser.add_argument("--change-request-id", default=None, help="Explicit change request id; only valid with one input.")
    parser.add_argument("--no-validate", action="store_true")
    args = parser.parse_args()

    feedback_paths = [Path(item) for item in args.feedback_records]
    if args.output and len(feedback_paths) != 1:
        raise SystemExit("--output can only be used with one feedback record.")
    if args.change_request_id and len(feedback_paths) != 1:
        raise SystemExit("--change-request-id can only be used with one feedback record.")

    output_paths: list[Path] = []
    for feedback_path in feedback_paths:
        feedback = load_json(feedback_path)
        record = build_change_request(feedback, args.change_request_id)
        output_path = Path(args.output) if args.output else output_path_for(feedback_path, Path(args.output_dir))
        write_json(output_path, record)
        output_paths.append(output_path)

    if not args.no_validate:
        validate_outputs(output_paths)

    print(f"KEL graph change request(s) written: {len(output_paths)}")
    for path in output_paths:
        record = load_json(path)
        print(f"- {path}: {record['target_layer']} / {record['change_type']} / {record['priority']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
