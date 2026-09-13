#!/usr/bin/env python3
"""Smoke-test KEL experience record creation."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_create_kel_experience_record_from_edpr_only(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    output = tmp_path / "kel_experience.json"
    cmd = [
        sys.executable,
        str(repo_root / "tools" / "kel" / "create_kel_experience_record.py"),
        "--edpr-json",
        str(repo_root / "knowledge" / "edpr" / "examples" / "EDPR_EXAMPLE_GDVLV_NO_ROLLER_CONTACT.json"),
        "--output",
        str(output),
    ]
    result = subprocess.run(cmd, cwd=repo_root, text=True, capture_output=True)
    assert result.returncode == 0, result.stderr

    record = json.loads(output.read_text(encoding="utf-8"))
    assert record["schema"] == "kel-experience-record/0.1"
    assert record["source_query"]["query_id"] == "edpr:p_gdvlv_no_roller_contact_001"
    assert record["status"] == "generated"
