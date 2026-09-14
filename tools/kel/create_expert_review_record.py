#!/usr/bin/env python3
"""
Create a KEL expert review record for a graph change request.

This tool records the expert decision gate. It does not modify the target
framework layer and does not move graph change requests between lifecycle
folders; promotion is a separate step.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = REPO_ROOT / "tools" / "kel" / "validate_kel_record.py"


FINAL_DECISIONS = {"accepted", "rejected", "needs_evidence", "needs_revision", "implemented", "superseded"}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=True)
        f.write("\n")


def slugify(value: str | None) -> str:
    raw = value or "review"
    slug = re.sub(r"[^A-Za-z0-9_.:-]+", "_", raw).strip("_").lower()
    return slug or "review"


def evidence_list(values: list[str] | None, evidence_file: str | None) -> list[str]:
    items = list(values or [])
    if evidence_file:
        for line in Path(evidence_file).read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped:
                items.append(stripped)
    return items


def default_implementation_target(change_request: dict[str, Any]) -> str | None:
    layer = change_request.get("target_layer")
    if not isinstance(layer, str):
        return None
    mapping = {
        "KEL": "knowledge/kel/",
        "EDPR": "knowledge/edpr/",
        "EDES": "knowledge/edes/",
        "EDAS": "knowledge/edas/",
        "EDIKB": "knowledge/edikb/",
        "Dataset": "knowledge/edikb/EDIKB_FULL_DATASET.csv",
        "Plotters": "plotters/",
        "Tools": "tools/",
        "Docs": "docs/",
        "StandardLayouts": "knowledge/edas/standard_ils_layouts.json",
    }
    return mapping.get(layer)


def build_review(args: argparse.Namespace) -> dict[str, Any]:
    change_request = load_json(Path(args.change_request))
    if change_request.get("schema") not in {"kel-graph-change-request/0.1", "kel-graph-change-request/0.2"}:
        raise ValueError("Input must be a kel-graph-change-request/0.1 or /0.2 record")

    decision = args.decision
    status = args.status or ("final" if decision else "draft")
    if status == "final" and decision is None:
        raise ValueError("Final reviews require --decision.")
    if status == "final" and not (isinstance(args.reviewer, str) and args.reviewer.strip()):
        raise ValueError("Final reviews require --reviewer.")
    if status == "final" and not (
        isinstance(args.decision_reason, str) and args.decision_reason.strip()
    ):
        raise ValueError("Final reviews require --decision-reason.")
    if decision and decision not in FINAL_DECISIONS:
        raise ValueError(f"Unknown decision {decision!r}.")

    change_id = str(change_request.get("change_request_id") or "unlinked")
    review_id = args.review_id or f"kel:review:{slugify(change_id.replace('kel:change:', ''))}"
    implementation_target = args.implementation_target
    if implementation_target is None and decision in {"accepted", "implemented", "needs_revision"}:
        implementation_target = default_implementation_target(change_request)

    required_evidence = evidence_list(args.required_evidence, args.required_evidence_file)
    if not required_evidence and decision == "needs_evidence":
        evidence_requirement = change_request.get("evidence_requirement")
        if isinstance(evidence_requirement, str) and evidence_requirement:
            required_evidence.append(evidence_requirement)

    return {
        "schema": "kel-expert-review/0.1",
        "review_id": review_id,
        "linked_change_request_id": change_id,
        "status": status,
        "decision": decision,
        "reviewer": args.reviewer,
        "reviewed_utc": utc_now() if status == "final" or decision else None,
        "decision_reason": args.decision_reason,
        "required_evidence": required_evidence,
        "implementation_target": implementation_target,
        "implementation_reference": args.implementation_reference,
    }


def validate_output(path: Path) -> None:
    if not VALIDATOR.exists():
        return
    completed = subprocess.run([sys.executable, str(VALIDATOR), str(path)], cwd=str(REPO_ROOT), text=True)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def default_output_path(review: dict[str, Any], status: str) -> Path:
    base = Path("knowledge/kel/expert_reviews/final" if status == "final" else "knowledge/kel/expert_reviews/draft")
    stem = review["review_id"].replace("kel:review:", "").replace(":", "_")
    return base / f"{stem}.json"


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a KEL expert review record.")
    parser.add_argument("--change-request", required=True, help="KEL graph change request JSON.")
    parser.add_argument("--reviewer", default=None)
    parser.add_argument("--decision", choices=sorted(FINAL_DECISIONS), default=None)
    parser.add_argument("--status", choices=("draft", "final"), default=None)
    parser.add_argument("--decision-reason", default=None)
    parser.add_argument("--required-evidence", action="append", default=[])
    parser.add_argument("--required-evidence-file", default=None)
    parser.add_argument("--implementation-target", default=None)
    parser.add_argument("--implementation-reference", default=None)
    parser.add_argument("--review-id", default=None)
    parser.add_argument("--output", "-o", default=None)
    parser.add_argument("--no-validate", action="store_true")
    args = parser.parse_args()

    review = build_review(args)
    output = Path(args.output) if args.output else default_output_path(review, review["status"])
    write_json(output, review)
    if not args.no_validate:
        validate_output(output)

    print(f"KEL expert review record written: {output}")
    print(f"Status: {review['status']}")
    print(f"Decision: {review['decision']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
