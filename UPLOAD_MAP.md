# Manual Upload Map

Updated: 2026-09-11
Repository: sreekx007/Slay-ILS-Designer-V1.0
Target branch: main
Latest GitHub review: 2026-09-11
Remote commit reviewed: `20e1c07abe98bb42881d03e205fcec86b5275575`

The fetched `origin/main` is unchanged from the previous review. It contains
Phase 1 packaging, Phase 2, and the archived manifests. These local files still
match GitHub and need no upload: `.gitignore`, `plotters/slay_config.yaml`,
both original layout examples, `tools/plot_component.py`,
`tools/plot_design.py`, and the four versioned manifests under `superseded/`.

## Consolidated pending upload

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

## Pending: Phase 3 and documentation cleanup

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

Phase 3 remote commit: pending. No Phase 3 changes have been pushed by the assistant.


## Pending: Phase 4 basic plot QA

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

Phase 4 remote commit: pending. Generated `runs/` outputs remain local.

Phase 4 verification: 14 plotter tests passed. Component and ILT sample exports
completed without errors; ILT retained its existing builder warning.


## Pending: Phase 5 rendered layout correction

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
Keep runs/phase5 local. No Phase 5 changes have been pushed.


## Pending: Phase 6 coaxial Boss and component coverage

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
Upload the latest local copies where lists overlap. Phase 6 remote commit: pending.


## Phase 7: pending manual upload

Upload to identical relative paths; no new deletions.

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
