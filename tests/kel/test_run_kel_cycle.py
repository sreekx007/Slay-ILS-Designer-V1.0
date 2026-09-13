#!/usr/bin/env python3
"""Smoke-test the KEL cycle wrapper dry-run path."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_run_kel_cycle_dry_run(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    result = subprocess.run([
        sys.executable,
        str(repo_root / "tools" / "kel" / "run_kel_cycle.py"),
        "--label",
        "smoke",
        "--output-dir",
        str(tmp_path / "cycle"),
        "--feedback-text",
        "Plot must use the repository plotter.",
        "--dry-run",
    ], cwd=repo_root, text=True, capture_output=True)
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "dry_run"
    assert payload["step_count"] == 4


def test_run_kel_cycle_requires_complete_review_metadata(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    result = subprocess.run([
        sys.executable,
        str(repo_root / "tools" / "kel" / "run_kel_cycle.py"),
        "--output-dir", str(tmp_path / "cycle"),
        "--feedback-text", "Review this rule.",
        "--review-decision", "accepted",
        "--dry-run",
    ], cwd=repo_root, text=True, capture_output=True)
    assert result.returncode != 0
    assert "--review-decision requires --reviewer" in result.stderr
