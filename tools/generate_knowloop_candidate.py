#!/usr/bin/env python3
"""
Generate a Knowloop candidate JSON after a design query.

This tool should run after every query outcome: successful, partial, or failed.
It does not update official knowledge files. It records a candidate for later
human/expert review.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: Path | None) -> Any:
    if path is None:
        return None
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def safe_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def score_from_count(count: int, good: int, fair: int) -> int:
    if count >= good:
        return 5
    if count >= fair:
        return 4
    if count > 0:
        return 3
    return 2


def extract_recommendation_from_md(text: str) -> str | None:
    match = re.search(r"Candidate:\s*`?([^`\n]+)`?", text)
    if match:
        value = match.group(1).strip()
        return None if value in {"None", "null", ""} else value
    return None


def summarize_solution(solution_json: Any, solution_md: str | None) -> tuple[str | None, str, list[str]]:
    limitations: list[str] = []
    if isinstance(solution_json, dict):
        rec = solution_json.get("recommendation", {})
        candidate = rec.get("recommended_candidate") if isinstance(rec, dict) else None
        basis = rec.get("basis", "") if isinstance(rec, dict) else ""
        limitations.extend(solution_json.get("residual_risk", []) if isinstance(solution_json.get("residual_risk"), list) else [])
        return candidate, basis or "Structured solution JSON was generated.", limitations

    if solution_md:
        candidate = extract_recommendation_from_md(solution_md)
        limitations = [
            line.strip("- ").strip()
            for line in solution_md.splitlines()
            if line.strip().startswith("- This first-pass") or line.strip().startswith("- It ")
        ]
        summary = "Markdown solution was generated."
        if candidate:
            summary = f"Markdown solution recommended {candidate}."
        return candidate, summary, limitations

    return None, "No solution artifact was provided.", ["Solution output was not available to the Knowloop generator."]


def pmap_quality(edpr: dict[str, Any] | None) -> int:
    if not isinstance(edpr, dict):
        return 1
    pmap = edpr.get("pMap", {})
    if not isinstance(pmap, dict):
        return 1
    checks = [
        len(safe_list(pmap.get("requirements"))) > 0,
        len(safe_list(pmap.get("functions"))) > 0,
        len(safe_list(pmap.get("artifacts"))) > 0,
        len(safe_list(pmap.get("behaviours"))) > 0,
        len(safe_list(pmap.get("links"))) >= 3,
    ]
    return max(1, sum(1 for item in checks if item))


def count_zmc(edpr: dict[str, Any] | None) -> int:
    if not isinstance(edpr, dict):
        return 0
    req_form = edpr.get("requirementFormalization", {})
    if not isinstance(req_form, dict):
        return 0
    count = 0
    for value in req_form.values():
        for item in safe_list(value):
            if isinstance(item, dict) and all(isinstance(item.get(key), dict) and item.get(key) for key in ("Z", "M", "C")):
                count += 1
    return count


def retrieval_quality(context: dict[str, Any] | None) -> int:
    if not isinstance(context, dict):
        return 1
    components = len(safe_list(context.get("component_context")))
    rows = context.get("numeric_evidence", {}).get("row_count_returned", 0) if isinstance(context.get("numeric_evidence"), dict) else 0
    nodes = context.get("edikb_graph_context", {}).get("selected_node_count", 0) if isinstance(context.get("edikb_graph_context"), dict) else 0
    score = 1
    if components:
        score += 1
    if nodes:
        score += 1
    if rows:
        score += 2
    return min(score, 5)


def evidence_strength(context: dict[str, Any] | None) -> int:
    if not isinstance(context, dict):
        return 1
    rows = context.get("numeric_evidence", {}).get("row_count_returned", 0) if isinstance(context.get("numeric_evidence"), dict) else 0
    nodes = context.get("edikb_graph_context", {}).get("selected_node_count", 0) if isinstance(context.get("edikb_graph_context"), dict) else 0
    if rows >= 6:
        return 5
    if rows >= 2:
        return 4
    if rows == 1 or nodes >= 5:
        return 3
    if nodes:
        return 2
    return 1


def classify_candidate(
    outcome_status: str,
    candidate: str | None,
    edpr: dict[str, Any] | None,
    context: dict[str, Any] | None,
    human_comment: str | None,
) -> tuple[str, list[dict[str, str]]]:
    updates: list[dict[str, str]] = []
    if outcome_status == "failed":
        updates.append(
            {
                "update_id": "kl:update:failure_review",
                "target_layer": "Tools",
                "update_type": "improvement",
                "priority": "high",
                "issue": "Pipeline failed or did not produce a design result.",
                "suggested_change": "Review failing stage and add a regression example after correction.",
                "evidence_requirement": "Error trace and corrected rerun.",
                "status": "proposed",
            }
        )
        return "failure_record", updates

    pmap_score = pmap_quality(edpr)
    rows = 0
    if isinstance(context, dict) and isinstance(context.get("numeric_evidence"), dict):
        rows = int(context["numeric_evidence"].get("row_count_returned", 0) or 0)

    if pmap_score < 4:
        updates.append(
            {
                "update_id": "kl:update:pmap_apf_quality",
                "target_layer": "EDPR",
                "update_type": "improvement",
                "priority": "high",
                "issue": "EDPR parse has weak P-map/APF expression.",
                "suggested_change": "Improve parser prompt/example coverage and rerun check_pmap_apf.py.",
                "evidence_requirement": "Passing P-map/APF checker result.",
                "status": "proposed",
            }
        )

    if rows == 0:
        updates.append(
            {
                "update_id": "kl:update:missing_numeric_evidence",
                "target_layer": "Dataset",
                "update_type": "future_study",
                "priority": "medium",
                "issue": "No numeric evidence rows were retrieved for the comparison.",
                "suggested_change": "Add FEA/ML or literature-backed dataset rows for the queried design family.",
                "evidence_requirement": "Verified dataset rows or approved future study plan.",
                "status": "needs_evidence",
            }
        )

    if human_comment:
        updates.append(
            {
                "update_id": "kl:update:human_comment_review",
                "target_layer": "None",
                "update_type": "improvement",
                "priority": "medium",
                "issue": "Human feedback comment was provided and needs review.",
                "suggested_change": human_comment,
                "evidence_requirement": "Expert review decision.",
                "status": "proposed",
            }
        )

    if updates:
        return "improvement", updates
    if candidate:
        return "confirmation", []
    return "future_study_candidate", updates


def evidence_trace_from_context(context: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(context, dict):
        return []
    trace: list[dict[str, Any]] = []
    for item in safe_list(context.get("component_context")):
        if isinstance(item, dict):
            trace.append(
                {
                    "source_type": "EDES",
                    "source_id": item.get("component_id"),
                    "repo_path": item.get("repo_path"),
                    "note": "Component context retrieved.",
                }
            )
    graph = context.get("edikb_graph_context", {})
    if isinstance(graph, dict):
        trace.append(
            {
                "source_type": "EDIKB_GRAPH",
                "source_id": graph.get("graph_id"),
                "repo_path": "knowledge/edikb/EDIKB_FULL_KNOWLEDGE_GRAPH.json",
                "note": f"Selected {graph.get('selected_node_count', 0)} graph nodes and {graph.get('selected_edge_count', 0)} edges.",
            }
        )
    numeric = context.get("numeric_evidence", {})
    if isinstance(numeric, dict):
        trace.append(
            {
                "source_type": "EDIKB_DATASET",
                "source_id": numeric.get("match_mode"),
                "repo_path": numeric.get("repo_path"),
                "note": f"Retrieved {numeric.get('row_count_returned', 0)} numeric evidence rows.",
            }
        )
    return trace


def build_candidate(args: argparse.Namespace) -> dict[str, Any]:
    edpr = load_json(Path(args.edpr_json)) if args.edpr_json else None
    context = load_json(Path(args.context_json)) if args.context_json else None
    solution_json = load_json(Path(args.solution_json)) if args.solution_json else None
    solution_md = Path(args.solution_md).read_text(encoding="utf-8") if args.solution_md else None

    recommended_candidate, summary, limitations = summarize_solution(solution_json, solution_md)
    outcome_status = args.outcome_status
    if outcome_status == "auto":
        outcome_status = "successful" if recommended_candidate else "partial"

    human_comment = args.human_comment
    candidate_type, updates = classify_candidate(outcome_status, recommended_candidate, edpr, context, human_comment)

    query_id = None
    raw_text = None
    title = None
    if isinstance(edpr, dict):
        query_id = edpr.get("id")
        raw_text = edpr.get("sourceRequest", {}).get("rawText")
        title = edpr.get("problemIdentity", {}).get("title")
    elif isinstance(context, dict):
        problem = context.get("problem", {})
        query_id = problem.get("id")
        raw_text = problem.get("raw_text")
        title = problem.get("title")

    slug = re.sub(r"[^A-Za-z0-9_\\-]+", "_", str(query_id or "manual_query")).strip("_").lower()
    candidate_id = args.candidate_id or f"kl:candidate:{slug}:{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

    parse_score = score_from_count(count_zmc(edpr), good=2, fair=1)
    pmap_score = pmap_quality(edpr)
    ret_score = retrieval_quality(context)
    ev_score = evidence_strength(context)
    solution_score = 4 if recommended_candidate else 2
    confidence = "high" if min(parse_score, pmap_score, ret_score, ev_score, solution_score) >= 4 else "medium"
    if ev_score <= 2 or solution_score <= 2:
        confidence = "low"

    candidate = {
        "schema": "knowloop-feedback/0.1",
        "id": candidate_id,
        "candidate_type": candidate_type,
        "status": "generated",
        "created_utc": utc_now(),
        "source_query": {
            "query_id": query_id,
            "raw_text": raw_text,
            "problem_title": title,
        },
        "pipeline_trace": {
            "edpr_file": args.edpr_json,
            "context_file": args.context_json,
            "solution_file": args.solution_json or args.solution_md,
            "tools_used": [
                "EDPR_VALIDATOR.py",
                "check_pmap_apf.py",
                "retrieve_context.py",
                "solve_problem.py",
                "generate_knowloop_candidate.py",
            ],
        },
        "outcome_summary": {
            "design_outcome_status": outcome_status,
            "summary": summary,
            "recommended_candidate": recommended_candidate,
            "known_limitations": limitations,
        },
        "llm_self_rating": {
            "parse_quality": parse_score,
            "pmap_apf_quality": pmap_score,
            "retrieval_quality": ret_score,
            "solution_quality": solution_score,
            "evidence_strength": ev_score,
            "confidence": confidence,
            "rationale": "Auto-generated from EDPR structure, retrieval context, numeric evidence count, and solution availability.",
        },
        "human_feedback_rating": {
            "rating": args.human_rating,
            "scale": "1_to_5",
            "comment": human_comment,
            "reviewer": args.human_reviewer,
            "reviewed_utc": utc_now() if args.human_rating or human_comment else None,
        },
        "expert_review_decision": {
            "status": "pending_review",
            "decision": None,
            "target_layer": None,
            "reviewer": None,
            "reviewed_utc": None,
            "implementation_reference": None,
        },
        "suggested_updates": updates,
        "evidence_trace": evidence_trace_from_context(context),
        "promotion_policy": {
            "official_kb_update_allowed": False,
            "requires_human_review": True,
            "requires_evidence_for_behavior_rules": True,
            "candidate_kb_only_until_accepted": True,
        },
    }
    return candidate


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Knowloop candidate JSON after a design query.")
    parser.add_argument("--edpr-json", default=None)
    parser.add_argument("--context-json", default=None)
    parser.add_argument("--solution-json", default=None)
    parser.add_argument("--solution-md", default=None)
    parser.add_argument("--output", "-o", required=True)
    parser.add_argument("--candidate-id", default=None)
    parser.add_argument("--outcome-status", choices=("auto", "successful", "partial", "failed", "not_run"), default="auto")
    parser.add_argument("--human-rating", type=int, choices=(1, 2, 3, 4, 5), default=None)
    parser.add_argument("--human-comment", default=None)
    parser.add_argument("--human-reviewer", default=None)
    args = parser.parse_args()

    candidate = build_candidate(args)
    write_json(Path(args.output), candidate)
    print(f"Knowloop candidate written: {args.output}")
    print(f"Candidate type: {candidate['candidate_type']}")
    print(f"Status: {candidate['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
