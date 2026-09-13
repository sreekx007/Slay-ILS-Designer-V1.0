#!/usr/bin/env python3
"""
Validate KEL JSON records against the KEL schemas.

This validator prefers the jsonschema package when available. It also performs
lightweight policy checks that are specific to KEL governance.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


SCHEMA_BY_RECORD_SCHEMA = {
    "kel-experience-record/0.1": "knowledge/kel/schemas/KEL_EXPERIENCE_RECORD_SCHEMA.json",
    "kel-feedback-to-pmap-apf/0.1": "knowledge/kel/schemas/KEL_FEEDBACK_TO_PMAP_APF_SCHEMA.json",
    "kel-graph-change-request/0.1": "knowledge/kel/schemas/KEL_GRAPH_CHANGE_REQUEST_SCHEMA.json",
    "kel-expert-review/0.1": "knowledge/kel/schemas/KEL_EXPERT_REVIEW_SCHEMA.json",
    "kel-kg-sufficiency-report/0.1": "knowledge/kel/schemas/KEL_KG_SUFFICIENCY_REPORT_SCHEMA.json",
}


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[2]


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def validate_with_jsonschema(instance: Any, schema: dict[str, Any], path: Path) -> list[str]:
    try:
        import jsonschema  # type: ignore
    except ImportError:
        return []

    validator_cls = jsonschema.validators.validator_for(schema)
    validator_cls.check_schema(schema)
    validator = validator_cls(schema)
    errors = []
    for error in sorted(validator.iter_errors(instance), key=lambda item: list(item.path)):
        location = ".".join(str(part) for part in error.path) or "<root>"
        errors.append(f"{path}: {location}: {error.message}")
    return errors


def fallback_required_check(instance: dict[str, Any], schema: dict[str, Any], path: Path) -> list[str]:
    errors: list[str] = []
    for key in schema.get("required", []):
        if key not in instance:
            errors.append(f"{path}: missing required field '{key}'")
    return errors


def policy_checks(instance: dict[str, Any], path: Path) -> list[str]:
    errors: list[str] = []
    record_schema = instance.get("schema")

    if record_schema == "kel-graph-change-request/0.1":
        status = instance.get("status")
        review_ref = instance.get("expert_review_ref")
        implementation_ref = instance.get("implementation_ref")
        if status == "implemented" and not review_ref:
            errors.append(f"{path}: implemented graph change requests require expert_review_ref")
        if status == "implemented" and not implementation_ref:
            errors.append(f"{path}: implemented graph change requests require implementation_ref")

    if record_schema == "kel-expert-review/0.1":
        status = instance.get("status")
        decision = instance.get("decision")
        if status == "final" and decision is None:
            errors.append(f"{path}: final expert review requires a decision")
        if status == "final" and not str(instance.get("reviewer") or "").strip():
            errors.append(f"{path}: final expert review requires a reviewer")
        if status == "final" and not str(instance.get("decision_reason") or "").strip():
            errors.append(f"{path}: final expert review requires a decision_reason")

    return errors


def validate_file(path: Path, repo_root: Path) -> list[str]:
    instance = load_json(path)
    if not isinstance(instance, dict):
        return [f"{path}: KEL record must be a JSON object"]

    record_schema = instance.get("schema")
    if record_schema not in SCHEMA_BY_RECORD_SCHEMA:
        return [f"{path}: unknown or missing KEL schema '{record_schema}'"]

    schema_path = repo_root / SCHEMA_BY_RECORD_SCHEMA[record_schema]
    schema = load_json(schema_path)
    errors = validate_with_jsonschema(instance, schema, path)
    if not errors:
        errors.extend(fallback_required_check(instance, schema, path))
    errors.extend(policy_checks(instance, path))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate KEL JSON records.")
    parser.add_argument("paths", nargs="+", help="KEL JSON files to validate")
    parser.add_argument("--repo-root", type=Path, default=repo_root_from_script())
    args = parser.parse_args()

    all_errors: list[str] = []
    for raw_path in args.paths:
        path = Path(raw_path)
        all_errors.extend(validate_file(path, args.repo_root))

    if all_errors:
        for error in all_errors:
            print(error, file=sys.stderr)
        return 1

    print(f"Validated {len(args.paths)} KEL record(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
