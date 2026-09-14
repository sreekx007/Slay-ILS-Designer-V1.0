# KEL v0.2 Recommendations

Implementation status: Step 1 feedback decomposition, grouping,
de-duplication, and lifecycle reconciliation is complete locally.

## Purpose

KEL v0.1 establishes the governance loop:

```text
experience -> sufficiency -> feedback -> graph change request
-> expert review -> promotion trace
```

KEL v0.2 should improve automation quality, reduce duplicate records, and begin
closing the gap between reviewed change requests and actual framework updates.

The implementation-ready sequence, file touchpoints, regression fixtures, and
exit gates are defined in `KEL_V0_2_IMPLEMENTATION_PLAN.md`.

## Recommended Build Items

| Priority | Recommendation | Why It Matters |
|---|---|---|
| High | Add feedback grouping and de-duplication | Several feedback records can point to one root issue; grouping avoids noisy graph-change queues. |
| High | Add lifecycle move/supersede support | Promotion currently writes lifecycle copies; v0.2 should optionally move pending records or mark them superseded. |
| High | Add implementation planners per target layer | Accepted EDPR, EDAS, EDES, Plotter, and KEL changes need target-specific implementation checklists. |
| High | Strengthen plotter-backed layout gate | A layout plot should fail closed when repo plotter/build checks cannot represent the requested geometry. |
| Medium | Add richer feedback classifier | The rule-based classifier works for v0.1 but needs better component/action detection and confidence reporting. |
| Medium | Add graph-change grouping by target layer and change type | This will support expert batch review and avoid fragmented decisions. |
| Medium | Add KEL cycle integration tests | Test the full wrapper with realistic EDPR/context/solution/feedback fixtures. |
| Medium | Add review dashboards or summary reports | Experts need a compact view of pending, accepted, rejected, and implemented records. |
| Low | Add optional automatic Git branch/commit helpers | Useful later, but only after lifecycle and implementation gates are reliable. |

## Prioritized Q1-Driven Implementation Plan

The first KEL v0.2 implementation pass must follow this order:

| Order | Implementation gap | Q1 evidence | Completion test |
|---:|---|---|---|
| 1 | Feedback grouping and de-duplication | All Q1 feedback candidates and graph-change requests | Near-duplicate feedback is grouped into one change request while preserving every source feedback ID and evidence link. |
| 2 | EDPR/EDAS rule for vertical connectors | `Q1_GCR_09_Z_BRANCH_FOR_VERTICAL_CONNECTOR` | A vertical connector deterministically selects a Z-shaped `GD-B` and an `ILT-Z-*` layout; incompatible L-branch output fails validation. |
| 3 | GD-B-to-GD-ST anchoring and report gate | `Q1_GCR_03_BRANCH_CONNECTOR_EAST_DEFAULT`, `Q1_GCR_05_EAST_CONNECTIONS_LABELLED`, and `Q1_GCR_11_EAST_PARAMETERS_CONNECTIONS` | Every L or Z `GD-B` terminates at `GD-ST` through the terminal association defined by its selected anchor. The plot and report expose canonical `GD-ST` parameters, active slots, pipe-side connections, and branch associations; missing items fail the gate. |
| 4 | GD-SB valve protection with real geometry | `Q1_GCR_02_VALVE_EASB_DEFAULT` and `Q1_GCR_10_EASB_SHAPE_FROM_EDES` | A protected inline valve uses actual `GD-SB` geometry, parameters, contact ownership, connectors, and associations; a generic frame cannot satisfy the rule. |
| 5 | Two-branch valve representation gap | Q1 experience; dedicated feedback/change request still required | EDPR, EDAS, builder, plotter, and report represent two branch valves as distinct components with unambiguous topology and associations, or emit a machine-readable representation gap. |

This sequence moves KEL from recording lessons to improving the executable design workflow. Item 5 must first be formalized as a dedicated feedback record and graph-change request so its exact two-valve topology and acceptance evidence are traceable before implementation.

## Proposed v0.2 Milestone

KEL v0.2 can be considered complete when:

1. `run_kel_cycle.py` has a non-dry-run integration test with fixture data.
2. Similar feedback records can be grouped into one graph change request.
3. Accepted graph change requests produce target-specific implementation plans.
4. Plot-related design answers are blocked unless the repo plotter or an
   explicit representability-gap record is produced.
5. Q1 can be rerun and the system produces framework-backed gaps rather than a
   freehand design plot.
