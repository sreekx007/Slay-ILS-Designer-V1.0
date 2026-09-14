# Manual Upload Map

Updated: 2026-09-14
Repository: sreekx007/Slay-ILS-Designer-V1.0
Target branch: main
Latest GitHub review: 2026-09-13
Phase 1 and 2 baseline: `20e1c07abe98bb42881d03e205fcec86b5275575`
Phases 3 through 7 implementation: `4f0d3116f11fb6ba473a78a99d6e871dc5c64372`
Push-status record: `07f12357affa17d90458cbb2ee6311a62b780211`
Pending manual uploads: 0.

GitHub `main` contains KEL v0.1, Plotter Phases 1 through 7, and the KEL v0.2 release batch listed below. Generated `runs/` artifacts,
the local virtual environment, Python caches, staging files, and `.git/` remain
excluded.



## Paper 01A manuscript draft - confirmed

The engineering-professional manuscript draft and its claim/evidence register are included. The draft explains the S-lay ILT ontology, engineering data management, the EDES/EDAS/EDIKB/EDPR architecture, LLM/tool responsibilities, the valve-layout feedback case, KEL governance, preliminary repository verification, limitations, and the path to a controlled evaluation.

| Action | Repository path |
| --- | --- |
| Add | `papers/PAPER_01A_MANUSCRIPT_DRAFT.md` |
| Add | `papers/PAPER_01A_CLAIM_EVIDENCE_REGISTER.md` |
| Update | `papers/README.md` |
| Update | `framework_manifest.json` |
| Update | `UPLOAD_MAP.md` |

## Paper 01A and 01B drafting plans - confirmed

Audience-specific action plans and a shared ontology/figure storyboard are included. Paper 01A targets engineering professionals and engrXiv; Paper 01B targets AI researchers and arXiv. The shared figure plan maps temporary figures from the two author papers to final repository-backed redraws.

| Action | Repository path |
| --- | --- |
| Add | `papers/PAPER_01A_DRAFTING_ACTION_PLAN.md` |
| Add | `papers/PAPER_01B_DRAFTING_ACTION_PLAN.md` |
| Add | `papers/PAPER_01_SHARED_ONTOLOGY_FIGURE_PLAN.md` |
| Update | `papers/README.md` |
| Update | `framework_manifest.json` |
| Update | `UPLOAD_MAP.md` |

## Research reference registration - confirmed

The eight supplied publications are registered by citation, role, and source-file checksum. The two author papers are also mapped directly to the EDIKB Paper 1 and Paper 2 source families. Source PDFs remain outside Git; no paper binaries are uploaded.

| Action | Repository path |
| --- | --- |
| Update | `framework_manifest.json` |
| Update | `knowledge/edikb/EDIKB_FULL_KNOWLEDGE_GRAPH.json` |
| Update | `papers/README.md` |
| Update | `papers/PAPER_REFERENCE_REQUESTS.md` |
| Update | `papers/PAPER_01A_AI4D_KG_CASE_STUDY_OUTLINE.md` |
| Update | `papers/PAPER_01B_INDEPENDENT_FRAMEWORK_OUTLINE.md` |
| Update | `papers/PAPER_01_FIGURES_TABLES_AND_EVIDENCE_PLAN.md` |
| Add | `papers/REFERENCE_LIBRARY.md` |
| Add | `papers/EDIKB_SOURCE_PROVENANCE.json` |
| Update | `UPLOAD_MAP.md` |

## KEL v0.2 Steps 1 through 6 - release batch

