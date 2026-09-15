from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

try:
    from .common import REPO_ROOT, load_chunks, tokenize
except ImportError:  # pragma: no cover
    from common import REPO_ROOT, load_chunks, tokenize  # type: ignore


def build_vector_index(index_dir: Path) -> dict:
    chunks = load_chunks(index_dir)
    documents = []
    for chunk in chunks:
        text = " ".join([
            chunk.get("title", ""),
            chunk.get("text", ""),
            " ".join(chunk.get("symbolic_targets", [])),
            " ".join(chunk.get("keywords", [])),
        ])
        counts = Counter(tokenize(text))
        documents.append({
            "chunk_id": chunk["chunk_id"],
            "token_count": sum(counts.values()),
            "tokens": dict(sorted(counts.items())),
        })
    payload = {
        "backend": "lexical_tfidf_fallback",
        "document_count": len(documents),
        "documents": documents,
    }
    (index_dir / "lexical_index.json").write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    config = {
        "backend": "lexical_tfidf_fallback",
        "embedding_provider": None,
        "no_network": True,
        "chunks_file": "chunks.jsonl",
        "index_file": "lexical_index.json",
        "authority_note": "Vector/lexical retrieval suggests candidates only; symbolic grounding and deterministic gates decide use.",
    }
    (index_dir / "index_config.json").write_text(json.dumps(config, indent=2, sort_keys=True), encoding="utf-8")
    return config | {"document_count": len(documents)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the local no-network vector-search fallback index.")
    parser.add_argument("--index-dir", default="indexes/vector")
    args = parser.parse_args()
    payload = build_vector_index((REPO_ROOT / args.index_dir).resolve())
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
