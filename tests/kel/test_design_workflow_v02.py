#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
PLOTTERS = ROOT / "plotters"
sys.path.insert(0, str(TOOLS))
sys.path.insert(0, str(PLOTTERS))

from design_rules_v02 import extract_design_intent, validate_layout_against_intent, valve_moment_utilization
from solution_to_layout import materialize
from ils_builder import build_ils


def test_vertical_connector_is_distinct_and_selects_z_anchor() -> None:
    intent = extract_design_intent({"sourceRequest": {"rawText": "The branch connector shall be vertical."}, "designContext": {"workflowIntent": {"edprConfirmation": {"status": "confirmed"}}}})
    assert intent["connector"]["required_orientation"] == "vertical"
    spec, report = materialize({"design_intent": intent, "recommendation": {"recommended_candidate": "L-FT-F2"}})
    assert report["source_anchor"].startswith("ILT-Z-")
    assert next(c for c in spec["components"] if c["code"] == "GD-B")["variant"] == "Z"
    bad = json.loads(json.dumps(spec))
    next(c for c in bad["components"] if c["code"] == "GD-B")["variant"] = "L"
    assert validate_layout_against_intent(bad, intent)[0]["code"] == "VERTICAL_CONNECTOR_REQUIRES_GD_B_Z"
    unrelated = extract_design_intent({"sourceRequest": {"rawText": "Route the branch vertically; connector direction is unknown."}})
    assert unrelated["connector"]["required_orientation"] is None


def test_l_and_z_branches_require_declared_gdst_anchors() -> None:
    cases = (
        ("horizontal", "ILT-L-FT-F2", "L", "right1"),
        ("vertical", "ILT-Z-FT-F2", "Z", "top1"),
    )
    for orientation, candidate, variant, structure_feature in cases:
        intent = extract_design_intent({"sourceRequest": {"rawText": f"The branch connector shall be {orientation}."}, "designContext": {"workflowIntent": {"edprConfirmation": {"status": "confirmed"}}}})
        spec, _ = materialize({"design_intent": intent, "recommendation": {"recommended_candidate": candidate}})
        branch = next(c for c in spec["components"] if c["code"] == "GD-B")
        assert branch["variant"] == variant
        association = next(
            a for a in spec["associations"]
            if {a["from"]["component"], a["to"]["component"]} == {"B", "ST"}
        )
        assert association["to"]["feature"] == structure_feature
        gate = build_ils(spec).design_workflow_report()["branch_gd_st_gate"]
        assert gate["status"] == "passed"
        assert gate["unanchored_branch_ids"] == []

        missing_link = json.loads(json.dumps(spec))
        missing_link["associations"] = [
            a for a in missing_link["associations"]
            if {a["from"]["component"], a["to"]["component"]} != {"B", "ST"}
        ]
        gaps = validate_layout_against_intent(missing_link, intent)
        assert any(gap["code"] == "BRANCH_GD_ST_ASSOCIATION_REQUIRED" for gap in gaps)
        assert build_ils(missing_link).design_workflow_report()["branch_gd_st_gate"]["status"] == "failed"

    branch_only = json.loads(json.dumps(spec))
    branch_only["components"] = [c for c in branch_only["components"] if c["code"] != "GD-ST"]
    branch_only["associations"] = []
    branch_only["ils"]["design_gate"] = "advisory"
    gaps = validate_layout_against_intent(branch_only, intent)
    assert any(gap["code"] == "BRANCH_REQUIRES_GD_ST" for gap in gaps)
    report = build_ils(branch_only).design_workflow_report()
    assert report["status"] == "failed"
    assert "GD-B.requires.GD-ST" in report["unresolved_or_inactive_slots"]


def test_east_complete_gate_reports_parameters_slots_landings_and_associations() -> None:
    spec = {
        "schema_version": 1,
        "ils": {"name": "EA-ST complete fixture", "frame": "local", "connection_system": "F1", "ownership": "strict", "purpose": "detailed_design", "design_gate": "complete"},
        "pipeline": {"OD_pipe": 0.4064, "t_pipe": 0.021, "provenance": "DESIGN"},
        "components": [
            {"id": "TP", "code": "GD-TP", "centre_x": 0.0},
            {"id": "ST", "code": "GD-ST", "centre_x": 0.0, "L_top": 6.5, "H_top": 1.6, "P_vt": -0.6, "P_c1": 2.0, "P_c2": 1.0},
            {"id": "CON", "code": "GD-Con", "centre_x": 0.0, "conn_type": "F", "y_struct": -0.6}
        ],
        "associations": [
            {"type": "Connection", "connection": "F", "from": {"component": "TP", "feature": "conMid"}, "to": {"component": "CON", "feature": "pipeEnd"}},
            {"type": "Connection", "connection": "F", "from": {"component": "CON", "feature": "structEnd"}, "to": {"component": "ST", "feature": "slot3"}}
        ]
    }
    ils = build_ils(spec)
    report = ils.design_workflow_report()
    assert report["status"] == "passed"
    assert report["complete_design_claim_allowed"] is True
    st = report["ea_structures"][0]
    assert {"centre_x", "L_top", "H_top", "P_vt", "P_c1", "P_c2"} <= set(st["canonical_parameters"])
    assert st["active_connectors"][0]["connector_id"] == "CON"
    assert st["active_connectors"][0]["pipe_landing"] == "TP"
    assert not [f for f in ils.findings if f.severity == "error"]
    broken = json.loads(json.dumps(spec))
    broken["associations"].pop()
    assert any("ST.slot3.structure_association" in str(f) for f in build_ils(broken).findings)


