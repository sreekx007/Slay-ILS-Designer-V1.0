from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

try:
    from .common import REPO_ROOT
    from .query_vector_index import query_index
except ImportError:  # pragma: no cover
    from common import REPO_ROOT  # type: ignore
    from query_vector_index import query_index  # type: ignore

LAYER_KEYS = ("EDPR", "EDES", "EDAS", "EDIKB", "KEL", "MANIFEST", "README", "DOC")


def classify_target(target: str, fallback_layer: str) -> str:
    lower = target.lower()
    if lower.startswith("kel:") or target.startswith("Q"):
        return "KEL"
    if lower.startswith("edikb:") or lower.startswith("future_study:") or "CORRELATION" in target or "COVARIANCE" in target:
        return "EDIKB"
    if lower.startswith("edes:") or target.startswith("GD-"):
        return "EDES"
    if lower.startswith("edas:") or target.startswith("ILT-") or "ASSOCIATION" in target or "Z_BRANCH" in target:
        return "EDAS"
    if lower.startswith("edpr:"):
        return "EDPR"
    if "GATE" in target or "REQUIRES" in target or "PLOT" in target:
        return "KEL"
    return fallback_layer if fallback_layer in LAYER_KEYS else "DOC"


def ground_results(payload: Dict[str, Any]) -> Dict[str, Any]:
    grounded: Dict[str, List[str]] = {key: [] for key in LAYER_KEYS}
    evidence: List[Dict[str, Any]] = []
    unresolved: List[str] = []
    for result in payload.get("results", []):
        source_file = result.get("source_file")
        source_path = REPO_ROOT / source_file if source_file else None
        if not source_file or not source_path.exists():
            unresolved.append(result.get("chunk_id", "unknown"))
            continue
        targets = result.get("symbolic_targets") or [result.get("source_id") or result.get("chunk_id")]
        for target in targets:
            layer = classify_target(str(target), result.get("layer", "DOC"))
            if target not in grounded[layer]:
                grounded[layer].append(str(target))
        evidence.append({
            "chunk_id": result.get("chunk_id"),
            "source_file": source_file,
            "layer": result.get("layer"),
            "score": result.get("score"),
            "title": result.get("title"),
        })
    grounded = {key: values for key, values in grounded.items() if values}
    return {
        "query": payload.get("query"),
        "grounded_candidates": grounded,
        "evidence_chunks": evidence,
        "unresolved_chunks": unresolved,
        "authority_note": "Retrieved candidates are hints. Official use still requires source-record resolution, EDAS/EDPR/EDIKB applicability checks, and KEL/governance gates.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Ground vector-search results to symbolic framework layers.")
    parser.add_argument("--query", help="Run a query before grounding.")
    parser.add_argument("--results-json", help="Existing query result JSON file to ground.")
    parser.add_argument("--top-k", type=int, default=8)
    parser.add_argument("--index-dir", default="indexes/vector")
    args = parser.parse_args()
    if args.results_json:
        payload = json.loads(Path(args.results_json).read_text(encoding="utf-8"))
    elif args.query:
        payload = query_index(args.query, (REPO_ROOT / args.index_dir).resolve(), args.top_k)
    else:
        raise SystemExit("Provide --query or --results-json")
    print(json.dumps(ground_results(payload), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
