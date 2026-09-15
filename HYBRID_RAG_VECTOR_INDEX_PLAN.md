# Hybrid RAG Vector Index Plan Spec

## Purpose

This document defines the implementation plan for adding a vector-retrieval layer to Slay-ILS-Designer without replacing the existing symbolic engineering knowledge base.

The goal is to improve semantic recall from varied human language, organization-specific terminology, reports, review comments, and engineering documents, while keeping EDPR, EDES, EDAS, EDIKB, KEL, schemas, tools, and workflow gates as the authoritative engineering layer.

## Core Principle

Vector retrieval suggests candidate knowledge.

Symbolic grounding and deterministic gates decide whether the candidate knowledge may be used.

```text
Natural-language query
-> vector retrieval for semantic candidates
-> symbolic grounding to EDPR / EDES / EDAS / EDIKB / KEL IDs
-> schema validation and workflow gates
-> governed output or explicit gap
```

Do not replace official JSON, CSV, Markdown, or graph records with embeddings. The vector index is a generated search artifact.

## Why This Is Needed

Engineering users and organizations use different words for similar concepts.

Examples:

| Human / document wording | Symbolic grounding target |
|---|---|
| strongback, top frame, upper frame | `GD-ST`, EDAS top-structure associations |
| base frame, stiffener bracket, lower support | `GD-SB`, valve/base protection gates |
| valve cannot ride rollers | `GD-VLV`, GD-SB protection, roller-contact limitation |
| vertical connector | `GD-B.variant = Z`, `ILT-Z-*` anchors |
| branch support | `GD-B`, `GD-ST`, `GD-Con`, terminal association |
| similar previous mistake | KEL root-cause records and implemented gates |
| is this sizing optimized? | EDIKB evidence, future-study candidates, correlation-gap records |

Without semantic retrieval, exact symbolic matching may miss relevant records.

Without symbolic grounding, vector retrieval may return relevant-looking but non-authoritative text.

The required solution is hybrid RAG.

## Scope

### In Scope

Vectorize searchable views generated from:

| Layer | Include |
|---|---|
| EDES | Component definitions, aliases, functions, constraints, parameters, assembly features |
| EDAS | Assembly rules, topology patterns, standard anchors, connection systems, emit/build rules |
| EDIKB | Behavior rules, evidence summaries, guidance, uncertainty notes, future study candidates |
| EDPR | Example problem formulations and parser prompt fragments suitable for retrieval |
| KEL | Feedback records, root-cause logs, graph change requests, expert reviews, implementation updates |
| Docs | Crosswalks, workflow docs, plotter plans, design gate docs |
| External reports later | Extracted chunks from PDFs, reports, review comments, meeting notes, and calculation narratives |

### Out of Scope For First Pass

- No automatic promotion from retrieved document text into official EDES/EDAS/EDIKB.
- No direct design decision from vector similarity alone.
- No embedding of binary drawings unless text extraction/OCR is separately implemented.
- No replacement of current retrieval, validator, plotter, or KEL tools.

## Recommended Generated Structure

```text
indexes/
  vector/
    chunks.jsonl
    metadata.json
    index_config.json
    embeddings.npy              # if using local FAISS / NumPy flow
    faiss.index                 # optional
```

If using Chroma or LanceDB:

```text
indexes/
  vector/
    chroma_db/
    chunks.jsonl
    metadata.json
    index_config.json
```

The `indexes/` folder should be generated and may be excluded from Git if embeddings are large. The chunk-generation script should be committed.

## Chunk Schema

Each chunk should retain a link to the authoritative source.

```json
{
  "chunk_id": "chunk:edes:GD-SB:001",
  "source_id": "edes:GD-SB",
  "source_file": "knowledge/edes/EDES_GD-SB_KNOWLEDGE.json",
  "layer": "EDES",
  "record_type": "component",
  "title": "GD-SB base protection structure",
  "text": "GD-SB is a base protection structure below the header pipe...",
  "keywords": ["GD-SB", "base frame", "stiffener bracket", "roller protection"],
  "symbolic_targets": ["edes:GD-SB", "gate:HEADER_VALVE_REQUIRES_GD_SB"],
  "status": "official",
  "created_from_sha256": "..."
}
```

For KEL:

