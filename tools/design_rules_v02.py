#!/usr/bin/env python3
"""Shared KEL v0.2 design-intent extraction and fail-closed workflow rules.

The functions in this module are deliberately deterministic.  They do not
replace the EDPR LLM parser; they validate the parser output and provide a
safe fallback for the two phrases that motivated KEL v0.2.
"""

from __future__ import annotations

import json
import re
from typing import Any


Z_ANCHOR_PREFIX = "ILT-Z-"
L_ANCHOR_PREFIX = "ILT-L-"


def _walk(value: Any):
    yield value
    if isinstance(value, dict):
        for child in value.values():
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def _text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False).lower()


def _structured_orientation(edpr: dict[str, Any]) -> tuple[str | None, str | None]:
    explicit = edpr.get("designContext", {}).get("workflowIntent", {}).get("connectorOrientation")
    if isinstance(explicit, str) and explicit.lower() in {"vertical", "horizontal"}:
        return explicit.lower(), "designContext.workflowIntent.connectorOrientation"
    for section in ("knownInputs", "constraints", "requirements"):
        for item in edpr.get(section, []):
            if not isinstance(item, dict):
                continue
            parameter = str(item.get("parameter") or item.get("name") or "").lower()
            value = str(item.get("value") or item.get("statement") or "").lower()
            if "connector" in parameter or "connector" in value:
                if re.search(r"\bvertical\b", value):
                    return "vertical", f"{section}.{item.get('id', 'item')}"
                if re.search(r"\bhorizontal\b", value):
                    return "horizontal", f"{section}.{item.get('id', 'item')}"
    return None, None


def _raw_orientation(raw: str) -> tuple[str | None, str | None]:
    # Requiring both words in one short phrase keeps branch direction and
    # drawing orientation separate from connector orientation.
    patterns = {
        "vertical": r"(?:vertical\s+connector|connector(?:\s+\w+){0,3}\s+vertical)",
        "horizontal": r"(?:horizontal\s+connector|connector(?:\s+\w+){0,3}\s+horizontal)",
    }
    for orientation, pattern in patterns.items():
        if re.search(pattern, raw, re.I):
            return orientation, "sourceRequest.rawText"
    return None, None


def _capacity_ratio(text: str, explicit: Any) -> float | None:
    if isinstance(explicit, (int, float)):
        value = float(explicit)
        return value / 100.0 if value > 1.0 else value
    match = re.search(r"(?:capacity[^.%]{0,30}|)(\d+(?:\.\d+)?)\s*%\s+of\s+the\s+pipeline", text, re.I)
    return float(match.group(1)) / 100.0 if match else None


