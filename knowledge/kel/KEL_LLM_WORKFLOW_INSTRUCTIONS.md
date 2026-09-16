# KEL LLM Workflow Instructions

## Purpose

These instructions are for an LLM that receives a subsea ILS design query and
must use the Slay-ILS-Designer framework rather than answering from general
intuition.

The LLM must treat a design query as a governed workflow:

```text
query -> EDPR/P-map/APF -> retrieval -> EDAS layout JSON -> builder checks
      -> plotter output if requested -> KEL experience and sufficiency record
```

## Entry Point

Use `framework_manifest.json` as the repository discovery map.

It is not the full operating prompt. After reading the manifest, load the
workflow instructions and layer knowledge referenced by the task:

| Need | Read / Use |
|---|---|
| Parse a natural-language design query | `knowledge/edpr/EDPR_PARSER_PROMPT_RUNTIME.md` |
| Emit a buildable layout | `knowledge/edas/EDAS_SHARED_KNOWLEDGE.json` |
| Choose component parameters and constraints | Relevant `knowledge/edes/EDES_GD-*.json` files |
| Use standard layout precedent | `knowledge/edas/standard_ils_layouts.json` |
| Retrieve behavior evidence | `knowledge/edikb/EDIKB_FULL_KNOWLEDGE_GRAPH.json` and dataset |
| Create or validate plots | `plotters/README.md`, `tools/plot_design.py`, `plotters/ils_builder.py` |
| Capture experience and feedback | `knowledge/kel/KEL_WORKFLOW.md` and KEL schemas |

## Non-Negotiable Gate

Do not jump directly from user prose to a freehand solution or custom plot.

For a design query, the LLM must first create or obtain an EDPR/P-map/APF
representation, retrieve the relevant EDES/EDAS/EDIKB knowledge, and determine
whether the requested layout can be represented by the current schemas and
plotter.

If the requested design cannot be represented, say so explicitly and create a
KEL gap or feedback record. Do not hide the gap by sketching geometry outside
the model.

## Plotting Policy

When the user requests a layout plot:

1. Emit or select a valid EDAS layout JSON.
2. Build it with `plotters/ils_builder.py` or the approved CLI wrapper.
3. Read builder findings and repair the layout when possible.
4. Plot from the built object using the repository plotter.
5. Report warnings, missing parameters, simplified connector modelling, and
   unsupported requested features.

A custom sketch is allowed only as a clearly labelled non-authoritative concept
view when no framework-backed plot can be produced. It must not be presented as
the proposed engineering layout.

## Q1 Lesson Captured

The Q1 ILT test exposed a workflow failure:

- A custom conceptual plot was produced without using the repository ILS plotter.
- The branch was drawn as a simple vertical branch, but a vertical connector
  requires a `GD-B` Z-branch.
- `EA-SB` and `EA-ST` were sketched generically instead of using EDES/EDAS
  geometry and parameters.
- Connections and connector slots were not represented through the buildable
  layout model.

Correct behavior:

- Use EDPR/P-map/APF first.
- Retrieve `GD-VLV`, `GD-B`, `GD-ST`, `GD-SB`, `GD-Con`, and relevant EDAS
  branch/connector rules.
- Use the EDAS standard `ILT-Z-*` anchors when a vertical connector is requested.
- When `GD-SB` protects `GD-VLV`, and when `GD-ST` supports `GD-B`, size the structure from the protected/supported component envelope and clearance basis instead of leaving EDAS defaults in place.
- When `GD-VLV` is paired with `GD-SH`, treat it as a stiff inline component inside a shroud and retrieve the analogous `ILS-SHTP` / C1 EDIKB evidence before choosing valve position or shroud length. Flag `EDIKB_USEFULNESS_JUDGEMENT_FAILURE` if those useful nodes are missed.
- After retrieving C1 shroud-plus-stiff-body evidence, apply it in the layout basis. State evidence refs, shroud `V/L1/L2` basis, valve/stiff-body position basis, region mapping, and applicability limits; otherwise mark `SHROUD_STIFF_EVIDENCE_NOT_APPLIED`.
- When a branch valve is present, use a compatible `ILT-L-*` or `ILT-Z-*` standard anchor. Keep the branch tee/entry, branch valve, and branch end inside `GD-ST`; do not choose `F2`/`F2D` by default unless the design basis states strain/moment evidence for the branch pocket and header penalty.
- Use the repository plotter when plotting.
- Record any unsupported hybrid requirement as a KEL gap.

