#!/usr/bin/env python3
"""Find and repair duplicate KEL graph-request lifecycle states."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STATUS_RANK = {
    "superseded": 0,
    "pending": 1,
    "needs_revision": 2,
    "needs_evidence": 2,
    "rejected": 3,
    "accepted": 4,
    "implemented": 5,
}
GRAPH_SCHEMAS = {"kel-graph-change-request/0.1", "kel-graph-change-request/0.2"}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=True)
        handle.write("\n")


def rel(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def lifecycle_records(root: Path) -> list[tuple[Path, dict[str, Any]]]:
    records: list[tuple[Path, dict[str, Any]]] = []
    for path in sorted(root.glob("*/*.json")):
        data = load_json(path)
        if isinstance(data, dict) and data.get("schema") in GRAPH_SCHEMAS:
            records.append((path, data))
    return records


def linked_values(record: dict[str, Any], plural: str, singular: str, fallback: str) -> list[str]:
    values = record.get(plural)
    if isinstance(values, list):
        cleaned = sorted({str(value) for value in values if str(value).strip()})
        if cleaned:
            return cleaned
    value = record.get(singular)
    return [str(value)] if isinstance(value, str) and value.strip() else [fallback]


def superseded_record(record: dict[str, Any], authoritative: dict[str, Any], authoritative_path: Path, root: Path) -> dict[str, Any]:
    return {
        "schema": "kel-graph-change-request/0.2",
        "change_request_id": str(record["change_request_id"]),
        "status": "superseded",
        "created_utc": str(record.get("created_utc") or utc_now()),
        "linked_experience_ids": linked_values(record, "linked_experience_ids", "linked_experience_id", "kel:experience:unlinked"),
        "linked_feedback_ids": linked_values(record, "linked_feedback_ids", "linked_feedback_id", "kel:feedback:unlinked"),
        "feedback_group_id": record.get("feedback_group_id"),
        "target_layer": str(record.get("target_layer") or "Docs"),
        "change_type": str(record.get("change_type") or "new_design_guidance"),
        "problem_observed": str(record.get("problem_observed") or "Superseded lifecycle duplicate."),
        "proposed_change": str(record.get("proposed_change") or "Use the authoritative lifecycle record."),
        "evidence_requirement": str(record.get("evidence_requirement") or "See the authoritative lifecycle record."),
        "priority": str(record.get("priority") or "medium"),
        "expert_review_ref": record.get("expert_review_ref"),
        "implementation_ref": record.get("implementation_ref"),
        "superseded_by": {
            "change_request_id": str(authoritative["change_request_id"]),
            "status": str(authoritative["status"]),
            "repo_path": rel(authoritative_path, root),
        },
    }


def destination_for(source: Path, root: Path) -> Path:
    target = root / "superseded" / source.name
    if not target.exists() or target.resolve() == source.resolve():
        return target
    suffix = source.parent.name.replace("-", "_")
    return target.with_name(f"{target.stem}__from_{suffix}{target.suffix}")


def reconcile(root: Path, apply: bool) -> tuple[dict[str, Any], int]:
    by_id: dict[str, list[tuple[Path, dict[str, Any]]]] = {}
    for path, record in lifecycle_records(root):
        by_id.setdefault(str(record.get("change_request_id")), []).append((path, record))

    report: dict[str, Any] = {
        "schema": "kel-lifecycle-reconciliation/0.2",
        "created_utc": utc_now(),
        "mode": "applied" if apply else "dry_run",
        "lifecycle_root": root.as_posix(),
        "authoritative_records": [],
        "actions": [],
        "conflicts": [],
    }
    planned: list[tuple[Path, Path, dict[str, Any]]] = []
    for change_id in sorted(by_id):
        entries = by_id[change_id]
        highest = max(STATUS_RANK.get(str(record.get("status")), -1) for _, record in entries)
        leaders = [(path, record) for path, record in entries if STATUS_RANK.get(str(record.get("status")), -1) == highest]
        if len(leaders) != 1:
            report["conflicts"].append(
                f"{change_id}: multiple equally authoritative records: "
                + ", ".join(rel(path, root) for path, _ in leaders)
            )
            continue
        authoritative_path, authoritative = leaders[0]
        report["authoritative_records"].append({
            "change_request_id": change_id,
            "status": str(authoritative.get("status")),
            "repo_path": rel(authoritative_path, root),
        })
        for source, record in entries:
            if source == authoritative_path:
                continue
            if source.parent.name == "superseded" and record.get("status") == "superseded":
                continue
            destination = destination_for(source, root)
            replacement = superseded_record(record, authoritative, authoritative_path, root)
            report["actions"].append({
                "change_request_id": change_id,
                "source": rel(source, root),
                "destination": rel(destination, root),
                "reason": f"authoritative status is {authoritative.get('status')}",
            })
            planned.append((source, destination, replacement))

    if apply and report["conflicts"]:
        return report, 2
    if apply:
        for source, destination, replacement in planned:
            write_json(destination, replacement)
            if source.resolve() != destination.resolve():
                source.unlink()
    return report, 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Reconcile duplicate KEL graph-request lifecycle states.")
    parser.add_argument("--lifecycle-root", default="knowledge/kel/graph_change_requests")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--report", default=None)
    args = parser.parse_args()

    root = Path(args.lifecycle_root)
    report, returncode = reconcile(root, args.apply)
    if args.report:
        write_json(Path(args.report), report)
    print(json.dumps(report, indent=2, ensure_ascii=True))
    if report["conflicts"]:
        print(f"Lifecycle conflicts: {len(report['conflicts'])}", file=sys.stderr)
    return returncode


if __name__ == "__main__":
    raise SystemExit(main())
