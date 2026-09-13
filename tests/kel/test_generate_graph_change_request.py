#!/usr/bin/env python3
"""Smoke-test KEL graph change request generation."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_generate_graph_change_request(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    feedback = tmp_path / "feedback.json"
    output = tmp_path / "change.json"
    feedback.write_text(json.dumps({
        "schema": "kel-feedback-to-pmap-apf/0.1",
        "feedback_id": "kel:feedback:test:vertical_connector",
        "linked_experience_id": "kel:experience:test",
        "created_utc": "2026-09-13T00:00:00Z",
        "raw_feedback_text": "A vertical connector needs a Z-shaped GD-B branch.",
        "feedback_type": "correction",
        "structured_feedback": {
            "affected_requirement": None,
            "affected_function": None,
            "affected_behavior": None,
            "affected_structure": None,
            "affected_constraint": None,
            "pmap_issue": "A vertical connector needs a Z-shaped GD-B branch.",
            "apf_action": "revise_solution_or_knowledge_item_after_expert_review",
            "priority": "high",
        },
    }), encoding="utf-8")

    result = subprocess.run([
        sys.executable,
        str(repo_root / "tools" / "kel" / "generate_graph_change_request.py"),
        str(feedback),
        "--output",
        str(output),
    ], cwd=repo_root, text=True, capture_output=True)
    assert result.returncode == 0, result.stderr

    record = json.loads(output.read_text(encoding="utf-8"))
    assert record["schema"] == "kel-graph-change-request/0.1"
    assert record["target_layer"] == "EDAS"
    assert record["change_type"] == "new_assembly_constraint"
    assert record["priority"] == "high"