## Required Output Discipline

Every design response should include:

| Output | Rule |
|---|---|
| Text overview | Give a compact text-based layout illustration first. |
| Connections | State type, location, and count. Distinguish piping from support/structural connections. |
| Assumptions | State default assumptions and unresolved inputs. |
| Stress/strain | Prefer layouts minimizing strain/stress and mark likely peak locations; do not invent FEA values. |
| Support sizing | If a support/protection structure is added, state the supported component envelope and the explicit GD-ST/GD-SB dimensions used. |
| Shroud + stiff component | If GD-SH is combined with GD-VLV, GD-TP, or GD-TT, retrieve C1 shroud-plus-stiff-body EDIKB evidence and state applicability limits before recommending placement or length. Layouts must show how evidence was applied or be marked evidence-not-applied. |
| Branch valve + GD-ST | For branch-owned valves, state selected ILT-L/ILT-Z anchor, connection system basis, GD-ST span, and tee/valve/end containment. F2/F2D needs explicit evidence; otherwise prefer PS. |
| Plot | Ask whether the user wants a plot unless the user directly requests one. If plotting, use the repository plotter when possible, declare any strain-watch labels through model-anchored `plot_annotations`, and ask the user for feedback after the plot is shown. |
| Confidence | State confidence and knowledge sufficiency. |
| KEL trace | Record feedback, gaps, and expert-review candidates when the interaction reveals missing knowledge or tooling. |
## Plot annotation and feedback rule

When a plot includes likely high-strain or transition watch locations, the LLM must not place arrows by image-pixel judgement. It must declare `plot_annotations` in the layout JSON and anchor each pointer to a model coordinate, preferably a component feature resolved by the builder, for example `{"component": "B", "feature": "tee"}` or `{"component": "ST", "feature": "right1"}`. The plot report must show `plot_annotation_anchors = passed`; otherwise the plot is not acceptable for review.

After every plotted layout, the LLM must ask the human user for feedback. The feedback request should explicitly ask whether component placement, connection-type labels, and strain-watch pointer locations are acceptable.

Connector component labels are not required. The required plot labels are connection-type labels for non-weld GD-ST/GD-SB structural connections, such as `F`, `P`, `S`, or `D`. `W` weld connections remain unlabelled.

## Q9 plot semantic-symbol rule

For ILT plots, do not let analysis artifacts replace engineering symbols. Branch valves shall be drawn with a valve-body symbol even when represented internally as a `GD-B` point mass. Branch connector hardware shall be represented by the connection/support symbol, not by a mass star or tonnage label. Non-weld `GD-ST`/`GD-SB` connection labels (`F`, `P`, `S`, `D`) must be visibly labelled at the structure-side connection. Suppress unnecessary circular pipe-side connector node symbols. Anchor `GD-ST` labels to the top edge. Draw tee junctions as regular nodes. If the query asks for likely max strain or strain location, include a model-anchored `strain_watch` plot annotation before presenting the plot.

## Inline valve with GD-SB base check

When a header inline component such as GD-VLV is protected by GD-SB because it cannot contact or ride stinger rollers, the agent must not use generic EDAS base defaults as final layout dimensions. It must size GD-SB from the protected component envelope plus limited clearance, explicitly check the elevation/connector arm against EDIKB evidence that larger vertical offsets increase strain, and expose the basis in the design record. If the base is much lower than needed, the layout is not ready for review.

For complete or paper-test plots, GD-SB/GD-ST connectors must be explicit GD-Con objects with pipe-side landing on GD-TP or another valid connector host. Do not connect a support connector directly to a GD-VLV end node or plain header pipe. If the user requests peak strain on the pipeline, place the strain marker on the pipeline near the connector/load-transfer station; if the exact station is uncertain, label it as probable/uncertain rather than anchoring to a support corner.

