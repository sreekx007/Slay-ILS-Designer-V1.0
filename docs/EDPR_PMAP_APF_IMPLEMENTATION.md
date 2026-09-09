# EDPR P-map/APF Implementation

## Purpose

This document defines how EDPR should express a natural-language design request using P-map and APF concepts before retrieval and solving.

The intent is to prevent a weak parse where the LLM jumps directly from user text to candidate components without making the problem structure visible.

## Core Rule

Every normal design query should be represented as:

```text
Natural-language request
-> APF interpretation
-> P-map nodes and links
-> APF-style requirement tuples
-> EDES/EDAS/EDIKB retrieval plan
-> solver plan
```

## APF Mapping

| APF Concept | Meaning In This Framework | EDPR Location |
|---|---|---|
| Action | What the design agent must do: compare, select, configure, generate, validate, explain, or plan study | `problemIdentity.problemType`, `requirements`, `solverPlan.solverMode`, `solverPlan.steps` |
| Product | The design object: component, subassembly, assembly, standard layout, or candidate option | `pMap.artifacts`, `candidateComponents`, `candidateAssemblies`, `standardLayoutCandidates` |
| Function | What the product must achieve: support, isolate, route flow, reduce strain, protect equipment, enable installation | `pMap.functions`, `requirements`, `behaviourConcerns` |

Until the EDPR metaschema has a direct top-level `apf` object, APF is encoded through these existing fields.

## P-map Node Types

| P-map Node | Required For | Example |
|---|---|---|
| Requirement | User must/should statements, objectives, constraints, preferences | Minimize header and branch strain |
| Function | Intended purpose of the design | Provide branch connection from header pipe |
| Artifact | Physical product or option being considered | `edes:GD-B`, `edes:GD-ST`, `ILS-ILT` |
| Behaviour | Response to be predicted, compared, or controlled | Peak nominal strain in branch pipe |
| Issue | Missing input, ambiguity, tradeoff, uncertainty, evidence limitation | Top-frame connection system unspecified |

## P-map Links

P-map links should explain why retrieval and solving are needed.

Minimum useful links for design problems:

| Link Type | Meaning |
|---|---|
| `requires_artifact` | Requirement needs a component, assembly, or layout |
| `requires_function` | Requirement depends on a function being achieved |
| `drives_behaviour_check` | Requirement creates a response/evaluation concern |
| `has_issue` | Requirement/artifact/behaviour has missing data or ambiguity |
| `maps_to_evaluation_variable` | Behaviour links to a measurable quantity |
| `maps_to_retrieval_target` | P-map node identifies EDES/EDAS/EDIKB context to retrieve |

## APF Requirement Tuple

EDPR uses APF-style requirement tuples:

```text
r = (Z, M, C)
```

| Tuple Item | Meaning | Example |
|---|---|---|
| `Z` | Zone, domain, option set, condition, or evaluation region | L-shaped ILT candidate layouts |
| `M` | Metric, response, feature, or validity measure | Peak nominal strain in header pipeline |
| `C` | Constraint, comparison, objective, preference, or verification condition | Minimize / rank lower values better |

## Implementation In The Pipeline

The EDPR parser must populate:

- `pMap.requirements`
- `pMap.functions`
- `pMap.artifacts`
- `pMap.behaviours`
- `pMap.issues` where relevant
- `pMap.links`
- `requirementFormalization`
- `retrievalPlan`
- `numericComparisonPlan` when comparison or ranking is requested
- `interactionEffectPlan` when component interactions may matter

The checker script `tools/check_pmap_apf.py` verifies that the EDPR object is not merely schema-valid, but also structurally useful.

## Practical Interpretation

For a query such as:

```text
ILT layout. Branch is L-shaped with horizontal connector. Branch can be fixed to the top frame or free to slide. Give the solution that minimizes strains on header and branch lines.
```

The EDPR parser should express:

| Layer | Expected Interpretation |
|---|---|
| Action | Compare and select |
| Product | ILT branch layout options |
| Function | Provide branch connection while controlling installation strain |
| Behaviours | Header strain and branch strain |
| Issue | Top-frame connection system and evidence applicability |
| Numeric Plan | Retrieve Paper 2 branch layout rows |
| Interaction Plan | Use direct combined layout evidence before isolated superposition |

## Why This Matters

P-map/APF improves:

- traceability from user request to ontology retrieval
- retrieval quality
- consistency of LLM reasoning
- later Knowloop feedback classification
- paper-ready explanation of the design framework

It also makes failures more diagnosable. If a design answer is weak, we can locate the failure at APF interpretation, P-map construction, retrieval, numeric ranking, or solver judgement.
