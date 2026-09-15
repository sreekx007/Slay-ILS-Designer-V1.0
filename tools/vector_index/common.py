"""Shared helpers for the local hybrid RAG vector-index prototype.

The implementation intentionally uses a deterministic lexical backend. It gives the
repository a no-network retrieval layer that can be tested and reviewed before any
external embedding service is introduced.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE_PATHS = [
    "knowledge/edes",
    "knowledge/edas",
    "knowledge/edikb",
    "knowledge/edpr",
    "knowledge/kel",
    "docs",
    "README.md",
    "framework_manifest.json",
]

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "have",
    "in", "is", "it", "its", "of", "on", "or", "that", "the", "this", "to", "was",
    "were", "with", "without", "when", "where", "which", "what", "how", "into", "than",
}

ALIASES = {
    "strongback": ["gd-st", "top frame", "top structure", "support frame"],
    "topframe": ["gd-st", "top frame"],
    "top": ["gd-st"],
    "frame": ["gd-st"],
    "base": ["gd-sb", "base structure", "support base"],
    "shroud": ["gd-sh", "tapered shroud"],
    "valve": ["gd-vlv", "header valve", "branch valve"],
    "roller": ["roller contact", "cannot ride rollers", "gd-sb"],
    "ride": ["cannot ride rollers", "gd-sb"],
    "vertical": ["z branch", "gd-b.variant=z", "ilt-z"],
    "horizontal": ["l branch", "gd-b", "branch connector"],
    "connector": ["gd-con", "connection", "association"],
    "spacing": ["p-s spacing", "connector spacing", "correlation", "future study"],
    "optimized": ["optimization", "correlation", "future study", "strain"],
    "strain": ["peak strain", "bending moment", "low strain"],
    "label": ["plot annotation", "plot labels", "q8"],
    "plot": ["plotter", "annotation", "label"],
}

PHRASE_EXPANSIONS = {
    "valve cannot ride rollers": ["gd-vlv", "gd-sb", "HEADER_VALVE_REQUIRES_GD_SB", "roller contact"],
    "cannot ride rollers": ["gd-vlv", "gd-sb", "HEADER_VALVE_REQUIRES_GD_SB"],
    "strongback support": ["gd-st", "gd-b", "gd-con", "branch-to-gd-st"],
    "branch connector": ["gd-b", "gd-con", "gd-st", "association"],
    "vertical connector": ["gd-b.variant=z", "ilt-z", "z branch", "gd-st"],
    "base frame too large": ["gd-sb", "support sizing", "component sizing", "q3"],
    "previous plot label": ["plot annotation", "connection labels", "q8"],
    "connector spacing optimized": ["gdst_ps_spacing", "future study", "correlation", "p-s spacing"],
    "sizing optimized": ["future study", "correlation", "dimension strain covariance"],
}

SYMBOL_PATTERNS = [
    re.compile(r"\bGD-[A-Za-z0-9]+\b"),
    re.compile(r"\bILT-[A-Za-z0-9*_.-]+\b"),
    re.compile(r"\b[A-Z][A-Z0-9]+(?:_[A-Z0-9]+){2,}\b"),
    re.compile(r"\bQ\d+_\d+[A-Z0-9_]*\b"),
]


def repo_path(path: Path) -> str:
    return path.resolve().relative_to(REPO_ROOT).as_posix()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def normalize_token(token: str) -> str:
    return token.lower().replace("_", "-")


def tokenize(text: str, expand: bool = True) -> List[str]:
    raw = re.findall(r"[A-Za-z0-9][A-Za-z0-9_.:/+-]*", text.lower())
    tokens: List[str] = []
    for token in raw:
        token = normalize_token(token)
        if len(token) < 2 or token in STOPWORDS:
            continue
        tokens.append(token)
        compact = token.replace("-", "")
        if compact != token:
            tokens.append(compact)
        if expand and token in ALIASES:
            tokens.extend(tokenize(" ".join(ALIASES[token]), expand=False))
    if expand:
        lower = text.lower()
        for phrase, additions in PHRASE_EXPANSIONS.items():
            if phrase in lower:
                tokens.extend(tokenize(" ".join(additions), expand=False))
    return tokens


def infer_layer(path: Path) -> str:
    rel = repo_path(path).lower()
    if "/edes/" in f"/{rel}" or rel.startswith("knowledge/edes"):
        return "EDES"
    if "/edas/" in f"/{rel}" or rel.startswith("knowledge/edas"):
        return "EDAS"
    if "/edikb/" in f"/{rel}" or rel.startswith("knowledge/edikb"):
        return "EDIKB"
    if "/edpr/" in f"/{rel}" or rel.startswith("knowledge/edpr"):
        return "EDPR"
    if "/kel/" in f"/{rel}" or rel.startswith("knowledge/kel"):
        return "KEL"
    if rel == "framework_manifest.json":
        return "MANIFEST"
    if rel == "readme.md":
        return "README"
    if rel.startswith("docs/"):
        return "DOC"
    return "DOC"


def flatten_json(value: Any, prefix: str = "") -> str:
    parts: List[str] = []
    if isinstance(value, dict):
        for key, subvalue in value.items():
            label = f"{prefix}.{key}" if prefix else str(key)
            if isinstance(subvalue, (dict, list)):
                parts.append(flatten_json(subvalue, label))
            else:
                parts.append(f"{label}: {subvalue}")
    elif isinstance(value, list):
        for idx, item in enumerate(value):
            parts.append(flatten_json(item, f"{prefix}[{idx}]" if prefix else f"[{idx}]"))
    else:
        parts.append(f"{prefix}: {value}" if prefix else str(value))
    return "\n".join(part for part in parts if part)


def title_from_record(record: Any, fallback: str) -> str:
    if isinstance(record, dict):
        for key in ("id", "candidate_id", "feedback_id", "group_id", "review_id", "name", "title", "label", "component_id", "layout_id"):
            value = record.get(key)
            if value:
                return str(value)
    return fallback


def record_type_from(path: Path, record: Any) -> str:
    rel = repo_path(path).lower()
    if "future_study_candidates" in rel:
        return "future_study_candidate"
    if "root_cause" in rel:
        return "root_cause_log"
    if "feedback_records" in rel:
        return "kel_feedback"
    if "expert_reviews" in rel:
        return "kel_expert_review"
    if "implementation" in rel and infer_layer(path) == "KEL":
        return "kel_implementation"
    if isinstance(record, dict):
        for key in ("record_type", "type", "schema", "category"):
            value = record.get(key)
            if value:
                return str(value)
    suffix = path.suffix.lower().lstrip(".") or "text"
    return f"{infer_layer(path).lower()}_{suffix}"


def status_from(path: Path, record: Any) -> str:
    rel = repo_path(path).lower()
    if "/implemented/" in rel:
        return "implemented"
    if "/accepted/" in rel:
        return "accepted"
    if "/rejected/" in rel:
        return "rejected"
    if "/candidates/" in rel or "future_study_candidates" in rel:
        return "candidate"
    if isinstance(record, dict):
        for key in ("status", "decision", "lifecycle_state"):
            value = record.get(key)
            if value:
                return str(value)
    return "current"


def symbolic_targets(text: str, path: Path | None = None, record: Any = None) -> List[str]:
    targets = set()
    for pattern in SYMBOL_PATTERNS:
        for match in pattern.findall(text):
            targets.add(match)
    lower = text.lower()
    rules = {
        "HEADER_VALVE_REQUIRES_GD_SB": ["header valve", "base structure", "cannot ride rollers", "roller contact"],
        "BRANCH_TO_GD_ST_ASSOCIATION": ["branch", "gd-st", "top frame", "association"],
        "GD_B_VERTICAL_CONNECTOR_TO_Z_BRANCH": ["vertical connector", "z branch", "ilt-z"],
        "GD_SB_GD_ST_SUPPORT_SIZING_GATE": ["support sizing", "base structure depth", "base structure length", "dimension"],
        "PLOT_LABEL_ANNOTATION_GATE": ["plot", "label", "annotation", "connection labels"],
        "GDST_PS_SPACING_CORRELATION_GAP": ["p-s", "connector spacing", "correlation"],
        "GDVLV_GDSH_STIFF_COMPONENT_EVIDENCE": ["gd-vlv", "gd-sh", "stiff component", "tapered shroud"],
    }
    for target, phrases in rules.items():
        if any(phrase in lower for phrase in phrases):
            targets.add(target)
    if path is not None:
        layer = infer_layer(path)
        rel = repo_path(path)
        stem = path.stem
        if layer == "KEL":
            targets.add(f"kel:{stem}")
        elif layer == "EDIKB":
            targets.add(f"edikb:{stem}")
        elif layer == "EDES":
            targets.add(f"edes:{stem}")
        elif layer == "EDAS":
            targets.add(f"edas:{stem}")
        if "future_study_candidates" in rel:
            targets.add(f"future_study:{stem}")
    if isinstance(record, dict):
        for key in ("id", "candidate_id", "feedback_id", "group_id", "review_id", "component_id", "layout_id"):
            value = record.get(key)
            if value:
                targets.add(str(value))
    return sorted(targets)


def document_frequency(doc_tokens: Sequence[Sequence[str]]) -> Dict[str, int]:
    df: Dict[str, int] = defaultdict(int)
    for tokens in doc_tokens:
        for token in set(tokens):
            df[token] += 1
    return dict(df)


def score_query(query: str, chunks: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    query_tokens = tokenize(query)
    query_counts = Counter(query_tokens)
    doc_tokens = [tokenize(chunk.get("text", "") + " " + chunk.get("title", "") + " " + " ".join(chunk.get("symbolic_targets", []))) for chunk in chunks]
    df = document_frequency(doc_tokens)
    total_docs = max(len(chunks), 1)
    q_norm = math.sqrt(sum(count * count for count in query_counts.values())) or 1.0
    results: List[Dict[str, Any]] = []
    query_lower = query.lower()
    for chunk, tokens in zip(chunks, doc_tokens):
        counts = Counter(tokens)
        dot = 0.0
        for token, q_count in query_counts.items():
            if token not in counts:
                continue
            idf = math.log((total_docs + 1) / (df.get(token, 0) + 1)) + 1.0
            dot += q_count * counts[token] * idf
        d_norm = math.sqrt(sum(count * count for count in counts.values())) or 1.0
        score = dot / (q_norm * d_norm)
        combined = " ".join([chunk.get("title", ""), chunk.get("text", ""), " ".join(chunk.get("symbolic_targets", []))]).lower()
        for phrase, additions in PHRASE_EXPANSIONS.items():
            if phrase in query_lower:
                for addition in additions:
                    if addition.lower() in combined:
                        score += 0.08
        for target in chunk.get("symbolic_targets", []):
            t = str(target).lower()
            if t in query_lower or t.replace("_", " ").lower() in query_lower:
                score += 0.12
        if chunk.get("record_type") == "future_study_candidate" and any(word in query_lower for word in ("optimized", "correlation", "spacing", "covariance")):
            score += 0.08
        if chunk.get("layer") == "KEL" and any(word in query_lower for word in ("mistake", "previous", "label", "base frame", "valve")):
            score += 0.05
        if score > 0:
            result = dict(chunk)
            result["score"] = round(score, 6)
            results.append(result)
    results.sort(key=lambda item: item["score"], reverse=True)
    return results


def load_chunks(index_dir: Path) -> List[Dict[str, Any]]:
    chunks_path = index_dir / "chunks.jsonl"
    chunks: List[Dict[str, Any]] = []
    with chunks_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                chunks.append(json.loads(line))
    return chunks
