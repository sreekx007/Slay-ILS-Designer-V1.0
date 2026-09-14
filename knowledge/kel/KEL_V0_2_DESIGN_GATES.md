# KEL v0.2 Design Workflow Gates

KEL v0.2 turns accepted feedback into deterministic checks used by EDPR,
the evidence solver, EDAS layout materialization, and the repository plotter.
Generated outputs remain concept-screening artifacts until expert review.

## Vertical connector

EDPR records connector orientation separately from branch routing, branch
take-off direction, and page orientation. A required vertical connector limits
the standard-layout candidate set to `ILT-Z-*` and requires `GD-B.variant = Z`.
If no compatible Z anchor remains, layout emission returns a representation gap.
It never substitutes an L branch.

## EA-ST exposure

An assembly report containing GD-ST emits canonical GD-ST parameters, active
connector slots and types, corresponding GD-Con instances, GD-TP/GD-TT/GD-PIP/
GD-BOSS pipe landings, and association indices. The plot parameter panel shows
the same canonical parameters, connector layout, gate status, and branch-frame
associations.

`ils.design_gate = complete` makes missing connectors, landings, or associations
build errors. `study_only` marks published-paper reconstructions that use
implicit connectors; those plots cannot claim complete-design status.

## Valve protection

The workflow stops before selecting EA-SB until it knows whether roller passage
is in scope, underside or top protection, equipment and thick-section envelopes,
roller geometry, clearance, load cases, acceptance measure, connector spacing
and system basis, compatible connector evidence, valve capacity ratio, and
combined valve moment evidence.

An EA-SB concept must contain the repository's GD-SB geometry and contact model.
A top frame is a separate GD-ST. Connector choice without compatible evidence
has status `needs_evidence`. Valve moment acceptance is:

```text
utilization = maximum valve bending moment
              / (valve capacity ratio * pipeline allowable bending moment)
```

Every required load case must have utilization no greater than 1.0. A stated
80 percent capacity does not choose a support topology and does not create a
strain-minimization objective.

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
