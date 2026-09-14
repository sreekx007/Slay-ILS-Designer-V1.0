# KEL Terminology

## KEL

Knowledge Evolution Loop. A closed-loop governance layer that converts design interactions into reviewed knowledge updates.

## Experience Record

A structured record of one design-query lifecycle, including query, parse, retrieval, solution, plot, confidence, sufficiency rating, feedback, and review status.

## Querier Feedback

Natural-language feedback from the user or engineer after reviewing a proposed solution.

## Feedback-To-P-map/APF Record

A structured conversion of querier feedback into affected requirements, objectives, functions, behaviours, structures, constraints, issues, and actions.

## Knowledge Sufficiency Rating

A judgement of whether the current EDPR/EDES/EDAS/EDIKB knowledge was sufficient for the query.

Allowed values:

```text
sufficient
partially_sufficient
insufficient
unknown
```

## Graph Change Request

A proposed update to a target framework layer. It may add, revise, or flag missing knowledge.

## Expert Review

The domain-expert decision gate before any generated KEL output becomes official framework knowledge.

## Promotion

The controlled implementation of an accepted change request into EDPR, EDES, EDAS, EDIKB, datasets, tools, plotters, or documentation.


## Atomic Feedback Record

A KEL v0.2 record containing one observed issue and one requested action. It
retains the original feedback ID, linked experience, source text span,
classification confidence, affected components, target layers, and evidence.

## Feedback Fingerprint

A deterministic SHA-256 value derived from normalized target, change type,
affected components, issue, and action. Exact fingerprints are safe duplicate
candidates; different fingerprints within one topic group require review.

## Feedback Group

A de-duplicated KEL v0.2 record containing one canonical topic and every member
atomic ID, source feedback ID, experience ID, fingerprint, and evidence link.

## Lifecycle Reconciliation

The idempotent audit that ensures one change-request ID has one authoritative
status. A stale copy is moved to `superseded` with a pointer to the authoritative
record. Equal-rank conflicting states are reported and are not changed.
