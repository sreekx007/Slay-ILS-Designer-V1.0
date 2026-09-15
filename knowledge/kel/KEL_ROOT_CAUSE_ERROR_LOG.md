# KEL Root Cause Error Log

This log records root-cause analysis for each implemented KEL candidate. It is organized by KEL item, not by overall error class. Each entry separates immediate workflow failure, available knowledge that should have been used, missing EDIKB/correlation data where relevant, and the resulting KEL strategy.

## Summary pattern

```text
primary_pattern :: most implemented KELs were caused by missing fail-closed workflow gates or evidence-application gates
secondary_pattern :: several KELs exposed weak retrieval/use of available EDAS/EDES/EDIKB constraints
tertiary_pattern :: some KELs need additional coupled EDIKB covariance/correlation data for stronger ranking, especially connector/support stiffness interactions
strategy :: add deterministic gates first; add coupled evidence datasets second
```

## Q1.01 Branch direction / schematic branch shape

```text
kel_record :: Q1_01_BRANCH_DIRECTION
observed_error :: branch geometry was drawn in a simplified or wrong direction rather than as a framework-backed GD-B layout
root_cause :: freehand/schematic plotting bypassed EDAS/GD-B topology and repository plotter geometry
available_knowledge_missed :: EDES GD-B branch component; EDAS ILT family anchors
edikb_gap :: low; this was a representation failure, not a behavior-data failure
implemented_response :: require repository plotter/EDAS geometry and reject unsupported sketch geometry as authoritative design output
```

## Q1.02 Valve EA-SB default / header valve protection

```text
kel_record :: Q1_02_VALVE_EASB_DEFAULT
observed_error :: header valve was treated as acceptable without compulsory GD-SB/base protection context
root_cause :: mandatory valve-protection constraint was not checked before concept/layout emission
available_knowledge_missed :: EDES GD-VLV roller-contact limitation; EDES/EDAS GD-SB geometry; valveProtection workflow fields
edikb_gap :: medium; direct valve + base FEA data remains useful, but absence of data should have blocked design acceptance
implemented_response :: VALVE_PROTECTION_INPUTS_MISSING and HEADER_VALVE_REQUIRES_GD_SB gates
```

## Q1.03 Branch connector EA-ST default

```text
kel_record :: Q1_03_BRANCH_CONNECTOR_EAST_DEFAULT
observed_error :: branch connector was not anchored to a top frame as a default branch-layout requirement
root_cause :: branch topology was emitted without enforcing GD-B-to-GD-ST terminal association
available_knowledge_missed :: EDAS ILT anchors define GD-B termination at GD-ST; EDES GD-ST features exist
edikb_gap :: low for representation; medium for ranking fixed/slotted support behavior
implemented_response :: BRANCH_REQUIRES_GD_ST and BRANCH_GD_ST_ASSOCIATION_REQUIRED gates
```

## Q1.04 Plot scale

```text
kel_record :: Q1_04_PLOT_SCALE
observed_error :: plot scale made the actual structure unreadable or visually misleading
root_cause :: presentation layer optimized output canvas around labels/tables rather than readable engineering geometry
available_knowledge_missed :: plotter already had component extents and geometry bounds
edikb_gap :: none; visualization failure
implemented_response :: plot QA, bounded label correction, and later CSV sidecar policy for long parameter data
```

## Q1.05 EA-ST connections labelled

```text
kel_record :: Q1_05_EAST_CONNECTIONS_LABELLED
observed_error :: top-frame-to-pipeline/branch connection types were missing or illegible in plot output
root_cause :: plot/report did not expose active GD-ST connector slots and connection types clearly enough for review
available_knowledge_missed :: component_spec active_connectors(system); GD-Con associations; named connection systems F/P/S/D
edikb_gap :: low for labels; medium for connector stiffness ranking
implemented_response :: report active connectors and associations; plot non-weld connection type labels
```

## Q1.06 Piping connections scope

