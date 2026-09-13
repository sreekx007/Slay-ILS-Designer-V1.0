#!/usr/bin/env python3
"""
Evaluate whether current framework knowledge was sufficient for a design query.

The output is a KEL sufficiency report. It is meant to feed experience records,
feedback review, and later graph change request generation.
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


def load_json(path: Path | None) -> Any:
    if path is None:
        return None
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def read_text(path: Path | None) -> str | None:
    if path is None:
        return None
    return path.read_text(encoding="utf-8")


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=True)
        f.write("\n")


def repo_path(path: Path | None) -> str | None:
    if path is None:
        return None
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(REPO_ROOT))
    except ValueError:
        return str(resolved)


def safe_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def slugify(value: str | None) -> str:
    raw = value or "manual_query"
    slug = re.sub(r"[^A-Za-z0-9_.:-]+", "_", raw).strip("_").lower()
    return slug or "manual_query"


def walk(value: Any):
    yield value
    if isinstance(value, dict):
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def collect_component_targets(edpr: dict[str, Any] | None) -> list[str]:
    if not isinstance(edpr, dict):
        return []
    targets: set[str] = set()
    for node in walk(edpr):
        if isinstance(node, str) and node.startswith("edes:"):
            targets.add(node)
    return sorted(targets)


def explicit_missing_issues(edpr: dict[str, Any] | None) -> list[str]:
    if not isinstance(edpr, dict):
        return []
    pmap = edpr.get("pMap", {})
    issues = safe_list(pmap.get("issues")) if isinstance(pmap, dict) else []
    flagged: list[str] = []
    for issue in issues:
        if not isinstance(issue, dict):
            continue
        text = json.dumps(issue, ensure_ascii=True).lower()
        if "missing" in text or "no current" in text or "insufficient" in text or "not available" in text:
            flagged.append(str(issue.get("label") or issue.get("id") or text))
    return flagged


def solution_available(solution_json: Any, solution_md: str | None) -> bool:
    if isinstance(solution_json, dict):
        return True
    if solution_md is not None and solution_md.strip():
        return True
    return False


def coverage_from_inputs(edpr: dict[str, Any] | None, context: dict[str, Any] | None, has_solution: bool) -> dict[str, Any]:
    component_targets = collect_component_targets(edpr)
    component_context = safe_list(context.get("component_context")) if isinstance(context, dict) else []
    missing_components = [item for item in component_context if isinstance(item, dict) and item.get("missing")]

    graph = context.get("edikb_graph_context", {}) if isinstance(context, dict) else {}
    numeric = context.get("numeric_evidence", {}) if isinstance(context, dict) else {}
    node_count = int(graph.get("selected_node_count", 0) or 0) if isinstance(graph, dict) else 0
    edge_count = int(graph.get("selected_edge_count", 0) or 0) if isinstance(graph, dict) else 0
    row_count = int(numeric.get("row_count_returned", 0) or 0) if isinstance(numeric, dict) else 0
    missing_issues = explicit_missing_issues(edpr)

    return {
        "component_targets": component_targets,
        "component_context_count": len(component_context),
        "missing_component_count": len(missing_components),
        "edikb_node_count": node_count,
        "edikb_edge_count": edge_count,
        "numeric_evidence_rows": row_count,
        "solution_available": has_solution,
        "explicit_missing_issue_count": len(missing_issues),
    }


def evidence_strength(coverage: dict[str, Any]) -> int:
    rows = coverage["numeric_evidence_rows"]
    nodes = coverage["edikb_node_count"]
    if rows >= 6:
        return 5
    if rows >= 2:
        return 4
    if rows == 1 or nodes >= 5:
        return 3
    if nodes:
        return 2
    return 1


def determine_sufficiency(coverage: dict[str, Any], edpr_present: bool, context_present: bool) -> str:
    if not edpr_present:
        return "unknown"
    if not context_present and not coverage["solution_available"]:
        return "insufficient"

    has_missing = coverage["missing_component_count"] > 0 or coverage["explicit_missing_issue_count"] > 0
    has_knowledge = coverage["edikb_node_count"] > 0 or coverage["numeric_evidence_rows"] > 0 or coverage["component_context_count"] > 0
    strong_evidence = coverage["numeric_evidence_rows"] >= 2 and coverage["edikb_node_count"] >= 3

    if has_missing:
        return "partially_sufficient" if has_knowledge or coverage["solution_available"] else "insufficient"
    if strong_evidence and coverage["solution_available"]:
        return "sufficient"
    if has_knowledge or coverage["solution_available"]:
        return "partially_sufficient"
    return "insufficient"


def confidence_from(sufficiency: str, strength: int, coverage: dict[str, Any]) -> str:
    if sufficiency == "sufficient" and strength >= 4 and coverage["solution_available"]:
        return "high"
    if sufficiency in {"sufficient", "partially_sufficient"} and strength >= 2:
        return "medium"
    return "low"


def build_gaps(coverage: dict[str, Any], missing_issues: list[str], edpr_present: bool, context_present: bool) -> list[dict[str, str]]:
    gaps: list[dict[str, str]] = []
    if not edpr_present:
        gaps.append({
            "gap_type": "missing_edpr",
            "target_layer": "EDPR",
            "issue": "No EDPR problem representation was supplied.",
            "suggested_action": "Generate and validate EDPR before sufficiency assessment.",
            "priority": "high",
            "evidence_requirement": "Valid EDPR JSON and P-map/APF checker output.",
        })
    if not context_present:
        gaps.append({
            "gap_type": "missing_retrieval_context",
            "target_layer": "Tools",
            "issue": "No retrieval context was supplied.",
            "suggested_action": "Run tools/retrieve_context.py and repeat KEL sufficiency evaluation.",
            "priority": "high",
            "evidence_requirement": "Retrieval context JSON.",
        })
    if coverage["missing_component_count"] > 0:
        gaps.append({
            "gap_type": "missing_component_context",
            "target_layer": "EDES",
            "issue": f"{coverage['missing_component_count']} requested component context item(s) were missing.",
            "suggested_action": "Add or correct EDES component knowledge files or retrieval component IDs.",
            "priority": "high",
            "evidence_requirement": "EDES component schema/content and retrieval rerun.",
        })
    if coverage["numeric_evidence_rows"] == 0:
        gaps.append({
            "gap_type": "missing_numeric_evidence",
            "target_layer": "Dataset",
            "issue": "No numeric EDIKB evidence rows were retrieved.",
            "suggested_action": "Add dataset rows or create a future FEA/ML study candidate for the queried comparison.",
            "priority": "medium",
            "evidence_requirement": "Verified numeric evidence rows or approved future study plan.",
        })
    if coverage["edikb_node_count"] == 0:
        gaps.append({
            "gap_type": "missing_graph_context",
            "target_layer": "EDIKB",
            "issue": "No EDIKB graph nodes were retrieved.",
            "suggested_action": "Add behavior/guidance nodes or improve retrieval terms for this problem family.",
            "priority": "medium",
            "evidence_requirement": "Relevant EDIKB nodes and retrieval rerun.",
        })
    if not coverage["solution_available"]:
        gaps.append({
            "gap_type": "missing_solution_artifact",
            "target_layer": "Tools",
            "issue": "No solution artifact was supplied.",
            "suggested_action": "Run tools/solve_problem.py or provide a solution Markdown/JSON artifact.",
            "priority": "medium",
            "evidence_requirement": "Solution artifact linked to the EDPR and retrieval context.",
        })
    for item in missing_issues:
        gaps.append({
            "gap_type": "explicit_missing_issue",
            "target_layer": "EDIKB",
            "issue": item,
            "suggested_action": "Review whether this issue should become a graph change request or future FEA/ML study.",
            "priority": "medium",
            "evidence_requirement": "Expert review and supporting evidence before official promotion.",
        })
    return gaps


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    edpr_path = Path(args.edpr_json) if args.edpr_json else None
    context_path = Path(args.context_json) if args.context_json else None
    solution_json_path = Path(args.solution_json) if args.solution_json else None
    solution_md_path = Path(args.solution_md) if args.solution_md else None

    edpr = load_json(edpr_path)
    context = load_json(context_path)
    solution_json = load_json(solution_json_path)
    solution_md = read_text(solution_md_path)

    edpr_present = isinstance(edpr, dict)
    context_present = isinstance(context, dict)
    has_solution = solution_available(solution_json, solution_md)
    coverage = coverage_from_inputs(edpr if edpr_present else None, context if context_present else None, has_solution)
    missing_issues = explicit_missing_issues(edpr if edpr_present else None)
    strength = evidence_strength(coverage)
    sufficiency = determine_sufficiency(coverage, edpr_present, context_present)
    confidence = confidence_from(sufficiency, strength, coverage)

    source_id = None
    if edpr_present:
        source_id = edpr.get("id") or edpr.get("problemIdentity", {}).get("title")
    assessment_id = args.assessment_id or f"kel:sufficiency:{slugify(source_id)}:{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

    return {
        "schema": "kel-kg-sufficiency-report/0.1",
        "assessment_id": assessment_id,
        "created_utc": utc_now(),
        "linked_experience_id": args.linked_experience_id,
        "inputs": {
            "edpr_json": repo_path(edpr_path),
            "context_json": repo_path(context_path),
            "solution_artifact": repo_path(solution_json_path or solution_md_path),
        },
        "ratings": {
            "knowledge_sufficiency": sufficiency,
            "evidence_strength": strength,
            "confidence": confidence,
        },
        "coverage": coverage,
        "gaps": build_gaps(coverage, missing_issues, edpr_present, context_present),
        "rationale": "Computed from EDPR component targets and missing issues, retrieval component coverage, EDIKB graph coverage, numeric evidence row count, and solution artifact availability.",
    }


def validate_output(path: Path) -> None:
    if not VALIDATOR.exists():
        return
    completed = subprocess.run([sys.executable, str(VALIDATOR), str(path)], cwd=str(REPO_ROOT), text=True)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate KEL knowledge sufficiency for a design query.")
    parser.add_argument("--edpr-json", default=None)
    parser.add_argument("--context-json", default=None)
    parser.add_argument("--solution-json", default=None)
    parser.add_argument("--solution-md", default=None)
    parser.add_argument("--linked-experience-id", default=None)
    parser.add_argument("--assessment-id", default=None)
    parser.add_argument("--output", "-o", required=True)
    parser.add_argument("--no-validate", action="store_true")
    args = parser.parse_args()

    if args.solution_json and args.solution_md:
        raise SystemExit("Use either --solution-json or --solution-md, not both.")

    report = build_report(args)
    output_path = Path(args.output)
    write_json(output_path, report)
    if not args.no_validate:
        validate_output(output_path)

    print(f"KEL sufficiency report written: {output_path}")
    print(f"Knowledge sufficiency: {report['ratings']['knowledge_sufficiency']}")
    print(f"Evidence strength: {report['ratings']['evidence_strength']}")
    print(f"Gap count: {len(report['gaps'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