| Action | Repository path |
| --- | --- |
| Update | `framework_manifest.json` |
| Update | `knowledge/edas/EDAS_SHARED_KNOWLEDGE.json` |
| Update | `knowledge/edpr/EDPR_APF_PARSER_PROMPT.md` |
| Update | `knowledge/edpr/EDPR_PARSER_PROMPT_RUNTIME.md` |
| Add | `knowledge/kel/atomic_feedback_records/candidates/KEL_V0_2_TWO_BRANCH_VALVE_REPRESENTATION_GAP.json` |
| Add | `knowledge/kel/atomic_feedback_records/candidates/README.md` |
| Add | `knowledge/kel/feedback_groups/candidates/KEL_V0_2_TWO_BRANCH_VALVE_REPRESENTATION_GAP.json` |
| Add | `knowledge/kel/feedback_groups/candidates/README.md` |
| Add | `knowledge/kel/graph_change_requests/pending/KEL_V0_2_GCR_TWO_BRANCH_VALVE_REPRESENTATION_GAP.json` |
| Delete | `knowledge/kel/graph_change_requests/pending/Q1_GCR_08_MUST_USE_REPO_PLOTTER.json` |
| Add | `knowledge/kel/graph_change_requests/superseded/Q1_GCR_08_MUST_USE_REPO_PLOTTER.json` |
| Add | `knowledge/kel/graph_change_requests/superseded/README.md` |
| Add | `knowledge/kel/implementation_plans/implemented/Q1_GCR_08_MUST_USE_REPO_PLOTTER.plan.json` |
| Add | `knowledge/kel/implementation_plans/implemented/README.md` |
| Update | `knowledge/kel/KEL_ARCHITECTURE.md` |
| Update | `knowledge/kel/KEL_TERMINOLOGY.md` |
| Add | `knowledge/kel/KEL_V0_2_DESIGN_GATES.md` |
| Add | `knowledge/kel/KEL_V0_2_IMPLEMENTATION_PLAN.md` |
| Update | `knowledge/kel/KEL_V0_2_RECOMMENDATIONS.md` |
| Update | `knowledge/kel/KEL_WORKFLOW.md` |
| Add | `knowledge/kel/lifecycle_reports/KEL_V0_2_STEP1_Q1_RECONCILIATION.json` |
| Add | `knowledge/kel/lifecycle_reports/README.md` |
| Update | `knowledge/kel/README.md` |
| Add | `knowledge/kel/schemas/KEL_ATOMIC_FEEDBACK_SCHEMA.json` |
| Add | `knowledge/kel/schemas/KEL_FEEDBACK_GROUP_SCHEMA.json` |
| Add | `knowledge/kel/schemas/KEL_GRAPH_CHANGE_REQUEST_V0_2_SCHEMA.json` |
| Add | `knowledge/kel/schemas/KEL_IMPLEMENTATION_PLAN_SCHEMA.json` |
| Add | `knowledge/kel/schemas/KEL_LIFECYCLE_RECONCILIATION_SCHEMA.json` |
| Add | `knowledge/kel/templates/KEL_ATOMIC_FEEDBACK_TEMPLATE.json` |
| Add | `knowledge/kel/templates/KEL_FEEDBACK_GROUP_TEMPLATE.json` |
| Add | `knowledge/kel/templates/KEL_GRAPH_CHANGE_REQUEST_V0_2_TEMPLATE.json` |
| Add | `knowledge/kel/templates/KEL_IMPLEMENTATION_PLAN_TEMPLATE.json` |
| Update | `plotters/ils_builder.py` |
| Update | `plotters/ils_plotter.py` |
| Update | `README.md` |
| Update | `schemas/EDPR_METASCHEMA.json` |
| Add | `tests/kel/fixtures/EDPR_Q1_VERTICAL_CONNECTOR.json` |
| Add | `tests/kel/fixtures/EDPR_VALVE_12IN_80PCT_INCOMPLETE.json` |
| Add | `tests/kel/fixtures/VALVE_EASB_COMPLETE_DESIGN.json` |
| Add | `tests/kel/fixtures/VALVE_EASB_COMPOUND_FEEDBACK.json` |
| Add | `tests/kel/test_design_workflow_v02.py` |
| Add | `tests/kel/test_feedback_v02.py` |
| Add | `tests/kel/test_release_tools_v02.py` |
| Update | `tests/kel/test_run_kel_cycle.py` |
| Update | `tools/_plot_cli.py` |
| Add | `tools/design_rules_v02.py` |
| Update | `tools/kel/create_expert_review_record.py` |
| Add | `tools/kel/create_implementation_plan.py` |
| Add | `tools/kel/decompose_feedback.py` |
| Add | `tools/kel/feedback_v02.py` |
| Update | `tools/kel/generate_graph_change_request.py` |
| Add | `tools/kel/group_feedback.py` |
| Add | `tools/kel/migrate_v01_to_v02.py` |
| Update | `tools/kel/promote_accepted_kel_change.py` |
| Add | `tools/kel/reconcile_lifecycle.py` |
| Update | `tools/kel/run_kel_cycle.py` |
| Add | `tools/kel/summarize_kel_status.py` |
| Update | `tools/kel/validate_kel_record.py` |
| Update | `tools/retrieve_context.py` |
| Update | `tools/solution_to_layout.py` |
| Update | `tools/solve_problem.py` |
| Update | `UPLOAD_MAP.md` |

