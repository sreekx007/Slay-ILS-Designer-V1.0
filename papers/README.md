# Papers Workspace

This folder contains preprint planning material for the AI4D / Slay-ILS-Designer research papers. These files are outlines, evidence plans, and a reviewed reference registry; they are not yet citation-ready manuscripts.

Repository status at 2026-09-14: KEL v0.2 Steps 1 through 4 and Step 6 are implemented. Step 5 is deliberately represented as a machine-readable two-branch-valve topology gap pending expert review. The paper outlines below have been synchronized with that behavior.

## Current Draft Set

| File | Purpose |
|---|---|
| `PAPER_01A_AI4D_KG_CASE_STUDY_OUTLINE.md` | User-directed Paper 1 outline: AI4D as data management, smart querying, ontology-grounded graph building, and KEL-governed industrial structural design practice. |
| `PAPER_01B_INDEPENDENT_FRAMEWORK_OUTLINE.md` | Alternative Paper 1 outline from an independent framing: governed neuro-symbolic design assistant for subsea inline structures. |
| `PAPER_01_FIGURES_TABLES_AND_EVIDENCE_PLAN.md` | Shared plan for figures, tables, evidence, and repository artifacts needed by either version. |
| `PAPER_01A_DRAFTING_ACTION_PLAN.md` | engrXiv-oriented drafting plan for engineering professionals without assumed AI/ML expertise. |
| `PAPER_01B_DRAFTING_ACTION_PLAN.md` | arXiv-oriented research plan for AI specialists who need the mechanical/structural domain explained. |
| `PAPER_01_SHARED_ONTOLOGY_FIGURE_PLAN.md` | Shared realistic-to-schematic-to-ontology storyboard, source-paper placeholder map, and figure production method. |
| `PAPER_REFERENCE_REQUESTS.md` | Status of supplied references and the literature still needed before a citation-ready preprint. |
| `REFERENCE_LIBRARY.md` | Citation-ready registry for the eight supplied papers, with checksums and manuscript roles. |
| `EDIKB_SOURCE_PROVENANCE.json` | Machine-readable mapping from the two author papers to the EDIKB Paper 1 and Paper 2 source families. |

## Recommended Next Step

Execute `PAPER_01A_DRAFTING_ACTION_PLAN.md` and `PAPER_01B_DRAFTING_ACTION_PLAN.md` against the shared evidence base. Begin with the R7/R8 claim-to-evidence matrix and the realistic-to-schematic ontology storyboard in `PAPER_01_SHARED_ONTOLOGY_FIGURE_PLAN.md`. Keep the manuscripts separate: Paper 01A teaches engineering data management for engrXiv, while Paper 01B presents and evaluates the governed AI architecture for arXiv.

## Source-Paper Handling

The reviewed PDFs remain outside the Git repository. `REFERENCE_LIBRARY.md` records their source filenames and SHA-256 checksums, while `EDIKB_SOURCE_PROVENANCE.json` records the two author-paper mappings. This keeps citation and evidence provenance in Git without redistributing third-party PDFs.
