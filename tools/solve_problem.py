#!/usr/bin/env python3
"""
Create a first-pass, evidence-traceable design recommendation from an EDPR
retrieval context package.

This is not a replacement for engineering judgement or FEA. It ranks available
numeric evidence rows where possible, then emits graph/dataset trace notes for
an LLM or engineer to use in the final answer.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

from design_rules_v02 import workflow_blockers

SHROUD_STIFF_REQUIRED_REFS = {
    "edikb:p1_c1_shtp_nonadditive_01",
    "edikb:p1_c1_shtp_location_01",
    "edikb:p1_c1_shtp_peakloc_01",
    "edikb:p1_c1_shtp_size_01",
}


def selected_edikb_ids(context: dict[str, Any]) -> set[str]:
    graph = context.get("edikb_graph_context", {})
    return {str(node.get("id")) for node in graph.get("selected_nodes", []) if isinstance(node, dict)}


def shroud_stiff_judgement_flags(context: dict[str, Any]) -> list[dict[str, Any]]:
    intent = context.get("design_intent", {})
    gate = intent.get("shroud_stiff_component", {}) if isinstance(intent, dict) else {}
    if not gate.get("required"):
        return []
    selected = selected_edikb_ids(context)
    missing = sorted(SHROUD_STIFF_REQUIRED_REFS - selected)
    rows = context.get("numeric_evidence", {}).get("rows", [])
    has_shtp_rows = any(isinstance(row, dict) and str(row.get("component_system")) == "GD-SH+GD-TP" for row in rows)
    flags: list[dict[str, Any]] = []
    if missing or not has_shtp_rows:
        flags.append({
            "code": "EDIKB_USEFULNESS_JUDGEMENT_FAILURE",
            "status": "retrieval_gap",
            "message": "GD-VLV + GD-SH was present, but analogous GD-SH + stiff-component EDIKB evidence was not fully retrieved. Existing GD-TT/GD-TP + GD-SH C1 evidence must be considered useful by analogy before recommending valve placement or shroud length.",
            "missing_edikb_refs": missing,
            "missing_numeric_shtp_rows": not has_shtp_rows,
        })
    return flags


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def safe_float(value: Any) -> float | None:
    try:
        if value is None or str(value).strip() == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def choose_candidate_key(row: dict[str, str]) -> str:
    for key in (
        "layout_id",
        "layout_id_source_style",
        "component_system",
        "component_type",
        "system_type",
        "assembly_archetype",
        "case_id",
    ):
        value = row.get(key)
        if value:
            return value
    return "unclassified_candidate"


def response_is_minimize_target(row: dict[str, str]) -> bool:
    metric = " ".join(
        row.get(key, "")
        for key in ("response_metric", "response_target", "response_location", "peak_location")
    ).lower()
    return any(term in metric for term in ("strain", "moment", "bending", "curvature"))


def summarize_numeric_rows(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[choose_candidate_key(row)].append(row)

    summaries: list[dict[str, Any]] = []
    for candidate, candidate_rows in grouped.items():
        values = [
            safe_float(row.get("response_value"))
            for row in candidate_rows
            if response_is_minimize_target(row)
        ]
        values = [value for value in values if value is not None]
        if values:
            score = max(values)
            average = mean(values)
        else:
            score = None
            average = None

        evidence_ids = [row.get("case_id") for row in candidate_rows if row.get("case_id")]
        summaries.append(
            {
                "candidate": candidate,
                "score_lower_is_better": score,
                "average_response_value": average,
                "evidence_row_count": len(candidate_rows),
                "evidence_case_ids": evidence_ids[:20],
                "response_units": sorted({row.get("response_unit", "") for row in candidate_rows if row.get("response_unit")}),
                "response_targets": sorted({row.get("response_target", "") for row in candidate_rows if row.get("response_target")}),
            }
        )

    return sorted(
        summaries,
        key=lambda item: (
            item["score_lower_is_better"] is None,
            item["score_lower_is_better"] if item["score_lower_is_better"] is not None else 1.0e30,
            item["candidate"],
        ),
    )


def collect_graph_cues(context: dict[str, Any], limit: int = 20) -> list[dict[str, Any]]:
    cues: list[dict[str, Any]] = []
    graph = context.get("edikb_graph_context", {})
    for node in graph.get("selected_nodes", []):
        if not isinstance(node, dict):
            continue
        node_type = str(node.get("type", "")).lower()
        label = node.get("label") or node.get("id")
        if any(term in node_type for term in ("guidance", "rule", "candidate", "behavior", "behaviour")):
            cues.append(
                {
                    "id": node.get("id"),
                    "type": node.get("type"),
                    "label": label,
                    "source_family": node.get("source_family") or node.get("source_families"),
                }
            )
        if len(cues) >= limit:
            break
    return cues


def build_solution(context: dict[str, Any]) -> dict[str, Any]:
    rows = context.get("numeric_evidence", {}).get("rows", [])
    numeric_ranking = summarize_numeric_rows(rows) if isinstance(rows, list) else []
    graph_cues = collect_graph_cues(context)
    design_intent = context.get("design_intent", {})
    blockers = workflow_blockers(design_intent)
    judgement_flags = shroud_stiff_judgement_flags(context)

    recommendation = None
    if numeric_ranking and numeric_ranking[0].get("score_lower_is_better") is not None:
        recommendation = {
            "recommended_candidate": numeric_ranking[0]["candidate"],
            "basis": "Lowest worst-case numeric response value among retrieved evidence rows.",
            "confidence": "evidence_limited_screening",
        }
    else:
        recommendation = {
            "recommended_candidate": None,
            "basis": "No directly rankable numeric evidence rows were retrieved. Use graph guidance and mark conclusion as qualitative.",
            "confidence": "qualitative_only",
        }

    if blockers:
        recommendation = {
            "recommended_candidate": None,
            "basis": "Design emission is blocked by KEL v0.2 clarification or representation gates.",
            "confidence": "blocked_pending_input",
        }

    return {
        "solution_package_type": "edpr_first_pass_solution",
        "schema_version": "0.1",
        "problem": context.get("problem", {}),
        "design_intent": design_intent,
        "workflow_gates": {"status": "blocked" if blockers else "passed", "blockers": blockers},
        "judgement_flags": judgement_flags,
        "recommendation": recommendation,
        "numeric_ranking": numeric_ranking,
        "graph_cues": graph_cues,
        "engineering_notes": [
            "Use EDAS to confirm topology and interface validity before selecting a final concept.",
            "Use EDES to confirm component-specific constraints such as roller contact, support conditions, and installation envelope.",
            "If feature interactions are present, combined evidence overrides simple addition of isolated component effects.",
            "When GD-VLV is combined with GD-SH, use GD-SH + stiff-component C1 evidence by analogy before deciding valve placement or shroud length; record applicability limits.",
            "Every concept must consider reduction of high strain and bending moment; formal optimization requires an explicit EDPR objective and compatible evidence.",
            "If no direct numeric evidence exists, mark the comparison as a future FEA/ML study candidate.",
        ],
        "residual_risk": [
            "This first-pass script does not run FEA.",
            "It ranks only the rows retrieved into the context package.",
            "It treats lower strain/moment/curvature metrics as better unless future EDPR objectives specify otherwise.",
        ],
    }


def to_markdown(solution: dict[str, Any]) -> str:
    problem = solution.get("problem", {})
    rec = solution.get("recommendation", {})
    lines = [
        f"# EDPR First-Pass Solution: {problem.get('title') or problem.get('id') or 'Untitled'}",
        "",
        "## Recommendation",
        "",
        f"- Candidate: `{rec.get('recommended_candidate')}`",
        f"- Basis: {rec.get('basis')}",
        f"- Confidence: `{rec.get('confidence')}`",
        "",
        "## Numeric Ranking",
        "",
    ]

    ranking = solution.get("numeric_ranking", [])
    if ranking:
        lines.append("| Rank | Candidate | Lower-is-better score | Rows | Evidence case IDs |")
        lines.append("| --- | --- | ---: | ---: | --- |")
        for idx, item in enumerate(ranking, 1):
            score = item.get("score_lower_is_better")
            score_text = "" if score is None else f"{score:g}"
            evidence = ", ".join(item.get("evidence_case_ids", [])[:6])
            lines.append(f"| {idx} | `{item.get('candidate')}` | {score_text} | {item.get('evidence_row_count')} | {evidence} |")
    else:
        lines.append("No numeric rows were available for ranking.")

    lines.extend(["", "## Graph Cues", ""])
    cues = solution.get("graph_cues", [])
    if cues:
        for cue in cues:
            lines.append(f"- `{cue.get('id')}`: {cue.get('label')} ({cue.get('type')})")
    else:
        lines.append("No graph guidance/rule nodes were selected.")

    lines.extend(["", "## Judgement Flags", ""])
    flags = solution.get("judgement_flags", [])
    if flags:
        for flag in flags:
            lines.append(f"- `{flag.get('code')}`: {flag.get('message')}")
    else:
        lines.append("No judgement-failure flags were raised.")

    lines.extend(["", "## Engineering Notes", ""])
    for note in solution.get("engineering_notes", []):
        lines.append(f"- {note}")

    lines.extend(["", "## Residual Risk", ""])
    for risk in solution.get("residual_risk", []):
        lines.append(f"- {risk}")

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Create first-pass solution from EDPR retrieval context.")
    parser.add_argument("context_json", help="Path to retrieval context JSON from retrieve_context.py.")
    parser.add_argument("--output", "-o", default=None, help="Output file path. Default: stdout.")
    parser.add_argument("--format", choices=("json", "md"), default="md")
    args = parser.parse_args()

    context = load_json(Path(args.context_json))
    solution = build_solution(context)
    text = json.dumps(solution, indent=2, ensure_ascii=False) + "\n" if args.format == "json" else to_markdown(solution)

    if args.output:
        write_text(Path(args.output), text)
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
