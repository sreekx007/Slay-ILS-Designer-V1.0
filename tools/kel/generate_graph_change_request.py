#!/usr/bin/env python3
"""Generate v0.1 single-feedback or v0.2 grouped KEL graph change requests."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from feedback_v02 import infer_target_and_type, slugify


REPO_ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = REPO_ROOT / "tools" / "kel" / "validate_kel_record.py"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=True)
        handle.write("\n")


def short_issue(text: str, limit: int = 500) -> str:
    cleaned = " ".join(text.split())
    return cleaned if len(cleaned) <= limit else cleaned[: limit - 3].rstrip() + "..."


def infer_target_and_type_v01(feedback: dict[str, Any]) -> tuple[str, str]:
    raw = str(feedback.get("raw_feedback_text") or "")
    structured = feedback.get("structured_feedback") if isinstance(feedback.get("structured_feedback"), dict) else {}
    return infer_target_and_type(str(feedback.get("feedback_type") or "clarification"), raw, str(structured.get("apf_action") or ""))


def evidence_requirement_for(target_layer: str, change_type: str, text: str) -> str:
    if change_type == "new_workflow_gate":
        return "Demonstrate one design query through EDPR/P-map/APF, retrieval, EDAS layout build, builder findings, and repository plotter output or an explicit representation gap."
    if change_type == "new_output_policy":
        return "Provide before/after answer examples and verify that every source KEL feedback ID remains linked."
    if change_type == "new_tool_capability":
        return "Add a buildable example and regression test showing the requested capability can be represented, built, plotted, and reported."
    if target_layer == "EDAS":
        return "Provide an EDAS layout example, successful build validation, declared associations, and repository plotter output demonstrating the rule."
    if target_layer == "EDES":
        return "Provide the EDES parameter or constraint update, schema validation, and a component or assembly plot example."
    if target_layer == "Plotters":
        return "Provide before/after plot output, plot report, and regression coverage for represented geometry, labels, scale, and connections."
    if target_layer == "EDPR":
        return "Provide EDPR parser input/output and P-map/APF checks showing the objective, rule, assumption, or clarification is captured."
    if target_layer == "EDIKB":
        return "Provide traceable evidence, source case, or an FEA/ML study definition before promotion to behavior knowledge."
    return f"Expert review must confirm this is reusable framework knowledge: {short_issue(text, 180)}"


def proposed_change_for(target_layer: str, change_type: str, text: str, action: str) -> str:
    lower = text.lower()
    if change_type == "new_workflow_gate":
        return "Require EDPR/P-map/APF, EDES/EDAS/EDIKB retrieval, buildable EDAS layout JSON, builder findings, and repository plotter use before presenting authoritative geometry."
    if "vertical connector" in lower or "z-shaped" in lower or "z branch" in lower:
        return "Map a vertical connector to GD-B variant Z and a compatible ILT-Z standard-layout anchor before plotting."
    if "ea-st" in lower or "gd-st" in lower or "branch connector" in lower:
        return "Expose GD-ST parameters, active connector slots, pipe-side landings, and branch-to-top or branch-to-side associations in the layout, plot, and report."
    if ("ea-sb" in lower or "gd-sb" in lower or "base structure" in lower) and "valve" in lower:
        return "Require valve protection to use actual GD-SB geometry and explicit dimensions, contact ownership, connectors, associations, and evidence or unresolved assumptions."
    if "two branch valve" in lower or "two branch valves" in lower:
        return "Represent two distinct branch valve stations end to end with stable IDs, branch ownership, piping connections, plots, and reports."
    return f"Implement `{action}` for the grouped issue after expert review: {short_issue(text, 260)}"


def build_v01(feedback: dict[str, Any], explicit_id: str | None = None) -> dict[str, Any]:
    target_layer, change_type = infer_target_and_type_v01(feedback)
    feedback_id = str(feedback.get("feedback_id") or "kel:feedback:unlinked")
    structured = feedback.get("structured_feedback") if isinstance(feedback.get("structured_feedback"), dict) else {}
    raw = str(feedback.get("raw_feedback_text") or structured.get("pmap_issue") or "")
    priority = str(structured.get("priority") or "medium")
    if target_layer in {"EDAS", "Plotters", "Tools"} and change_type in {"new_assembly_constraint", "new_tool_capability"}:
        priority = "high"
    change_id = explicit_id or f"kel:change:{slugify(feedback_id.removeprefix('kel:feedback:'))}"
    action = str(structured.get("apf_action") or "expert_review_required")
    return {
        "schema": "kel-graph-change-request/0.1",
        "change_request_id": change_id,
        "status": "pending",
        "created_utc": utc_now(),
        "linked_experience_id": str(feedback.get("linked_experience_id") or "kel:experience:unlinked"),
        "linked_feedback_id": feedback_id,
        "target_layer": target_layer,
        "change_type": change_type,
        "problem_observed": short_issue(raw),
        "proposed_change": proposed_change_for(target_layer, change_type, raw, action),
        "evidence_requirement": evidence_requirement_for(target_layer, change_type, raw),
        "priority": priority,
        "expert_review_ref": None,
        "implementation_ref": None,
    }


def build_v02(group: dict[str, Any], explicit_id: str | None = None) -> dict[str, Any]:
    text = str(group.get("canonical_issue") or "")
    action = str(group.get("canonical_action") or "expert_review_required")
    target_layer = str(group["target_layer"])
    change_type = str(group["change_type"])
    change_id = explicit_id or f"kel:change:{slugify(str(group['group_key']))}"
    return {
        "schema": "kel-graph-change-request/0.2",
        "change_request_id": change_id,
        "status": "pending",
        "created_utc": utc_now(),
        "linked_experience_ids": list(group["linked_experience_ids"]),
        "linked_feedback_ids": list(group["member_feedback_ids"]),
        "feedback_group_id": str(group["feedback_group_id"]),
        "target_layer": target_layer,
        "change_type": change_type,
        "problem_observed": short_issue(text),
        "proposed_change": proposed_change_for(target_layer, change_type, text, action),
        "evidence_requirement": evidence_requirement_for(target_layer, change_type, text),
        "priority": str(group.get("priority") or "medium"),
        "expert_review_ref": None,
        "implementation_ref": None,
        "superseded_by": None,
    }


def build_change_request(record: dict[str, Any], explicit_id: str | None = None) -> dict[str, Any]:
    schema = record.get("schema")
    if schema == "kel-feedback-to-pmap-apf/0.1":
        return build_v01(record, explicit_id)
    if schema == "kel-feedback-group/0.2":
        return build_v02(record, explicit_id)
    raise ValueError("Input must be kel-feedback-to-pmap-apf/0.1 or kel-feedback-group/0.2")


def validate_outputs(paths: list[Path]) -> None:
    completed = subprocess.run([sys.executable, str(VALIDATOR), *map(str, paths)], cwd=REPO_ROOT, text=True)
    if completed.returncode:
        raise SystemExit(completed.returncode)


def output_path_for(input_path: Path, output_dir: Path, record: dict[str, Any]) -> Path:
    if record.get("schema") == "kel-feedback-group/0.2":
        return output_dir / f"{record['group_key']}.graph_change_request.json"
    stem = input_path.stem
    if stem.startswith("Q1_"):
        stem = stem.replace("Q1_", "Q1_GCR_", 1)
    return output_dir / f"{stem}.graph_change_request.json"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate KEL graph change requests from feedback or groups.")
    parser.add_argument("feedback_records", nargs="+")
    parser.add_argument("--output", "-o", default=None)
    parser.add_argument("--output-dir", default="knowledge/kel/graph_change_requests/pending")
    parser.add_argument("--change-request-id", default=None)
    parser.add_argument("--no-validate", action="store_true")
    args = parser.parse_args()
    if (args.output or args.change_request_id) and len(args.feedback_records) != 1:
        raise SystemExit("--output and --change-request-id require exactly one input record.")

    paths: list[Path] = []
    for raw_path in args.feedback_records:
        input_path = Path(raw_path)
        source = load_json(input_path)
        change = build_change_request(source, args.change_request_id)
        output_path = Path(args.output) if args.output else output_path_for(input_path, Path(args.output_dir), source)
        write_json(output_path, change)
        paths.append(output_path)
    if not args.no_validate:
        validate_outputs(paths)
    print(f"KEL graph change request(s) written: {len(paths)}")
    for path in paths:
        record = load_json(path)
        print(f"- {path}: {record['target_layer']} / {record['change_type']} / {record['priority']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
