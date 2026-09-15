from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List

try:
    from .common import (
        DEFAULT_SOURCE_PATHS,
        REPO_ROOT,
        flatten_json,
        infer_layer,
        record_type_from,
        repo_path,
        sha256_text,
        status_from,
        symbolic_targets,
        title_from_record,
    )
except ImportError:  # pragma: no cover - direct script execution
    from common import (  # type: ignore
        DEFAULT_SOURCE_PATHS,
        REPO_ROOT,
        flatten_json,
        infer_layer,
        record_type_from,
        repo_path,
        sha256_text,
        status_from,
        symbolic_targets,
        title_from_record,
    )

TEXT_EXTENSIONS = {".md", ".txt", ""}
DATA_EXTENSIONS = {".json", ".csv"}


def iter_source_files(source_paths: List[str]) -> Iterable[Path]:
    for item in source_paths:
        path = (REPO_ROOT / item).resolve()
        if not path.exists():
            continue
        if path.is_file():
            if path.suffix.lower() in TEXT_EXTENSIONS | DATA_EXTENSIONS:
                yield path
            continue
        for child in sorted(path.rglob("*")):
            if child.is_file() and child.suffix.lower() in TEXT_EXTENSIONS | DATA_EXTENSIONS:
                if "__pycache__" not in child.parts:
                    yield child


def chunk_id(path: Path, label: str, ordinal: int, text: str) -> str:
    base = f"{repo_path(path)}::{label}::{ordinal}::{sha256_text(text)[:12]}"
    safe = "".join(ch if ch.isalnum() or ch in "._:-/" else "-" for ch in base)
    return safe.replace("/", "__")


def make_chunk(path: Path, title: str, text: str, record: Any, ordinal: int) -> Dict[str, Any]:
    text = text.strip()
    return {
        "chunk_id": chunk_id(path, title, ordinal, text),
        "source_id": title,
        "source_file": repo_path(path),
        "layer": infer_layer(path),
        "record_type": record_type_from(path, record),
        "title": title,
        "text": text,
        "keywords": symbolic_targets(text, path, record)[:30],
        "symbolic_targets": symbolic_targets(text, path, record),
        "status": status_from(path, record),
        "created_from_sha256": sha256_text(text),
    }


def split_markdown(text: str, max_chars: int = 2200) -> List[tuple[str, str]]:
    sections: List[tuple[str, List[str]]] = []
    current_title = "document"
    current_lines: List[str] = []
    for line in text.splitlines():
        if line.startswith("#"):
            if current_lines:
                sections.append((current_title, current_lines))
            current_title = line.strip("# ") or "section"
            current_lines = [line]
        else:
            current_lines.append(line)
    if current_lines:
        sections.append((current_title, current_lines))
    chunks: List[tuple[str, str]] = []
    for title, lines in sections:
        block = "\n".join(lines).strip()
        if len(block) <= max_chars:
            chunks.append((title, block))
            continue
        paragraphs = [p.strip() for p in block.split("\n\n") if p.strip()]
        current = ""
        part = 1
        for paragraph in paragraphs:
            if current and len(current) + len(paragraph) + 2 > max_chars:
                chunks.append((f"{title} part {part}", current.strip()))
                part += 1
                current = ""
            current += paragraph + "\n\n"
        if current.strip():
            chunks.append((f"{title} part {part}" if part > 1 else title, current.strip()))
    return chunks


def interesting_json_records(value: Any) -> Iterable[Any]:
    if isinstance(value, dict):
        keys = set(value.keys())
        record_keys = {
            "id", "candidate_id", "feedback_id", "group_id", "review_id", "component_id",
            "layout_id", "schema", "record_type", "issue", "root_cause", "future_study_candidate",
        }
        if keys & record_keys:
            yield value
        for subvalue in value.values():
            if isinstance(subvalue, (dict, list)):
                yield from interesting_json_records(subvalue)
    elif isinstance(value, list):
        for item in value:
            yield from interesting_json_records(item)


def chunks_from_json(path: Path) -> List[Dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    records = list(interesting_json_records(data))
    chunks: List[Dict[str, Any]] = []
    file_text = flatten_json(data)
    chunks.append(make_chunk(path, path.stem, file_text[:6000], data, 0))
    seen_hashes = {chunks[0]["created_from_sha256"]}
    for idx, record in enumerate(records, start=1):
        text = flatten_json(record)
        digest = sha256_text(text)
        if digest in seen_hashes or not text.strip():
            continue
        seen_hashes.add(digest)
        chunks.append(make_chunk(path, title_from_record(record, f"{path.stem} record {idx}"), text, record, idx))
    return chunks


def chunks_from_csv(path: Path, max_rows: int = 300) -> List[Dict[str, Any]]:
    chunks: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = []
        for idx, row in enumerate(reader):
            if idx >= max_rows:
                break
            rows.append(row)
    summary = f"CSV rows indexed: {len(rows)}\n" + "\n".join(flatten_json(row) for row in rows[:25])
    chunks.append(make_chunk(path, path.stem, summary, {"record_type": "csv_summary"}, 0))
    for idx, row in enumerate(rows[:120], start=1):
        title = title_from_record(row, f"{path.stem} row {idx}")
        chunks.append(make_chunk(path, title, flatten_json(row), row, idx))
    return chunks


def chunks_from_text(path: Path) -> List[Dict[str, Any]]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    chunks: List[Dict[str, Any]] = []
    for idx, (title, block) in enumerate(split_markdown(text)):
        if block.strip():
            chunks.append(make_chunk(path, title or path.stem, block, {"record_type": "markdown_section"}, idx))
    return chunks


def build_chunks(source_paths: List[str], index_dir: Path) -> Dict[str, Any]:
    index_dir.mkdir(parents=True, exist_ok=True)
    chunks: List[Dict[str, Any]] = []
    files = list(iter_source_files(source_paths))
    for path in files:
        try:
            if path.suffix.lower() == ".json":
                chunks.extend(chunks_from_json(path))
            elif path.suffix.lower() == ".csv":
                chunks.extend(chunks_from_csv(path))
            else:
                chunks.extend(chunks_from_text(path))
        except Exception as exc:  # keep index build robust; surface source error as a chunk
            chunks.append(make_chunk(path, f"{path.stem} parse_error", f"Parse error: {exc}", {"record_type": "parse_error"}, 0))
    chunks_path = index_dir / "chunks.jsonl"
    with chunks_path.open("w", encoding="utf-8", newline="\n") as handle:
        for chunk in chunks:
            handle.write(json.dumps(chunk, ensure_ascii=False, sort_keys=True) + "\n")
    metadata = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "backend": "lexical_tfidf_fallback",
        "source_paths": source_paths,
        "source_file_count": len(files),
        "chunk_count": len(chunks),
        "chunks_file": chunks_path.as_posix(),
        "version": "0.1",
    }
    (index_dir / "metadata.json").write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser(description="Build source chunks for the local hybrid RAG vector index.")
    parser.add_argument("--index-dir", default="indexes/vector", help="Output index directory.")
    parser.add_argument("--source", action="append", dest="sources", help="Source path to index. Repeatable.")
    args = parser.parse_args()
    source_paths = args.sources or DEFAULT_SOURCE_PATHS
    metadata = build_chunks(source_paths, (REPO_ROOT / args.index_dir).resolve())
    print(json.dumps(metadata, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