def extract_design_intent(edpr: dict[str, Any]) -> dict[str, Any]:
    """Return normalized intent without inventing engineering inputs."""
    raw = str(edpr.get("sourceRequest", {}).get("rawText") or edpr.get("problem", {}).get("raw_text") or "")
    workflow = edpr.get("designContext", {}).get("workflowIntent", {})
    if not isinstance(workflow, dict):
        workflow = {}
    orientation, orientation_source = _structured_orientation(edpr)
    if orientation is None:
        orientation, orientation_source = _raw_orientation(raw)

    lower = raw.lower()
    objective_text = " ".join(str(v) for v in _walk(edpr.get("objectiveFunction", [])) if isinstance(v, str)).lower()
    strain_optimization = bool(re.search(r"(?:minimi[sz]e|minimum|lowest|reduc(?:e|tion)|optim(?:i[sz]e|um)).{0,24}strain|strain.{0,24}(?:minimi[sz]e|minimum|lowest|reduc(?:e|tion)|optim)", lower + " " + objective_text))
    strain_moment_terms = bool(re.search(r"\b(strain|moment|bending|curvature)\b", lower + " " + objective_text))
    confirmation = workflow.get("edprConfirmation", {})
    if not isinstance(confirmation, dict):
        confirmation = {}
    confirmation_status = str(confirmation.get("status") or "required_before_design")

    valve_cfg = workflow.get("valveProtection", {})
    if not isinstance(valve_cfg, dict):
        valve_cfg = {}
    valve_present = bool(re.search(r"\bvalve\b", lower)) or bool(valve_cfg)
    capacity = _capacity_ratio(raw, valve_cfg.get("capacityRatio"))
    protection_requested = bool(valve_cfg) or bool(re.search(r"\b(protect|protection|support|base structure|ea-sb|gd-sb)\b", lower)) or capacity is not None
    header_valve_requires_base = valve_present

    required = {
        "roller_passage_in_scope": valve_cfg.get("rollerPassageInScope"),
        "protection_mode": valve_cfg.get("protectionMode"),
        "valve_envelope": valve_cfg.get("valveEnvelope"),
        "actuator_envelope": valve_cfg.get("actuatorEnvelope"),
        "flange_envelope": valve_cfg.get("flangeEnvelope"),
        "local_thick_section_envelope": valve_cfg.get("localThickSectionEnvelope"),
        "roller_geometry": valve_cfg.get("rollerGeometry"),
        "required_clearance": valve_cfg.get("requiredClearance"),
        "load_cases": valve_cfg.get("loadCases"),
        "acceptance_measure": valve_cfg.get("acceptanceMeasure"),
        "connector_spacing_basis": valve_cfg.get("connectorSpacingBasis"),
        "connector_system": valve_cfg.get("connectorSystem"),
        "connector_evidence_refs": valve_cfg.get("connectorEvidenceRefs"),
        "moment_evidence": valve_cfg.get("momentEvidence"),
    }
    missing = [key for key, value in required.items() if value in (None, "", [], {})]
    if capacity is None:
        missing.append("valve_capacity_ratio")
    moment_check = {"status": "not_evaluated", "cases": []}
    moment = required.get("moment_evidence")
    if isinstance(moment, dict) and capacity is not None:
        cases = moment.get("cases") if isinstance(moment.get("cases"), list) else [moment]
        checked = []
        for index, case in enumerate(cases, 1):
            if not isinstance(case, dict):
                continue
            maximum = case.get("maximum_valve_moment_kNm")
            allowable = case.get("pipeline_allowable_moment_kNm")
            if isinstance(maximum, (int, float)) and isinstance(allowable, (int, float)) and allowable > 0:
                utilization = float(maximum) / (capacity * float(allowable))
                checked.append({"id": case.get("id", f"case_{index}"), "utilization": utilization, "status": "passed" if utilization <= 1.0 else "failed"})
        if checked:
            moment_check = {"status": "passed" if all(case["status"] == "passed" for case in checked) else "failed", "cases": checked}
        else:
            required["moment_evidence"] = None
            if "moment_evidence" not in missing:
                missing.append("moment_evidence")
    evidence_fields = {"connector_evidence_refs", "moment_evidence"}
    clarification_missing = [key for key in missing if key not in evidence_fields]
    evidence_missing = [key for key in missing if key in evidence_fields]
    if header_valve_requires_base and clarification_missing:
        valve_status = "needs_clarification"
    elif header_valve_requires_base and evidence_missing:
        valve_status = "needs_evidence"
    elif header_valve_requires_base:
        valve_status = "ready"
    else:
        valve_status = "not_applicable"

    two_cfg = workflow.get("twoBranchValves", {})
    if not isinstance(two_cfg, dict):
        two_cfg = {}
    two_requested = bool(two_cfg) or bool(re.search(r"\b(?:two|2)\s+(?:branch\s+)?valves?\b", lower))
    topology = two_cfg.get("topology")
    instances = two_cfg.get("instances") if isinstance(two_cfg.get("instances"), list) else []
    two_missing = []
    if two_requested:
        if topology not in {"two_on_one_branch", "one_on_each_of_two_branches"}:
            two_missing.append("accepted_topology")
        if len(instances) != 2 or any(not isinstance(v, dict) or not v.get("id") or not v.get("parentBranch") for v in instances):
            two_missing.append("two_distinct_valve_instances_with_parent_branch")

    return {
        "connector": {
            "required_orientation": orientation,
            "source": orientation_source,
            "branch_routing_is_separate": True,
            "drawing_orientation_is_separate": True,
        },
        "edpr_confirmation": {
            "status": confirmation_status,
            "confirmed": confirmation_status in {"confirmed", "reviewed_confirmed", "user_confirmed"},
            "rule": "Emit EDPR/problem understanding for user review before concept generation or layout emission.",
        },
        "objectives": {
            "strain_optimization_requested": strain_optimization,
            "strain_moment_reduction_default": not strain_optimization,
            "strain_moment_terms_present": strain_moment_terms,
            "rule": "Every concept must at least consider reduction of high strain and bending moment; formal optimization requires an explicit objective and compatible evidence.",
        },
        "valve_protection": {
            "valve_present": valve_present,
            "gate_required": bool(header_valve_requires_base),
            "capacity_ratio": capacity,
            "inputs": required,
            "missing_inputs": missing if header_valve_requires_base else [],
            "missing_clarifications": clarification_missing if header_valve_requires_base else [],
            "missing_evidence": evidence_missing if header_valve_requires_base else [],
            "status": valve_status,
            "moment_check": moment_check,
            "rule": "A header valve or other header component that cannot bear roller contact requires GD-SB protection; an 80% valve capacity is a constraint, not a support selection.",
        },
        "two_branch_valves": {
            "requested": two_requested,
            "topology": topology,
            "instances": instances,
            "missing_inputs": two_missing,
            "status": "representation_gap" if two_requested and two_missing else "ready" if two_requested else "not_applicable",
        },
    }


