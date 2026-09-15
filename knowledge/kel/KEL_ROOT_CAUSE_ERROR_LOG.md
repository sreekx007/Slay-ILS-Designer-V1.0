# KEL Root Cause Error Log

This log reviews the implemented KEL lessons by error mechanism. It is not a blame list. It separates unavailable knowledge from failures to retrieve, correlate, constrain, or apply knowledge that already existed in EDPR/EDES/EDAS/EDIKB/tooling.

## Working diagnosis

```text
primary root cause :: workflow did not fail closed before design/plot emission
secondary root cause :: available EDIKB/EDAS constraints were retrieved late, not retrieved, or not converted into layout basis fields
tertiary root cause :: EDIKB has limited covariance/correlation coverage for coupled connector-system stiffness, support stiffness, component stiffness, and global strain redistribution
not primary :: pure absence of all relevant knowledge
```

The strongest pattern is not that EDIKB had no useful knowledge. In several cases, the repository already had relevant EDES geometry, EDAS standard anchors, EDIKB branch/connector trends, or prior KEL gates. The design response failed because the workflow proceeded from a plausible verbal answer to a plotted layout without first proving that the selected assembly satisfied required constraints and evidence use.

## Error class RC-01: EDPR/problem understanding not confirmed before design

```text
observed_errors :: concept generated before user confirmed EDPR/problem understanding
examples :: option-comparison branch/header-valve case; later branch-valve trials
root_cause :: workflow sequencing gap
knowledge_gap :: low
fix_strategy :: block design/plot until EDPR/APF/P-map understanding is emitted and confirmed
implemented_gates :: EDPR_CONFIRMATION_REQUIRED
```

This is a process control failure. Better EDIKB data would not by itself prevent the error if the agent can skip problem representation and confirmation.

## Error class RC-02: header valve emitted without compulsory base/protection structure

```text
observed_errors :: valve added on header line without GD-SB/base protection when roller contact or roller passage issue existed
examples :: 12-inch header valve; option 2 header valve
root_cause :: mandatory constraint not applied before layout generation
knowledge_gap :: low-to-medium
available_knowledge :: EDES GD-VLV cannot ride/contact rollers in relevant cases; EDES/EDAS contains GD-SB geometry; KEL now records compulsory GD-SB gate
fix_strategy :: header-valve intent must trigger valveProtection inputs and HEADER_VALVE_REQUIRES_GD_SB unless explicitly out of scope
implemented_gates :: VALVE_PROTECTION_INPUTS_MISSING; HEADER_VALVE_REQUIRES_GD_SB; SUPPORT_STRUCTURE_DIMENSIONS_DEFAULTED
```

This was a basic constraint failure more than a missing-correlation failure. Missing project inputs such as roller geometry, clearance and load cases should have stopped the workflow or produced a preliminary-only layout.

## Error class RC-03: strain and bending-moment reduction not considered by default

```text
observed_errors :: layout provided with no attempt to reduce strain or bending moment; large support dimensions used without correlation to strain response
examples :: base structure longer/deeper than valve; option layout with no strain-reduction basis
root_cause :: objective/evaluation defaults not enforced
knowledge_gap :: medium
available_knowledge :: EDIKB includes strain trends for shroud offset/length, connector systems, branch layouts and low/high strain regions
missing_knowledge :: stronger covariance between support length/depth/stiffness and global strain redistribution across full assemblies
fix_strategy :: every concept must state strain/moment screening basis; formal optimization still requires numeric evidence
implemented_gates :: DEFAULT_STRAIN_MOMENT_REDUCTION; support_sizing_gate; shroud_stiff_evidence_gate
```

There are two layers here. The workflow failed to use available qualitative trends. Separately, EDIKB still needs more coupled response data to quantify tradeoffs reliably.

## Error class RC-04: F2/F2D selected without reason

