# KEL v0.2 Design Workflow Gates

KEL v0.2 turns accepted feedback into deterministic checks used by EDPR,
the evidence solver, EDAS layout materialization, and the repository plotter.
Generated outputs remain concept-screening artifacts until expert review.

## Branch-to-GD-ST anchoring

Every `GD-B` branch emitted as part of an ILS must terminate at a declared
`GD-ST` feature. An L branch uses its horizontal terminal and a Z branch uses
its vertical terminal; the selected layout anchor defines the compatible
`GD-ST` feature, including post-specific features where applicable. A
regression trial first exposed the omission on a Z branch, but the same
visually-adjacent-without-association failure applies to L branches. Missing
`GD-ST` or a missing terminal association fails the complete-design gate. A
branch-only component study must be marked `study_only`.

## Branch-valve top-frame containment and connector system basis

When a valve is on a branch line, the branch valve is a branch-owned feature of
`GD-B`, not a header valve that triggers `GD-SB`. The layout must start from a
compatible `ILT-L-*` or `ILT-Z-*` standard anchor, place the branch tee/entry,
branch valve, and branch end inside the associated `GD-ST` span, and expose this
through the report as `branch_valve_top_frame_gate`.

`F2` and `F2D` are not default choices for this case. They may be used only when
the design basis provides strain or moment evidence that a low-strain pocket is
needed on the branch and that the header-strain penalty is accepted. Without
that basis, `PS` is the preferred standard-anchor family. Violations raise
`BRANCH_VALVE_OUTSIDE_GD_ST_SPAN` or `UNJUSTIFIED_F2_FOR_BRANCH_VALVE`.

## Connector orientation and branch family

EDPR records connector orientation separately from branch routing, branch
take-off direction, and page orientation. A required vertical connector limits
the standard-layout candidate set to `ILT-Z-*` and requires `GD-B.variant = Z`.
If no compatible Z anchor remains, layout emission returns a representation gap.
It never substitutes an L branch. This orientation gate is separate from the
branch-to-`GD-ST` anchoring gate, which applies to both L and Z branches.

## GD-ST exposure

An assembly report containing GD-ST emits canonical GD-ST parameters, active
connector slots and types, corresponding GD-Con instances, GD-TP/GD-TT/GD-PIP/
GD-BOSS pipe landings, and association indices. The plot parameter panel shows
the same canonical parameters, connector layout, gate status, and branch-frame
associations.

`ils.design_gate = complete` makes missing connectors, landings, or associations
build errors. `study_only` marks published-paper reconstructions that use
implicit connectors; those plots cannot claim complete-design status.

## Valve protection

The workflow stops before selecting GD-SB until it knows whether roller passage
is in scope, underside or top protection, equipment and thick-section envelopes,
roller geometry, clearance, load cases, acceptance measure, connector spacing
and system basis, compatible connector evidence, valve capacity ratio, and
combined valve moment evidence.

A GD-SB concept must contain the repository's GD-SB geometry and contact model.
A top frame is a separate GD-ST. Connector choice without compatible evidence
has status `needs_evidence`. Valve moment acceptance is:

```text
utilization = maximum valve bending moment
              / (valve capacity ratio * pipeline allowable bending moment)
```

Every required load case must have utilization no greater than 1.0. A stated
80 percent capacity does not choose a support topology and does not create a
strain-minimization objective.

## Support and protection structure sizing

When `GD-SB` is introduced to protect `GD-VLV`, the base-structure dimensions
must be explicitly fitted to the valve envelope, actuator/stem clearance, roller
clearance, and connector spacing basis. Leaving `P_l1`, `P_l2`, `P_v`, or
`P_vt` to generic EDAS defaults fails the support-sizing gate. The same rule
applies by family to `GD-ST` when it supports `GD-B`: the top-frame length,
height, and vertical offset must be fitted to the branch terminal and connector
geometry before the layout can claim complete status.

## Shroud plus stiff inline component evidence

When `GD-VLV` is combined with `GD-SH`, the workflow treats the valve as a
stiff inline component inside an offset shroud. This is analogous to the
accepted `ILS-SHTP` / `GD-SH + GD-TP/GD-TT` C1 evidence pattern: combined
response is non-additive, stiff-component position relative to the shroud X2
region matters, peak strain can remain governed by the shroud transition
region, and shroud/stiff-component lengths must be checked against available
EDIKB rows before recommending a placement. The solver must flag
`EDIKB_USEFULNESS_JUDGEMENT_FAILURE` when this interaction is present but those
useful EDIKB nodes or numeric rows are not selected.

Retrieval alone is not enough. A layout that contains `GD-VLV + GD-SH` must show
how the C1 evidence was applied to `GD-SH.V`, `GD-SH.L1`, `GD-SH.L2`, the stiff
component position relative to X2/X3/X4 or equivalent curvature regions, and
the evidence applicability limits. If these basis fields are absent, the report
raises `SHROUD_STIFF_EVIDENCE_NOT_APPLIED` and the layout remains a preliminary
geometry sketch.

## Two branch valves

The current accepted topology is unresolved. EDPR emits
`TWO_BRANCH_VALVE_TOPOLOGY_UNRESOLVED` unless expert-reviewed input supplies one
of the supported topology names and two distinct valve instances with parent
branch ownership. No layout or plot is emitted while that gap is active. The
pending atomic feedback, feedback group, and graph-change request preserve the
requirement for review and later end-to-end implementation.

## Commands

```text
python tools/kel/create_implementation_plan.py CHANGE.json --output PLAN.json
python tools/kel/summarize_kel_status.py --format json
python tools/kel/migrate_v01_to_v02.py knowledge/kel/feedback_records/candidates/*.json --output-root runs/kel/migration
```
