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
    intent = extract_design_intent({"sourceRequest": {"rawText": "The branch connector shall be vertical."}})
    assert intent["connector"]["required_orientation"] == "vertical"
    spec, report = materialize({"design_intent": intent, "recommendation": {"recommended_candidate": "L-FT-F2"}})
    assert report["source_anchor"].startswith("ILT-Z-")
    assert next(c for c in spec["components"] if c["code"] == "GD-B")["variant"] == "Z"
    bad = json.loads(json.dumps(spec))
    next(c for c in bad["components"] if c["code"] == "GD-B")["variant"] = "L"
    assert validate_layout_against_intent(bad, intent)[0]["code"] == "VERTICAL_CONNECTOR_REQUIRES_GD_B_Z"
    unrelated = extract_design_intent({"sourceRequest": {"rawText": "Route the branch vertically; connector direction is unknown."}})
    assert unrelated["connector"]["required_orientation"] is None


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
    assert validate_layout_against_intent(generic, complete_intent)[0]["code"] == "EA_SB_REQUIRES_GD_SB"


def test_ps_without_compatible_valve_evidence_creates_fea_candidate() -> None:
    fixture = json.loads((ROOT / "tests/kel/fixtures/VALVE_EASB_COMPLETE_DESIGN.json").read_text(encoding="utf-8"))
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

