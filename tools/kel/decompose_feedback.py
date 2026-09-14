#!/usr/bin/env python3
"""Decompose v0.1 KEL feedback records into traceable atomic v0.2 issues."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from convert_feedback_to_pmap_apf import apf_action_for, priority_for
from feedback_v02 import (
    affected_components,
    atomic_feedback_type,
    group_key_for,
    infer_target_and_type,
    sha256_text,
    slugify,
    unique_strings,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = REPO_ROOT / "tools" / "kel" / "validate_kel_record.py"
BULLET_RE = re.compile(r"(?m)^\s*(?:[-*\u2022]|\d+[.)])\s+")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=True)
        handle.write("\n")


def clean_unit(value: str) -> str:
    return " ".join(value.split()).strip()


def feedback_units(text: str) -> list[tuple[str, int, int]]:
    bullets = list(BULLET_RE.finditer(text))
    if bullets:
        units: list[tuple[str, int, int]] = []
        preamble = clean_unit(text[: bullets[0].start()])
        if preamble:
            units.append((preamble, 0, bullets[0].start()))
        for index, match in enumerate(bullets):
            end = bullets[index + 1].start() if index + 1 < len(bullets) else len(text)
            cleaned = clean_unit(text[match.end() : end])
            if cleaned:
                units.append((cleaned, match.end(), end))
        return units

    paragraphs = [match for match in re.finditer(r"\S(?:.*?)(?=\n\s*\n|\Z)", text, re.S) if clean_unit(match.group())]
    if len(paragraphs) > 1:
        return [(clean_unit(match.group()), match.start(), match.end()) for match in paragraphs]

    cleaned = clean_unit(text)
    return [(cleaned, 0, len(text))] if cleaned else []


def source_evidence(record: dict[str, Any]) -> list[str]:
    values: list[Any] = []
    for key in ("evidence_refs", "evidence_links", "source_refs"):
        value = record.get(key)
        if isinstance(value, list):
            values.extend(value)
    return unique_strings(values)


def build_atomic_records(source: dict[str, Any]) -> list[dict[str, Any]]:
    if source.get("schema") != "kel-feedback-to-pmap-apf/0.1":
        raise ValueError("Input must be a kel-feedback-to-pmap-apf/0.1 record")
    text = str(source.get("raw_feedback_text") or "")
    source_id = str(source.get("feedback_id") or "kel:feedback:unlinked")
    experience_id = str(source.get("linked_experience_id") or "kel:experience:unlinked")
    created_utc = str(source.get("created_utc") or "unknown")
    records: list[dict[str, Any]] = []
    for index, (unit, start, end) in enumerate(feedback_units(text), start=1):
        feedback_type, confidence, reasons = atomic_feedback_type(unit)
        components = affected_components(unit)
        action = apf_action_for(feedback_type)
        target_layer, change_type = infer_target_and_type(feedback_type, unit, action)
        group_key = group_key_for(unit, components)
        fingerprint = sha256_text(target_layer, change_type, ",".join(components), unit, action)
        source_slug = slugify(source_id.removeprefix("kel:feedback:"))
        atomic_id = f"kel:feedback-atomic:{source_slug}:{index:02d}:{fingerprint[:12]}"
        records.append({
            "schema": "kel-atomic-feedback/0.2",
            "atomic_feedback_id": atomic_id,
            "source_feedback_id": source_id,
            "linked_experience_id": experience_id,
            "created_utc": created_utc,
            "source_text": unit,
            "source_span": {"start": start, "end": max(end, start + 1)},
            "feedback_type": feedback_type,
            "classification": {
                "method": "deterministic_rules",
                "confidence": confidence,
                "reasons": reasons,
            },
            "observed_issue": unit,
            "requested_action": action,
            "affected_components": components,
            "target_layers": [target_layer],
            "change_type": change_type,
            "evidence_refs": source_evidence(source),
            "priority": priority_for(feedback_type),
            "fingerprint": fingerprint,
            "group_key": group_key,
            "status": "candidate",
        })
    return records


def validate(paths: list[Path]) -> None:
    if not paths:
        return
    completed = subprocess.run([sys.executable, str(VALIDATOR), *map(str, paths)], cwd=REPO_ROOT, text=True)
    if completed.returncode:
        raise SystemExit(completed.returncode)


def main() -> int:
    parser = argparse.ArgumentParser(description="Decompose KEL v0.1 feedback into atomic v0.2 records.")
    parser.add_argument("feedback_records", nargs="+")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--no-validate", action="store_true")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    paths: list[Path] = []
    for source_path_text in args.feedback_records:
        source_path = Path(source_path_text)
        for index, record in enumerate(build_atomic_records(load_json(source_path)), start=1):
            output_path = output_dir / f"{source_path.stem}.atomic_{index:02d}.json"
            write_json(output_path, record)
            paths.append(output_path)
    if not args.no_validate:
        validate(paths)
    print(f"KEL atomic feedback record(s) written: {len(paths)}")
    for path in paths:
        print(f"- {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
