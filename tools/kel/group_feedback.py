#!/usr/bin/env python3
"""Group and de-duplicate KEL v0.2 atomic feedback without losing source IDs."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from feedback_v02 import priority_for_members, sha256_text, slugify, unique_strings


REPO_ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = REPO_ROOT / "tools" / "kel" / "validate_kel_record.py"


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=True)
        handle.write("\n")


def most_common(values: list[str]) -> str:
    counts = Counter(values)
    return sorted(counts, key=lambda value: (-counts[value], value))[0]


def joined_unique(values: list[str]) -> str:
    result: list[str] = []
    for value in values:
        if value not in result:
            result.append(value)
    return "; ".join(result)


def build_group(group_key: str, members: list[dict[str, Any]]) -> dict[str, Any]:
    ordered = sorted(members, key=lambda item: str(item["atomic_feedback_id"]))
    targets = [str(item["target_layers"][0]) for item in ordered]
    change_types = [str(item.get("change_type") or "new_design_guidance") for item in ordered]
    fingerprints = unique_strings([item.get("fingerprint") for item in ordered])
    fingerprint = sha256_text(group_key)
    group_id = f"kel:feedback-group:{slugify(group_key)}:{fingerprint[:12]}"
    return {
        "schema": "kel-feedback-group/0.2",
        "feedback_group_id": group_id,
        "created_utc": sorted(str(item.get("created_utc") or "unknown") for item in ordered)[0],
        "canonical_issue": joined_unique([str(item["observed_issue"]) for item in ordered]),
        "canonical_action": joined_unique([str(item["requested_action"]) for item in ordered]),
        "target_layer": most_common(targets),
        "change_type": most_common(change_types),
        "priority": priority_for_members(ordered),
        "fingerprint": fingerprint,
        "group_key": group_key,
        "member_feedback_ids": [str(item["atomic_feedback_id"]) for item in ordered],
        "member_fingerprints": fingerprints,
        "source_feedback_ids": unique_strings([item.get("source_feedback_id") for item in ordered]),
        "linked_experience_ids": unique_strings([item.get("linked_experience_id") for item in ordered]),
        "evidence_refs": unique_strings([ref for item in ordered for ref in item.get("evidence_refs", [])]),
        "grouping": {
            "method": "deterministic_topic_key_v0.2",
            "exact_fingerprint_match": len(fingerprints) == 1,
            "review_required": len(fingerprints) != 1,
        },
        "status": "candidate",
    }


def group_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        if record.get("schema") != "kel-atomic-feedback/0.2":
            raise ValueError("Inputs must be kel-atomic-feedback/0.2 records")
        buckets.setdefault(str(record["group_key"]), []).append(record)
    return [build_group(key, buckets[key]) for key in sorted(buckets)]


def validate(paths: list[Path]) -> None:
    completed = subprocess.run([sys.executable, str(VALIDATOR), *map(str, paths)], cwd=REPO_ROOT, text=True)
    if completed.returncode:
        raise SystemExit(completed.returncode)


def main() -> int:
    parser = argparse.ArgumentParser(description="Group and de-duplicate KEL atomic feedback.")
    parser.add_argument("atomic_feedback_records", nargs="+")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--no-validate", action="store_true")
    args = parser.parse_args()

    records = [load_json(Path(value)) for value in args.atomic_feedback_records]
    groups = group_records(records)
    output_dir = Path(args.output_dir)
    paths: list[Path] = []
    for group in groups:
        output_path = output_dir / f"{group['group_key']}.feedback_group.json"
        write_json(output_path, group)
        paths.append(output_path)
    if not args.no_validate:
        validate(paths)
    print(f"KEL feedback group(s) written: {len(paths)}")
    for path in paths:
        group = load_json(path)
        print(f"- {path}: {len(group['member_feedback_ids'])} member(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
