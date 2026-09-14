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
| 6 | Q1 case study failure and correction path | Use Q1 feedback and KEL v0.2 records | Corrected/fail-closed outputs are ready; initial before artifact still needs curation |
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
| `knowledge/kel/KEL_V0_2_IMPLEMENTATION_PLAN.md` | Scope, ordering, completion state, and current Step 5 representation-gap boundary. |
| `knowledge/kel/KEL_V0_2_DESIGN_GATES.md` | Authoritative description of implemented connector, EA-ST, valve-protection, and topology gates. |
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
| Workflow correction | Repository code/tests at `c3157c6`: vertical connector selects `ILT-Z-FT-PS`; EA-ST exposure is reported; unsupported valve protection and unresolved two-valve topology fail closed. |
| Final representative output | Use the Q1 vertical-connector emitted layout/plot and the 12-inch valve `VALVE_PROTECTION_INPUTS_MISSING` report as paired successful and fail-closed artifacts. |

## Supplied Literature Coverage

| Area | Registered source | Status and use |
|---|---|---|
| P-map/problem formulation | R1 and R4 | Supplied. Use for representation and ontology-annotation limitations. |
| OAM / assembly ontology | R2 and R3 | Supplied. Use for object, hierarchy, association, and product-information claims. |
| Human-in-the-loop KG design | R5 | Supplied. Use as the KnowLoop comparison and expert-supervision precedent. |
| APF for high-cost simulation design | R6 | Supplied. Use for requirement-to-formulation context; distinguish its solver-independent evaluation from this repository's P-map/APF implementation. |
| EDIKB Paper 1 | R7 | Supplied primary source for IW/EA, Type A/B/C, and isolated-component behavior. |
| EDIKB Paper 2 | R8 | Supplied primary source for EA-ST, EA-SB, connection systems, branch assemblies, and mass-position behavior. |
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

The synchronized implementation baseline is commit `c3157c6` (2026-09-14):

- 23 KEL tests passed;
- 29 plotter/solver tests passed;
- 40 KEL instance documents and 10 KEL schemas validated;
- all four repository EDPR examples validated;
- the lifecycle status report found zero authoritative conflicts.

Generated files under `runs/` are reproducible local artifacts and should be
curated into a publication evidence package before citation or release.
