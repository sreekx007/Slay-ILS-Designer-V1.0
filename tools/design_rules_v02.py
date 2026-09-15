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
    branch_valve_cfg = workflow.get("branchValve", {})
    if not isinstance(branch_valve_cfg, dict):
        branch_valve_cfg = {}
    branch_valve_requested = bool(branch_valve_cfg) or bool(re.search(
        r"\b(?:branch(?:\s+line|\s+pipe)?|horizontal\s+leg)\b.{0,80}\bvalve\b|\bvalve\b.{0,80}\b(?:branch(?:\s+line|\s+pipe)?|horizontal\s+leg)\b",
        lower,
    ))
    capacity = _capacity_ratio(raw, valve_cfg.get("capacityRatio"))
    protection_requested = bool(valve_cfg) or bool(re.search(r"\b(protect|protection|support|base structure|ea-sb|gd-sb)\b", lower)) or capacity is not None
    header_valve_requires_base = bool(valve_cfg) or bool(valve_present and not branch_valve_requested)

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

    shroud_cfg = workflow.get("shroudStiffComponent", {})
    if not isinstance(shroud_cfg, dict):
        shroud_cfg = {}
    shroud_text = lower + " " + _text(workflow)
    shroud_present = bool(re.search(r"\b(?:shroud|gd-sh|tapered\s+shrouds?)\b", shroud_text)) or bool(shroud_cfg)
    stiff_inline_present = valve_present or bool(re.search(r"\b(?:gd-vlv|gd-tt|gd-tp|thick\s+(?:pipe|body|component)|stiff\s+(?:pipe|body|component))\b", shroud_text))
    shroud_interaction_required = bool(shroud_present and stiff_inline_present)

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
        "branch_valve": {
            "requested": branch_valve_requested,
            "location": branch_valve_cfg.get("location") or ("horizontal_leg" if re.search(r"\bhorizontal\s+leg\b", lower) else "branch_line" if branch_valve_requested else None),
            "top_frame_required": bool(branch_valve_requested),
            "preferred_standard_anchor": "ILT-Z-FT-PS" if orientation == "vertical" else "ILT-L-FT-PS" if orientation == "horizontal" else None,
            "avoid_connection_systems_without_basis": ["F2", "F2D"],
            "default_connection_system": "PS",
            "rule": "For a branch valve, keep the branch entry, branch valve and branch end inside the GD-ST span. Do not default to F2/F2D unless a strain/moment evidence basis justifies a low-strain pocket on the branch and accepts the header penalty.",
            "status": "requires_top_frame_containment_gate" if branch_valve_requested else "not_applicable",
        },
        "shroud_stiff_component": {
            "required": shroud_interaction_required,
            "components": [code for code, present in (("GD-SH", shroud_present), ("GD-VLV", valve_present)) if present],
            "analogous_precedent": "ILS-SHTP / GD-SH + GD-TP or GD-TT",
            "required_knowledge_refs": [
                "edes:GD-SH",
                "edes:GD-VLV",
                "edas:ILS-SHTP",
                "edikb:p1_c1_shtp_nonadditive_01",
                "edikb:p1_c1_shtp_location_01",
                "edikb:p1_c1_shtp_peakloc_01",
                "edikb:p1_c1_shtp_size_01",
                "edikb:guidance_keep_gdtp_out_of_shroud_x2",
                "edikb:guidance_limit_gdtp_size_inside_shroud",
                "edikb:guidance_consider_long_shroud_only_with_verification",
            ],
            "status": "requires_edikb_retrieval" if shroud_interaction_required else "not_applicable",
            "rule": "When GD-VLV is combined with GD-SH, treat the valve as a stiff inline component inside an offset shroud and retrieve the analogous C1 GD-SH + thick-component EDIKB evidence before recommending placement or shroud length.",
            "judgement_failure_flag": "Do not dismiss existing GD-TT/GD-TP + GD-SH evidence as irrelevant merely because the stiff component is a valve; flag a retrieval-usefulness judgement failure if those EDIKB nodes are not selected.",
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

    basis = spec.get("design_basis", {}) if isinstance(spec.get("design_basis", {}), dict) else {}
    branch_valve_intent = intent.get("branch_valve", {}) if isinstance(intent.get("branch_valve", {}), dict) else {}
    branch_valve_required = bool(branch_valve_intent.get("requested"))
    if branch_valve_required or any("P_bv" in c or "mass_valve" in c for c in branches):
        top_by_id = {str(c.get("id") or f"top_{index}"): c for index, c in enumerate(tops, 1)}
        branch_to_top: dict[str, str] = {}
        branch_ids = {str(c.get("id") or f"branch_{index}") for index, c in enumerate(branches, 1)}
        top_ids = set(top_by_id)
        for association in spec.get("associations", []) or []:
            if association.get("type") != "Connection":
                continue
            ends = [
                str((association.get("from") or {}).get("component")),
                str((association.get("to") or {}).get("component")),
            ]
            linked_branch = next((item for item in ends if item in branch_ids), None)
            linked_top = next((item for item in ends if item in top_ids), None)
            if linked_branch and linked_top:
                branch_to_top[linked_branch] = linked_top
        outside_messages = []
        for index, branch in enumerate(branches, 1):
            branch_id = str(branch.get("id") or f"branch_{index}")
            explicit_branch_valve = branch_valve_required or "P_bv" in branch or "mass_valve" in branch
            if not explicit_branch_valve:
                continue
            top = top_by_id.get(branch_to_top.get(branch_id, ""))
            if not top:
                continue
            try:
                tee_x = float(branch.get("centre_x", 0.0))
                p_b1 = float(branch.get("P_b1"))
                p_bv = float(branch.get("P_bv", p_b1 / 2.0))
                st_cx = float(top.get("centre_x", 0.0))
                st_len = float(top.get("L_top"))
            except (TypeError, ValueError):
                continue
            span = (st_cx - st_len / 2.0, st_cx + st_len / 2.0)
            points = {"tee": tee_x, "valve": tee_x + p_bv, "end": tee_x + p_b1}
            outside = {name: value for name, value in points.items() if value < span[0] - 1e-6 or value > span[1] + 1e-6}
            if outside:
                outside_messages.append(f"{branch_id} outside GD-ST span {span}: " + ", ".join(f"{k}={v:.4f}" for k, v in outside.items()))
        if outside_messages:
            gaps.append({
                "code": "BRANCH_VALVE_OUTSIDE_GD_ST_SPAN",
                "message": "Branch-valve layouts must keep branch tee/entry, branch valve, and branch end inside the associated GD-ST top-frame span; " + "; ".join(outside_messages),
            })
        connection_system = str((spec.get("ils") or {}).get("connection_system") or "").upper()
        f2_basis = basis.get("connection_system_basis") or basis.get("f2_evidence_refs")
        if connection_system in {"F2", "F2D"} and f2_basis in (None, "", [], {}):
            gaps.append({
                "code": "UNJUSTIFIED_F2_FOR_BRANCH_VALVE",
                "message": "F2/F2D shall not be selected by default for a branch-valve top-frame layout; provide strain/moment evidence for the low-strain branch pocket and the accepted header penalty, otherwise prefer the PS standard anchor.",
            })

    has_valve_shroud = any(c.get("code") == "GD-VLV" for c in components) and any(c.get("code") == "GD-SH" for c in components)
    if has_valve_shroud or intent.get("shroud_stiff_component", {}).get("required"):
        required_basis = {
            "shroud_stiff_evidence_refs",
            "shroud_dimensions_basis",
            "stiff_component_position_basis",
            "shroud_regions_basis",
            "applicability_limits",
        }
        missing_basis = sorted(name for name in required_basis if basis.get(name) in (None, "", [], {}))
        if missing_basis:
            gaps.append({
                "code": "SHROUD_STIFF_EVIDENCE_NOT_APPLIED",
                "message": "GD-VLV + GD-SH layouts must apply analogous C1 GD-SH + stiff-component EDIKB evidence to shroud V/L1/L2 and valve placement; retrieval alone is insufficient.",
                "missing_basis": missing_basis,
                "required_evidence_refs": intent.get("shroud_stiff_component", {}).get("required_knowledge_refs", []),
            })
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



