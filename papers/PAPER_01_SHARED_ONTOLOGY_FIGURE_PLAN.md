# Paper 01 Shared Ontology and Figure Plan

## Purpose

Paper 01A and Paper 01B need a common, technically consistent visual foundation while presenting it at different levels. Paper 01A will use the figures to teach engineering professionals how structured data enables AI. Paper 01B will use them to teach AI researchers why domain ontology, topology constraints, and evidence scope matter in mechanical design.

## Core Visual Narrative

The opening visual sequence should be:

```text
S-lay installation context
  -> realistic ILT assembly
  -> simplified assembly schematic
  -> parameterized components and interfaces
  -> ontology nodes and relations
  -> executable knowledge and validation workflow
```

This sequence prevents the ontology from appearing as arbitrary database terminology. Every node and relation is introduced through something visible in the engineering assembly.

## Source-Paper Placeholder Map

The following figures may be cropped from the author-supplied PDFs for internal drafting. Final public figures should be redrawn or rebuilt in a consistent vector style unless reuse rights and image quality are confirmed.

| Purpose | Temporary source | Source location | Final treatment |
|---|---|---|---|
| S-lay ILT physical context | R7 Figure 4, “A Typical Inline Tee Structure and its overbend passage” | R7 source PDF page 6 | Redraw a clean vessel/stinger/ILT context diagram or use a rights-cleared image montage. |
| Representative ILT assembly | R7 Figure 7, “A Typical ILT Assembly” | R7 source PDF page 8 | Use as the realistic-view panel, then recreate labels and callouts. |
| Overall structural schematic | R8 Figure 5, “Overall Assembly - Schematic Representation” | R8 source PDF page 10 | Rebuild as vector geometry using canonical component names. |
| Top and base structure forms | R8 Figures 1–3 | R8 source PDF pages 7–8 | Redraw as matched isometric/end/side views. |
| Branch layout taxonomy | R8 Figure 15 | R8 source PDF page 16 | Recreate L and Z branch families from the repository's GD-B definitions. |
| Connector taxonomy | R8 Figure 16 and connection systems in Figures 17–18 | R8 source PDF pages 17–18 | Redraw F/S and F1/F2/PS/deadband relationships with consistent symbols. |
| Schematic abstraction examples | R8 Figure 19 | R8 source PDF page 19 | Use as a visual reference; rebuild from EDES/EDAS objects. |
| EA-ST, EA-SB, and branch parameters | R8 Figures 22–25 | R8 source PDF pages 22–23 | Recreate as publication-quality parameter diagrams tied to canonical JSON field names. |
| Mechanical behavior classes | R7 Figures 14–16 and Table II | R7 source PDF pages 10–12 | Redraw compact Type A/B/C mechanism diagrams. |
| Offset geometry and response regions | R7 Figures 44–45 | R7 source PDF page 37 | Recreate if used in the evidence/behavior explanation. |

## Planned Shared Figures

### S1. S-Lay ILT Physical Context

Show vessel firing line, stinger rollers, overbend curvature, header, inline structure, and travel direction. Paper 01A should emphasize the engineering lifecycle; Paper 01B should emphasize why geometry and contact make unconstrained generation unsafe.

### S2. Realistic Assembly to Parameterized Schematic

Four panels:

1. realistic ILT assembly;
2. simplified overall schematic;
3. separated header, branch, valve, EA-ST, EA-SB, connectors, and supports;
4. parameter labels and interfaces.

This is the main introductory ontology figure requested for both papers.

### S3. S-Lay ILT Ontology Map

Map visible objects into:

- function nodes;
- component/structure nodes;
- geometry and parameter nodes;
- assembly-feature and association nodes;
- behavior/evidence nodes;
- requirement/issue nodes.

Then show their repository ownership in EDES, EDAS, EDIKB, and EDPR. Use solid lines for asserted relationships, dashed lines for retrieved evidence, and a separate visual style for unresolved gaps.

### S4. Physical and Mechanical Classifications

Show the R7 IW/EA physical classification beside the Type A/B/C mechanical classification, with two or three representative components. Avoid reproducing the full source tables if a smaller explanatory graphic is clearer.

### S5. Connection and Branch Topology

Show F1, F2, PS, and deadband systems alongside L and Z branch families. Identify which relations are geometry, connection type, active slot, or assembly association.

### S6. Governed AI Architecture

Show human request -> EDPR -> EDES/EDAS retrieval -> EDIKB evidence -> deterministic tools -> candidate/clarification/gap -> plot/report -> KEL graph evolution -> expert review.

Paper 01A labels should use plain-language subtitles. Paper 01B may add formal graph and transition symbols.

### S7. Q1 Failure and Correction Trace

Compare the initial plausible but incomplete concept with the governed result. Annotate topology selection, missing valve-protection inputs, parameter exposure, associations, plot source, and fail-closed two-valve gap.

### S8. Evidence Provenance and Applicability

Trace one R7 claim and one R8 claim from publication -> extracted EDIKB source family -> behavior rule/numeric case -> EDPR retrieval -> output statement. Show where parameter-range and topology compatibility are checked.

## Figure Allocation by Paper

| Figure | Paper 01A | Paper 01B |
|---|---|---|
| S1 | Full, early | Compact domain primer |
| S2 | Full teaching figure | Full abstraction ladder |
| S3 | Plain-language ontology | Formal typed-graph version |
| S4 | Simplified classification | Domain-validity basis |
| S5 | Worked engineering example | Constraint and representability example |
| S6 | Plain-language workflow | Formal system architecture |
| S7 | Main case study | Experimental error analysis |
| S8 | Explain evidence management | Define provenance/evidence precision |

## Production Method

I can produce these images. The preferred workflow is deterministic rather than generative:

1. Extract temporary crops from R7 and R8 for internal layout work.
2. Rebuild geometry with the repository's ILS plotter where a canonical component or assembly exists.
3. Draw ontology, workflow, and provenance diagrams as editable SVG/PDF vector graphics.
4. Export high-resolution PNG previews for review.
5. Keep source files, captions, citation IDs, and a figure-change log in the repository.
6. Render the final paper and inspect every figure at page size before release.

Image generation may help with a nontechnical conceptual illustration, but it should not create engineering geometry, connections, or parameter diagrams. Those visuals need traceable vector construction from EDES/EDAS and the published sources.

## Repository Layout When Figure Work Starts

```text
papers/
  figures/
    shared/
      source_placeholders/
      editable/
      rendered/
    paper01a/
    paper01b/
  figure_sources.json
```

`figure_sources.json` should record figure ID, manuscript use, source publication, original figure/page, reuse status, redraw status, generator/script, and current output path.

## Acceptance Criteria

- Every engineering object and parameter matches the repository vocabulary or is explicitly marked as illustrative.
- Every reused source element has a source citation and verified reuse status.
- Text is legible at final page width.
- Color is not the only carrier of meaning.
- Schematic geometry does not imply an unsupported design conclusion.
- Paper 01A can be understood without prior KG/ML knowledge.
- Paper 01B contains enough mechanical context for an AI reviewer to evaluate topology and evidence errors.