This release batch implements atomic feedback grouping and lifecycle repair,
vertical-connector Z selection, the EA-ST complete-design exposure gate, the
EA-SB valve clarification/evidence gate with canonical GD-SB geometry, and the
implementation-plan, migration, and lifecycle status tools. The two-branch-valve
case is deliberately retained as a machine-readable representation gap pending
expert topology review. Generated `runs/`, `.venv/`, Python caches, staging
scripts, and `.git/` stay local.

## KEL v0.1 governance toolchain - confirmed

Source package commit: `7d1d380 Add KEL governance toolchain`
Source ZIP SHA-256: `e43dca776b696728d05f5ce174f8458194e0a76bd65fe9c610ddd1acd6123bad`
GitHub integration commit: `6d69db2134b830a54dc568245fa9819555df4a54`

The reviewed package contributes 73 mapped files. This integration also updates the root README and upload map, and adds the development requirements file. The manual upload set is 76 repository paths:

| Action | Repository path |
| --- | --- |
| Update | `framework_manifest.json` |
| Update | `README.md` |
| Add | `requirements-dev.txt` |
| Update | `UPLOAD_MAP.md` |
| Add | `knowledge/kel/examples/EXAMPLE_01_VALVE_DESIGN_KEL_RECORD.json` |
| Add | `knowledge/kel/examples/EXAMPLE_02_BRANCH_DESIGN_KEL_RECORD.json` |
| Add | `knowledge/kel/experience_records/accepted/README.md` |
| Add | `knowledge/kel/experience_records/candidates/README.md` |
| Add | `knowledge/kel/experience_records/implemented/README.md` |
| Add | `knowledge/kel/experience_records/rejected/README.md` |
| Add | `knowledge/kel/expert_reviews/draft/README.md` |
| Add | `knowledge/kel/expert_reviews/final/Q1_REVIEW_08_MUST_USE_REPO_PLOTTER.json` |
| Add | `knowledge/kel/expert_reviews/final/README.md` |
| Add | `knowledge/kel/feedback_records/accepted/README.md` |
| Add | `knowledge/kel/feedback_records/candidates/Q1_01_BRANCH_DIRECTION.json` |
| Add | `knowledge/kel/feedback_records/candidates/Q1_02_VALVE_EASB_DEFAULT.json` |
| Add | `knowledge/kel/feedback_records/candidates/Q1_03_BRANCH_CONNECTOR_EAST_DEFAULT.json` |
| Add | `knowledge/kel/feedback_records/candidates/Q1_04_PLOT_SCALE.json` |
| Add | `knowledge/kel/feedback_records/candidates/Q1_05_EAST_CONNECTIONS_LABELLED.json` |
| Add | `knowledge/kel/feedback_records/candidates/Q1_06_PIPING_CONNECTIONS_SCOPE.json` |
| Add | `knowledge/kel/feedback_records/candidates/Q1_07_STRESS_STRAIN_OBJECTIVE.json` |
| Add | `knowledge/kel/feedback_records/candidates/Q1_08_MUST_USE_REPO_PLOTTER.json` |
| Add | `knowledge/kel/feedback_records/candidates/Q1_09_Z_BRANCH_FOR_VERTICAL_CONNECTOR.json` |
| Add | `knowledge/kel/feedback_records/candidates/Q1_10_EASB_SHAPE_FROM_EDES.json` |
| Add | `knowledge/kel/feedback_records/candidates/Q1_11_EAST_PARAMETERS_CONNECTIONS.json` |
| Add | `knowledge/kel/feedback_records/candidates/README.md` |
| Add | `knowledge/kel/feedback_records/implemented/README.md` |
| Add | `knowledge/kel/feedback_records/rejected/README.md` |
| Add | `knowledge/kel/graph_change_requests/accepted/README.md` |
| Add | `knowledge/kel/graph_change_requests/implemented/Q1_GCR_08_MUST_USE_REPO_PLOTTER.json` |
| Add | `knowledge/kel/graph_change_requests/implemented/README.md` |
| Add | `knowledge/kel/graph_change_requests/pending/Q1_GCR_01_BRANCH_DIRECTION.json` |
| Add | `knowledge/kel/graph_change_requests/pending/Q1_GCR_02_VALVE_EASB_DEFAULT.json` |
| Add | `knowledge/kel/graph_change_requests/pending/Q1_GCR_03_BRANCH_CONNECTOR_EAST_DEFAULT.json` |
| Add | `knowledge/kel/graph_change_requests/pending/Q1_GCR_04_PLOT_SCALE.json` |
| Add | `knowledge/kel/graph_change_requests/pending/Q1_GCR_05_EAST_CONNECTIONS_LABELLED.json` |
| Add | `knowledge/kel/graph_change_requests/pending/Q1_GCR_06_PIPING_CONNECTIONS_SCOPE.json` |
| Add | `knowledge/kel/graph_change_requests/pending/Q1_GCR_07_STRESS_STRAIN_OBJECTIVE.json` |
| Add | `knowledge/kel/graph_change_requests/pending/Q1_GCR_08_MUST_USE_REPO_PLOTTER.json` |
| Add | `knowledge/kel/graph_change_requests/pending/Q1_GCR_09_Z_BRANCH_FOR_VERTICAL_CONNECTOR.json` |
| Add | `knowledge/kel/graph_change_requests/pending/Q1_GCR_10_EASB_SHAPE_FROM_EDES.json` |
| Add | `knowledge/kel/graph_change_requests/pending/Q1_GCR_11_EAST_PARAMETERS_CONNECTIONS.json` |
| Add | `knowledge/kel/graph_change_requests/pending/README.md` |
| Add | `knowledge/kel/graph_change_requests/rejected/README.md` |
| Add | `knowledge/kel/KEL_ARCHITECTURE.md` |
| Add | `knowledge/kel/KEL_LLM_WORKFLOW_INSTRUCTIONS.md` |
| Add | `knowledge/kel/KEL_TERMINOLOGY.md` |
| Add | `knowledge/kel/KEL_V0_2_RECOMMENDATIONS.md` |
| Add | `knowledge/kel/KEL_WORKFLOW.md` |
| Add | `knowledge/kel/README.md` |
| Add | `knowledge/kel/schemas/KEL_EXPERIENCE_RECORD_SCHEMA.json` |
| Add | `knowledge/kel/schemas/KEL_EXPERT_REVIEW_SCHEMA.json` |
| Add | `knowledge/kel/schemas/KEL_FEEDBACK_TO_PMAP_APF_SCHEMA.json` |
| Add | `knowledge/kel/schemas/KEL_GRAPH_CHANGE_REQUEST_SCHEMA.json` |
| Add | `knowledge/kel/schemas/KEL_KG_SUFFICIENCY_REPORT_SCHEMA.json` |
| Add | `knowledge/kel/templates/KEL_EXPERIENCE_RECORD_TEMPLATE.json` |
| Add | `knowledge/kel/templates/KEL_EXPERT_REVIEW_TEMPLATE.json` |
| Add | `knowledge/kel/templates/KEL_FEEDBACK_TO_PMAP_APF_TEMPLATE.json` |
| Add | `knowledge/kel/templates/KEL_GRAPH_CHANGE_REQUEST_TEMPLATE.json` |
| Add | `knowledge/kel/templates/KEL_KG_SUFFICIENCY_REPORT_TEMPLATE.json` |
| Add | `tests/kel/test_convert_feedback_to_pmap_apf.py` |
| Add | `tests/kel/test_create_expert_review_record.py` |
| Add | `tests/kel/test_create_kel_experience_record.py` |
| Add | `tests/kel/test_evaluate_kg_sufficiency.py` |
| Add | `tests/kel/test_generate_graph_change_request.py` |
| Add | `tests/kel/test_kel_examples_validate.py` |
| Add | `tests/kel/test_promote_accepted_kel_change.py` |
| Add | `tests/kel/test_run_kel_cycle.py` |
| Add | `tools/kel/convert_feedback_to_pmap_apf.py` |
| Add | `tools/kel/create_expert_review_record.py` |
| Add | `tools/kel/create_kel_experience_record.py` |
| Add | `tools/kel/evaluate_kg_sufficiency.py` |
| Add | `tools/kel/generate_graph_change_request.py` |
| Add | `tools/kel/promote_accepted_kel_change.py` |
| Add | `tools/kel/run_kel_cycle.py` |
| Add | `tools/kel/validate_kel_record.py` |

