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
| 6 | Planned controlled example package | Use future frozen examples after workflow stabilization | Not ready; do not use current exploratory trials as evidence |
| 7 | Dataset sufficiency and parametric-study expansion | New diagram: historical design KG -> gap map -> FEA/parametric studies -> ML surrogate | Needs drafting |

## Recommended Tables

| Table | Title | Purpose |
|---|---|---|
| 1 | Framework layer responsibilities | Defines EDPR, EDES, EDAS, EDIKB, and KEL. |
| 2 | FBS-OAM mapping for subsea inline structures | Shows why assemblies, geometry, parameters, and connections must be graph nodes. |
| 3 | P-map/APF contribution beyond FBS | Clarifies why P-map/APF is a problem formulation gate. |
| 4 | Future example-to-KEL trace mapping | Demonstrates practical knowledge evolution after examples are reviewed. |
| 5 | Historical dataset insufficiency modes | Lists outliers, scaling gaps, missing fields, rare topologies, project-time sparsity. |
| 6 | Future ML roles | Maps ML to surrogate modeling, active learning, gap detection, uncertainty, and optimization. |

## Repository Evidence To Cite Internally

| Repo artifact | Paper use |
|---|---|
| `framework_manifest.json` | Framework classification, layer inventory, toolchain scope. |
| `README.md` | Current user-facing workflow and toolchain claims. |
| `docs/ONTOLOGY_CROSSWALK.md` | EDES/EDAS/EDIKB/EDPR boundaries and FBS-OAM split. |
| `docs/EDPR_PMAP_APF_IMPLEMENTATION.md` | P-map/APF explanation and parser workflow. |
| `knowledge/kel/README.md` | KEL purpose, graph-evolution scope, and governance lifecycle. |
| `knowledge/kel/KEL_ARCHITECTURE.md` | Traceability chain and toolchain list. |
| `tools/design_rules_v02.py` | Encoded rules for GD-B-to-GD-ST anchoring, connector orientation, GD-SB, and representation gaps. |
| `plotters/` | Evidence that geometry/plot output is tool-backed. |

## Future Controlled Example Evidence Package

To make the final example section publication-ready, collect:

| Evidence item | Needed content |
|---|---|
| Preselected user query | Exact wording frozen before execution. |
| Confirmed EDPR | Problem understanding reviewed and accepted before design generation. |
| Retrieval package | EDES, EDAS, EDIKB, and source evidence used for the run. |
| Workflow output | Layout JSON and plot/report, or typed blocker with missing information. |
| Human review | Independent review comments, scoring, and adjudicated decision. |
| KEL trace | Feedback records, grouped issues, graph-change requests, and implementation evidence if the example identifies a reusable lesson. |

## Supplied Literature Coverage

| Area | Registered source | Status and use |
|---|---|---|
| P-map/problem formulation | R1 and R4 | Supplied. Use for representation and ontology-annotation limitations. |
| OAM / assembly ontology | R2 and R3 | Supplied. Use for object, hierarchy, association, and product-information claims. |
| Human-in-the-loop KG design | R5 | Supplied. Use as a human-in-the-loop LLM/KG comparison and expert-supervision precedent. |
| APF for high-cost simulation design | R6 | Supplied. Use for requirement-to-formulation context; distinguish its solver-independent evaluation from this repository's P-map/APF implementation. |
| EDIKB Paper 1 | R7 | Supplied primary source for IW/EA, Type A/B/C, and isolated-component behavior. |
| EDIKB Paper 2 | R8 | Supplied primary source for EA-ST and EA-SB (normalized in the manuscripts to GD-ST and GD-SB), connection systems, branch assemblies, and mass-position behavior. |
| Original FBS theory | Not yet supplied | Still required before manuscript release. |
| Engineering KGs, RAG/tool use, and active learning/surrogates | Not yet supplied | Still required for related work and future-ML claims. |
| Applicable subsea design codes | Not yet supplied | Still required for code-compliance and allowable claims. |

### EDIKB Evidence Requirement

R7 and R8 establish publication-level provenance for the existing Paper 1 and Paper 2 EDIKB families. Before a quantitative figure, table, or claim is used in the preprint, add a claim-level link to the paper table/figure, case ID, parameter range, response location, and limitation. Do not cite a graph filename alone as evidence.

## Suggested Preprint Evidence Standard

Before release, every technical claim should be tagged as one of:

| Tag | Meaning |
|---|---|
| Repo-demonstrated | Directly demonstrated by current code, schema, record, or test. |
| Domain-expert assertion | Based on engineering expertise; should be clearly marked. |
| Literature-supported | Supported by cited papers. |
| Future work | Proposed but not yet implemented. |

This tagging will make the preprint stronger and safer. It will also help convert the paper into a job-application talking artifact because each claim has a defensible basis.

## Current Repository Verification Baseline

Do not present current repository test counts or exploratory run outputs as research-paper results. Software verification logs should be frozen later as supplementary development evidence after the controlled example protocol is finalized.
