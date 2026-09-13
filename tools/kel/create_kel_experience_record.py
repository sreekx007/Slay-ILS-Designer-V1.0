#!/usr/bin/env python3
"""
Create a KEL experience record after a design query.

The record is an experience anchor. Later tools can attach querier feedback,
graph change requests, expert reviews, and implementation references to it.
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


def extract_source_query(edpr: dict[str, Any] | None, context: dict[str, Any] | None) -> dict[str, Any]:
    query_id = None
    raw_text = None
    title = None

    if isinstance(edpr, dict):
        query_id = edpr.get("id")
        raw_text = edpr.get("sourceRequest", {}).get("rawText")
        title = edpr.get("problemIdentity", {}).get("title")

    if (not query_id or not raw_text or not title) and isinstance(context, dict):
        problem = context.get("problem", {})
        if isinstance(problem, dict):
            query_id = query_id or problem.get("id")
            raw_text = raw_text or problem.get("raw_text")
            title = title or problem.get("title")

    return {
        "query_id": query_id,
        "raw_text": raw_text or "Raw query text not available to KEL generator.",
        "problem_title": title,
    }


def summarize_edpr(edpr: dict[str, Any] | None, path: Path | None) -> dict[str, Any]:
    if not isinstance(edpr, dict):
        return {
            "artifact_id": None,
            "repo_path": repo_path(path),
            "summary": "EDPR artifact was not provided.",
        }

    pmap = edpr.get("pMap", {})
    reqs = len(safe_list(pmap.get("requirements"))) if isinstance(pmap, dict) else 0
    funcs = len(safe_list(pmap.get("functions"))) if isinstance(pmap, dict) else 0
    arts = len(safe_list(pmap.get("artifacts"))) if isinstance(pmap, dict) else 0
    behs = len(safe_list(pmap.get("behaviours"))) if isinstance(pmap, dict) else 0
    links = len(safe_list(pmap.get("links"))) if isinstance(pmap, dict) else 0
    summary = f"EDPR parsed with {reqs} requirements, {funcs} functions, {arts} artifacts, {behs} behaviours, and {links} links."

    return {
        "artifact_id": edpr.get("id"),
        "repo_path": repo_path(path),
        "summary": summary,
    }


def summarize_context(context: dict[str, Any] | None, path: Path | None) -> dict[str, Any]:
    if not isinstance(context, dict):
        return {
            "artifact_id": None,
            "repo_path": repo_path(path),
            "summary": "Retrieval context was not provided.",
        }

    component_count = len(safe_list(context.get("component_context")))
    graph = context.get("edikb_graph_context", {})
    numeric = context.get("numeric_evidence", {})
    node_count = graph.get("selected_node_count", 0) if isinstance(graph, dict) else 0
    row_count = numeric.get("row_count_returned", 0) if isinstance(numeric, dict) else 0
    summary = f"Retrieved {component_count} component contexts, {node_count} EDIKB graph nodes, and {row_count} numeric evidence rows."

    return {
        "artifact_id": context.get("retrieval_id") or context.get("id"),
        "repo_path": repo_path(path),
        "summary": summary,
    }


def extract_recommendation_from_md(text: str) -> str | None:
    match = re.search(r"Candidate:\s*`?([^`\n]+)`?", text)
    if match:
        value = match.group(1).strip()
        return None if value in {"", "None", "null"} else value
    return None


def summarize_solution(solution_json: Any, solution_md: str | None, path: Path | None) -> tuple[dict[str, Any], list[str]]:
    limitations: list[str] = []

    if isinstance(solution_json, dict):
        recommendation = solution_json.get("recommendation", {})
        candidate = recommendation.get("recommended_candidate") if isinstance(recommendation, dict) else None
        basis = recommendation.get("basis") if isinstance(recommendation, dict) else None
        residual = solution_json.get("residual_risk")
        limitations.extend(str(item) for item in safe_list(residual))
        summary = basis or "Structured solution JSON was generated."
        if candidate:
            summary = f"Recommended candidate {candidate}. {summary}"
        return {
            "artifact_id": solution_json.get("id") or candidate,
            "repo_path": repo_path(path),
            "summary": summary,
        }, limitations

    if solution_md is not None:
        candidate = extract_recommendation_from_md(solution_md)
        for line in solution_md.splitlines():
            stripped = line.strip("- ").strip()
            if stripped.startswith("This first-pass") or stripped.startswith("It "):
                limitations.append(stripped)
        summary = "Markdown solution was generated."
        if candidate:
            summary = f"Markdown solution recommended {candidate}."
        return {
            "artifact_id": candidate,
            "repo_path": repo_path(path),
            "summary": summary,
        }, limitations

    return {
        "artifact_id": None,
        "repo_path": repo_path(path),
        "summary": "Solution artifact was not provided.",
    }, ["No solution artifact was available when the KEL record was generated."]


def summarize_plot(layout_report: dict[str, Any] | None, plot_report: dict[str, Any] | None, plot_path: Path | None) -> tuple[dict[str, Any], list[str]]:
    limitations: list[str] = []
    if isinstance(plot_report, dict):
        status = plot_report.get("plot_status") or plot_report.get("status") or "unknown"
        warnings = safe_list(plot_report.get("warnings"))
        errors = safe_list(plot_report.get("errors"))
        limitations.extend(str(item) for item in warnings + errors)
        return {
            "artifact_id": plot_report.get("candidate") or plot_report.get("id"),
            "repo_path": repo_path(plot_path),
            "summary": f"Plot report available with status {status}.",
        }, limitations

    if isinstance(layout_report, dict):
        status = layout_report.get("status") or "unknown"
        warnings = safe_list(layout_report.get("warnings"))
        errors = safe_list(layout_report.get("errors"))
        limitations.extend(str(item) for item in warnings + errors)
        return {
            "artifact_id": layout_report.get("candidate") or layout_report.get("id"),
            "repo_path": repo_path(plot_path),
            "summary": f"Layout report available with status {status}; final plot report not provided.",
        }, limitations

    return {
        "artifact_id": None,
        "repo_path": repo_path(plot_path),
        "summary": "Plot artifact was not provided.",
    }, []


def evidence_strength(context: dict[str, Any] | None) -> int:
    if not isinstance(context, dict):
        return 1
    numeric = context.get("numeric_evidence", {})
    graph = context.get("edikb_graph_context", {})
    rows = numeric.get("row_count_returned", 0) if isinstance(numeric, dict) else 0
    nodes = graph.get("selected_node_count", 0) if isinstance(graph, dict) else 0
    if rows >= 6:
        return 5
    if rows >= 2:
        return 4
    if rows == 1 or nodes >= 5:
        return 3
    if nodes:
        return 2
    return 1


def knowledge_sufficiency(edpr: dict[str, Any] | None, context: dict[str, Any] | None, solution_available: bool) -> str:
    if not isinstance(edpr, dict):
        return "unknown"

    missing_component = False
    row_count = 0
    node_count = 0
    if isinstance(context, dict):
        missing_component = any(isinstance(item, dict) and item.get("missing") for item in safe_list(context.get("component_context")))
        numeric = context.get("numeric_evidence", {})
        graph = context.get("edikb_graph_context", {})
        row_count = int(numeric.get("row_count_returned", 0) or 0) if isinstance(numeric, dict) else 0
        node_count = int(graph.get("selected_node_count", 0) or 0) if isinstance(graph, dict) else 0

    pmap = edpr.get("pMap", {})
    issues_text = json.dumps(pmap.get("issues", []), ensure_ascii=True).lower() if isinstance(pmap, dict) else ""
    explicit_missing = "missing" in issues_text or "no current" in issues_text or "insufficient" in issues_text

    if missing_component or explicit_missing:
        return "partially_sufficient" if solution_available else "insufficient"
    if row_count >= 2 and node_count >= 3 and solution_available:
        return "sufficient"
    if row_count > 0 or node_count > 0 or solution_available:
        return "partially_sufficient"
    return "insufficient"


def llm_confidence(sufficiency: str, strength: int, solution_available: bool) -> str:
    if sufficiency == "sufficient" and strength >= 4 and solution_available:
        return "high"
    if sufficiency in {"sufficient", "partially_sufficient"} and strength >= 2 and solution_available:
        return "medium"
    return "low"


def build_record(args: argparse.Namespace) -> dict[str, Any]:
    edpr_path = Path(args.edpr_json) if args.edpr_json else None
    context_path = Path(args.context_json) if args.context_json else None
    solution_json_path = Path(args.solution_json) if args.solution_json else None
    solution_md_path = Path(args.solution_md) if args.solution_md else None
    layout_report_path = Path(args.layout_report) if args.layout_report else None
    plot_report_path = Path(args.plot_report) if args.plot_report else None
    plot_path = Path(args.plot_path) if args.plot_path else plot_report_path or layout_report_path
    knowloop_path = Path(args.knowloop_json) if args.knowloop_json else None

    edpr = load_json(edpr_path)
    context = load_json(context_path)
    solution_json = load_json(solution_json_path)
    solution_md = read_text(solution_md_path)
    layout_report = load_json(layout_report_path)
    plot_report = load_json(plot_report_path)
    knowloop = load_json(knowloop_path)

    source_query = extract_source_query(edpr if isinstance(edpr, dict) else None, context if isinstance(context, dict) else None)
    slug = slugify(source_query.get("query_id") or source_query.get("problem_title"))
    experience_id = args.experience_id or f"kel:experience:{slug}:{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

    solution_trace, solution_limitations = summarize_solution(solution_json, solution_md, solution_json_path or solution_md_path)
    plot_trace, plot_limitations = summarize_plot(layout_report, plot_report, plot_path)
    solution_available = solution_trace["artifact_id"] is not None or solution_trace["repo_path"] is not None
    strength = evidence_strength(context if isinstance(context, dict) else None)
    sufficiency = knowledge_sufficiency(edpr if isinstance(edpr, dict) else None, context if isinstance(context, dict) else None, solution_available)
    confidence = llm_confidence(sufficiency, strength, solution_available)

    limitations = solution_limitations + plot_limitations
    if isinstance(knowloop, dict):
        outcome = knowloop.get("outcome_summary", {})
        limitations.extend(str(item) for item in safe_list(outcome.get("known_limitations")) if isinstance(outcome, dict))

    knowloop_refs = []
    if isinstance(knowloop, dict):
        knowloop_refs.append({
            "id": str(knowloop.get("id") or "knowloop:candidate:unidentified"),
            "repo_path": repo_path(knowloop_path),
        })

    record = {
        "schema": "kel-experience-record/0.1",
        "experience_id": experience_id,
        "status": "generated",
        "created_utc": utc_now(),
        "source_query": source_query,
        "edpr_trace": summarize_edpr(edpr if isinstance(edpr, dict) else None, edpr_path),
        "retrieval_trace": summarize_context(context if isinstance(context, dict) else None, context_path),
        "solution_trace": solution_trace,
        "plot_trace": plot_trace,
        "ratings": {
            "llm_confidence": confidence,
            "knowledge_sufficiency": sufficiency,
            "evidence_strength": strength,
            "rationale": "Auto-generated from EDPR availability, retrieval coverage, numeric evidence count, graph node count, solution availability, and explicit missing-knowledge issues.",
        },
        "limitations": sorted(set(item for item in limitations if item)),
        "feedback_refs": [],
        "graph_change_request_refs": [],
        "expert_review_refs": knowloop_refs,
    }
    return record


def validate_output(path: Path) -> None:
    if not VALIDATOR.exists():
        return
    completed = subprocess.run([sys.executable, str(VALIDATOR), str(path)], cwd=str(REPO_ROOT), text=True)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a KEL experience record after a design query.")
    parser.add_argument("--edpr-json", default=None)
    parser.add_argument("--context-json", default=None)
    parser.add_argument("--solution-json", default=None)
    parser.add_argument("--solution-md", default=None)
    parser.add_argument("--layout-report", default=None)
    parser.add_argument("--plot-report", default=None)
    parser.add_argument("--plot-path", default=None)
    parser.add_argument("--knowloop-json", default=None)
    parser.add_argument("--experience-id", default=None)
    parser.add_argument("--output", "-o", required=True)
    parser.add_argument("--no-validate", action="store_true")
    args = parser.parse_args()

    if args.solution_json and args.solution_md:
        raise SystemExit("Use either --solution-json or --solution-md, not both.")

    output_path = Path(args.output)
    record = build_record(args)
    write_json(output_path, record)
    if not args.no_validate:
        validate_output(output_path)

    print(f"KEL experience record written: {output_path}")
    print(f"Experience id: {record['experience_id']}")
    print(f"Knowledge sufficiency: {record['ratings']['knowledge_sufficiency']}")
    print(f"LLM confidence: {record['ratings']['llm_confidence']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
