# KEL - Knowledge Evolution Loop

KEL is the closed-loop knowledge evolution layer for Slay-ILS-Designer.

It records each design interaction as an engineering experience, captures querier feedback, evaluates whether the current EDPR/EDES/EDAS/EDIKB knowledge was sufficient, and proposes expert-reviewed updates to the official knowledge system.

## Position In The Framework

```text
KnowLoop = front-end conceptual design support and feedback candidate capture
KEL = full closed-loop knowledge evolution governance
```

KEL does not replace KnowLoop. It extends the feedback idea into a traceable lifecycle:

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
| Experience record | Captures the full design-query experience and trace |
| Feedback-to-P-map/APF record | Converts natural-language feedback into structured issue/action form |
| Graph change request | Proposes a specific update to a target framework layer |
| Expert review record | Records accept/reject/needs-evidence decisions |

## Folder Structure

```text
knowledge/kel/
  KEL_LLM_WORKFLOW_INSTRUCTIONS.md
  KEL_V0_2_RECOMMENDATIONS.md
  schemas/
  templates/
  experience_records/
  feedback_records/
  graph_change_requests/
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
| KnowLoop | Provides earlier feedback-candidate pattern and human-review policy |
| Plotters | Provide design pictures attached to experience records |
