# Paper 01A Claim and Evidence Register

**Manuscript:** PAPER_01A_MANUSCRIPT_DRAFT.md
**Register version:** 0.1
**Purpose:** distinguish publication-supported statements, repository-demonstrated behavior, author assertions, and planned work before engrXiv release.

## Evidence Classes

| Class | Meaning |
|---|---|
| Literature-supported | The cited publication supports the statement within its stated scope |
| Repository-demonstrated | Current schemas, code, records, reports, or tests demonstrate the software behavior |
| Domain-expert assertion | Requires confirmation and ownership by the paper authors |
| Future work | Proposed activity or capability that is not presented as implemented |

## Claim Register

| ID | Section | Claim or claim family | Evidence | Class | Draft status | Release action |
|---|---|---|---|---|---|---|
| A01 | 1-2 | An S-lay ILT is an interacting assembly whose stiffness, elevation, contact, mass, and connections influence overbend behavior | R7 [7]; R8 [8] | Literature-supported | Supported at paper level | Confirm wording against final figures and cited sections |
| A02 | 2.1 | Physical IW/EA and mechanical Type A/B/C classifications | R7 Table I, Table II, Figures 14-16 | Literature-supported | Checked | Add exact manuscript page/section references during typesetting |
| A03 | 2.2 | GD-ST and GD-SB differ in location, contact, and load-transfer role | R8 Figures 1-5 and component discussion | Literature-supported | Checked | Redraw rights-cleared Figure 2 |
| A04 | 2.3 | F/P/S/D connector primitives and F1/F2/F1D/F2D/PS/PSD systems | R8 Figure 16, Table VI, Figures 17-18 | Literature-supported | Checked | Verify symbol rendering in final figure |
| A05 | 2.3 | GD-ST, GD-SB, Z-branch, and L-branch parameters are part of the schematic representation | R8 Figures 22-25 and Table VIII | Literature-supported | Checked | Map publication notation to canonical repository fields |
| A06 | 3.4, 9.1 | Quantitative evidence is bounded by geometry, topology, model, response, and study limitations | R7 Discussion/Limitations; R8 Sections VI, XI-XIII | Literature-supported | Checked | Retain limitations beside any later numeric result |
| A07 | 4.1 | Product and assembly information benefit from explicit hierarchy and associations | R2 [2]; R3 [3] | Literature-supported | Paper-level support | Verify final paraphrase after citation review |
| A08 | 4.2 | P-map represents requirements, functions, artifacts, behaviors, issues, and links | R1 [1]; R4 [4] | Literature-supported | Paper-level support | Check terminology against final source notes |
| A09 | 4.2 | Solver-independent APF motivates structured objectives and constraints | R6 [6] | Literature-supported | Paper-level support | Keep distinction from repository implementation explicit |
| A10 | 4.4, 6.6 | Human feedback can be captured and supervised through an LLM/KG loop | R5 [5]; repository KEL records | Literature-supported and repository-demonstrated | Qualified | Treat KEL graph evolution as a repository contribution; use R5 only for the broader expert-supervision precedent |
| A11 | 4.1 | EDES, EDAS, EDIKB, and EDPR have separate ownership boundaries | docs/ONTOLOGY_CROSSWALK.md; schemas; framework_manifest.json | Repository-demonstrated | Checked | Freeze repository release |
| A12 | 5 | Plotting and validation are deterministic repository operations | plotters/; tools/plot_design.py; tools/solution_to_layout.py; tests | Repository-demonstrated | Checked | Archive representative reports and plots |
| A13 | 6.3-6.4 | The incomplete 12-inch valve request must emit missing-input/evidence blockers | tools/design_rules_v02.py; EDPR_VALVE_12IN_80PCT_INCOMPLETE.json; KEL tests | Repository-demonstrated | Checked | Capture command and JSON output in evidence package |
| A14 | 6.4 | Moment utilization uses demand divided by capacity ratio times pipeline allowable basis | tools/design_rules_v02.py | Repository-demonstrated arithmetic | Checked | Authors confirm engineering notation and allowable definition |
| A15 | 6.5 | Every GD-B branch requires a declared GD-ST terminal association for L-horizontal and Z-vertical layouts; vertical intent additionally restricts output to GD-B Z and ILT-Z anchors | tools/design_rules_v02.py; plotters/ils_builder.py; EDPR_Q1_VERTICAL_CONNECTOR.json; KEL tests | Repository-demonstrated | Checked | Archive L, Z, missing-frame, and missing-association regression outputs |
| A16 | 6.6 | KEL decomposes, groups, fingerprints, reviews, implements, promotes, and reconciles records | knowledge/kel/; tools/kel/; tests/kel/ | Repository-demonstrated | Checked | Add lifecycle diagram and archived sample |
| A17 | 6.6-7.2 | Current KEL status has zero invalid JSON and zero authoritative conflicts, with one implemented and eleven pending changes | tools/kel/summarize_kel_status.py output on 2026-09-14 | Repository-demonstrated | Checked | Save status output in frozen evidence package |
| A18 | 7.2 | 24 KEL tests and 29 plotter/solver tests pass | pytest and unittest runs on 2026-09-14 | Repository-demonstrated | Checked | Re-run on submission tag and store logs |
| A19 | 6.2 | Increased GD-SB/shroud vertical offset can increase strain within the R7 Type B1 study domain | R7 Section IX and associated result tables/figures | Literature-supported | Provisional | Add exact case/table, parameter range, response location, and limitation before release |
| A20 | 7.3 | The governed representation improves visibility of requirements, unknowns, parameters, associations, and gaps in the worked case | Before/after artifact package | Repository-demonstrated case analysis | Partially supported | Curate the original output and final machine-readable reports |
| A21 | 7.4 | Comparative superiority over unguided or retrieval-only LLMs | Planned controlled evaluation | Future work | Not claimed as a result | Execute protocol before adding performance conclusions |
| A22 | 9.3 | Parametric FEA, surrogate modeling, uncertainty, and active study selection can extend evidence coverage | Proposed roadmap | Future work | Clearly labelled | Add supporting literature before release |
| A23 | 8 | Recommended organizational ownership and staged adoption model | Authors' proposed practice | Domain-expert assertion | Draft | Authors review for compatibility with intended industrial setting |
| A24 | 9.2 | Applicable code-compliance statements | Project codes not yet registered | Domain-expert assertion / missing source | Withheld | Supply intended code editions before adding compliance claims |

## Quantitative Evidence Rule

Before any EDIKB number enters the manuscript, caption, or table, record:

1. publication ID;
2. source family;
3. table or figure;
4. case ID;
5. input and parameter range;
6. response quantity and location;
7. modeling limitation;
8. reason the evidence applies to the new problem.

Publication-level provenance alone is insufficient.

## Draft Review Priorities

1. Authors confirm domain terminology and the valve-case interpretation.
2. Build the R7/R8 row-level evidence matrix for every quantitative statement retained.
3. Curate reproducible before/after case artifacts.
4. Complete the controlled evaluation before changing preliminary observations into performance claims.
5. Add missing canonical literature and applicable code references.
