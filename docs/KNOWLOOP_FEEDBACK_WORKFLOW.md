# Knowloop Feedback Workflow

## Purpose

Knowloop is the feedback and learning loop for Slay-ILS-Designer.

It captures what happened after every design query, including successful answers, weak answers, failed parses, missing evidence, useful confirmations, and suggested future study candidates.

The Knowloop candidate knowledge base is exploratory. It does not directly modify EDPR, EDES, EDAS, EDIKB, standard layouts, datasets, or tools.

## Core Rule

Every design query must emit a Knowloop candidate JSON.

```text
Design query
-> EDPR parse
-> retrieval
-> solution
-> Knowloop candidate JSON
-> human/expert review
-> accepted updates promoted to official KB
```

## Why Emit Candidates For Successful Queries?

Successful queries are also useful evidence. They show:

- EDPR parsing worked
- P-map/APF representation was sufficient
- retrieval found the right context
- dataset evidence supported the recommendation
- no immediate official KB update was needed

These become confirmation candidates.

## Candidate Types

| Candidate Type | Meaning |
|---|---|
| `confirmation` | Framework worked well; no official KB update required |
| `improvement` | Output worked but some part can improve |
| `correction` | Something was wrong and should be fixed |
| `new_knowledge_candidate` | A possible new rule, parameter, assembly relation, or guidance node was identified |
| `future_study_candidate` | Needs FEA, ML, calculation, or literature evidence before promotion |
| `failure_record` | Parse, retrieval, validation, or solve failed |

## Status Flow

| Status | Meaning |
|---|---|
| `generated` | LLM/tool emitted candidate after a query |
| `human_reviewed` | User/engineer gave a rating or comment |
| `needs_evidence` | Interesting but requires FEA/ML/literature support |
| `expert_accepted` | Domain expert approved the candidate |
| `expert_rejected` | Domain expert rejected it |
| `implemented` | Accepted update has been applied to official KB |
| `superseded` | Replaced by later/better candidate |

## Review Roles

| Review Layer | Actor | Purpose |
|---|---|---|
| LLM self-rating | LLM/tool | Initial quality judgement and trace notes |
| Human feedback rating | User/engineer | Practical quality rating after reading the answer |
| Expert review decision | Domain expert | Decide whether official KB should change |

## Promotion Policy

Official KB update is allowed only after expert acceptance.

| Candidate Target | Official Target |
|---|---|
| Wrong parse / missing P-map/APF | EDPR prompt, EDPR schema, EDPR examples |
| Missing component information | EDES |
| Missing assembly logic | EDAS |
| Missing behavior rule | EDIKB graph |
| Missing numeric evidence | EDIKB dataset or FEA/ML study queue |
| Missing layout archetype | Standard layouts |
| Tool failure | Runtime tools |
| Explanation/crosswalk gap | Docs |

## Folder Structure

```text
knowledge/knowloop/
  KNOWLOOP_FEEDBACK_SCHEMA.json
  templates/
    KL_CANDIDATE_TEMPLATE.json
  candidates/
    KL_CANDIDATE_<query_id>.json
  accepted/
    KL_ACCEPTED_<query_id>.json
  rejected/
    KL_REJECTED_<query_id>.json
  review_log/
    KNOWLOOP_REVIEW_LOG.md
```

## How To Use In Runtime

After each design query, run:

```bash
python tools/generate_knowloop_candidate.py \
  --edpr-json runs/test/problem.edpr.json \
  --context-json runs/test/problem.retrieval_context.json \
  --solution-json runs/test/problem.solution.json \
  --output knowledge/knowloop/candidates/KL_CANDIDATE_test.json
```

If the solution is Markdown only, pass it using `--solution-md`.

The pipeline runner should emit Knowloop candidates automatically when possible.

## Human Feedback Fields

The generated candidate contains:

```json
"human_feedback_rating": {
  "rating": null,
  "scale": "1_to_5",
  "comment": null,
  "reviewer": null,
  "reviewed_utc": null
}
```

The user or expert can fill this later.

## Practical Learning Use

Knowloop is also useful for skill development. It creates a record of:

- which queries the framework handles well
- where EDPR parsing fails
- where EDIKB evidence is insufficient
- which feature interactions need future FEA/ML
- which design rules repeatedly prove useful

This makes the framework grow through controlled engineering learning rather than uncontrolled prompt drift.
