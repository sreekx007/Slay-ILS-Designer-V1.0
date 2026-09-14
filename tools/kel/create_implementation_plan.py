#!/usr/bin/env python3
"""Create a target-layer checklist from an expert-accepted KEL change."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path


LAYER_ACTIONS = {
    "EDPR": ["Update parser rule and explicit intent fields.", "Add EDPR validation fixture."],
    "EDES": ["Update canonical component properties or behaviour.", "Validate component schema and example."],
    "EDAS": ["Implement assembly constraint and fail-closed validation.", "Add compatible and incompatible layout tests."],
    "EDIKB": ["Add evidence-scoped rule or gap node.", "Verify sources and applicability domain."],
    "Dataset": ["Define columns, units, provenance and acceptance checks.", "Validate new rows and de-duplication."],
    "Plotters": ["Expose the accepted geometry and associations.", "Run plot QA and report-gate tests."],
    "Tools": ["Implement deterministic command behavior.", "Add unit and end-to-end tests."],
    "KEL": ["Update schema, lifecycle and governance tooling.", "Run idempotency and policy tests."],
    "Docs": ["Update the authoritative workflow documentation.", "Check manifest and links."],
    "StandardLayouts": ["Add or revise reviewed anchors.", "Build every affected anchor and validate topology."],
}


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_plan(change: dict, created_utc: str | None = None) -> dict:
    if change.get("schema") not in {"kel-graph-change-request/0.1", "kel-graph-change-request/0.2"}:
        raise ValueError("Input must be a KEL graph change request")
    if change.get("status") not in {"accepted", "implemented"} or not change.get("expert_review_ref"):
        raise ValueError("Implementation plans require an expert-accepted or implemented change with expert_review_ref")
    layer = str(change["target_layer"])
    slug = re.sub(r"[^A-Za-z0-9_.:-]+", "_", str(change["change_request_id"]).removeprefix("kel:change:"))
    actions = LAYER_ACTIONS.get(layer, LAYER_ACTIONS["Tools"])
    evidence = [str(change.get("evidence_requirement"))]
    implemented = change.get("status") == "implemented"
    implementation_ref = change.get("implementation_ref") or {}
    return {
        "schema": "kel-implementation-plan/0.2",
        "implementation_plan_id": f"kel:implementation-plan:{slug}",
        "created_utc": created_utc or now(),
        "status": "implemented" if implemented else "planned",
        "source_change_request_id": str(change["change_request_id"]),
        "source_change_request_status": str(change["status"]),
        "expert_review_ref": change["expert_review_ref"],
        "target_layer": layer,
        "requirements": [str(change["proposed_change"])],
        "changed_paths": [],
        "evidence": evidence,
        "checklist": [{"id": f"step_{i}", "action": action, "status": "complete" if implemented else "pending"} for i, action in enumerate(actions, 1)],
        "tests": [f"Focused {layer} regression test", "KEL schema and governance validation"],
        "review": {"reviewer": None, "decision": None, "notes": None},
        "completion": {"implemented_utc": created_utc or now() if implemented else None, "verified_utc": None, "implementation_ref": implementation_ref.get("repo_path") if implemented else None},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("change_request")
    parser.add_argument("--output", required=True)
    parser.add_argument("--created-utc")
    args = parser.parse_args()
    change = json.loads(Path(args.change_request).read_text(encoding="utf-8"))
    plan = build_plan(change, args.created_utc)
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(plan, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