def workflow_blockers(intent: dict[str, Any]) -> list[dict[str, Any]]:
    blockers: list[dict[str, Any]] = []
    confirmation = intent.get("edpr_confirmation", {})
    if confirmation and not confirmation.get("confirmed"):
        blockers.append({
            "code": "EDPR_CONFIRMATION_REQUIRED",
            "status": "needs_user_confirmation",
            "required_action": "Emit EDPR/problem understanding and wait for user confirmation before design generation or layout emission.",
        })
    valve = intent.get("valve_protection", {})
    if valve.get("status") == "needs_clarification":
        blockers.append({
            "code": "VALVE_PROTECTION_INPUTS_MISSING",
            "status": "needs_clarification",
            "missing": valve.get("missing_inputs", []),
            "required_action": "Capture envelope, roller/contact, clearance, load-case, connector-spacing and compatible moment-evidence inputs before selecting EA-SB.",
        })
    if valve.get("moment_check", {}).get("status") == "failed":
        blockers.append({
            "code": "VALVE_MOMENT_CAPACITY_EXCEEDED",
            "status": "failed",
            "cases": valve.get("moment_check", {}).get("cases", []),
            "required_action": "Reject or redesign the concept; valve moment utilization exceeds 1.0.",
        })
    if valve.get("status") == "needs_evidence":
        blockers.append({
            "code": "VALVE_PROTECTION_EVIDENCE_MISSING",
            "status": "needs_evidence",
            "missing": valve.get("missing_evidence", []),
            "required_action": "Create a combined GD-VLV + GD-SB FEA study for connector selection and valve bending moment.",
            "study_candidate": {"type": "future_fea_study", "components": ["GD-VLV", "GD-SB"], "outputs": ["maximum valve bending moment", "pipeline response", "connector loads"]},
        })
    two = intent.get("two_branch_valves", {})
    if two.get("status") == "representation_gap":
        blockers.append({
            "code": "TWO_BRANCH_VALVE_TOPOLOGY_UNRESOLVED",
            "status": "representation_gap",
            "missing": two.get("missing_inputs", []),
            "required_action": "Expert review must fix the topology and two branch-owned valve instances before layout emission.",
        })
    return blockers


def eligible_anchor_ids(library: dict[str, Any], intent: dict[str, Any]) -> list[str]:
    ids = [str(item.get("id")) for item in library.get("anchors", []) if isinstance(item, dict)]
    if intent.get("connector", {}).get("required_orientation") == "vertical":
        return sorted(value for value in ids if value.startswith(Z_ANCHOR_PREFIX))
    return sorted(ids)


