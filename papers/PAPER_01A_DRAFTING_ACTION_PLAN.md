# Paper 01A Drafting Action Plan

## Audience and Publication Route

**Primary audience:** practicing structural, mechanical, subsea, and pipeline engineers who have little or no formal background in data science, machine learning, knowledge graphs, or LLM systems.

**Planned repository:** engrXiv.

**Reader outcome:** an engineering professional should understand why useful engineering AI begins with disciplined data representation, how an ontology turns familiar design objects into reusable knowledge, how the LLM fits into that system, and where human engineering review remains mandatory.

The writing should introduce every AI term through an engineering example before using the formal term. Mathematical AI detail should be limited to what is needed to explain traceability, retrieval, evidence scope, and governance.

## Working Thesis

Industrial AI for conceptual engineering is primarily a data and knowledge-management problem. Historical drawings, calculations, reports, analysis results, and expert corrections become useful to an AI assistant only after components, assemblies, parameters, relationships, behavior evidence, assumptions, and limitations are represented consistently. Slay-ILS-Designer demonstrates this approach for S-lay subsea inline structures.

## Research Questions

1. How can fragmented engineering information be converted into a reusable and reviewable design-knowledge system?
2. How do component, assembly, behavior, and problem ontologies improve retrieval and conceptual-design reasoning?
3. What work should be performed by the LLM, and what work should remain with deterministic tools and engineers?
4. How can design-review feedback improve the knowledge system without automatically contaminating approved engineering knowledge?

## Planned Contributions

| Contribution | Paper 01A treatment |
|---|---|
| S-lay ILT ontology introduction | Explain the ontology through recognizable components, assembly drawings, parameters, interfaces, and strain behavior from R7 and R8. |
| Engineering data-management model | Show how documents and tacit experience become governed EDES, EDAS, EDIKB, and EDPR records. |
| Accessible AI workflow | Explain ontology, knowledge graph, retrieval, LLM, validation gate, and feedback loop in engineering language. |
| Repository-backed case study | Demonstrate the Q1 ILT request, the initial failure modes, the corrected workflow, and the fail-closed boundary. |
| Human-governed learning | Explain KEL as the controlled evolutionary loop for graph change. |

## Opening Ontology Sequence

The ontology must appear near the beginning, immediately after the engineering problem is introduced. Add one notation statement explaining that R7/R8 use EA-ST and EA-SB while the manuscripts normalize these terms to GD-ST and GD-SB without changing the underlying concepts.

### Step 1: Show the physical design object

Use a temporary snapshot from R7 Figure 4 or Figure 7 to show that an ILT is a complete assembly moving through the S-lay overbend, rather than a single pipe fitting.

### Step 2: Reduce the realistic assembly to a schematic

Use R8 Figure 5 as the temporary overall-assembly schematic, supported by R8 Figures 1–3 for the top structure, base structure, and their relationship to the header pipeline.

### Step 3: Expose design parameters and interfaces

Use R8 Figures 22–25 to introduce the GD-ST, GD-SB, Z-branch, and L-branch parameter sets. Use R8 Figures 16–18 when explaining connector and connection-system representation.

### Step 4: Convert the schematic into ontology records

Create a new vector figure that maps:

```text
real assembly
  -> component objects and parameters
  -> connection and association records
  -> behavior/evidence records
  -> current design-problem record
```

Use the repository terms EDES, EDAS, EDIKB, and EDPR only after the reader understands this physical-to-data transformation.

### Step 5: Link ontology to the two published domain papers

State that R7 supplies the physical IW/EA classification, Type A/B/C mechanical classification, and isolated-component behavior basis. State that R8 extends the ontology and behavior basis to GD-ST, GD-SB, connection systems, and branch assemblies. Quantitative statements must retain table/figure/case and applicability limits through `EDIKB_SOURCE_PROVENANCE.json`.

## Section-by-Section Draft Plan