def test_valve_query_stops_and_complete_fixture_uses_real_gdsb() -> None:
    query = {"sourceRequest": {"rawText": "An ILS layout is required. Header line is 12 inch and it has a valve. It has a bending moment capacity of 80% of the pipeline. Design a suitable layout."}}
    intent = extract_design_intent(query)
    assert intent["valve_protection"]["status"] == "needs_clarification"
    assert intent["objectives"]["strain_optimization_requested"] is False
    assert "roller_geometry" in intent["valve_protection"]["missing_inputs"]
    with pytest.raises(ValueError, match="VALVE_PROTECTION_INPUTS_MISSING"):
        materialize({"design_intent": intent, "recommendation": {"recommended_candidate": "ILT-L-FT-PS"}})

    fixture = json.loads((ROOT / "tests/kel/fixtures/VALVE_EASB_COMPLETE_DESIGN.json").read_text(encoding="utf-8"))
    complete_intent = extract_design_intent(fixture)
    assert complete_intent["valve_protection"]["status"] == "ready"
    assert valve_moment_utilization(400, 0.8, 625) == 0.8
    assert complete_intent["valve_protection"]["moment_check"]["cases"][0]["utilization"] == 0.8
    layout = fixture["layout"]
    assert not validate_layout_against_intent(layout, complete_intent)
    assert "GD-SB" in build_ils(layout).codes
    generic = json.loads(json.dumps(layout))
    generic["components"] = [c for c in generic["components"] if c["code"] != "GD-SB"]
    assert validate_layout_against_intent(generic, complete_intent)[0]["code"] == "HEADER_VALVE_REQUIRES_GD_SB"


def test_gdsb_protecting_valve_requires_explicit_sizing() -> None:
    intent = extract_design_intent({
        "sourceRequest": {"rawText": "Design an ILS assembly that consists of a valve welded inline with the pipeline."},
        "designContext": {"workflowIntent": {"edprConfirmation": {"status": "confirmed"}, "valveProtection": {
            "rollerPassageInScope": True,
            "protectionMode": "GD-SB",
            "valveEnvelope": {"source": "default GD-VLV"},
            "actuatorEnvelope": {"source": "default GD-VLV stem"},
            "flangeEnvelope": {"source": "not modelled"},
            "localThickSectionEnvelope": {"source": "not applicable"},
            "rollerGeometry": {"source": "placeholder"},
            "requiredClearance": 0.1,
            "loadCases": ["placeholder"],
            "acceptanceMeasure": "review_only",
            "connectorSpacingBasis": "placeholder",
            "connectorSystem": "PS",
            "connectorEvidenceRefs": ["placeholder"],
            "momentEvidence": {"cases": [{"id": "placeholder", "maximum_valve_moment_kNm": 10, "pipeline_allowable_moment_kNm": 100}]},
            "capacityRatio": 1.0
        }}}
    })
    defaulted = {
        "components": [
            {"id": "vlv1", "code": "GD-VLV", "centre_x": 0.0},
            {"id": "sb1", "code": "GD-SB", "centre_x": 0.0},
        ],
        "associations": []
    }
    gaps = validate_layout_against_intent(defaulted, intent)
    assert any(gap["code"] == "SUPPORT_STRUCTURE_DIMENSIONS_DEFAULTED" for gap in gaps)
    report = build_ils({"schema_version": 1, "ils": {"design_gate": "advisory"}, "pipeline": {"OD_pipe": 0.3048, "t_pipe": 0.0159}, **defaulted}).design_workflow_report()
    assert report["support_sizing_gate"]["status"] == "failed"
    assert "sb1.sizing.defaulted_to_EDAS" in report["unresolved_or_inactive_slots"]

    valve_sized = json.loads(json.dumps(defaulted))
    valve_sized["components"][1].update({"P_l1": 1.8, "P_l2": 0.18, "P_vt": -0.12, "P_v": 0.55})
    gaps = validate_layout_against_intent(valve_sized, intent)
    assert not [gap for gap in gaps if gap["code"] == "SUPPORT_STRUCTURE_DIMENSIONS_DEFAULTED"]
    report = build_ils({"schema_version": 1, "ils": {"design_gate": "advisory"}, "pipeline": {"OD_pipe": 0.3048, "t_pipe": 0.0159}, **valve_sized}).design_workflow_report()
    assert report["support_sizing_gate"]["status"] == "passed"


def test_ps_without_compatible_valve_evidence_creates_fea_candidate() -> None:
    fixture = json.loads((ROOT / "tests/kel/fixtures/VALVE_EASB_COMPLETE_DESIGN.json").read_text(encoding="utf-8"))
    fixture["designContext"]["workflowIntent"]["edprConfirmation"] = {"status": "confirmed"}
    cfg = fixture["designContext"]["workflowIntent"]["valveProtection"]
    cfg["connectorSystem"] = "PS"
    cfg.pop("connectorEvidenceRefs")
    cfg.pop("momentEvidence")
    intent = extract_design_intent(fixture)
    assert intent["valve_protection"]["status"] == "needs_evidence"
    from design_rules_v02 import workflow_blockers
    blocker = workflow_blockers(intent)[0]
    assert blocker["code"] == "VALVE_PROTECTION_EVIDENCE_MISSING"
    assert blocker["study_candidate"]["type"] == "future_fea_study"


def test_two_branch_valve_request_emits_representation_gap() -> None:
    intent = extract_design_intent({"sourceRequest": {"rawText": "Place two branch valves in the ILS."}})
    assert intent["two_branch_valves"]["status"] == "representation_gap"
    with pytest.raises(ValueError, match="TWO_BRANCH_VALVE_TOPOLOGY_UNRESOLVED"):
        materialize({"design_intent": intent, "recommendation": {"recommended_candidate": "ILT-L-FT-F2"}})

