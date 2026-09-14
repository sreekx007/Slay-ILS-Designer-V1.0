#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/kel"))

from create_implementation_plan import build_plan
from migrate_v01_to_v02 import migrate
from summarize_kel_status import summarize
from validate_kel_record import validate_file


def accepted_change() -> dict:
    return {
        "schema": "kel-graph-change-request/0.2",
        "change_request_id": "kel:change:test_accepted",
        "status": "accepted",
        "target_layer": "EDAS",
        "proposed_change": "Require the accepted assembly relation.",
        "evidence_requirement": "Accepted expert evidence.",
        "expert_review_ref": {"id": "kel:review:test", "repo_path": "review.json"},
    }


def test_implementation_plan_requires_acceptance_and_validates(tmp_path: Path) -> None:
    plan = build_plan(accepted_change(), "2026-09-14T00:00:00Z")
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(plan), encoding="utf-8")
    assert not validate_file(path, ROOT)
    pending = accepted_change(); pending["status"] = "pending"
    with pytest.raises(ValueError, match="expert-accepted"):
        build_plan(pending)


def test_migration_is_idempotent_and_preserves_sources(tmp_path: Path) -> None:
    sources = sorted((ROOT / "knowledge/kel/feedback_records/candidates").glob("Q1_*.json"))
    before = {path: path.read_bytes() for path in sources}
    atomic, groups = migrate(sources, tmp_path)
    first = {path.relative_to(tmp_path): path.read_bytes() for path in [*atomic, *groups]}
    atomic2, groups2 = migrate(sources, tmp_path)
    second = {path.relative_to(tmp_path): path.read_bytes() for path in [*atomic2, *groups2]}
    assert first == second
    assert before == {path: path.read_bytes() for path in sources}
    assert len(atomic) == 11
    assert groups


def test_repository_status_has_no_authoritative_lifecycle_conflict() -> None:
    report = summarize(ROOT / "knowledge/kel")
    assert report["headline"]["lifecycle_conflicts"] == 0
    assert report["headline"]["atomic_feedback"] >= 1
    assert report["headline"]["feedback_groups"] >= 1