```text
kel_record :: Q1_06_PIPING_CONNECTIONS_SCOPE
observed_error :: connection wording mixed piping connections with support/structural connection assumptions
root_cause :: EDPR/problem representation did not keep connection categories separate
available_knowledge_missed :: EDES distinction between inline welds, branch topology, GD-Con structural connectors, and support associations
edikb_gap :: low; terminology/classification failure
implemented_response :: workflow instructions require distinguishing piping, support, and structural connections
```

## Q1.07 Stress/strain objective

```text
kel_record :: Q1_07_STRESS_STRAIN_OBJECTIVE
observed_error :: generated concepts did not consider strain or bending moment reduction by default
root_cause :: solver/design response lacked a default screening objective for high strain and moment when user did not phrase a formal optimization target
available_knowledge_missed :: EDIKB strain/moment response regions; branch and connector trend rows
edikb_gap :: medium; more coupled full-layout covariance data is still needed
implemented_response :: DEFAULT_STRAIN_MOMENT_REDUCTION rule and workflow text requiring strain/moment screening basis
```

## Q1.08 Must use repo plotter

```text
kel_record :: Q1_08_MUST_USE_REPO_PLOTTER
observed_error :: custom sketch was presented as layout evidence without repository EDES/EDAS/plotter backing
root_cause :: no hard gate forced framework-backed geometry before plotting
available_knowledge_missed :: repository plotter and EDAS layout definitions existed
edikb_gap :: none; tool-use governance failure
implemented_response :: LLM workflow gate requiring EDPR/retrieval/EDAS layout/build checks before authoritative plot presentation
```

## Q1.09 Z branch for vertical connector

```text
kel_record :: Q1_09_Z_BRANCH_FOR_VERTICAL_CONNECTOR
observed_error :: vertical connector request was represented as an L/simple branch instead of GD-B variant Z
root_cause :: connector orientation was confused with drawing direction or branch routing
available_knowledge_missed :: GD-B.variant Z and ILT-Z-* standard anchors
edikb_gap :: low for topology; medium for ranking Z connector systems
implemented_response :: VERTICAL_CONNECTOR_REQUIRES_GD_B_Z and ILT-Z candidate selection
```

## Q1.10 EA-SB shape from EDES

```text
kel_record :: Q1_10_EASB_SHAPE_FROM_EDES
observed_error :: base structure was drawn as a generic frame rather than canonical GD-SB geometry
root_cause :: plot/design output bypassed EDES component geometry and contact model
available_knowledge_missed :: EDES GD-SB trapezoid/contact geometry and parameters
edikb_gap :: low for geometry; medium for valve/base interaction behavior
implemented_response :: require actual GD-SB component, not generic support sketch
```

## Q1.11 EA-ST parameters and connections

```text
kel_record :: Q1_11_EAST_PARAMETERS_CONNECTIONS
observed_error :: top-frame parameters, active connectors, pipe-side landings and branch associations were not exposed
root_cause :: report/plot treated GD-ST as a visual object rather than a reviewable parameterized assembly object
available_knowledge_missed :: GD-ST canonical parameters, active_connectors, GD-Con/GD-TP landings, associations
edikb_gap :: medium for connector/stiffness covariance, low for parameter exposure
implemented_response :: design_workflow_report exposes GD-ST parameters, slots, associations, missing landings and complete-design gate
```

## Q2.01 EDPR confirmation before design

```text
kel_record :: Q2_01_EDPR_CONFIRMATION_BEFORE_DESIGN
observed_error :: concept generation proceeded before EDPR/problem understanding was emitted and confirmed
root_cause :: conversational workflow skipped problem-representation checkpoint
available_knowledge_missed :: EDPR/P-map/APF workflow already existed
edikb_gap :: none; process sequencing failure
implemented_response :: EDPR_CONFIRMATION_REQUIRED blocker
```

## Q2.02 Header valve requires GD-SB