```json
{
  "chunk_id": "chunk:kel:Q2_02:001",
  "source_id": "kel:feedback:Q2_02_HEADER_VALVE_REQUIRES_GD_SB",
  "source_file": "knowledge/kel/feedback_records/implemented/Q2_02_HEADER_VALVE_REQUIRES_GD_SB.json",
  "layer": "KEL",
  "record_type": "root_cause_or_feedback",
  "title": "Header valve requires GD-SB protection",
  "text": "Previous KEL feedback found that a header valve was added without required base/protection structure...",
  "symbolic_targets": ["edes:GD-VLV", "edes:GD-SB", "gate:HEADER_VALVE_REQUIRES_GD_SB"],
  "status": "implemented"
}
```

For EDIKB future study candidates:

```json
{
  "chunk_id": "chunk:edikb_future:GDST_PS_SPACING:001",
  "source_id": "edikb:future_study:gdst_ps_spacing_branch_valve_strain_01",
  "source_file": "knowledge/edikb/future_study_candidates/GDST_PS_SPACING_BRANCH_VALVE_STRAIN_01.json",
  "layer": "EDIKB",
  "record_type": "future_study_candidate",
  "title": "GD-ST length and P-S connector spacing correlation",
  "text": "Future correlation study needed before claiming GD-ST length or P-S connector spacing is low-strain optimized...",
  "symbolic_targets": ["GD-ST", "GD-B", "GD-Con", "GD-VLV"],
  "status": "candidate"
}
```

## Implementation Phases

### Phase 1 - Chunk Generator

Add:

```text
tools/vector_index/build_chunks.py
```

Responsibilities:

1. Walk configured source paths.
2. Parse JSON, CSV, and Markdown.
3. Generate normalized text chunks.
4. Attach source metadata and symbolic targets.
5. Write `indexes/vector/chunks.jsonl`.
6. Write `indexes/vector/metadata.json`.

Recommended source paths:

```text
knowledge/edes/
knowledge/edas/
knowledge/edikb/
knowledge/edpr/
knowledge/kel/
docs/
README.md
framework_manifest.json
```

Generated chunks should be deterministic where possible.

### Phase 2 - Embedding Builder

Add:

```text
tools/vector_index/build_vector_index.py
```

Responsibilities:

1. Read `chunks.jsonl`.
2. Generate embeddings using configured backend.
3. Save vector index and metadata.
4. Preserve chunk IDs and source links.

Recommended initial embedding backend:

- Option A: local sentence-transformers if available.
- Option B: OpenAI embeddings if API is configured.
- Option C: simple placeholder lexical index for offline smoke tests.

The first implementation should support a no-network fallback so tests can run.

### Phase 3 - Retrieval CLI

Add:

```text
tools/vector_index/query_vector_index.py
```

Example:

```bash
python tools/vector_index/query_vector_index.py \
  --query "valve cannot ride rollers, need lower support" \
  --top-k 8
```

Expected output should include:

```json
{
  "query": "valve cannot ride rollers, need lower support",
  "results": [
    {
      "score": 0.83,
      "chunk_id": "chunk:edes:GD-SB:001",
      "source_id": "edes:GD-SB",
      "source_file": "knowledge/edes/EDES_GD-SB_KNOWLEDGE.json",
      "layer": "EDES",
      "symbolic_targets": ["edes:GD-SB", "gate:HEADER_VALVE_REQUIRES_GD_SB"]
    }
  ]
}
```

### Phase 4 - Symbolic Grounding

Add:

```text
tools/vector_index/ground_retrieval.py
```

Responsibilities:

1. Accept vector retrieval results.
2. Resolve `source_file` and `source_id`.
3. Load authoritative JSON/Markdown source.
4. Extract official IDs, component codes, gates, evidence refs, and lifecycle status.
5. Return grounded candidates grouped by framework layer.

Example grounded output:

```json
{
  "grounded_candidates": {
    "EDES": ["edes:GD-VLV", "edes:GD-SB"],
    "EDAS": ["edas:layout:ILT-Z-FT-PS"],
    "EDIKB": ["edikb:future_study:gdvlv_gdsb_contact_moment_01"],
    "KEL": ["kel:feedback:Q2_02_HEADER_VALVE_REQUIRES_GD_SB"],
    "gates": ["HEADER_VALVE_REQUIRES_GD_SB", "VALVE_PROTECTION_INPUTS_MISSING"]
  },
  "unresolved_chunks": []
}
```

### Phase 5 - Workflow Integration

Add vector retrieval as an optional pre-retrieval step.

Suggested integration points:

1. EDPR parser support:
   - use semantic retrieval to help map natural phrases to EDPR artifacts and issues.
2. `tools/retrieve_context.py`:
   - optionally accept vector-grounded candidates as retrieval hints.
3. `tools/design_rules_v02.py`:
   - do not trust vector results directly;
   - only use grounded symbolic IDs and structured fields.
