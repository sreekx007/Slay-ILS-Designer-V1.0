# EDIKB Future Study Candidates

This folder stores browsable future FEA/ML/correlation study candidate records.

Use it for unresolved behavior questions that need new numeric evidence before the
workflow can claim optimized sizing, connector selection, or coupled response
prediction. These records do not update official EDIKB behavior rules by
themselves. They are a backlog for future FEA/DOE/ML work and should be promoted
only after expert review and verified dataset rows.

Relationship to other folders:

- `knowledge/kel/feedback_records/candidates/` records human feedback and workflow issues.
- `knowledge/kel/graph_change_requests/` records proposed knowledge/tool changes.
- `knowledge/edikb/EDIKB_FULL_KNOWLEDGE_GRAPH.json` contains official graph nodes, including some `MLStudyCandidate` nodes.
- This folder provides a direct, easy-to-browse study backlog for candidates from EDIKB and KEL.

Suggested fields:

```json
{
  "schema": "edikb-future-study-candidate/0.1",
  "candidate_id": "...",
  "title": "...",
  "source": "kel|edikb|manual_review",
  "status": "candidate",
  "study_type": "future_fea_study|future_ml_study|future_correlation_study|future_doe_study",
  "components": [],
  "variables": [],
  "responses": [],
  "reason": "...",
  "required_before_claim": "...",
  "linked_records": []
}
```
