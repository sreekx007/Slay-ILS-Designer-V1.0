#!/usr/bin/env python3
"""Smoke-test KEL graph change promotion."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_promote_accepted_kel_change(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    change = tmp_path / "change.json"
    review = tmp_path / "explicit_output_review.json"
    output = tmp_path / "implemented.json"
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
        "implementation_ref": None,
    }), encoding="utf-8")
    review.write_text(json.dumps({
        "schema": "kel-expert-review/0.1",
        "review_id": "kel:review:test",
        "linked_change_request_id": "kel:change:test",
        "status": "final",
        "decision": "accepted",
        "reviewer": "test-reviewer",
        "reviewed_utc": "2026-09-13T00:01:00Z",
        "decision_reason": "Implemented in test docs.",
        "required_evidence": [],
        "implementation_target": "knowledge/kel/",
        "implementation_reference": "knowledge/kel/KEL_LLM_WORKFLOW_INSTRUCTIONS.md",
    }), encoding="utf-8")

    result = subprocess.run([
        sys.executable,
        str(repo_root / "tools" / "kel" / "promote_accepted_kel_change.py"),
        "--change-request",
        str(change),
        "--review",
        str(review),
        "--status",
        "implemented",
        "--output",
        str(output),
    ], cwd=repo_root, text=True, capture_output=True)
    assert result.returncode == 0, result.stderr

    record = json.loads(output.read_text(encoding="utf-8"))
    assert record["status"] == "implemented"
    assert record["expert_review_ref"]["id"] == "kel:review:test"
    assert record["implementation_ref"]["repo_path"] == "knowledge/kel/KEL_LLM_WORKFLOW_INSTRUCTIONS.md"
    assert not (repo_root / "knowledge" / "kel" / "expert_reviews" / "final" / review.name).exists()


def test_rejected_review_cannot_be_promoted_as_accepted(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    change = tmp_path / "change.json"
    review = tmp_path / "rejected_review.json"
    output = tmp_path / "accepted.json"
    change.write_text(json.dumps({
        "schema": "kel-graph-change-request/0.1",
        "change_request_id": "kel:change:rejected-test",
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
        "implementation_ref": None,
    }), encoding="utf-8")
    review.write_text(json.dumps({
        "schema": "kel-expert-review/0.1",
        "review_id": "kel:review:rejected-test",
        "linked_change_request_id": "kel:change:rejected-test",
        "status": "final",
        "decision": "rejected",
        "reviewer": "test-reviewer",
        "reviewed_utc": "2026-09-13T00:01:00Z",
        "decision_reason": "Rejected for smoke test.",
        "required_evidence": [],
        "implementation_target": None,
        "implementation_reference": None,
    }), encoding="utf-8")
    result = subprocess.run([
        sys.executable,
        str(repo_root / "tools" / "kel" / "promote_accepted_kel_change.py"),
        "--change-request", str(change), "--review", str(review),
        "--status", "accepted", "--output", str(output),
    ], cwd=repo_root, text=True, capture_output=True)
    assert result.returncode != 0
    assert "conflicts with review decision" in result.stderr
    assert not output.exists()
