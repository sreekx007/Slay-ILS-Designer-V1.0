#!/usr/bin/env python3
"""
Convert querier feedback into a structured KEL feedback-to-P-map/APF record.

This is a deterministic first-pass converter. It is intentionally conservative:
it records the raw feedback, classifies the likely feedback type, links to EDPR
P-map items when available, and emits an APF-style action for expert review.
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


def read_text_argument(value: str | None, path: str | None) -> str:
    if value and path:
        raise SystemExit("Use either --feedback-text or --feedback-file, not both.")
    if path:
        return Path(path).read_text(encoding="utf-8").strip()
    if value:
        return value.strip()
    raise SystemExit("Provide --feedback-text or --feedback-file.")


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=True)
        f.write("\n")


def safe_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def slugify(value: str | None) -> str:
    raw = value or "feedback"
    slug = re.sub(r"[^A-Za-z0-9_.:-]+", "_", raw).strip("_").lower()
    return slug or "feedback"


def tokenise(text: str) -> set[str]:
    stop = {
        "the",
        "and",
        "for",
        "with",
        "that",
        "this",
        "should",
        "could",
        "would",
        "need",
        "needs",
        "design",
        "solution",
    }
    return {tok for tok in re.findall(r"[A-Za-z0-9][A-Za-z0-9_\-]{2,}", text.lower()) if tok not in stop}


def classify_feedback(text: str) -> str:
    lower = text.lower()
    if any(phrase in lower for phrase in ("z-shaped", "z branch", "z-shaped gd-b", "vertical connector needs", "vertical connector requires")):
        return "correction"
    if any(word in lower for word in ("strain", "stress", "max stress", "max strain", "minimizes strain", "minimizes stress")):
        return "design_objective_requirement"
    if any(phrase in lower for phrase in ("connections mentioned", "piping connections", "connection type", "number of connections")):
        return "answer_format_requirement"
    if any(phrase in lower for phrase in ("always ask", "always give", "always mention", "text based", "text-based", "initial overview", "presentation", "output policy")):
        return "answer_format_requirement"
    if any(phrase in lower for phrase in ("default condition", "default assumption", "always need to be associated", "always needs to be associated", "cannot ride", "cannot take")):
        return "default_assumption"
    if any(word in lower for word in ("plot", "label", "overlap", "scale", "drawing", "picture", "zoomed")):
        if any(word in lower for word in ("wrong", "incorrect", "below", "upwards", "upward", "too small", "cannot be zoomed", "need to be labelled", "labeled", "plotted")):
            return "plot_correction"
        return "poor_plot"
    if any(word in lower for word in ("not enough evidence", "insufficient evidence", "no data", "dataset", "fea", "verify", "proof")):
        return "insufficient_evidence"
    if any(word in lower for word in ("assumption", "assume", "assumed")) and any(word in lower for word in ("wrong", "incorrect", "not")):
        return "wrong_assumption"
    if any(word in lower for word in ("wrong", "incorrect", "not correct", "mistake", "error")):
        return "correction"
    if any(word in lower for word in ("missing component", "add component", "add shroud", "add taper", "add support", "add valve")):
        return "missing_component"
    if any(word in lower for word in ("must", "shall", "cannot", "should not", "avoid", "limit", "allowable", "clearance", "constraint")):
        return "missing_constraint"
    if any(word in lower for word in ("better", "alternative", "instead", "prefer", "use ")) and any(word in lower for word in ("layout", "component", "solution", "option")):
        return "better_design_alternative"
    if any(word in lower for word in ("future", "study", "ml", "test", "benchmark")):
        return "future_study"
    return "clarification"


def priority_for(feedback_type: str) -> str:
    if feedback_type in {
        "correction",
        "missing_constraint",
        "missing_component",
        "incorrect_behavior",
        "wrong_assumption",
        "plot_correction",
        "default_assumption",
        "design_objective_requirement",
    }:
        return "high"
    if feedback_type in {"insufficient_evidence", "poor_plot", "answer_format_requirement", "better_design_alternative", "future_study"}:
        return "medium"
    return "low"


def pmap_nodes(edpr: dict[str, Any] | None, key: str) -> list[dict[str, Any]]:
    if not isinstance(edpr, dict):
        return []
    pmap = edpr.get("pMap", {})
    if not isinstance(pmap, dict):
        return []
    return [item for item in safe_list(pmap.get(key)) if isinstance(item, dict)]


def node_text(node: dict[str, Any]) -> str:
    return json.dumps(node, ensure_ascii=True).lower()


def best_match(feedback: str, nodes: list[dict[str, Any]]) -> str | None:
    tokens = tokenise(feedback)
    best_node: dict[str, Any] | None = None
    best_score = 0
    for node in nodes:
        text = node_text(node)
        score = sum(1 for token in tokens if token in text)
        ontology_links = " ".join(str(item).lower() for item in safe_list(node.get("ontologyLinks")))
        score += sum(1 for token in tokens if token in ontology_links)
        if score > best_score:
            best_node = node
            best_score = score
    if best_node is None or best_score == 0:
        return None
    return str(best_node.get("id") or best_node.get("label"))


def apf_action_for(feedback_type: str) -> str:
    actions = {
        "clarification": "review_feedback_and_clarify_problem_representation",
        "correction": "revise_solution_or_knowledge_item_after_expert_review",
        "missing_constraint": "add_or_strengthen_constraint_in_edpr_and_solution_checks",
        "missing_component": "review_component_targets_and_update_edes_or_edpr_if_confirmed",
        "incorrect_behavior": "revise_behavior_interpretation_and_link_to_edikb_rule",
        "wrong_assumption": "revise_assumption_and_add_explicit_edpr_known_or_unknown_input",
        "insufficient_evidence": "create_evidence_gap_or_future_fea_ml_study_candidate",
        "poor_plot": "review_plotter_output_and_add_plot_validation_rule",
        "plot_correction": "correct_plot_geometry_labels_or_scale_and_add_regression_case",
        "answer_format_requirement": "add_or_update_kel_output_presentation_policy",
        "default_assumption": "add_default_design_assumption_for_expert_review_and_reuse",
        "design_objective_requirement": "add_design_objective_or_ranking_rule_for_stress_strain_minimization",
        "better_design_alternative": "compare_alternative_candidate_and_update_solution_ranking_if_supported",
        "future_study": "create_future_study_candidate_with_required_parameters",
    }
    return actions[feedback_type]


def linked_experience_id(experience: dict[str, Any] | None, explicit: str | None) -> str:
    if explicit:
        return explicit
    if isinstance(experience, dict) and isinstance(experience.get("experience_id"), str):
        return experience["experience_id"]
    return "kel:experience:unlinked"


def build_record(args: argparse.Namespace) -> dict[str, Any]:
    feedback_text = read_text_argument(args.feedback_text, args.feedback_file)
    edpr = load_json(Path(args.edpr_json)) if args.edpr_json else None
    experience = load_json(Path(args.experience_json)) if args.experience_json else None
    feedback_type = args.feedback_type or classify_feedback(feedback_text)
    feedback_id = args.feedback_id or f"kel:feedback:{slugify(linked_experience_id(experience, args.linked_experience_id))}:{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

    affected_requirement = best_match(feedback_text, pmap_nodes(edpr if isinstance(edpr, dict) else None, "requirements"))
    affected_function = best_match(feedback_text, pmap_nodes(edpr if isinstance(edpr, dict) else None, "functions"))
    affected_behavior = best_match(feedback_text, pmap_nodes(edpr if isinstance(edpr, dict) else None, "behaviours"))
    affected_structure = best_match(feedback_text, pmap_nodes(edpr if isinstance(edpr, dict) else None, "artifacts"))
    affected_constraint = affected_requirement if feedback_type == "missing_constraint" else None

    issue = feedback_text
    if len(issue) > 240:
        issue = issue[:237].rstrip() + "..."

    return {
        "schema": "kel-feedback-to-pmap-apf/0.1",
        "feedback_id": feedback_id,
        "linked_experience_id": linked_experience_id(experience, args.linked_experience_id),
        "created_utc": utc_now(),
        "raw_feedback_text": feedback_text,
        "feedback_type": feedback_type,
        "structured_feedback": {
            "affected_requirement": affected_requirement,
            "affected_function": affected_function,
            "affected_behavior": affected_behavior,
            "affected_structure": affected_structure,
            "affected_constraint": affected_constraint,
            "pmap_issue": issue,
            "apf_action": apf_action_for(feedback_type),
            "priority": priority_for(feedback_type),
        },
    }


def validate_output(path: Path) -> None:
    if not VALIDATOR.exists():
        return
    completed = subprocess.run([sys.executable, str(VALIDATOR), str(path)], cwd=str(REPO_ROOT), text=True)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert querier feedback into KEL P-map/APF feedback JSON.")
    parser.add_argument("--feedback-text", default=None)
    parser.add_argument("--feedback-file", default=None)
    parser.add_argument("--edpr-json", default=None)
    parser.add_argument("--experience-json", default=None)
    parser.add_argument("--linked-experience-id", default=None)
    parser.add_argument("--feedback-id", default=None)
    parser.add_argument("--feedback-type", choices=(
        "clarification",
        "correction",
        "missing_constraint",
        "missing_component",
        "incorrect_behavior",
        "wrong_assumption",
        "insufficient_evidence",
        "poor_plot",
        "plot_correction",
        "answer_format_requirement",
        "default_assumption",
        "design_objective_requirement",
        "better_design_alternative",
        "future_study",
    ), default=None)
    parser.add_argument("--output", "-o", required=True)
    parser.add_argument("--no-validate", action="store_true")
    args = parser.parse_args()

    record = build_record(args)
    output_path = Path(args.output)
    write_json(output_path, record)
    if not args.no_validate:
        validate_output(output_path)

    print(f"KEL feedback record written: {output_path}")
    print(f"Feedback type: {record['feedback_type']}")
    print(f"Priority: {record['structured_feedback']['priority']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
