# Papers Workspace

This folder contains the Paper 01A working manuscript, preprint planning material, evidence controls, and the reviewed reference registry. The manuscript is a technical-review draft and is not yet submission-ready.

Current status: the papers folder now treats the manuscripts as framework drafts. Validated example results, comparative evaluation, and publication-ready case evidence are deferred until the design workflow is stable and controlled examples have been reviewed.

Both manuscripts use `GD-ST` and `GD-SB` after an opening note maps the source papers' `EA-ST`/`EA-SB` notation to the repository identifiers. The mapping changes terminology only. The generalized assembly gate requires every `GD-B` branch to terminate at `GD-ST` through a declared association; this applies to L-horizontal and Z-vertical branch terminals.

## Current Draft Set

| File | Purpose |
|---|---|
| `PAPER_01A_AI4D_KG_CASE_STUDY_OUTLINE.md` | User-directed Paper 1 outline: AI4D as data management, smart querying, ontology-grounded graph building, and KEL-governed industrial structural design practice. |
| `PAPER_01B_INDEPENDENT_FRAMEWORK_OUTLINE.md` | Alternative Paper 1 outline from an independent framing: governed neuro-symbolic design assistant for subsea inline structures. |
| `PAPER_01_FIGURES_TABLES_AND_EVIDENCE_PLAN.md` | Shared plan for figures, tables, evidence, and repository artifacts needed by either version. |
| `PAPER_01A_DRAFTING_ACTION_PLAN.md` | engrXiv-oriented drafting plan for engineering professionals without assumed AI/ML expertise. |
| `PAPER_01B_DRAFTING_ACTION_PLAN.md` | arXiv-oriented research plan for AI specialists who need the mechanical/structural domain explained. |
| `PAPER_01_SHARED_ONTOLOGY_FIGURE_PLAN.md` | Shared realistic-to-schematic-to-ontology storyboard, source-paper placeholder map, and figure production method. |
| `PAPER_01A_MANUSCRIPT_DRAFT.md` | Complete Paper 01A working manuscript for engineering-professional review and planned engrXiv submission. |
| `PAPER_01B_MANUSCRIPT_DRAFT.md` | Complete Paper 01B working manuscript for AI-research review and planned arXiv submission. |
| `PAPER_01A_CLAIM_EVIDENCE_REGISTER.md` | Claim classification, evidence source, draft status, and release action for Paper 01A. |
| `PAPER_REFERENCE_REQUESTS.md` | Status of supplied references and the literature still needed before a citation-ready preprint. |
| `REFERENCE_LIBRARY.md` | Citation-ready registry for the eight supplied papers, with checksums and manuscript roles. |
| `EDIKB_SOURCE_PROVENANCE.json` | Machine-readable mapping from the two author papers to the EDIKB Paper 1 and Paper 2 source families. |

## Recommended Next Step

Review `PAPER_01A_MANUSCRIPT_DRAFT.md` for domain terminology and authorship metadata. Then complete the R7/R8 row-level evidence matrix, final ontology/workflow figures, and a controlled example protocol before adding any results section. Paper 01B remains a separate AI-research manuscript.

## Source-Paper Handling

The reviewed PDFs remain outside the Git repository. `REFERENCE_LIBRARY.md` records their source filenames and SHA-256 checksums, while `EDIKB_SOURCE_PROVENANCE.json` records the two author-paper mappings. This keeps citation and evidence provenance in Git without redistributing third-party PDFs.

## Manuscripts and Preliminary Figures

- PAPER_01A_MANUSCRIPT_DRAFT.md - engineering-professional draft with explanatory workflow figures.
- PAPER_01B_MANUSCRIPT_DRAFT.md - AI-research draft with formal architecture and planned benchmark design.
- figures/generate_preliminary_figures.py - reproducible generator for workflow and component-ontology diagrams.
- figures/generate_repository_schematic.py - reproducible ILS-Plotter export with manuscript-scale fonts and a geometry-focused image; companion reports retain the complete design-workflow payload.
- figures/figure_sources.json - figure source and status register.
- figures/preliminary/shared_component_ontology_primer.svg - shared ten-component visual vocabulary used before the EDES/EDAS discussion.
- figures/preliminary/ - SVG and PNG previews plus the ILS-Plotter schematic and machine-readable reports.
