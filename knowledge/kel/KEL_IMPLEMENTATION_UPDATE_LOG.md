# KEL Implementation Update Log

Brief machine-style log of implemented KEL lessons and toolchain updates. This file is for fast agent handoff; authoritative records remain in `knowledge/kel/feedback_records/`, `graph_change_requests/`, `expert_reviews/`, `implementation_plans/`, and `lifecycle_reports/`.

## Q1/Q2 pending candidate implementation batch - 2026-09-15

```text
scope :: pending Q1/Q2 KEL candidates promoted to implemented lifecycle
edpr :: enforced EDPR confirmation before layout/design generation
edpr :: vertical connector -> GD-B.variant=Z + ILT-Z-* candidate family
edas :: unknown layout candidates fail closed; no heuristic anchor substitution
plotter :: repository plotter required for framework-backed geometry
plotter :: connection labels + parameter exposure improved for GD-ST/GD-SB workflows
rules :: header valve requires canonical GD-SB when roller/contact protection is needed
rules :: default design screening considers strain + bending moment reduction
records :: Q1/Q2 feedback/GCR records moved to implemented; pending/superseded reconciled
papers :: premature trial-result language removed from paper drafts
validation :: KEL records validated; tool unittest suite passed in release batch
```

## Q3 support-structure sizing KEL - 2026-09-15

```text
trigger :: plotted GD-SB/GD-ST dimensions exceeded or contradicted supported component envelope
plotters/ils_builder.py :: added support_sizing_gate
plotters/ils_builder.py :: GD-SB protecting GD-VLV requires explicit P_l1/P_l2/P_v/P_vt
plotters/ils_builder.py :: GD-ST supporting GD-B requires explicit L_top/H_top/P_vt for complete status
tools/design_rules_v02.py :: added SUPPORT_STRUCTURE_DIMENSIONS_DEFAULTED validation
edpr/kel docs :: support/protection structures must be fitted to supported component envelope
records :: Q3 feedback/review/GCR/plan/closeout added
validation :: tests/kel/test_design_workflow_v02.py passed
```

## Q4 valve-shroud stiff-component retrieval KEL - 2026-09-15

```text
trigger :: GD-VLV + GD-SH was not recognized as analogous to GD-TP/GD-TT + GD-SH evidence
tools/design_rules_v02.py :: added shroud_stiff_component intent gate
tools/retrieve_context.py :: retrieves ILS-SHTP and GD-SH+GD-TP/GD-TT C1 evidence for GD-VLV+GD-SH
tools/solve_problem.py :: added EDIKB_USEFULNESS_JUDGEMENT_FAILURE when useful shroud-stiff evidence is missed
edpr/kel docs :: GD-VLV inside GD-SH treated as stiff inline component with analogous C1 evidence
records :: Q4 feedback/review/GCR/plan/closeout added
validation :: targeted KEL regression + tool unittest suite passed
```

## Q5 shroud-stiff evidence application KEL - 2026-09-15

```text
trigger :: retrieval occurred but layout did not apply C1 shroud/stiff-body evidence to geometry basis
plotters/ils_builder.py :: added shroud_stiff_evidence_gate
tools/design_rules_v02.py :: added SHROUD_STIFF_EVIDENCE_NOT_APPLIED validation
design_basis :: requires shroud_stiff_evidence_refs + shroud_dimensions_basis + stiff_component_position_basis + shroud_regions_basis + applicability_limits
edpr/kel docs :: retrieval alone is insufficient; layout/report must state evidence application
records :: Q5 feedback/review/GCR/plan/closeout added
validation :: KEL record validation + tests/kel + tool unittest suite passed
```

## Q6 branch-valve top-frame containment KEL - 2026-09-15

```text
trigger :: Z-branch heavy valve concept used F2 without evidence and placed branch tee/valve outside GD-ST span
tools/design_rules_v02.py :: added branchValve intent extraction
tools/design_rules_v02.py :: branch valve no longer triggers header GD-SB gate
tools/design_rules_v02.py :: added BRANCH_VALVE_OUTSIDE_GD_ST_SPAN
tools/design_rules_v02.py :: added UNJUSTIFIED_F2_FOR_BRANCH_VALVE
plotters/ils_builder.py :: added branch_valve_top_frame_gate
plotters/ils_builder.py :: reports tee/valve/end containment inside GD-ST span
plotters/ils_builder.py :: reports F2/F2D missing evidence basis
edpr/kel docs :: branch valve uses compatible ILT-L/ILT-Z anchor; prefer PS unless F2/F2D evidence exists
records :: Q6 feedback/review/GCR/plan/closeout added
validation :: KEL record validation + 11 KEL tests + 32 tool unittests passed
```

## Q7 root-cause strategy and plot-output readability update - 2026-09-15

```text
trigger :: repeated KEL lessons showed basic design errors plus paper-unusable plots compressed by parameter tables
knowledge/kel/KEL_ROOT_CAUSE_ERROR_LOG.md :: added per-implemented-KEL root-cause entries separating workflow failures from EDIKB data gaps
analysis :: primary cause = fail-closed workflow/evidence-application gaps; secondary cause = missing coupled stiffness/covariance data
plotters/ils_plotter.py :: assembly plot defaults to geometry-only figure
plotters/ils_plotter.py :: added write_parameter_csv for assembly/component parameters and connector slot context
tools/_plot_cli.py :: emits *.parameters.csv and records parameter_csv path in plot report
plotters/ils_plotter.py :: plot connection labels now show only F/P/S/D letter; W remains omitted
tests :: updated label/CLI tests and stale KEL lifecycle tests
validation :: 10 affected plot tests + 32 plot/tool tests + 29 KEL tests + 32 full tool unittests passed
```

## Q8 plot annotation and feedback prompt KEL - 2026-09-15

```text
trigger :: strain-watch arrows were placed by pixel judgement, required connection-type label scope was unclear, and LLM did not ask for feedback after plot emission
plotters/ils_plotter.py :: added model-coordinate plot_annotations support resolved through live component features or explicit x/y data
plotters/ils_plotter.py :: records plot annotation anchor resolution in figure metadata
tools/_plot_cli.py :: reports plot_annotations and fails unresolved requested annotation anchors
tools/_plot_cli.py :: added required_structure_connection_labels check for non-weld GD-ST/GD-SB structural connection type labels
policy :: connector component labels are not required; required labels are F/P/S/D connection-type labels, W omitted
manifest/kel docs :: LLM must ask whether plot is required after solution proposal and must ask for feedback after plotted layout
validation :: tool unittest suite covers model-anchored annotations, invalid annotation failure, and required GD-ST connection-type label reporting
```