```text
kel_record :: Q2_02_HEADER_VALVE_REQUIRES_GD_SB
observed_error :: valve was added on header line without required base/protection structure
root_cause :: header-valve protection was not treated as a compulsory constraint
available_knowledge_missed :: EDES GD-VLV limitation and GD-SB protection component; valveProtection inputs
edikb_gap :: medium; direct valve + GD-SB moment/contact evidence still needed for final design, but omission should have blocked concept acceptance
implemented_response :: HEADER_VALVE_REQUIRES_GD_SB plus missing-input/evidence blockers
```

## Q2.03 Connection labels legible

```text
kel_record :: Q2_03_CONNECTION_LABELS_LEGIBLE
observed_error :: GD-ST connection types were absent or too small to review in plot
root_cause :: plot labeling did not prioritize connection-type review information
available_knowledge_missed :: association connection fields and GD-Con type values
edikb_gap :: none for label legibility
implemented_response :: connection_label_legibility check and later compact F/P/S/D-only plot labels
```

## Q2.04 Default strain/moment reduction

```text
kel_record :: Q2_04_DEFAULT_STRAIN_MOMENT_REDUCTION
observed_error :: layout did not demonstrate any strain or bending-moment reduction attempt
root_cause :: design workflow allowed geometry selection without response-screening basis
available_knowledge_missed :: EDIKB strain/moment trends and response-region warnings
edikb_gap :: medium-to-high for multi-component covariance and global response ranking
implemented_response :: objective gate requiring high-strain/high-moment consideration even without formal optimization wording
```

## Two-branch-valve representation gap

```text
kel_record :: KEL_V0_2_TWO_BRANCH_VALVE_REPRESENTATION_GAP
observed_error :: two branch valves could not be represented unambiguously as branch-owned instances with topology, stations, associations and envelopes
root_cause :: schema/workflow lacked accepted topology and stable valve instance semantics
available_knowledge_missed :: not applicable; topology itself was unresolved
edikb_gap :: high until topology is expert-defined and analyzable
implemented_response :: emit TWO_BRANCH_VALVE_TOPOLOGY_UNRESOLVED and do not plot until expert topology review is complete
```

## Q3 Support structure sized to component

```text
kel_record :: Q3_01_SUPPORT_STRUCTURE_SIZED_TO_COMPONENT
observed_error :: GD-SB/GD-ST dimensions were much larger than the valve/branch envelope and contradicted the stated recommendation
root_cause :: EDAS defaults were used as design dimensions without fitting to protected/supported component envelope
available_knowledge_missed :: component envelopes and explicit GD-SB/GD-ST sizing parameters
edikb_gap :: medium; relation between support dimensions, stiffness and global strain needs stronger coupled data
implemented_response :: SUPPORT_STRUCTURE_DIMENSIONS_DEFAULTED and support_sizing_gate
```

## Q4 Valve-shroud stiff-component EDIKB retrieval

```text
kel_record :: Q4_01_VALVE_SHROUD_STIFF_COMPONENT_EDIKB
observed_error :: GD-VLV + GD-SH was not identified as analogous to stiff-component + shroud behavior
root_cause :: retrieval usefulness judgement failed; component name difference hid a behavior analogy
available_knowledge_missed :: ILS-SHTP and GD-SH + GD-TP/GD-TT C1 evidence nodes
edikb_gap :: medium; direct GD-VLV + GD-SH evidence remains missing
implemented_response :: shroud_stiff_component intent, C1 evidence retrieval, EDIKB_USEFULNESS_JUDGEMENT_FAILURE flag
```

## Q5 Shroud-stiff evidence applied

```text
kel_record :: Q5_01_SHROUD_STIFF_EVIDENCE_APPLIED
observed_error :: C1 shroud/stiff evidence was retrieved but not applied to valve placement or shroud dimensions
root_cause :: retrieval and design-basis application were not coupled by a gate
available_knowledge_missed :: retrieved C1 evidence refs, shroud position/length and region guidance
edikb_gap :: medium; direct valve rows still useful, but analogous evidence was available
implemented_response :: SHROUD_STIFF_EVIDENCE_NOT_APPLIED and shroud_stiff_evidence_gate requiring explicit design_basis fields
```

