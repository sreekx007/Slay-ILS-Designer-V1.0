#!/usr/bin/env python3
"""Smoke-test KEL templates and examples using the repo validator."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_kel_examples_and_templates_validate() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    files = sorted((repo_root / "knowledge" / "kel" / "templates").glob("*.json"))
    files += sorted((repo_root / "knowledge" / "kel" / "examples").glob("*.json"))
    cmd = [
        sys.executable,
        str(repo_root / "tools" / "kel" / "validate_kel_record.py"),
        *[str(path) for path in files],
    ]
    result = subprocess.run(cmd, cwd=repo_root, text=True, capture_output=True)
    assert result.returncode == 0, result.stderr