4. KEL:
   - retrieve similar prior KEL root causes before answering design queries.

Command option idea:

```bash
python tools/run_design_workflow.py \
  --edpr-json path/to/problem.json \
  --output-dir runs/problem \
  --plot \
  --use-vector-retrieval
```

## Retrieval Policy

Vector retrieval may:

- suggest relevant components;
- suggest possible assemblies;
- suggest behavior evidence;
- suggest similar KEL failures;
- suggest future study candidates;
- suggest external document passages.

Vector retrieval must not:

- approve an engineering claim;
- bypass EDPR confirmation;
- bypass EDES/EDAS/EDIKB validation;
- bypass KEL review;
- create official knowledge automatically;
- treat similarity as applicability.

## Grounding Rules

1. Every retrieved chunk must map back to `source_file`.
2. Official framework records must expose `source_id` or symbolic ID.
3. If a retrieved chunk cannot be grounded, classify it as `unresolved_context`.
4. If a retrieved external document passage suggests new knowledge, create a candidate record, not an official update.
5. If retrieved evidence is analogous but not direct, mark it as `analogous_evidence`.
6. If no sufficient evidence exists, create or link a future study candidate.

## KEL Integration

When a vector retrieval result surfaces a KEL record, the workflow should use it as a warning signal.

Example:

```text
Query: "header valve, cannot ride rollers"
Retrieved KEL: Q2_02_HEADER_VALVE_REQUIRES_GD_SB
Action: force valve-protection gates before layout emission
```

KEL retrieval should help prevent repeated failure modes:

- missing GD-SB for header valve;
- branch connector not associated with GD-ST;
- freehand plot not generated by repo plotter;
- ungrounded strain-watch arrows;
- failure to ask post-plot feedback;
- treating EDAS precedent as optimized correlation.

## External Document Ingestion

Future phase:

```text
documents/
  source_reports/
  extracted/
```

Pipeline:

```text
PDF/report/email/note
-> text extraction
-> chunking
-> vector index
-> semantic retrieval
-> candidate EDES/EDAS/EDIKB/KEL/future-study record
-> expert review
-> official promotion if accepted
```

Do not ingest copyrighted or proprietary reports into Git unless permitted. Store only metadata, extracted permitted snippets, or local/private indexes as appropriate.

## Tests

Add tests:

```text
tests/vector_index/test_chunk_generation.py
tests/vector_index/test_symbolic_grounding.py
tests/vector_index/test_query_examples.py
```

Minimum test queries:

| Query | Expected symbolic targets |
|---|---|
| valve cannot ride rollers | `GD-VLV`, `GD-SB`, `HEADER_VALVE_REQUIRES_GD_SB` |
| strongback support for branch connector | `GD-ST`, `GD-B`, `GD-Con`, branch-to-GD-ST association |
| vertical connector branch | `GD-B.variant=Z`, `ILT-Z-*` |
| base frame too large for valve | support sizing KEL / GD-SB dimension gate |
| similar previous plot label issue | Q8 KEL plot annotation / label scope records |
| is connector spacing optimized | EDIKB future study candidate for GD-ST P-S spacing |

Tests should pass without external embedding API by using deterministic mock embeddings or lexical fallback.

## First Implementation Milestone

Milestone 1 is complete when:

1. `build_chunks.py` generates `chunks.jsonl` from EDES, EDAS, EDIKB, KEL, EDPR, docs.
2. `query_vector_index.py` returns relevant candidate chunks for the six minimum test queries.
3. `ground_retrieval.py` maps retrieved chunks to symbolic IDs and source files.
4. Tests pass without network.
5. Documentation explains that the vector index is a generated semantic search layer, not official engineering knowledge.

## Second Implementation Milestone

Milestone 2 is complete when:

1. `retrieve_context.py` can optionally use grounded vector candidates.
2. KEL root-cause records are retrieved as warning signals.
3. Future study candidates are retrieved when optimization/correlation evidence is missing.
4. The governed workflow report records whether vector retrieval was used and which grounded IDs were added.

## Paper Language

Suggested wording for the paper:

> The framework maintains a symbolic knowledge base as the authoritative engineering layer and generates vector-indexed retrieval views from the same records and from external documents. Vector retrieval improves semantic recall from varied engineering language; symbolic grounding maps retrieved candidates to official EDPR, EDES, EDAS, EDIKB, and KEL identifiers; deterministic gates decide whether the grounded knowledge is applicable. This hybrid RAG layer is a future improvement aimed at reducing natural-language interpretation loopholes without weakening engineering governance.

