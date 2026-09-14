# Paper 1 Figures, Tables, and Evidence Plan

## Purpose

This document lists the figures, tables, repository artifacts, and evidence needed to turn either Paper 1 outline into a preprint.

## Recommended Figures

| Figure | Title | Source / Build Method | Status |
|---|---|---|---|
| 1 | AI4D workflow for industrial structural design | Draw from EDPR -> EDES/EDAS/EDIKB -> tools -> KEL chain | Draft from repo docs |
| 2 | Knowledge layer separation | Use `docs/ONTOLOGY_CROSSWALK.md` layer definitions | Ready for diagram drafting |
| 3 | FBS-OAM mapping for ILS/ILT assemblies | New conceptual diagram: Function/Behavior/Structure plus OAM assembly features | Needs drafting |
| 4 | P-map/APF query decomposition | Use `docs/EDPR_PMAP_APF_IMPLEMENTATION.md` | Ready for diagram drafting |
| 5 | KEL feedback-to-graph-change lifecycle | Use `knowledge/kel/KEL_ARCHITECTURE.md` | Ready for diagram drafting |
| 6 | Q1 case study failure and correction path | Use Q1 feedback and KEL v0.2 records | Needs curated before/after artifacts |
| 7 | Dataset sufficiency and parametric-study expansion | New diagram: historical design KG -> gap map -> FEA/parametric studies -> ML surrogate | Needs drafting |

## Recommended Tables

| Table | Title | Purpose |
|---|---|---|
| 1 | Framework layer responsibilities | Defines EDPR, EDES, EDAS, EDIKB, Knowloop, KEL. |
| 2 | FBS-OAM mapping for subsea inline structures | Shows why assemblies, geometry, parameters, and connections must be graph nodes. |
| 3 | P-map/APF contribution beyond FBS | Clarifies why P-map/APF is a problem formulation gate. |
| 4 | Q1 failure-to-KEL update mapping | Demonstrates practical knowledge evolution. |
| 5 | Historical dataset insufficiency modes | Lists outliers, scaling gaps, missing fields, rare topologies, project-time sparsity. |
| 6 | Future ML roles | Maps ML to surrogate modeling, active learning, gap detection, uncertainty, and optimization. |

## Repository Evidence To Cite Internally

| Repo artifact | Paper use |
|---|---|
| `framework_manifest.json` | Framework classification, layer inventory, toolchain scope. |
| `README.md` | Current user-facing workflow and toolchain claims. |
| `docs/ONTOLOGY_CROSSWALK.md` | EDES/EDAS/EDIKB/EDPR boundaries and FBS-OAM split. |
| `docs/EDPR_PMAP_APF_IMPLEMENTATION.md` | P-map/APF explanation and parser workflow. |
| `knowledge/kel/README.md` | KEL purpose and position relative to Knowloop. |
| `knowledge/kel/KEL_ARCHITECTURE.md` | Traceability chain and toolchain list. |
| `knowledge/kel/KEL_V0_2_IMPLEMENTATION_PLAN.md` | Evidence of KEL v0.2 gates driven by Q1 feedback. |
| `tests/kel/` | Evidence that gates are testable, not only narrative. |
| `tools/design_rules_v02.py` | Encoded design-intent rules for vertical connector, EA-SB, and representation gaps. |
| `plotters/` | Evidence that geometry/plot output is tool-backed. |

## Q1 Case Study Evidence Package

To make the Q1 case study publication-ready, collect:

| Evidence item | Needed content |
|---|---|
| Original user query | Exact wording of Q1. |
| Initial assistant output | Text overview and plot that failed review, if acceptable to include. |
| Human feedback | The numbered feedback list from the review. |
| KEL records | Atomic feedback, grouped records, graph change requests, expert reviews, implementation plans. |
| Workflow correction | How v0.2 gates now handle vertical connector, EA-ST, EA-SB, plotter use, and two-valve gap. |
| Final representative output | A corrected or fail-closed workflow artifact from the repo. |

## Evidence Needed From Research Papers

The manuscript should not claim these areas without citations:

| Area | Citation need |
|---|---|
| FBS | Original or accepted FBS design-theory references. |
| OAM / assembly ontology | References defining object/assembly/feature/association modeling. |
| Knowledge graphs in engineering design | Engineering KG survey or applied design KG papers. |
| LLM + RAG + tools | Foundational RAG and tool-use references. |
| Human-in-the-loop KG evolution | KnowLoop paper and related human-review KG update work. |
| Active learning / surrogate modeling | Engineering design optimization and FEA surrogate references. |
| Subsea pipeline/ILS behavior | Domain papers supporting strain/stress behavior and ILS component trends. |

## Suggested Preprint Evidence Standard

Before release, every technical claim should be tagged as one of:

| Tag | Meaning |
|---|---|
| Repo-demonstrated | Directly demonstrated by current code, schema, record, or test. |
| Domain-expert assertion | Based on engineering expertise; should be clearly marked. |
| Literature-supported | Supported by cited papers. |
| Future work | Proposed but not yet implemented. |

This tagging will make the preprint stronger and safer. It will also help convert the paper into a job-application talking artifact because each claim has a defensible basis.
