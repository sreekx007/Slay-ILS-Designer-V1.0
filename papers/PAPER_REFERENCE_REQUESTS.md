# Reference and Source Material Status

## Supplied and Registered

Eight papers have been reviewed and registered in `REFERENCE_LIBRARY.md`. The set now covers P-map problem formulation, OAM/CPM product and assembly models, ontology-development challenges, human-in-the-loop LLM/KG conceptual design, solver-independent APF, and the two domain papers underlying EDIKB.

The two author-supplied subsea papers are primary domain evidence:

1. R7 is the source anchor for the EDIKB Paper 1 inline-behavior family, including the IW/EA and Type A/B/C classifications and isolated component trends.
2. R8 is the source anchor for the EDIKB Paper 2 families covering EA-ST, EA-SB, connector arrangements, branch assemblies, and mass-position behavior.

Their machine-readable mapping is in `EDIKB_SOURCE_PROVENANCE.json`. The PDFs remain outside the repository; the registry records filenames and SHA-256 checksums for exact-copy identification.

## Still Needed Before a Citation-Ready Preprint

| Priority | Reference type | Why it remains necessary |
|---|---|---|
| 1 | Original or accepted FBS design-theory papers | R5 uses FBS, but the manuscript should cite the original theoretical basis directly. |
| 1 | Applicable subsea pipeline and installation design codes | Needed for code-capacity, allowable, and formal design-compliance claims. |
| 2 | Engineering knowledge-graph survey and applied design-KG papers | Needed to position EDES/EDAS/EDIKB against the broader field. |
| 2 | Foundational RAG and tool-using LLM papers | Needed for retrieval and deterministic-tool orchestration claims. |
| 2 | Active learning, FEA surrogate modeling, and uncertainty references | Needed for the proposed ML and parametric-study expansion. |
| 3 | Engineering knowledge-management and lessons-learned papers | Useful for the industrial AI4D framing and organizational-learning claims. |

## Citation Use

| Citation group | Registered anchors | Paper role |
|---|---|---|
| Design theory and formulation | R1, R4, R6 | P-map, ontology annotation, and APF problem formulation. |
| Product and assembly ontology | R2, R3 | OAM/CPM objects, associations, hierarchy, and lifecycle information. |
| Human-in-the-loop AI design | R5 | LLM/KG design precedent and expert-supervision comparison. |
| Domain evidence | R7, R8 | EDIKB classifications, S-lay strain behavior, structures, connections, and branch-layout evidence. |

## Evidence Discipline

Repository behavior can demonstrate the implemented workflow, while literature supports theory and domain claims. Each final manuscript statement should be labeled during drafting as repo-demonstrated, literature-supported, domain-expert assertion, or future work. Quantitative EDIKB statements require claim-level traceability beyond a bibliography entry.
