#!/usr/bin/env python3
"""Smoke-test KEL knowledge sufficiency evaluation."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_evaluate_kg_sufficiency_from_edpr_only(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    output = tmp_path / "sufficiency.json"
    cmd = [
        sys.executable,
        str(repo_root / "tools" / "kel" / "evaluate_kg_sufficiency.py"),
        "--edpr-json",
        str(repo_root / "knowledge" / "edpr" / "examples" / "EDPR_EXAMPLE_GDVLV_NO_ROLLER_CONTACT.json"),
        "--output",
        str(output),
    ]
    result = subprocess.run(cmd, cwd=repo_root, text=True, capture_output=True)
    assert result.returncode == 0, result.stderr

    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["schema"] == "kel-kg-sufficiency-report/0.1"
    assert report["ratings"]["knowledge_sufficiency"] in {
        "sufficient",
        "partially_sufficient",
        "insufficient",
        "unknown",
    }
    assert isinstance(report["gaps"], list)
