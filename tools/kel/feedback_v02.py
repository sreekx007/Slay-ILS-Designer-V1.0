"""Shared deterministic normalization rules for KEL v0.2 feedback tooling."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from convert_feedback_to_pmap_apf import apf_action_for, classify_feedback, priority_for


PRIORITY_RANK = {"low": 0, "medium": 1, "high": 2}


def slugify(value: str | None) -> str:
    raw = value or "feedback"
    slug = re.sub(r"[^A-Za-z0-9_.:-]+", "_", raw).strip("_").lower()
    return slug or "feedback"


def normalized_text(value: str) -> str:
    text = value.lower().replace("–", "-").replace("—", "-")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def sha256_text(*values: str) -> str:
    payload = "\x1f".join(normalized_text(value) for value in values)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def atomic_feedback_type(text: str) -> tuple[str, float, list[str]]:
    lower = normalized_text(text)
    if "not asked whether" in lower or "was not asked whether" in lower:
        return "clarification", 0.98, ["missing explicit design clarification"]
    if "no aim of strain optimization" in lower or "no aim of stress optimization" in lower:
        return "wrong_assumption", 0.98, ["feedback rejects an inferred optimization objective"]
    evidence_phrases = (
        "basis of", "basis for", "evidence", "correlation", "was that analysis",
        "analysis done", "not provided", "not done", "no data", "fea",
    )
    if any(phrase in lower for phrase in evidence_phrases):
        return "insufficient_evidence", 0.92, ["feedback requests a missing engineering basis or evidence"]
    feedback_type = classify_feedback(text)
    return feedback_type, 0.82, ["v0.1 deterministic feedback classifier"]


def affected_components(text: str) -> list[str]:
    lower = normalized_text(text)
    checks = [
        (("ea st",), "EA-ST"),
        (("gd st", "top frame"), "GD-ST"),
        (("ea sb",), "EA-SB"),
        (("gd sb", "base structure", "base frame"), "GD-SB"),
        (("gd b", "z branch", "z shaped"), "GD-B"),
        (("valve",), "GD-VLV"),
        (("connector", "p s support", "p-s support"), "GD-Con"),
        (("thick pipe",), "GD-TP"),
        (("header", "pipeline"), "GD-PIP"),
    ]
    found: list[str] = []
    for phrases, component in checks:
        if any(phrase in lower for phrase in phrases):
            found.append(component)
    return sorted(set(found))


def group_key_for(text: str, components: list[str] | None = None) -> str:
    lower = normalized_text(text)
    if "base structure" in lower and ("depth" in lower or "vertical offset" in lower):
        return "valve_base_depth_clearance"
    if ("base structure" in lower or "ea bs" in lower or "ea sb" in lower) and "length" in lower:
        return "base_length_strain_evidence"
    if ("p s" in lower or "p-s" in text.lower()) and ("bending moment" in lower or "stiff" in lower):
        return "connector_system_valve_moment_evidence"
    if "top frame" in lower and ("ask" in lower or "required" in lower or "protect" in lower):
        return "valve_top_frame_requirement"
    if "connector" in lower and ("spacing" in lower or "distance" in lower):
        return "connector_spacing_basis"
    if "vertical connector" in lower or "z branch" in lower or "z shaped" in lower:
        return "vertical_connector_z_branch"
    if "ea st" in lower or "gd st" in lower or (
        "branch connector" in lower and ("associate" in lower or "connection" in lower)
    ):
        return "ea_st_parameters_connections_associations"
    if ("ea sb" in lower or "gd sb" in lower) and "valve" in lower:
        return "ea_sb_valve_protection_geometry"
    if "repository plotter" in lower or "repo plotter" in lower or "freehand" in lower:
        return "repository_plotter_gate"
    if "plot" in lower and "scale" in lower:
        return "plot_scale"
    component_key = "_".join(item.lower().replace("-", "_") for item in sorted(components or []))
    keywords = [word for word in lower.split() if len(word) > 3][:8]
    base = "_".join(([component_key] if component_key else []) + keywords)
    return re.sub(r"[^a-z0-9_]+", "_", base).strip("_") or "general_feedback"


def infer_target_and_type(feedback_type: str, text: str, action: str = "") -> tuple[str, str]:
    lower = normalized_text(text)
    if "repository plotter" in lower or "repo plotter" in lower or "freehand" in lower:
        return "KEL", "new_workflow_gate"
    if "vertical connector" in lower or "z branch" in lower or "z shaped" in lower:
        return "EDAS", "new_assembly_constraint"
    if "ea st" in lower or "gd st" in lower or "branch connector" in lower:
        return "EDAS", "new_assembly_constraint"
    if "ea sb" in lower or "gd sb" in lower or "base structure" in lower:
        return "EDAS", "new_assembly_constraint"
    if "two branch valve" in lower or "two branch valves" in lower:
        return "Tools", "new_tool_capability"
    if feedback_type == "answer_format_requirement":
        return "KEL", "new_output_policy"
    if feedback_type in {"wrong_assumption", "missing_constraint", "design_objective_requirement", "clarification"}:
        return "EDPR", "new_design_guidance"
    if feedback_type == "insufficient_evidence":
        return "EDIKB", "future_fea_study"
    if "plot" in lower or "label" in lower or "drawing" in lower or "picture" in lower:
        return "Plotters", "new_plotting_rule"
    if "plot" in action.lower():
        return "Plotters", "new_plotting_rule"
    return "Docs", "new_design_guidance"


def priority_for_members(members: list[dict[str, Any]]) -> str:
    return max(
        (str(member.get("priority") or "low") for member in members),
        key=lambda value: PRIORITY_RANK.get(value, -1),
    )


def unique_strings(values: list[Any]) -> list[str]:
    return sorted({str(value) for value in values if isinstance(value, str) and value.strip()})


def v01_feedback_view(text: str, feedback_type: str | None = None) -> dict[str, Any]:
    kind = feedback_type or classify_feedback(text)
    return {
        "schema": "kel-feedback-to-pmap-apf/0.1",
        "raw_feedback_text": text,
        "feedback_type": kind,
        "structured_feedback": {
            "pmap_issue": text,
            "apf_action": apf_action_for(kind),
            "priority": priority_for(kind),
        },
    }


def canonical_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