No deletions are required. Exclude the source ZIP, `.venv/`, `runs/`, Python caches, staging folders, and `.git/`.

## Consolidated Phase 3 through 7 upload  - confirmed

This combines Phases 3 through 7 so each path appears once.

| Action | Repository path |
| --- | --- |
| Update | `README.md` |
| Update | `UPLOAD_MAP.md` |
| Update | `framework_manifest.json` |
| Update | `knowledge/edas/EDAS_SHARED_KNOWLEDGE.json` |
| Update | `knowledge/edes/EDES_GD-BOSS_KNOWLEDGE.json` |
| Update | `plotters/README.md` |
| Update | `plotters/component_plotter.py` |
| Update | `plotters/component_spec.py` |
| Update | `plotters/ils_builder.py` |
| Update | `plotters/ils_plotter.py` |
| Update | `plotters/requirements.txt` |
| Update | `tools/_plot_cli.py` |
| Update | `tools/generate_knowloop_candidate.py` |
| Update | `tools/run_edpr_pipeline.py` |
| Update | `tools/test_plot_cli.py` |
| Add | `docs/PHASE7_SOLVER_PLOTTING.md` |
| Add | `plotters/_plot_defaults.py` |
| Add | `plotters/checkers/label_overlap_checker.py` |
| Add | `plotters/checkers/plot_checker.py` |
| Add | `plotters/config/component_catalog.json` |
| Add | `plotters/config/plot_style.yaml` |
| Add | `plotters/examples/example_boss_layout.json` |
| Add | `plotters/examples/example_edpr_ilt_layout.json` |
| Add | `plotters/plot_settings.py` |
| Add | `tools/solution_to_layout.py` |
| Add | `tools/test_plot_checker.py` |
| Add | `tools/test_plot_components.py` |
| Add | `tools/test_plot_labels.py` |
| Add | `tools/test_plot_settings.py` |
| Add | `tools/test_plot_solver.py` |

