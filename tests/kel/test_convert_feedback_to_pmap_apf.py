#!/usr/bin/env python3
"""Smoke-test KEL feedback conversion."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_convert_feedback_to_pmap_apf(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    output = tmp_path / "feedback.json"
    cmd = [
        sys.executable,
        str(repo_root / "tools" / "kel" / "convert_feedback_to_pmap_apf.py"),
        "--feedback-text",
        "The valve should not be near the roller and the transition is too short.",
        "--edpr-json",
        str(repo_root / "knowledge" / "edpr" / "examples" / "EDPR_EXAMPLE_GDVLV_NO_ROLLER_CONTACT.json"),
        "--linked-experience-id",
        "kel:experience:test",
        "--output",
        str(output),
    ]
    result = subprocess.run(cmd, cwd=repo_root, text=True, capture_output=True)
    assert result.returncode == 0, result.stderr

    record = json.loads(output.read_text(encoding="utf-8"))
    assert record["schema"] == "kel-feedback-to-pmap-apf/0.1"
    assert record["feedback_type"] == "missing_constraint"
    assert record["structured_feedback"]["priority"] == "high"


def test_convert_feedback_to_output_policy(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    output = tmp_path / "feedback_output_policy.json"
    cmd = [
        sys.executable,
        str(repo_root / "tools" / "kel" / "convert_feedback_to_pmap_apf.py"),
        "--feedback-text",
        "Always give a text based illustration for initial overview and always ask whether the human needs a plot.",
        "--linked-experience-id",
        "kel:experience:test",
        "--output",
        str(output),
    ]
    result = subprocess.run(cmd, cwd=repo_root, text=True, capture_output=True)
    assert result.returncode == 0, result.stderr

    record = json.loads(output.read_text(encoding="utf-8"))
    assert record["feedback_type"] == "answer_format_requirement"
    assert record["structured_feedback"]["apf_action"] == "add_or_update_kel_output_presentation_policy"


def test_convert_feedback_to_default_assumption(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    output = tmp_path / "feedback_default_assumption.json"
    cmd = [
        sys.executable,
        str(repo_root / "tools" / "kel" / "convert_feedback_to_pmap_apf.py"),
        "--feedback-text",
        "Record default condition for valves that they cannot ride the rollers or take contact loads.",
        "--linked-experience-id",
        "kel:experience:test",
        "--output",
        str(output),
    ]
    result = subprocess.run(cmd, cwd=repo_root, text=True, capture_output=True)
    assert result.returncode == 0, result.stderr

    record = json.loads(output.read_text(encoding="utf-8"))
    assert record["feedback_type"] == "default_assumption"
    assert record["structured_feedback"]["priority"] == "high"
