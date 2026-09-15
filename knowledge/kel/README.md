# KEL - Knowledge Evolution Loop

KEL is the closed-loop knowledge evolution layer for Slay-ILS-Designer.

It records each design interaction as an engineering experience, captures querier feedback, evaluates whether the current EDPR/EDES/EDAS/EDIKB knowledge was sufficient, and proposes expert-reviewed updates to the official knowledge system.

## Position In The Framework

```text
KnowLoop = legacy/front-end feedback candidate capture
KEL = active closed-loop knowledge evolution governance
```

KEL supersedes KnowLoop for governed learning and graph evolution. KnowLoop can still exist as a legacy evidence-candidate export, but KEL owns the traceable lifecycle:

```text
query -> EDPR/P-map/APF -> retrieval -> solution -> plot -> experience record
      -> querier feedback -> graph change request -> expert review -> promotion
```

## Core Rule

Generated KEL records are not official knowledge.

Only expert-accepted and implemented KEL change requests may update EDPR, EDES, EDAS, EDIKB, datasets, tools, plotters, or documentation.

## Primary Artifacts

| Artifact | Purpose |
|---|---|
| LLM workflow instructions | Defines how an LLM must run EDPR/retrieval/layout/plot/KEL gates before answering a design query |
| KEL v0.2 implementation plan | Defines the ordered code, schema, migration, test, and acceptance work for the Q1-driven v0.2 release |
| KEL implementation update log | Brief machine-style closeout notes for implemented KEL batches |
| KEL root-cause error log | Reviews why KEL-triggering errors occurred and separates workflow failures from EDIKB data gaps |
| Atomic feedback record | Stores one issue with its source span, classification, target, fingerprint, and original feedback link |
| Feedback group | Groups exact or topic-equivalent atomic issues while preserving every member and source ID |
| Lifecycle reconciliation report | Identifies one authoritative state per change-request ID and records supersession actions or conflicts |
| Design workflow gate | Enforces vertical-connector, EA-ST exposure, EA-SB valve-protection, and unresolved-topology behavior across EDPR, solver, EDAS, and plotter reports |
| Implementation plan | Turns an expert-accepted change into a target-layer checklist with evidence, paths, tests, review, and completion fields |
| Status summary | Counts v0.2 atomic/groups and lifecycle states, and reports authoritative conflicts |
| Experience record | Captures the full design-query experience and trace |
| Feedback-to-P-map/APF record | Converts natural-language feedback into structured issue/action form |
| Graph change request | Proposes a specific update to a target framework layer |
| Expert review record | Records accept/reject/needs-evidence decisions |

## Folder Structure

```text
knowledge/kel/
  KEL_LLM_WORKFLOW_INSTRUCTIONS.md
  KEL_V0_2_IMPLEMENTATION_PLAN.md
  KEL_V0_2_DESIGN_GATES.md
  KEL_V0_2_RECOMMENDATIONS.md
  KEL_IMPLEMENTATION_UPDATE_LOG.md
  KEL_ROOT_CAUSE_ERROR_LOG.md
  schemas/
  templates/
  experience_records/
  feedback_records/
  atomic_feedback_records/
  feedback_groups/
  graph_change_requests/
  lifecycle_reports/
  implementation_plans/
  expert_reviews/
  examples/
```

## Related Layers

| Layer | Relationship |
|---|---|
| EDPR | Supplies parsed problem, P-map, APF, objectives, constraints, and evidence needs |
| EDES | Receives component-property improvement requests |
| EDAS | Receives assembly/topology/load-path improvement requests |
| EDIKB | Receives behavior-rule, evidence, uncertainty, and future-study requests |
| KnowLoop | Provides earlier feedback-candidate export pattern only; KEL is authoritative for governed updates |
| Plotters | Provide design pictures attached to experience records |