No repository deletions are pending. Exclude `.venv/`, `runs/`, Python
cache directories, and the local `.git/` directory.


## Confirmed on GitHub

Phase 1 packaging, Phase 2 CLIs/examples/tests, and manifest archival were verified
at commit `20e1c07abe98bb42881d03e205fcec86b5275575`. All those files matched the local versions
at review time. Claude's expanded root README is included in that remote commit.
The four old versioned manifests are under superseded/; the obsolete YAML filename
and placeholder were removed. These earlier batches are no longer pending.

## Phase 3 and documentation cleanup  - confirmed

All paths are relative to the repository root. Upload the latest local versions.

| Action | Path |
| --- | --- |
| Add | `plotters/config/plot_style.yaml` |
| Add | `plotters/config/component_catalog.json` |
| Add | `plotters/plot_settings.py` |
| Add | `plotters/_plot_defaults.py` |
| Add | `tools/test_plot_settings.py` |
| Update | `plotters/component_plotter.py` |
| Update | `plotters/ils_plotter.py` |
| Update | `tools/_plot_cli.py` |
| Update | `plotters/README.md` |
| Update | `README.md` |
| Update | `framework_manifest.json` |
| Update | `UPLOAD_MAP.md` |

No remote deletions are needed for this batch. The root README preserves Claude's
overview with corrected paths, validator guidance, and plotting instructions.
Geometry model and builder files are unchanged.

