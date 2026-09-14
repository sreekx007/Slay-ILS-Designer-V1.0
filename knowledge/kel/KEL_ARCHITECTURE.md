# KEL Architecture

## Architectural Role

KEL is the experience and governance layer around the design assistant pipeline.

It captures how the framework performed, what evidence was available, where the knowledge was insufficient, and what changes should be reviewed by an expert.

## Main Modules

| Module | Responsibility |
|---|---|
| LLM workflow gate | Prevents direct free-form answering when EDPR/EDES/EDAS/EDIKB and plotter checks are required |
| Experience capture | Store the query, parse, retrieval trace, solution, plot, assumptions, ratings, and limitations |
| Feedback structuring | Convert querier comments into P-map/APF issue/action form |
| Atomic decomposition | Split compound comments at explicit feedback-item boundaries while retaining source spans |
| Grouping and de-duplication | Group exact or topic-equivalent issues and preserve all member/source IDs |
| Lifecycle reconciliation | Select one authoritative state per change-request ID and supersede stale copies |
| Sufficiency evaluation | Rate whether current knowledge was enough to answer the query |
| Change request generation | Propose updates to EDPR, EDES, EDAS, EDIKB, dataset, tools, plotters, or docs |
| Expert review | Accept, reject, revise, or request evidence |
| Promotion | Implement accepted updates and link them back to the originating experience |

## Tool Chain

```text
tools/kel/validate_kel_record.py
tools/kel/create_kel_experience_record.py
tools/kel/evaluate_kg_sufficiency.py
tools/kel/convert_feedback_to_pmap_apf.py
tools/kel/decompose_feedback.py
tools/kel/group_feedback.py
tools/kel/reconcile_lifecycle.py
tools/kel/generate_graph_change_request.py
tools/kel/create_expert_review_record.py
tools/kel/promote_accepted_kel_change.py
tools/kel/run_kel_cycle.py
```

Implemented KEL v0.1 and v0.2 Step 1 tools:

| Tool | Purpose |
|---|---|
| `tools/kel/validate_kel_record.py` | Validates KEL JSON records against schemas and policy checks |
| `tools/kel/create_kel_experience_record.py` | Creates a KEL experience record from EDPR, retrieval, solution, plot, and KnowLoop artifacts |
| `tools/kel/evaluate_kg_sufficiency.py` | Produces a structured KEL report on whether current EDPR/EDES/EDAS/EDIKB knowledge was sufficient |
| `tools/kel/convert_feedback_to_pmap_apf.py` | Converts querier feedback into structured P-map/APF issue/action form |
| `tools/kel/decompose_feedback.py` | Produces deterministic v0.2 atomic issues with source spans and fingerprints |
| `tools/kel/group_feedback.py` | Groups and de-duplicates atomic issues while preserving every source link |
| `tools/kel/reconcile_lifecycle.py` | Audits duplicate change-request IDs and moves stale copies to superseded |
| `tools/kel/generate_graph_change_request.py` | Converts KEL feedback records into pending expert-review graph change requests |
| `tools/kel/create_expert_review_record.py` | Creates draft or final expert review records linked to graph change requests |
| `tools/kel/promote_accepted_kel_change.py` | Promotes reviewed graph change requests into accepted or implemented lifecycle folders |
| `tools/kel/run_kel_cycle.py` | Runs the grouped KEL v0.2 flow by default; `--legacy-feedback-flow` retains the v0.1 path |

## Traceability Requirement

Every implemented framework update should be traceable back to:

```text
user query
EDPR/P-map/APF parse
retrieved context
solution artifact
plot artifact
querier feedback
atomic feedback IDs and source spans
feedback group and all member/source IDs
LLM self-rating
knowledge sufficiency rating
graph change request
expert review
implementation reference
```

## LLM-Facing Instruction Chain

`framework_manifest.json` is the discovery entry point. It tells the LLM which
layers and files exist, but it is not the complete operating prompt.

For design-query execution, the LLM-facing chain is:

```text
framework_manifest.json
-> knowledge/kel/KEL_LLM_WORKFLOW_INSTRUCTIONS.md
-> knowledge/edpr/EDPR_PARSER_PROMPT_RUNTIME.md
-> knowledge/edas/EDAS_SHARED_KNOWLEDGE.json
-> relevant EDES / EDAS / EDIKB files
-> plotters/README.md and plotter tools when a plot is requested
```

The Q1 ILT feedback established this as a required gate: the LLM must not
produce a freehand conceptual plot when a repository plotter and EDES/EDAS
geometry exist.
