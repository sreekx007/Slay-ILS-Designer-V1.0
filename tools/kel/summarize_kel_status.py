#!/usr/bin/env python3
"""Summarize KEL v0.1/v0.2 records and lifecycle conflicts."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


def summarize(root: Path) -> dict:
    schemas, statuses, graph_statuses = Counter(), Counter(), Counter()
    graph_locations = defaultdict(list)
    invalid = []
    for path in sorted(root.rglob("*.json")):
        relative_parts = set(path.relative_to(root).parts)
        if relative_parts & {"schemas", "templates", "examples"}:
            continue
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            invalid.append(f"{path}: {exc}")
            continue
        if not isinstance(record, dict) or not str(record.get("schema", "")).startswith("kel-"):
            continue
        schemas[str(record["schema"])] += 1
        status = record.get("status") or record.get("decision")
        if status:
            statuses[str(status)] += 1
        if str(record.get("schema", "")).startswith("kel-graph-change-request/"):
            graph_statuses[str(record.get("status"))] += 1
            graph_locations[str(record.get("change_request_id"))].append({"status": record.get("status"), "path": path.relative_to(root).as_posix()})
    conflicts = []
    for change_id, locations in sorted(graph_locations.items()):
        authoritative = [item for item in locations if item["status"] != "superseded"]
        if len(authoritative) > 1:
            conflicts.append({"change_request_id": change_id, "records": authoritative})
    return {
        "schema": "kel-status-summary/0.2",
        "created_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "root": root.as_posix(),
        "counts_by_schema": dict(sorted(schemas.items())),
        "counts_by_status": dict(sorted(statuses.items())),
        "headline": {
            "atomic_feedback": schemas["kel-atomic-feedback/0.2"],
            "feedback_groups": schemas["kel-feedback-group/0.2"],
            "pending_changes": graph_statuses["pending"],
            "needs_evidence": graph_statuses["needs_evidence"],
            "accepted_changes": graph_statuses["accepted"],
            "implemented_changes": graph_statuses["implemented"],
            "superseded_records": graph_statuses["superseded"],
            "lifecycle_conflicts": len(conflicts),
        },
        "lifecycle_conflicts": conflicts,
        "invalid_json": invalid,
    }


def markdown(report: dict) -> str:
    lines = ["# KEL Status", "", "| Measure | Count |", "| --- | ---: |"]
    for name, count in report["headline"].items():
        lines.append(f"| {name.replace('_', ' ').title()} | {count} |")
    lines.extend(["", f"Generated: `{report['created_utc']}`", ""])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default="knowledge/kel")
    parser.add_argument("--output")
    parser.add_argument("--format", choices=("json", "md"), default="json")
    args = parser.parse_args()
    report = summarize(Path(args.root))
    text = json.dumps(report, indent=2, ensure_ascii=True) + "\n" if args.format == "json" else markdown(report)
    if args.output:
        path = Path(args.output); path.parent.mkdir(parents=True, exist_ok=True); path.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 1 if report["lifecycle_conflicts"] or report["invalid_json"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