Keep `.venv/`, `runs/`, Python caches, and `.git/` local. Uploads through GitHub's
web interface must preserve the folders above. Do not upload an entire environment.

Phase 3 verification: default component and ILT images are pixel-identical to
fresh Phase 2 baselines. Configuration and CLI tests are recorded in the active
manifest. Basic QA is added in Phase 4 below; existing label overlaps remain deferred.

Phase 3 was pushed in commit `4f0d3116f11fb6ba473a78a99d6e871dc5c64372`.


## Phase 4 basic plot QA  - confirmed

| Action | Path |
| --- | --- |
| Add | `plotters/checkers/plot_checker.py` |
| Add | `tools/test_plot_checker.py` |
| Update | `tools/_plot_cli.py` |
| Update | `tools/test_plot_cli.py` |
| Update | `plotters/README.md` |
| Update | `README.md` |
| Update | `framework_manifest.json` |
| Update | `UPLOAD_MAP.md` |

Upload the latest version of files shared with the Phase 3 list. No deletions
are required. The checker reports basic export/content/bounds/clipping/scale
results and does not change geometry. Label/legend corrections remain Phase 5.
SVG/PDF blank-export checks are not independently rasterized; the live figure
is checked and the vector limits are stated in each report.

Phase 4 was pushed in commit `4f0d3116f11fb6ba473a78a99d6e871dc5c64372`.
Generated `runs/` outputs remain local.

Phase 4 verification: 14 plotter tests passed. Component and ILT sample exports
completed without errors; ILT retained its existing builder warning.


## Phase 5 rendered layout correction  - confirmed

| Action | Repository path |
| --- | --- |
| Add | plotters/checkers/label_overlap_checker.py |
| Add | tools/test_plot_labels.py |
| Update | plotters/checkers/plot_checker.py |
| Update | tools/_plot_cli.py |
| Update | plotters/README.md |
| Update | README.md |
| Update | framework_manifest.json |
| Update | UPLOAD_MAP.md |

Upload the latest local versions shared with earlier batches. No deletions.
The explicit ILT example now exports with leader labels and wrapped title/table,
and records before/after corrections and remaining issues. All 18 plotter tests passed after the final whitespace diagnostic; git diff
whitespace checks also passed.
Keep runs/phase5 local. Phase 5 was pushed in commit `4f0d3116f11fb6ba473a78a99d6e871dc5c64372`.


## Phase 6 coaxial Boss and component coverage  - confirmed

