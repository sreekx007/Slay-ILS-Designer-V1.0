#!/usr/bin/env python3
"""
Validate EDPR problem-map JSON files.

This validator is intentionally dependency-light. If the optional jsonschema
package is installed, it performs full Draft 2020-12 validation. It always runs
additional EDPR-specific checks for IDs, ontology links, retrieval plans, and
interaction-effect coverage.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


EDPR_ID_RE = re.compile(r"^edpr:[A-Za-z0-9_\-:]+$")
ONTOLOGY_ID_RE = re.compile(
    r"^(edes:|edas:|edikb:|ILS-|ILT-|paper[0-9]+:|EDIKB_|EDES_|EDAS_|"
    r"standard_ils_layout_archetype|local:|edpr:)[A-Za-z0-9_#:/.\-]+$"
)

MULTI_COMPONENT_HINTS = {
    "branch",
    "layout",
    "assembly",
    "combined",
    "interaction",
    "nested",
    "shroud",
    "top frame",
    "base structure",
    "inline tee",
    "ilt",
}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def walk(value: Any, path: str = "$"):
    yield path, value
    if isinstance(value, dict):
        for key, child in value.items():
            yield from walk(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk(child, f"{path}[{index}]")


def validate_with_jsonschema(schema: dict[str, Any], instance: dict[str, Any]) -> list[str]:
    try:
        import jsonschema  # type: ignore
    except Exception:
        return ["INFO: optional package 'jsonschema' not installed; skipped full JSON Schema validation."]

    validator = jsonschema.Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(instance), key=lambda err: list(err.path))
    return [f"ERROR: schema: {'/'.join(map(str, err.path)) or '$'}: {err.message}" for err in errors]


def collect_ids(instance: dict[str, Any]) -> tuple[set[str], list[str]]:
    ids: set[str] = set()
    messages: list[str] = []
    for path, value in walk(instance):
        if isinstance(value, dict) and isinstance(value.get("id"), str):
            item_id = value["id"]
            if not EDPR_ID_RE.match(item_id):
                messages.append(f"ERROR: {path}.id is not a valid EDPR ID: {item_id}")
            if item_id in ids:
                messages.append(f"ERROR: duplicate EDPR ID: {item_id}")
            ids.add(item_id)
    return ids, messages


def check_links(instance: dict[str, Any], ids: set[str]) -> list[str]:
    messages: list[str] = []
    for path, value in walk(instance):
        if isinstance(value, dict):
            if "ontologyLinks" in value:
                links = value["ontologyLinks"]
                if not isinstance(links, list):
                    messages.append(f"ERROR: {path}.ontologyLinks must be an array.")
                else:
                    for link in links:
                        if not isinstance(link, str) or not ONTOLOGY_ID_RE.match(link):
                            messages.append(f"WARNING: {path}.ontologyLinks contains non-standard ontology link: {link!r}")
            if {"source", "target", "relation"}.issubset(value) and str(value.get("id", "")).startswith("edpr:"):
                for endpoint in ("source", "target"):
                    ref = value.get(endpoint)
                    if isinstance(ref, str) and ref.startswith("edpr:") and ref not in ids:
                        messages.append(f"WARNING: {path}.{endpoint} references missing local ID: {ref}")
    return messages


def check_edpr_semantics(instance: dict[str, Any]) -> list[str]:
    messages: list[str] = []
    required_arrays = [
        "knownInputs",
        "unknownInputs",
        "requirements",
        "constraints",
        "evaluationVariables",
        "candidateComponents",
        "candidateAssemblies",
        "standardLayoutCandidates",
        "behaviourConcerns",
        "retrievalPlan",
        "numericComparisonPlan",
        "interactionEffectPlan",
        "rankingCriteria",
        "openQuestions",
        "assumptions",
        "evidenceTrace",
        "parserWarnings",
    ]
    for key in required_arrays:
        if not isinstance(instance.get(key), list):
            messages.append(f"ERROR: top-level field {key} must be an array.")

    raw_text = instance.get("sourceRequest", {}).get("rawText", "")
    text_blob = " ".join(
        [
            raw_text,
            instance.get("problemIdentity", {}).get("title", ""),
            json.dumps(instance.get("candidateComponents", [])),
            json.dumps(instance.get("candidateAssemblies", [])),
        ]
    ).lower()

    if any(hint in text_blob for hint in MULTI_COMPONENT_HINTS):
        if not instance.get("interactionEffectPlan"):
            messages.append(
                "WARNING: problem appears to involve a multi-component layout, but interactionEffectPlan is empty."
            )

    if "layout" in text_blob or "ilt" in text_blob or "standard" in text_blob:
        if not instance.get("standardLayoutCandidates"):
            messages.append(
                "WARNING: layout problem appears to need standardLayoutCandidates, but none are provided."
            )

    retrieval_types = {item.get("queryType") for item in instance.get("retrievalPlan", []) if isinstance(item, dict)}
    if instance.get("candidateComponents") and "component_definition" not in retrieval_types:
        messages.append("WARNING: candidateComponents exist, but retrievalPlan has no component_definition query.")
    if instance.get("candidateAssemblies") and "assembly_rule" not in retrieval_types:
        messages.append("WARNING: candidateAssemblies exist, but retrievalPlan has no assembly_rule query.")
    if instance.get("standardLayoutCandidates") and "standard_layout_archetype" not in retrieval_types:
        messages.append("WARNING: standardLayoutCandidates exist, but retrievalPlan has no standard_layout_archetype query.")

    numeric_words = {"compare", "rank", "minimize", "minimum", "maximum", "strain", "bending", "moment"}
    if any(word in raw_text.lower() for word in numeric_words) and not instance.get("numericComparisonPlan"):
        messages.append("WARNING: request looks quantitative, but numericComparisonPlan is empty.")

    return messages


def validate_file(schema_path: Path, instance_path: Path) -> int:
    messages: list[str] = []
    try:
        schema = load_json(schema_path)
        instance = load_json(instance_path)
    except Exception as exc:
        print(f"ERROR: failed to read JSON: {exc}")
        return 2

    messages.extend(validate_with_jsonschema(schema, instance))
    ids, id_messages = collect_ids(instance)
    messages.extend(id_messages)
    messages.extend(check_links(instance, ids))
    messages.extend(check_edpr_semantics(instance))

    errors = [msg for msg in messages if msg.startswith("ERROR")]
    warnings = [msg for msg in messages if msg.startswith("WARNING")]
    infos = [msg for msg in messages if msg.startswith("INFO")]

    print(f"EDPR validation: {instance_path}")
    print(f"Schema: {schema_path}")
    print(f"Result: {'FAIL' if errors else 'PASS'}")
    print(f"Errors: {len(errors)}")
    print(f"Warnings: {len(warnings)}")
    for msg in errors + warnings + infos:
        print(msg)

    return 1 if errors else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate EDPR problem-map JSON files.")
    parser.add_argument("instance", nargs="+", type=Path, help="EDPR JSON file(s) to validate")
    parser.add_argument(
        "--schema",
        type=Path,
        default=Path(__file__).with_name("EDPR_METASCHEMA_v0_1.json"),
        help="Path to EDPR metaschema JSON",
    )
    args = parser.parse_args()

    exit_code = 0
    for instance_path in args.instance:
        exit_code = max(exit_code, validate_file(args.schema, instance_path))
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
