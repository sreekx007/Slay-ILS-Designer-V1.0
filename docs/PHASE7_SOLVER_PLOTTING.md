# Phase 7: Solver plotting

Install plotters/requirements.txt, then run from repository root:

    python tools/run_edpr_pipeline.py --edpr-json knowledge/edpr/examples/EDPR_EXAMPLE_ILT_L_BRANCH_MIN_STRAIN.json --output-dir runs/phase7 --solution-format json --plot

Outputs: retrieval context, solution, layout, layout report, PNG, plot QA and Knowloop candidate. Markdown mode also produces a JSON solution sidecar. Without --plot the existing workflow is retained.

The bridge uses exact EDAS anchor IDs (ILT prefix may be omitted). L-ST-PS derives from ILT-L-FT-PS with branch support and association changed F to S using EDAS taxonomy. Unknown candidates fail. Null overrides remove inherited parameters.

This reconstructs study dimensions and implicit connectors; it does not size geometry to EDPR constraints, produce fabrication detail or run structural analysis. Provenance, derivation and risks are recorded; expert review is required.

Knowloop --layout-report and --plot-report retain automated evidence. Warnings/review mark outcomes partial, failures mark failed. Official knowledge and human ratings are untouched. Mapping/plot failures emit feedback before nonzero exit; earlier pipeline stages retain existing fail-fast behavior.

29 distinct tests passed, including end-to-end markdown/plot and Knowloop schema validation. The saved plot was visually inspected; existing tall table and mass limitations remain.
