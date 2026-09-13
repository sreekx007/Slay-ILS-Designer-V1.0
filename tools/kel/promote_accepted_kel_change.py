#!/usr/bin/env python3
"""
Promote a reviewed KEL graph change request into a lifecycle folder.

This tool links a final expert review back onto the graph change request and
writes an accepted or implemented copy. It does not edit EDPR/EDES/EDAS/EDIKB
content itself; that work must already be done or handled by a separate change.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = REPO_ROOT / "tools" / "kel" / "validate_kel_record.py"


STATUS_BY_DECISION = {
    "accepted": {"accepted", "implemented"},
    "implemented": {"implemented"},
    "rejected": {"rejected"},
    "needs_evidence": {"needs_evidence"},
    "needs_revision": {"needs_revision"},
    "superseded": {"superseded"},
}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=True)
        f.write("\n")


def slugify(value: str | None) -> str:
    raw = value or "change"
    slug = re.sub(r"[^A-Za-z0-9_.:-]+", "_", raw).strip("_").lower()
    return slug or "change"


def default_output_path(change_request: dict[str, Any], status: str) -> Path:
    base = REPO_ROOT / "knowledge" / "kel" / "graph_change_requests" / status
    stem = slugify(str(change_request.get("change_request_id", "change")).replace("kel:change:", "")).replace(":", "_")
    return base / f"{stem}.json"


def status_from_review(review: dict[str, Any], requested_status: str | None) -> str:
    decision = review.get("decision")
    allowed_statuses = STATUS_BY_DECISION.get(decision)
    if allowed_statuses is None:
        raise ValueError(f"Review decision {decision!r} cannot be promoted.")
    if requested_status:
        if requested_status not in allowed_statuses:
            allowed = ", ".join(sorted(allowed_statuses))
            raise ValueError(
                f"--status {requested_status} conflicts with review decision {decision!r}; "
                f"allowed status: {allowed}."
            )
        return requested_status
    return "implemented" if decision == "implemented" else str(decision)


def build_promoted_change(change_request: dict[str, Any], review: dict[str, Any], status: str) -> dict[str, Any]:
    if change_request.get("schema") != "kel-graph-change-request/0.1":
        raise ValueError("Change request must be kel-graph-change-request/0.1")
    if review.get("schema") != "kel-expert-review/0.1":
        raise ValueError("Review must be kel-expert-review/0.1")
    if review.get("status") != "final":
        raise ValueError("Only final expert reviews can promote graph change requests.")
    for field in ("reviewer", "reviewed_utc", "decision_reason"):
        if not (isinstance(review.get(field), str) and review[field].strip()):
            raise ValueError(f"Final expert review requires a nonempty {field}.")
    if review.get("linked_change_request_id") != change_request.get("change_request_id"):
        raise ValueError("Review linked_change_request_id does not match change_request_id.")
    implementation_reference = review.get("implementation_reference")
    if status == "implemented" and not (
        isinstance(implementation_reference, str) and implementation_reference.strip()
    ):
        raise ValueError("Implemented status requires a nonempty implementation_reference.")

    promoted = dict(change_request)
    promoted["status"] = status
    promoted["expert_review_ref"] = {
        "id": review.get("review_id"),
        "repo_path": None,
    }
    implementation_target = review.get("implementation_target")
    decision_reason = review.get("decision_reason")
    if implementation_target or implementation_reference or decision_reason:
        promoted["implementation_ref"] = {
            "target": implementation_target,
            "repo_path": implementation_reference,
            "notes": decision_reason,
        }
    else:
        promoted["implementation_ref"] = None
    return promoted


def validate(path: Path) -> None:
    completed = subprocess.run([sys.executable, str(VALIDATOR), str(path)], cwd=str(REPO_ROOT), text=True)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def maybe_copy_review(review_path: Path, status: str) -> Path | None:
    if status not in {"accepted", "implemented"}:
        return None
    target_dir = REPO_ROOT / "knowledge" / "kel" / "expert_reviews" / "final"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / review_path.name
    if review_path.resolve() != target.resolve():
        shutil.copy2(review_path, target)
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description="Promote a KEL graph change request after expert review.")
    parser.add_argument("--change-request", required=True, help="Graph change request JSON.")
    parser.add_argument("--review", required=True, help="Final expert review JSON.")
    parser.add_argument("--status", choices=("accepted", "implemented", "rejected", "needs_evidence", "needs_revision", "superseded"), default=None)
    parser.add_argument("--output", "-o", default=None)
    parser.add_argument("--no-validate", action="store_true")
    args = parser.parse_args()

    change_request_path = Path(args.change_request)
    review_path = Path(args.review)
    change_request = load_json(change_request_path)
    review = load_json(review_path)
    if not args.no_validate:
        validate(change_request_path)
        validate(review_path)
    status = status_from_review(review, args.status)
    promoted = build_promoted_change(change_request, review, status)

    output = Path(args.output) if args.output else default_output_path(promoted, status)
    write_json(output, promoted)
    review_copy = maybe_copy_review(review_path, status) if args.output is None else None
    if review_copy is not None:
        promoted["expert_review_ref"]["repo_path"] = str(review_copy.relative_to(REPO_ROOT))
        write_json(output, promoted)
    if not args.no_validate:
        validate(output)

    print(f"KEL graph change request promoted: {output}")
    print(f"Status: {status}")
    print(f"Review: {promoted['expert_review_ref']['id']}")
    if promoted.get("implementation_ref"):
        print(f"Implementation: {promoted['implementation_ref'].get('repo_path')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