| Section | Main purpose | Required evidence or visual |
|---|---|---|
| Abstract | Present the engineering knowledge-management problem, framework, case study, and bounded contribution in plain language. | Finalized after all results are frozen. |
| 1. Introduction | Explain why experienced engineering organizations still struggle to reuse design knowledge. Define the problem without assuming AI expertise. | Examples of reports, drawings, calculations, and tacit review knowledge. |
| 2. S-Lay ILTs and Their Ontology | Introduce the physical assembly, installation challenge, component/assembly classifications, realistic-to-schematic mapping, parameters, and connections. | Shared Figures S1–S4; R7 and R8. |
| 3. Why Engineering AI Starts With Data Management | Explain identifiers, controlled terms, parameters, relationships, evidence, provenance, versioning, and missing-data handling. | Before/after example: document fragment versus structured record. |
| 4. Knowledge Architecture | Explain EDES, EDAS, EDIKB, EDPR, and KEL using an engineering document-control analogy. | Layer diagram and one traceable design fact. |
| 5. Role of the LLM and Deterministic Tools | Separate language interpretation and explanation from validation, retrieval, layout construction, plotting, and tests. | Workflow diagram with human review points. |
| 6. Case Study: Q1 ILT Layout | Walk through request, problem interpretation, the generalized L/Z branch-to-GD-ST gate, orientation selection, retrieval, layout selection, plot, feedback, KEL changes, and current topology gap. | Q1 evidence package and repository-generated plots. |
| 7. Evaluation | Report whether the governed workflow exposes parameters, connections, assumptions, evidence, and representation gaps more reliably than an unconstrained response. | Completeness and traceability matrix. |
| 8. Organizational Application | Explain adoption: source inventory, ontology ownership, review roles, change control, and integration with existing engineering systems. | Practical implementation checklist. |
| 9. Limits and Future Development | Bound the prototype and explain the path to parametric FEA, surrogate models, uncertainty estimation, and optimization. | Evidence-coverage gap diagram. |
| 10. Conclusions | Restate the practical value for engineering knowledge reuse and controlled AI assistance. | No new claims. |

## Evaluation Package

Paper 01A should emphasize inspectable engineering outcomes rather than an AI leaderboard.

| Measure | Planned test |
|---|---|
| Problem completeness | Does EDPR expose objectives, constraints, missing inputs, and unrequested assumptions? |
| Topology validity | Does the selected layout comply with EDAS orientation and assembly rules? |
| Parameter visibility | Are geometry and connector parameters exposed in the report and plot? |
| Evidence traceability | Can each recommendation be traced to an EDIKB source family, case, and limitation? |
| Fail-closed behavior | Does the workflow stop and report a representation/evidence gap instead of inventing a layout? |
| Feedback governance | Can a correction be traced through atomic feedback, graph-change request, expert review, and implementation? |

## Writing Rules

- Define ontology as a controlled engineering description of objects, properties, relationships, and permitted meanings.
- Explain knowledge graphs as linked engineering records, not as an abstract AI technology.
- Introduce acronyms once and reinforce them with the same physical example.
- Prefer one worked trace from design request to plotted layout over many shallow examples.
- Keep equations to established engineering quantities or a small number of workflow definitions.
- Mark every claim as repo-demonstrated, literature-supported, domain-expert assertion, or future work during drafting.

## engrXiv Preparation

Checked 2026-09-14 against the official submission pages:

- Prepare a polished PDF; engrXiv also supports Word and OpenOffice, but PDF is preferred.
- Include an AI-assistance statement that identifies drafting and editing support, with the authors retaining responsibility for source verification, technical judgments, and final wording.
- Confirm the right to reuse or redraw every source-paper figure before public submission.
- Treat the public version as permanent and complete a final author and technical review before upload.
- Prepare title, abstract, keywords, author metadata, ORCID information, repository/code link, and a version note.
- Record the engrXiv DOI in the repository after posting.

Official checks: [engrXiv submissions](https://engrxiv.org/about/submissions), [engrXiv AI policy](https://engrxiv.org/ai-policy), and [engrXiv FAQ](https://engrxiv.org/faq).

## Execution Order

1. Freeze the contribution and audience boundary against Paper 01B.
2. Build the R7/R8 claim-to-evidence matrix.
3. Produce temporary source-paper crops and the first shared ontology figure.
4. Draft Sections 1 and 2 and review them as an engineering reader with no AI background.
5. Draft Sections 3–5 around one continuous data trace.
6. Curate the Q1 case-study evidence package and draft Sections 6 and 7.
7. Draft organizational application, limitations, and conclusions.
8. Perform technical, citation, accessibility, and non-specialist comprehension reviews.
9. Build the final PDF and engrXiv submission package.

## Definition of Draft-Ready

Paper 01A may enter full prose drafting when the contribution matrix, R7/R8 evidence matrix, shared ontology figure storyboard, Q1 case-study artifact list, and remaining-reference search list have been reviewed.