```text
observed_errors :: F2 top-frame connection selected for branch-valve case even though no low-strain pocket was needed and header penalty was likely
examples :: vertical connector + heavy branch valve on horizontal leg
root_cause :: standard layout anchor and connector-system evidence not used as a decision gate
knowledge_gap :: medium
available_knowledge :: EDIKB branch rows indicate F2 can reduce branch strain but gives high header strain; PS moderates header strain in Z cases
missing_knowledge :: broader connector-system covariance with frame stiffness, branch valve mass, and component placement
fix_strategy :: F2/F2D require explicit evidence basis; prefer PS when containment/support is needed without low-strain-pocket objective
implemented_gates :: UNJUSTIFIED_F2_FOR_BRANCH_VALVE; branch_valve_top_frame_gate
```

The immediate mistake was not lack of any F2 evidence. It was misuse of F2 as a default. More correlation data would improve ranking, but the design should already have asked: is a low-strain pocket required, and is the header penalty acceptable?

## Error class RC-05: branch topology/standard anchor not enforced

```text
observed_errors :: vertical connector represented with wrong/simplified branch shape; branch valve and tee placed outside top-frame span
examples :: Q1 vertical connector; Q6 Z-branch heavy branch valve
root_cause :: EDAS standard-layout precedent not applied before plot emission
knowledge_gap :: low
available_knowledge :: EDAS has ILT-L-* and ILT-Z-* anchors; GD-B supports L/Z variants and P_bv branch valve station
fix_strategy :: connector orientation selects branch family; branch tee, valve and end must be inside associated GD-ST span for branch-valve layouts
implemented_gates :: VERTICAL_CONNECTOR_REQUIRES_GD_B_Z; BRANCH_GD_ST_ASSOCIATION_REQUIRED; BRANCH_VALVE_OUTSIDE_GD_ST_SPAN
```

This was mainly a representation and standard-anchor failure.

## Error class RC-06: available analogous evidence not recognized as useful

```text
observed_errors :: GD-VLV + GD-SH treated as new situation; GD-TP/GD-TT + GD-SH evidence not used
examples :: valve with tapered shroud; valve plus top structure review
root_cause :: retrieval usefulness judgement failure
knowledge_gap :: medium
available_knowledge :: C1 GD-SH + GD-TP/GD-TT evidence covers non-additive response, stiff-body position and shroud length/region effects
missing_knowledge :: direct GD-VLV + GD-SH FEA rows with valve-specific envelopes, masses and load cases
fix_strategy :: retrieve analogous C1 shroud/stiff-component evidence; flag if missed; require layout basis showing how evidence was applied
implemented_gates :: EDIKB_USEFULNESS_JUDGEMENT_FAILURE; SHROUD_STIFF_EVIDENCE_NOT_APPLIED
```

This is a mixed cause. Direct valve-specific evidence is still missing, but analogous evidence was available and should have shaped the concept.

## Error class RC-07: plot looked valid while hiding or compressing critical review information

```text
observed_errors :: long parameter panel compressed geometry; labels too small or overlapped; connection labels too verbose
examples :: paper-use figures; GD-ST connection-label reviews
root_cause :: plot presentation carried too much tabular data inside figure canvas
knowledge_gap :: none
fix_strategy :: keep plot geometry readable; export parameters separately as CSV; show only F/P/S/D connection type labels and omit W labels
implemented_update :: assembly parameter CSV export; geometry-only assembly plot default; compact non-W connection labels
```

This is a visualization/reporting error, not an engineering-knowledge error.

## Data strategy implications

```text
priority_1 :: enforce workflow gates before adding more data
priority_2 :: convert retrieved evidence into required layout-basis fields
priority_3 :: add covariance/correlation datasets for connector system + support stiffness + component stiffness + mass placement
priority_4 :: add direct combined layouts for GD-VLV+GD-SB, GD-VLV+GD-SH, GD-B branch valve + GD-ST
priority_5 :: keep plots paper-readable and move detailed parameters to machine-readable sidecars
```

More EDIKB data is needed, especially for interaction effects. But the KEL strategy should not wait for complete data. The current higher-value improvement is fail-closed workflow behavior: if evidence is absent, weak, analogous, or not applied, the toolchain must say so before presenting a design as suitable.
