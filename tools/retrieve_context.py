#!/usr/bin/env python3
"""
Retrieve EDES, EDAS, standard-layout, EDIKB graph, and numeric evidence context
for an EDPR problem JSON file.

This is intentionally dependency-light. It does not perform vector search yet;
it performs deterministic ontology-ID and keyword retrieval over the repository
files so the framework can be tested end to end before adding embeddings.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST_NAMES = ("framework_manifest.json", "framework_manifest_v0_2.json")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def walk(value: Any):
    yield value
    if isinstance(value, dict):
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def normalize_token(value: Any) -> str:
    return str(value).strip().lower()


def compact_json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True).lower()


def tokenise(text: str) -> set[str]:
    stop = {
        "the",
        "and",
        "for",
        "with",
        "that",
        "this",
        "from",
        "into",
        "need",
        "give",
        "layout",
        "design",
        "solution",
    }
    return {tok for tok in re.findall(r"[A-Za-z0-9][A-Za-z0-9_\-]{2,}", text.lower()) if tok not in stop}


def find_manifest(repo_root: Path, explicit: str | None) -> Path | None:
    if explicit:
        path = Path(explicit)
        return path if path.is_absolute() else repo_root / path
    for name in DEFAULT_MANIFEST_NAMES:
        path = repo_root / name
        if path.exists():
            return path
    return None


def collect_retrieval_terms(edpr: dict[str, Any]) -> dict[str, set[str]]:
    component_ids: set[str] = set()
    assembly_ids: set[str] = set()
    layout_ids: set[str] = set()
    edikb_ids: set[str] = set()
    dataset_filters: list[dict[str, Any]] = []

    for item in edpr.get("candidateComponents", []):
        if isinstance(item, dict):
            value = item.get("componentId") or item.get("id")
            if isinstance(value, str) and value.startswith("edes:"):
                component_ids.add(value)

    for item in edpr.get("candidateAssemblies", []):
        if isinstance(item, dict):
            value = item.get("assemblyPatternId") or item.get("assemblyId") or item.get("id")
            if isinstance(value, str):
                assembly_ids.add(value)

    for item in edpr.get("standardLayoutCandidates", []):
        if isinstance(item, dict):
            for key in ("layoutId", "layoutFamily"):
                value = item.get(key)
                if isinstance(value, str):
                    layout_ids.add(value)

    for item in edpr.get("retrievalPlan", []):
        if not isinstance(item, dict):
            continue
        for target in as_list(item.get("targets")):
            if not isinstance(target, str):
                continue
            if target.startswith("edes:"):
                component_ids.add(target)
            elif target.startswith("edas:"):
                assembly_ids.add(target)
            elif target.startswith("edikb:") or target.startswith("EDIKB_"):
                edikb_ids.add(target)
            elif target.startswith("ILS-") or target.startswith("ILT-"):
                layout_ids.add(target)

    for item in edpr.get("numericComparisonPlan", []):
        if isinstance(item, dict):
            dataset_filters.append(item)

    for item in edpr.get("interactionEffectPlan", []):
        if not isinstance(item, dict):
            continue
        for key in (
            "componentSet",
            "isolatedEffectRules",
            "combinedEffectRules",
            "interactionCandidateRules",
            "requiredDatasetQueries",
        ):
            for value in as_list(item.get(key)):
                if not isinstance(value, str):
                    continue
                if value.startswith("edes:"):
                    component_ids.add(value)
                elif value.startswith("edikb:") or value.startswith("EDIKB_"):
                    edikb_ids.add(value)

    raw = edpr.get("sourceRequest", {}).get("rawText", "")
    title = edpr.get("problemIdentity", {}).get("title", "")
    semantic_tokens = tokenise(f"{raw} {title} {' '.join(component_ids)} {' '.join(layout_ids)}")

    return {
        "component_ids": component_ids,
        "assembly_ids": assembly_ids,
        "layout_ids": layout_ids,
        "edikb_ids": edikb_ids,
        "semantic_tokens": semantic_tokens,
        "dataset_filter_ids": {item.get("id", "") for item in dataset_filters if isinstance(item, dict)},
    }


def edes_file_for(component_id: str, repo_root: Path) -> Path:
    short = component_id.split(":", 1)[1]
    return repo_root / "knowledge" / "edes" / f"EDES_{short}_KNOWLEDGE.json"


def load_component_context(component_ids: set[str], repo_root: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for component_id in sorted(component_ids):
        path = edes_file_for(component_id, repo_root)
        if path.exists():
            out.append({"component_id": component_id, "repo_path": str(path.relative_to(repo_root)), "content": load_json(path)})
        else:
            out.append({"component_id": component_id, "repo_path": str(path.relative_to(repo_root)), "missing": True})
    return out


def load_assembly_context(repo_root: Path) -> dict[str, Any]:
    context: dict[str, Any] = {}
    paths = {
        "edas_shared": repo_root / "knowledge" / "edas" / "EDAS_SHARED_KNOWLEDGE.json",
        "standard_layouts": repo_root / "knowledge" / "edas" / "standard_ils_layouts.json",
    }
    for key, path in paths.items():
        if path.exists():
            context[key] = {"repo_path": str(path.relative_to(repo_root)), "content": load_json(path)}
        else:
            context[key] = {"repo_path": str(path.relative_to(repo_root)), "missing": True}
    return context


def filter_standard_layouts(standard_layout_content: Any, layout_ids: set[str]) -> dict[str, Any]:
    if not layout_ids:
        return {"matched": [], "note": "No standard-layout targets supplied by EDPR."}
    matches: list[Any] = []
    wanted = {normalize_token(x) for x in layout_ids}
    for node in walk(standard_layout_content):
        if isinstance(node, dict):
            text = compact_json_text(node)
            if any(item.lower() in text for item in wanted):
                matches.append(node)
    return {"matched": matches[:80], "match_count": len(matches), "targets": sorted(layout_ids)}


def filter_graph(graph: dict[str, Any], terms: dict[str, set[str]], max_nodes: int) -> dict[str, Any]:
    ids = terms["edikb_ids"]
    tokens = terms["semantic_tokens"] | {x.split(":", 1)[-1].lower() for x in terms["component_ids"]}
    tokens |= {x.lower() for x in terms["layout_ids"]}

    selected_nodes: list[dict[str, Any]] = []
    selected_node_ids: set[str] = set()

    # First pass: exact EDIKB rule/node IDs requested by EDPR. These should not
    # be crowded out by broader keyword hits.
    for node in graph.get("nodes", []):
        if not isinstance(node, dict):
            continue
        node_id = str(node.get("id", ""))
        if node_id in ids or f"edikb:{node_id}" in ids:
            selected_nodes.append(node)
            selected_node_ids.add(node_id)
        if len(selected_nodes) >= max_nodes:
            break

    # Second pass: semantic expansion for nearby guidance and ML candidates.
    for node in graph.get("nodes", []):
        if len(selected_nodes) >= max_nodes:
            break
        if not isinstance(node, dict):
            continue
        node_id = str(node.get("id", ""))
        if node_id in selected_node_ids:
            continue
        text = compact_json_text(node)
        if any(tok and tok in text for tok in tokens):
            selected_nodes.append(node)
            selected_node_ids.add(node_id)

    selected_edges: list[dict[str, Any]] = []
    for edge in graph.get("edges", []):
        if not isinstance(edge, dict):
            continue
        source = str(edge.get("source", ""))
        target = str(edge.get("target", ""))
        if source in selected_node_ids or target in selected_node_ids:
            selected_edges.append(edge)

    return {
        "graph_id": graph.get("id"),
        "selected_node_count": len(selected_nodes),
        "selected_edge_count": len(selected_edges),
        "selected_nodes": selected_nodes,
        "selected_edges": selected_edges[: max_nodes * 4],
    }


def row_matches_filter(row: dict[str, str], filters: dict[str, Any]) -> bool:
    if not filters:
        return False
    checked = 0
    passed = 0
    for key, wanted in filters.items():
        if key not in row:
            continue
        checked += 1
        cell = normalize_token(row.get(key, ""))
        values = [normalize_token(x) for x in as_list(wanted)]
        if not cell:
            continue
        if any(cell == value or value in cell or cell in value for value in values):
            passed += 1
    return checked > 0 and passed == checked


def filter_dataset(
    csv_path: Path,
    edpr: dict[str, Any],
    terms: dict[str, set[str]],
    max_rows: int,
) -> dict[str, Any]:
    if not csv_path.exists():
        return {"repo_path": str(csv_path), "missing": True, "rows": []}

    plans = [item for item in edpr.get("numericComparisonPlan", []) if isinstance(item, dict)]
    exact_rows: list[dict[str, str]] = []
    fallback_rows: list[dict[str, str]] = []
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            matched = any(row_matches_filter(row, plan.get("filters", {})) for plan in plans)
            if matched:
                exact_rows.append(row)
            elif not plans:
                text = " ".join(row.values()).lower()
                matched = any(tok in text for tok in terms["semantic_tokens"] | {x.lower() for x in terms["layout_ids"]})
                if matched:
                    fallback_rows.append(row)

    rows = exact_rows if exact_rows else fallback_rows

    return {
        "repo_path": str(csv_path.relative_to(REPO_ROOT)) if csv_path.is_relative_to(REPO_ROOT) else str(csv_path),
        "row_count_returned": min(len(rows), max_rows),
        "row_count_matched_before_limit": len(rows),
        "rows": rows[:max_rows],
        "match_mode": "numericComparisonPlan_exact" if exact_rows else "semantic_keyword_fallback",
        "note": "Rows are filtered by numericComparisonPlan first. Semantic keyword fallback is used only when no numericComparisonPlan rows are found.",
    }


def build_context_package(args: argparse.Namespace) -> dict[str, Any]:
    repo_root = Path(args.repo_root).resolve()
    edpr_path = Path(args.edpr_json).resolve()
    manifest_path = find_manifest(repo_root, args.manifest)

    edpr = load_json(edpr_path)
    manifest = load_json(manifest_path) if manifest_path and manifest_path.exists() else None
    terms = collect_retrieval_terms(edpr)

    graph_path = repo_root / "knowledge" / "edikb" / "EDIKB_FULL_KNOWLEDGE_GRAPH.json"
    dataset_path = repo_root / "knowledge" / "edikb" / "EDIKB_FULL_DATASET.csv"
    graph = load_json(graph_path) if graph_path.exists() else {"nodes": [], "edges": [], "missing": True}

    assembly_context = load_assembly_context(repo_root)
    standard_layout_subset = {}
    std_content = assembly_context.get("standard_layouts", {}).get("content")
    if std_content is not None:
        standard_layout_subset = filter_standard_layouts(std_content, terms["layout_ids"])

    return {
        "package_type": "edpr_retrieval_context",
        "schema_version": "0.1",
        "edpr_source": str(edpr_path),
        "repo_root": str(repo_root),
        "manifest_path": str(manifest_path) if manifest_path else None,
        "manifest_version": manifest.get("manifest_schema_version") if isinstance(manifest, dict) else None,
        "problem": {
            "id": edpr.get("id"),
            "title": edpr.get("problemIdentity", {}).get("title"),
            "raw_text": edpr.get("sourceRequest", {}).get("rawText"),
        },
        "retrieval_terms": {key: sorted(value) for key, value in terms.items()},
        "component_context": load_component_context(terms["component_ids"], repo_root),
        "assembly_context": assembly_context,
        "standard_layout_subset": standard_layout_subset,
        "edikb_graph_context": filter_graph(graph, terms, args.max_graph_nodes),
        "numeric_evidence": filter_dataset(dataset_path, edpr, terms, args.max_dataset_rows),
        "retrieval_notes": [
            "Deterministic retrieval only; add vector index retrieval later for semantic expansion.",
            "For quantitative ranking, prefer numeric_evidence rows over graph-only guidance.",
            "For combined layouts, inspect interactionEffectPlan and EDIKB interaction nodes before assuming additive effects.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Retrieve framework context for an EDPR problem JSON.")
    parser.add_argument("edpr_json", help="Path to EDPR problem JSON.")
    parser.add_argument("--repo-root", default=str(REPO_ROOT), help="Repository root. Default: parent of tools/.")
    parser.add_argument("--manifest", default=None, help="Manifest path relative to repo root or absolute path.")
    parser.add_argument("--output", "-o", default=None, help="Output JSON file. Default: print to stdout.")
    parser.add_argument("--max-graph-nodes", type=int, default=80)
    parser.add_argument("--max-dataset-rows", type=int, default=120)
    args = parser.parse_args()

    package = build_context_package(args)
    if args.output:
        write_json(Path(args.output), package)
    else:
        print(json.dumps(package, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
