from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from .common import REPO_ROOT, load_chunks, score_query
except ImportError:  # pragma: no cover
    from common import REPO_ROOT, load_chunks, score_query  # type: ignore


def query_index(query: str, index_dir: Path, top_k: int = 8) -> dict:
    chunks = load_chunks(index_dir)
    results = score_query(query, chunks)[:top_k]
    public_results = []
    for item in results:
        public_results.append({
            "score": item["score"],
            "chunk_id": item["chunk_id"],
            "source_id": item.get("source_id"),
            "source_file": item.get("source_file"),
            "layer": item.get("layer"),
            "record_type": item.get("record_type"),
            "title": item.get("title"),
            "status": item.get("status"),
            "symbolic_targets": item.get("symbolic_targets", []),
            "excerpt": item.get("text", "")[:420].replace("\n", " "),
        })
    return {"query": query, "top_k": top_k, "results": public_results}


def main() -> None:
    parser = argparse.ArgumentParser(description="Query the local hybrid RAG vector-search fallback index.")
    parser.add_argument("--query", required=True)
    parser.add_argument("--top-k", type=int, default=8)
    parser.add_argument("--index-dir", default="indexes/vector")
    parser.add_argument("--json", action="store_true", help="Kept for CLI clarity; output is always JSON.")
    args = parser.parse_args()
    payload = query_index(args.query, (REPO_ROOT / args.index_dir).resolve(), args.top_k)
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
