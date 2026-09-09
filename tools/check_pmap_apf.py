#!/usr/bin/env python3
"""
Check whether an EDPR JSON file expresses the problem using P-map/APF structure.

This is a semantic completeness checker, not a JSON Schema validator. Run it
after EDPR_VALIDATOR.py to catch parses that are valid JSON but weak problem
representations.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


MIN_LINKS_FOR_DESIGN = 3


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def non_empty_list(value: Any) -> bool:
    return isinstance(value, list) and len(value) > 0


def has_zmc(item: dict[str, Any]) -> bool:
    return all(isinstance(item.get(key), dict) and item.get(key) for key in ("Z", "M", "C"))


def count_zmc(requirement_formalization: dict[str, Any]) -> int:
    count = 0
    for key, value in requirement_formalization.items():
        if not isinstance(value, list):
            continue
        for item in value:
            if isinstance(item, dict) and has_zmc(item):
                count += 1
    return count


def linked_ids(pmap: dict[str, Any]) -> set[str]:
    ids: set[str] = set()
    for key in ("requirements", "functions", "artifacts", "behaviours", "issues"):
        for item in as_list(pmap.get(key)):
            if isinstance(item, dict) and isinstance(item.get("id"), str):
                ids.add(item["id"])
    return ids


def check_file(path: Path, strict: bool) -> tuple[int, list[str]]:
    messages: list[str] = []
    try:
        edpr = load_json(path)
    except Exception as exc:
        return 2, [f"ERROR: failed to read JSON: {exc}"]

    pmap = edpr.get("pMap", {})
    if not isinstance(pmap, dict):
        return 1, ["ERROR: pMap must be an object."]

    required_lists = {
        "requirements": "P-map requirement nodes",
        "functions": "P-map function nodes",
        "artifacts": "P-map artifact/product nodes",
        "behaviours": "P-map behaviour/response nodes",
        "links": "P-map relation links",
    }

    for key, label in required_lists.items():
        if not non_empty_list(pmap.get(key)):
            messages.append(f"ERROR: missing or empty {label}: pMap.{key}")

    if strict and len(as_list(pmap.get("links"))) < MIN_LINKS_FOR_DESIGN:
        messages.append(f"ERROR: pMap.links should contain at least {MIN_LINKS_FOR_DESIGN} links for design problems.")

    req_form = edpr.get("requirementFormalization", {})
    if not isinstance(req_form, dict) or count_zmc(req_form) == 0:
        messages.append("ERROR: requirementFormalization must include at least one APF-style Z/M/C tuple.")

    if not non_empty_list(edpr.get("retrievalPlan")):
        messages.append("ERROR: retrievalPlan is empty; P-map/APF did not produce retrieval intent.")

    problem_type = str(edpr.get("problemIdentity", {}).get("problemType", "")).lower()
    raw_text = str(edpr.get("sourceRequest", {}).get("rawText", "")).lower()
    needs_numeric = any(word in f"{problem_type} {raw_text}" for word in ("compare", "rank", "minimize", "maximum", "minimum", "strain", "moment"))
    if needs_numeric and not non_empty_list(edpr.get("numericComparisonPlan")):
        messages.append("WARNING: quantitative/comparison language found, but numericComparisonPlan is empty.")

    needs_interaction = any(word in raw_text for word in ("layout", "assembly", "branch", "combined", "with", "multiple"))
    if needs_interaction and not non_empty_list(edpr.get("interactionEffectPlan")):
        messages.append("WARNING: multi-component/layout language found, but interactionEffectPlan is empty.")

    ids = linked_ids(pmap)
    for idx, link in enumerate(as_list(pmap.get("links"))):
        if not isinstance(link, dict):
            messages.append(f"ERROR: pMap.links[{idx}] must be an object.")
            continue
        source = link.get("source")
        target = link.get("target")
        relation = link.get("relation")
        if not source or not target or not relation:
            messages.append(f"ERROR: pMap.links[{idx}] must include source, target, and relation.")
        for endpoint_name, endpoint in (("source", source), ("target", target)):
            if isinstance(endpoint, str) and endpoint.startswith("edpr:") and endpoint not in ids:
                messages.append(f"WARNING: pMap.links[{idx}].{endpoint_name} references an ID not found in pMap nodes: {endpoint}")

    if not messages:
        messages.append("PASS: EDPR contains usable P-map/APF structure.")

    has_errors = any(msg.startswith("ERROR") for msg in messages)
    return (1 if has_errors else 0), messages


def main() -> int:
    parser = argparse.ArgumentParser(description="Check EDPR P-map/APF semantic completeness.")
    parser.add_argument("edpr_json", nargs="+", type=Path)
    parser.add_argument("--strict", action="store_true", help="Require minimum relation density for design problems.")
    args = parser.parse_args()

    final_code = 0
    for path in args.edpr_json:
        code, messages = check_file(path, args.strict)
        final_code = max(final_code, code)
        print(f"P-map/APF check: {path}")
        print(f"Result: {'FAIL' if code else 'PASS'}")
        for msg in messages:
            print(msg)
        print("")
    return final_code


if __name__ == "__main__":
    sys.exit(main())