def choose_vertical_anchor(recommended: str | None, eligible: list[str]) -> str | None:
    if not eligible:
        return None
    name = str(recommended or "")
    if name.startswith(Z_ANCHOR_PREFIX) and name in eligible:
        return name
    if name.startswith(L_ANCHOR_PREFIX):
        direct = Z_ANCHOR_PREFIX + name[len(L_ANCHOR_PREFIX):]
        if direct in eligible:
            return direct
    # Preserve the connection system first, then FT/ST support taxonomy.
    tokens = name.replace("ILT-", "").split("-")
    system = tokens[-1] if tokens else ""
    support = tokens[-2] if len(tokens) > 1 else ""
    ranked = sorted(eligible, key=lambda x: (not x.endswith("-" + system), f"-{support}-" not in x, x))
    return ranked[0] if ranked else None


def validate_layout_against_intent(spec: dict[str, Any], intent: dict[str, Any]) -> list[dict[str, str]]:
    gaps: list[dict[str, str]] = []
    components = spec.get("components", [])
    branches = [c for c in components if c.get("code") == "GD-B"]
    tops = [c for c in components if c.get("code") == "GD-ST"]
    if branches:
        if not tops:
            gaps.append({
                "code": "BRANCH_REQUIRES_GD_ST",
                "message": "Every GD-B branch assembly must terminate at a GD-ST top-frame feature.",
            })
        else:
            branch_ids = {str(c.get("id") or f"branch_{index}") for index, c in enumerate(branches, 1)}
            top_ids = {str(c.get("id") or f"top_{index}") for index, c in enumerate(tops, 1)}
            anchored = set()
            for association in spec.get("associations", []) or []:
                if association.get("type") != "Connection":
                    continue
                ends = {
                    str((association.get("from") or {}).get("component")),
                    str((association.get("to") or {}).get("component")),
                }
                if ends & branch_ids and ends & top_ids:
                    anchored.update(ends & branch_ids)
            unanchored = sorted(branch_ids - anchored)
            if unanchored:
                gaps.append({
                    "code": "BRANCH_GD_ST_ASSOCIATION_REQUIRED",
                    "message": "Every GD-B branch requires a declared terminal association to GD-ST; unanchored branches: " + ", ".join(unanchored),
                })
    if intent.get("connector", {}).get("required_orientation") == "vertical":
        if not branches or any(c.get("variant", "L") != "Z" for c in branches):
            gaps.append({"code": "VERTICAL_CONNECTOR_REQUIRES_GD_B_Z", "message": "A vertical connector requires every selected branch to use GD-B variant Z and an ILT-Z-* anchor."})
    valve = intent.get("valve_protection", {})
    if valve.get("gate_required"):
        bases = [c for c in spec.get("components", []) if c.get("code") == "GD-SB"]
        if not bases:
            gaps.append({"code": "HEADER_VALVE_REQUIRES_GD_SB", "message": "A header GD-VLV or other non-roller-contact header component requires canonical GD-SB geometry; a generic frame or unsupported valve-only layout is insufficient."})
        else:
            required = {"P_l1", "P_l2", "P_v", "P_vt"}
            for index, base in enumerate(bases, 1):
                defaulted = sorted(required - set(base))
                if defaulted:
                    gaps.append({
                        "code": "SUPPORT_STRUCTURE_DIMENSIONS_DEFAULTED",
                        "message": "GD-SB used to protect GD-VLV must be dimensioned from the valve envelope and clearance basis instead of left at generic EDAS defaults.",
                        "component": str(base.get("id") or f"GD-SB[{index}]"),
                        "defaulted_parameters": defaulted,
                    })
    return gaps


def valve_moment_utilization(maximum_valve_moment: float, capacity_ratio: float, pipeline_allowable_moment: float) -> float:
    if maximum_valve_moment < 0 or not 0 < capacity_ratio <= 1 or pipeline_allowable_moment <= 0:
        raise ValueError("Moment must be non-negative, capacity ratio in (0, 1], and pipeline allowable moment positive")
    return maximum_valve_moment / (capacity_ratio * pipeline_allowable_moment)