## Q6 Branch-valve top-frame containment

```text
kel_record :: Q6_01_BRANCH_VALVE_TOP_FRAME_CONTAINMENT
observed_error :: branch valve concept selected F2 without basis and placed branch tee/valve outside GD-ST span
root_cause :: standard ILT-Z anchor precedent and connector-system evidence were not used as gates
available_knowledge_missed :: ILT-Z-FT-PS standard anchor, GD-B.P_bv, branch/connector EDIKB showing F2 branch benefit plus header penalty
edikb_gap :: medium; more covariance data needed for branch valve mass + GD-ST connector system + header strain redistribution
implemented_response :: BRANCH_VALVE_OUTSIDE_GD_ST_SPAN, UNJUSTIFIED_F2_FOR_BRANCH_VALVE, branch_valve_top_frame_gate
```

## Q7 Plot output readability / parameter CSV

```text
kel_record :: Q7_plot_output_readability
observed_error :: long parameter panel compressed actual plot geometry and made paper-use figures unreadable
root_cause :: visualization tried to carry review table and geometry in one canvas
available_knowledge_missed :: plotter already had report and sidecar artifact path capability
edikb_gap :: none; visualization/reporting failure
implemented_response :: assembly plot defaults to geometry-only; parameters exported to *.parameters.csv; plot connection labels reduced to non-weld connection letters
```

## Strategy implication by candidate

```text
candidate_group_q1_q2 :: strongest need is workflow gating and use of EDES/EDAS constraints before design emission
candidate_group_q3 :: add fitted-dimension basis and later support-dimension/strain covariance data
candidate_group_q4_q5 :: improve analogous evidence retrieval and force evidence application into layout basis
candidate_group_q6 :: add connector-system decision basis and branch-valve containment checks; later add coupled branch-valve/F2/PS covariance data
candidate_group_q7 :: keep paper figures visual; move parameter detail to machine-readable sidecars
```
## Q8.01 Model-anchored strain labels

```text
kel_record :: Q8_01_MODEL_ANCHORED_STRAIN_LABELS
observed_error :: peak-strain and branch-transition label pointers did not land on the intended physical locations
root_cause :: plot annotations were placed by approximate rendered-image coordinates instead of model geometry coordinates
available_knowledge_missed :: live builder feature coordinates exposed by ils.feature_xy and EDAS association feature names
edikb_gap :: none for plotting; actual strain magnitudes still require EDIKB/FEA evidence
implemented_response :: plot_annotations contract with component-feature or numeric model-coordinate anchors; unresolved anchors fail plot report
```

## Q8.02 Structure connection label scope

```text
kel_record :: Q8_02_STRUCTURE_CONNECTION_LABEL_SCOPE
observed_error :: label expectation was ambiguous between connector component labels and connection-type labels
root_cause :: workflow did not distinguish component identification from required connection-type review information
available_knowledge_missed :: association connection fields already encode F/P/S/D/W; prior plotter update already suppressed W
edikb_gap :: none; reporting and QA scope issue
implemented_response :: required_structure_connection_labels checks non-weld GD-ST/GD-SB structural connection type labels only; connector component labels are not required
```

## Q8.03 Post-plot feedback request

```text
kel_record :: Q8_03_POST_PLOT_FEEDBACK_REQUEST
observed_error :: LLM emitted a plot without asking the human user for feedback afterward
root_cause :: conversation workflow ended at artifact delivery instead of closing the human review loop
available_knowledge_missed :: KEL human-feedback lifecycle requires explicit human review input for improvement capture
edikb_gap :: none; workflow sequencing failure
implemented_response :: manifest and KEL instructions require feedback request after any plotted layout, covering component placement, connection-type labels and strain-watch pointer locations
```
