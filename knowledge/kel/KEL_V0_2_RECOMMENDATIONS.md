# KEL v0.2 Recommendations

## Purpose

KEL v0.1 establishes the governance loop:

```text
experience -> sufficiency -> feedback -> graph change request
-> expert review -> promotion trace
```

KEL v0.2 should improve automation quality, reduce duplicate records, and begin
closing the gap between reviewed change requests and actual framework updates.

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

## Q1-Driven v0.2 Implementation Candidates

The Q1 ILT test should drive early v0.2 work:

| Change Request | Recommended v0.2 Action |
|---|---|
| `Q1_GCR_09_Z_BRANCH_FOR_VERTICAL_CONNECTOR` | Teach EDPR/layout selection that vertical connectors require `GD-B` variant `Z` and an `ILT-Z-*` anchor. |
| `Q1_GCR_11_EAST_PARAMETERS_CONNECTIONS` | Require plots/reports to expose `GD-ST` parameters, active connector slots, branch association, and pipe-side connection points. |
| `Q1_GCR_10_EASB_SHAPE_FROM_EDES` | Ensure EA-SB protection is represented with `GD-SB` geometry and parameters, not a generic frame sketch. |
| `Q1_GCR_02_VALVE_EASB_DEFAULT` | Add a default assumption/rule that valves cannot ride rollers or take contact loads and need explicit protection. |
| `Q1_GCR_07_STRESS_STRAIN_OBJECTIVE` | Add EDPR ranking guidance for minimizing strain/stress and marking likely peak zones without inventing FEA values. |

## Proposed v0.2 Milestone

KEL v0.2 can be considered complete when:

1. `run_kel_cycle.py` has a non-dry-run integration test with fixture data.
2. Similar feedback records can be grouped into one graph change request.
3. Accepted graph change requests produce target-specific implementation plans.
4. Plot-related design answers are blocked unless the repo plotter or an
   explicit representability-gap record is produced.
5. Q1 can be rerun and the system produces framework-backed gaps rather than a
   freehand design plot.
