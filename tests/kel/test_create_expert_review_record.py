#!/usr/bin/env python3
"""Smoke-test KEL expert review record creation."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_create_expert_review_record(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    change = tmp_path / "change.json"
    output = tmp_path / "review.json"
    change.write_text(json.dumps({
        "schema": "kel-graph-change-request/0.1",
        "change_request_id": "kel:change:test",
        "status": "pending",
        "created_utc": "2026-09-13T00:00:00Z",
        "linked_experience_id": "kel:experience:test",
        "linked_feedback_id": "kel:feedback:test",
        "target_layer": "KEL",
        "change_type": "new_workflow_gate",
        "problem_observed": "Test problem.",
        "proposed_change": "Test change.",
        "evidence_requirement": "Test evidence.",
        "priority": "high",
        "expert_review_ref": None,
    }), encoding="utf-8")

    result = subprocess.run([
        sys.executable,
        str(repo_root / "tools" / "kel" / "create_expert_review_record.py"),
        "--change-request",
        str(change),
        "--reviewer",
        "test-reviewer",
        "--decision",
        "accepted",
        "--decision-reason",
        "Accepted for smoke test.",
        "--output",
        str(output),
    ], cwd=repo_root, text=True, capture_output=True)
    assert result.returncode == 0, result.stderr

    record = json.loads(output.read_text(encoding="utf-8"))
    assert record["schema"] == "kel-expert-review/0.1"
    assert record["status"] == "final"
    assert record["decision"] == "accepted"
    assert record["implementation_target"] == "knowledge/kel/"
