#!/usr/bin/env python3
"""Create v0.2 atomic feedback and groups without changing v0.1 sources."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from decompose_feedback import build_atomic_records
from group_feedback import group_records
from validate_kel_record import validate_file, repo_root_from_script


def write_stable(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(data, indent=2, ensure_ascii=True) + "\n"
    if not path.exists() or path.read_text(encoding="utf-8") != content:
        path.write_text(content, encoding="utf-8")


def migrate(sources: list[Path], output_root: Path) -> tuple[list[Path], list[Path]]:
    repo = repo_root_from_script()
    atomic = []
    for source in sorted(sources):
        errors = validate_file(source, repo)
        if errors:
            raise ValueError("; ".join(errors))
        record = json.loads(source.read_text(encoding="utf-8"))
        atomic.extend(build_atomic_records(record))
    atomic_paths = []
    for item in sorted(atomic, key=lambda value: value["atomic_feedback_id"]):
        name = item["atomic_feedback_id"].removeprefix("kel:feedback-atomic:").replace(":", "_") + ".json"
        path = output_root / "atomic" / name
        write_stable(path, item); atomic_paths.append(path)
    group_paths = []
    for group in group_records(atomic):
        path = output_root / "groups" / f"{group['group_key']}.json"
        write_stable(path, group); group_paths.append(path)
    return atomic_paths, group_paths


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("feedback_records", nargs="+")
    parser.add_argument("--output-root", required=True)
    args = parser.parse_args()
    atomic, groups = migrate([Path(value) for value in args.feedback_records], Path(args.output_root))
    print(json.dumps({"atomic_records": len(atomic), "feedback_groups": len(groups), "sources_modified": False}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