| Action | Repository path |
| --- | --- |
| Update | plotters/component_spec.py |
| Update | plotters/ils_builder.py |
| Update | plotters/component_plotter.py |
| Update | plotters/ils_plotter.py |
| Update | plotters/config/component_catalog.json |
| Update | plotters/config/plot_style.yaml |
| Update | plotters/_plot_defaults.py |
| Add | plotters/examples/example_boss_layout.json |
| Add | tools/test_plot_components.py |
| Update | tools/test_plot_settings.py |
| Update | knowledge/edes/EDES_GD-BOSS_KNOWLEDGE.json |
| Update | knowledge/edas/EDAS_SHARED_KNOWLEDGE.json |
| Update | plotters/README.md |
| Update | framework_manifest.json |
| Update | UPLOAD_MAP.md |

Boss follows the user's 11 Sep clarification: a coaxial sleeve with bore larger
than the enclosed thick section OD; header material remains intact. Optional
source_pip resolves matching outer dimensions without pinning omitted fields.
Sleeve steel is counted separately in mass and CoG. Actual sleeve attachment is
not invented and remains a warning. GD-BrPipe and GD-B stay distinct.

Verification: 24 plotter tests passed, including all 12 component and assembly
renders, bore rejection, short thick-section coverage, source matching,
round-trip omissions and mass/header preservation. Generated Boss PNG inspected.
No remote deletions. Keep runs/phase6 and temporary run scripts local.
Phase 6 was pushed in commit `4f0d3116f11fb6ba473a78a99d6e871dc5c64372`.


## Phase 7  - confirmed

These paths were pushed in commit `4f0d3116f11fb6ba473a78a99d6e871dc5c64372`.
No new deletions were required.

- tools/solution_to_layout.py
- tools/run_edpr_pipeline.py
- tools/generate_knowloop_candidate.py
- tools/test_plot_solver.py
- plotters/examples/example_edpr_ilt_layout.json
- plotters/requirements.txt
- docs/PHASE7_SOLVER_PLOTTING.md
- README.md
- plotters/README.md
- framework_manifest.json
- UPLOAD_MAP.md

Exclude runs/phase7 and .venv. Old manifests remain in superseded. 29 distinct tests passed, including EDPR-to-plot and Knowloop schema validation.

## Paper 01B and preliminary figures - confirmed

Added the Paper 01B manuscript and reproducible preliminary SVG/PNG figures. Paper 01A now embeds an engineering workflow, ILT abstraction ladder, KEL lifecycle and repository-generated ILT schematic. Updated papers/README.md, framework_manifest.json and UPLOAD_MAP.md.

## Paper component ontology primer

| Action | Repository path |
| --- | --- |
| Update | `papers/PAPER_01A_MANUSCRIPT_DRAFT.md` |
| Update | `papers/PAPER_01B_MANUSCRIPT_DRAFT.md` |
| Update | `papers/README.md` |
| Update | `papers/figures/generate_preliminary_figures.py` |
| Add | `papers/figures/generate_repository_schematic.py` |
| Update | `papers/figures/figure_sources.json` |
| Add | `papers/figures/preliminary/shared_component_ontology_primer.svg` |
| Add | `papers/figures/preliminary/shared_component_ontology_primer.png` |
| Update | `papers/figures/preliminary/shared_repository_ilt_schematic.svg` |
| Update | `papers/figures/preliminary/shared_repository_ilt_schematic.png` |
| Update | `papers/figures/preliminary/shared_repository_ilt_schematic.svg.report.json` |
| Update | `papers/figures/preliminary/shared_repository_ilt_schematic.png.report.json` |
| Update | `framework_manifest.json` |
| Update | `UPLOAD_MAP.md` |

Both papers now introduce the ten established GD component classes used in these manuscripts before using them in EDES/EDAS reasoning. The shared preliminary figure distinguishes pipe parts, thick-section representations, inline equipment, branch assemblies, external structures, contact envelopes and connector behavior. The repository-generated schematic now uses manuscript-scale fonts and a geometry-focused image while retaining the complete design-workflow payload in its companion reports. No source-paper PDFs are added to Git.

## Generalized branch anchoring and paper notation

