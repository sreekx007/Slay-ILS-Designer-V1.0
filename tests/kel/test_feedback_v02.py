#!/usr/bin/env python3
"""Regression tests for KEL v0.2 decomposition, grouping, and lifecycle repair."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
TOOLS = REPO_ROOT / "tools" / "kel"


def run_tool(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, *args], cwd=REPO_ROOT, text=True, capture_output=True)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_compound_valve_feedback_decomposes_into_five_stable_records(tmp_path: Path) -> None:
    source = REPO_ROOT / "tests" / "kel" / "fixtures" / "VALVE_EASB_COMPOUND_FEEDBACK.json"
    output = tmp_path / "atomic"
    command = (str(TOOLS / "decompose_feedback.py"), str(source), "--output-dir", str(output))
    first = run_tool(*command)
    assert first.returncode == 0, first.stderr
    paths = sorted(output.glob("*.json"))
    assert len(paths) == 5
    records = [load(path) for path in paths]
    assert {record["group_key"] for record in records} == {
        "valve_base_depth_clearance",
        "base_length_strain_evidence",
        "connector_system_valve_moment_evidence",
        "valve_top_frame_requirement",
        "connector_spacing_basis",
    }
    assert {record["source_feedback_id"] for record in records} == {"kel:feedback:valve_easb:compound_review"}
    assert len({record["fingerprint"] for record in records}) == 5
    before = {path.name: path.read_bytes() for path in paths}
    second = run_tool(*command)
    assert second.returncode == 0, second.stderr
    assert before == {path.name: path.read_bytes() for path in paths}


def test_q1_east_feedback_groups_into_one_traceable_change_request(tmp_path: Path) -> None:
    sources = [
        REPO_ROOT / "knowledge" / "kel" / "feedback_records" / "candidates" / name
        for name in (
            "Q1_03_BRANCH_CONNECTOR_EAST_DEFAULT.json",
            "Q1_05_EAST_CONNECTIONS_LABELLED.json",
            "Q1_11_EAST_PARAMETERS_CONNECTIONS.json",
        )
    ]
    atomic_dir = tmp_path / "atomic"
    result = run_tool(str(TOOLS / "decompose_feedback.py"), *map(str, sources), "--output-dir", str(atomic_dir))
    assert result.returncode == 0, result.stderr
    atomic_paths = sorted(atomic_dir.glob("*.json"))
    assert len(atomic_paths) == 3

    group_dir = tmp_path / "groups"
    result = run_tool(str(TOOLS / "group_feedback.py"), *map(str, atomic_paths), "--output-dir", str(group_dir))
    assert result.returncode == 0, result.stderr
    group_paths = sorted(group_dir.glob("*.json"))
    assert len(group_paths) == 1
    group = load(group_paths[0])
    assert group["group_key"] == "ea_st_parameters_connections_associations"
    assert len(group["member_feedback_ids"]) == 3
    assert len(group["source_feedback_ids"]) == 3
    assert group["grouping"]["review_required"] is True

    gcr = tmp_path / "grouped_gcr.json"
    result = run_tool(str(TOOLS / "generate_graph_change_request.py"), str(group_paths[0]), "--output", str(gcr))
    assert result.returncode == 0, result.stderr
    change = load(gcr)
    assert change["schema"] == "kel-graph-change-request/0.2"
    assert change["target_layer"] == "EDAS"
    assert len(change["linked_feedback_ids"]) == 3
    assert change["feedback_group_id"] == group["feedback_group_id"]

    review = tmp_path / "grouped_gcr.review.json"
    result = run_tool(
        str(TOOLS / "create_expert_review_record.py"), "--change-request", str(gcr),
        "--decision", "needs_evidence", "--reviewer", "test-reviewer",
        "--decision-reason", "Grouped request needs analysis evidence.", "--output", str(review),
    )
    assert result.returncode == 0, result.stderr
    promoted = tmp_path / "grouped_gcr.needs_evidence.json"
    result = run_tool(
        str(TOOLS / "promote_accepted_kel_change.py"), "--change-request", str(gcr),
        "--review", str(review), "--status", "needs_evidence", "--output", str(promoted),
    )
    assert result.returncode == 0, result.stderr
    promoted_record = load(promoted)
    assert promoted_record["schema"] == "kel-graph-change-request/0.2"
    assert promoted_record["status"] == "needs_evidence"
    assert len(promoted_record["linked_feedback_ids"]) == 3


def test_lifecycle_reconciliation_supersedes_pending_duplicate_idempotently(tmp_path: Path) -> None:
    root = tmp_path / "graph_change_requests"
    pending = root / "pending" / "Q1_GCR_08_MUST_USE_REPO_PLOTTER.json"
    implemented = root / "implemented" / pending.name
    pending.parent.mkdir(parents=True)
    implemented.parent.mkdir(parents=True)
    implemented_source = REPO_ROOT / "knowledge" / "kel" / "graph_change_requests" / "implemented" / pending.name
    implemented_record = load(implemented_source)
    pending_record = dict(implemented_record)
    pending_record["status"] = "pending"
    pending_record["expert_review_ref"] = None
    pending_record["implementation_ref"] = None
    pending.write_text(json.dumps(pending_record, indent=2) + "\n", encoding="utf-8")
    shutil.copy2(implemented_source, implemented)
    report_path = tmp_path / "report.json"

    result = run_tool(
        str(TOOLS / "reconcile_lifecycle.py"), "--lifecycle-root", str(root),
        "--apply", "--report", str(report_path),
    )
    assert result.returncode == 0, result.stderr
    assert not pending.exists()
    superseded = root / "superseded" / pending.name
    assert superseded.exists()
    record = load(superseded)
    assert record["schema"] == "kel-graph-change-request/0.2"
    assert record["status"] == "superseded"
    assert record["superseded_by"]["status"] == "implemented"
    assert len(load(report_path)["actions"]) == 1

    rerun_report = tmp_path / "report_rerun.json"
    result = run_tool(
        str(TOOLS / "reconcile_lifecycle.py"), "--lifecycle-root", str(root),
        "--apply", "--report", str(rerun_report),
    )
    assert result.returncode == 0, result.stderr
    assert load(rerun_report)["actions"] == []