| Action | Repository path |
| --- | --- |
| Update | `tools/design_rules_v02.py` |
| Update | `plotters/ils_builder.py` |
| Update | `tests/kel/test_design_workflow_v02.py` |
| Update | `knowledge/edas/EDAS_SHARED_KNOWLEDGE.json` |
| Update | `knowledge/kel/KEL_V0_2_DESIGN_GATES.md` |
| Update | `knowledge/kel/KEL_V0_2_IMPLEMENTATION_PLAN.md` |
| Update | `knowledge/kel/KEL_V0_2_RECOMMENDATIONS.md` |
| Update | `README.md` |
| Update | `framework_manifest.json` |
| Update | `papers/PAPER_01A_MANUSCRIPT_DRAFT.md` |
| Update | `papers/PAPER_01B_MANUSCRIPT_DRAFT.md` |
| Update | `papers/PAPER_01A_DRAFTING_ACTION_PLAN.md` |
| Update | `papers/PAPER_01B_DRAFTING_ACTION_PLAN.md` |
| Update | `papers/PAPER_01A_AI4D_KG_CASE_STUDY_OUTLINE.md` |
| Update | `papers/PAPER_01B_INDEPENDENT_FRAMEWORK_OUTLINE.md` |
| Update | `papers/PAPER_01_FIGURES_TABLES_AND_EVIDENCE_PLAN.md` |
| Update | `papers/PAPER_01_SHARED_ONTOLOGY_FIGURE_PLAN.md` |
| Update | `papers/PAPER_01A_CLAIM_EVIDENCE_REGISTER.md` |
| Update | `papers/PAPER_REFERENCE_REQUESTS.md` |
| Update | `papers/REFERENCE_LIBRARY.md` |
| Update | `papers/EDIKB_SOURCE_PROVENANCE.json` |
| Update | `papers/README.md` |
| Update | `papers/figures/preliminary/shared_repository_ilt_schematic.svg.report.json` |
| Update | `papers/figures/preliminary/shared_repository_ilt_schematic.png.report.json` |
| Update | `UPLOAD_MAP.md` |

The core gate is implemented in commit `31a57d378a70f4aa8f232ed8a50130f85b3bfbea`. Every `GD-B` branch in an emitted ILS now requires `GD-ST` and a declared terminal association. The regression covers an L branch with a horizontal terminal, a Z branch with a vertical terminal, a missing association, and a missing top frame. A branch-only component study may remain `study_only` but cannot claim a complete ILS layout.

Both manuscripts now use `GD-ST` and `GD-SB` consistently after an opening note maps the source papers' `EA-ST` and `EA-SB` notation. The mapping is terminological and does not change the source concepts or evidence meaning. Validation baseline: 24 KEL tests and 29 plotter/solver tests pass.

## Paper 01A case 02 Option 2 KEL feedback - local candidate records

| Action | Repository path |
| --- | --- |
| Add | `knowledge/kel/experience_records/candidates/PAPER01A_CASE02_OPTION2.json` |
| Add | `knowledge/kel/feedback_records/candidates/Q2_01_EDPR_CONFIRMATION_BEFORE_DESIGN.json` |
| Add | `knowledge/kel/feedback_records/candidates/Q2_02_HEADER_VALVE_REQUIRES_GD_SB.json` |
| Add | `knowledge/kel/feedback_records/candidates/Q2_03_CONNECTION_LABELS_LEGIBLE.json` |
| Add | `knowledge/kel/feedback_records/candidates/Q2_04_DEFAULT_STRAIN_MOMENT_REDUCTION.json` |
| Update | `UPLOAD_MAP.md` |

The four records preserve the user's wording and link it to one querier-reviewed experience record. Structured fields use the current manuscript notation `GD-SB` and `GD-ST`; the raw feedback retains `GS-SB` and `EA-ST`. They remain KEL candidates and do not modify authoritative EDAS, EDPR, plotter, or graph rules until grouping and expert review.
