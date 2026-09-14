# Paper 01B Drafting Action Plan

## Audience and Publication Route

**Primary audience:** AI, knowledge-representation, neuro-symbolic systems, LLM-agent, and engineering-informatics researchers who understand AI methods but may not understand S-lay installation or subsea structural-assembly design.

**Planned repository:** arXiv.

**Reader outcome:** an AI researcher should understand the physical validity problem, the formal separation of problem/component/assembly/evidence knowledge, the role of deterministic design gates, the human-governed update lifecycle, and the experimental evidence needed to assess the architecture.

## Working Thesis

An LLM can support safety-relevant conceptual engineering only when natural-language reasoning is constrained by explicit problem, component, assembly, and evidence representations; deterministic tools enforce representability and validation; and expert review governs persistent knowledge changes. Slay-ILS-Designer is a domain-grounded prototype of this governed neuro-symbolic architecture.

## Research Questions

1. Does layered symbolic representation reduce invalid or unsupported engineering outputs relative to unguided and retrieval-only LLM workflows?
2. Which knowledge layers and deterministic gates contribute to topology validity, parameter completeness, evidence traceability, and calibrated refusal?
3. Can natural-language expert feedback be decomposed and grouped into reviewable knowledge-change proposals without losing provenance?
4. How should an AI system represent cases where the domain knowledge or assembly language is insufficient?
5. Which aspects of the architecture are domain-specific, and which can generalize to other assembly-intensive engineering problems?

## Planned Contributions

| Contribution | Paper 01B treatment |
|---|---|
| Layered symbolic model | Define EDPR, EDES, EDAS, EDIKB, and KEL as distinct graphs/record families with controlled interfaces. |
| Domain-grounded ontology | Formalize the mapping from S-lay ILT geometry and behavior into component, assembly, parameter, connection, and evidence nodes. |
| Tool-backed reasoning architecture | Specify how parsing, retrieval, validation, solving, materialization, plotting, and QA interact. |
| Governed feedback lifecycle | Describe atomic feedback, grouping/de-duplication, graph-change requests, expert decisions, implementation plans, and promotion. |
| Fail-closed semantics | Treat missing topology or evidence as a machine-readable system outcome rather than a generative prompt failure. |
| Comparative evaluation | Compare unguided, retrieval-only, ontology-constrained, and full governed workflows with reproducible prompts and artifacts. |

## Opening Domain and Ontology Sequence

Paper 01B should introduce the ontology early, but its purpose is to make the AI problem formally understandable.

### Step 1: Give the minimum mechanical context

Use a temporary R7 Figure 4 or Figure 7 snapshot to explain the S-lay overbend, the header/branch/valve/frame assembly, and why geometry, stiffness, elevation, contact, and connection location affect behavior.

### Step 2: Show abstraction levels

Use R8 Figure 5 for the assembly schematic and R8 Figures 22–25 for parameterized component and branch representations. Present this as an abstraction ladder:

```text
physical asset -> geometric schematic -> parameterized object -> typed graph -> executable design gate
```

### Step 3: Define ontology entities and relations

Introduce FBS/OAM concepts, then define the repository mapping:

- EDES: component identity, geometry, parameters, functions, interfaces, and local constraints;
- EDAS: valid assembly topology, associations, anchors, connection rules, and materialization contracts;
- EDIKB: behavior rules, numeric evidence, applicability, uncertainty, and provenance;
- EDPR: query-specific objectives, constraints, artifacts, behaviors, issues, and tool plan;
- KEL: reviewable state transitions for persistent knowledge evolution.

### Step 4: Anchor domain validity in R7 and R8

Use R7 for the IW/EA and Type A/B/C basis and R8 for external structures, connector systems, and branch assemblies. The ontology figure must distinguish domain facts from repository design decisions and from future hypotheses.

## Section-by-Section Draft Plan

| Section | Main purpose | Required evidence or formal content |
|---|---|---|
| Abstract | State the architecture, domain, experimental comparison, and bounded findings. | Complete after evaluation. |
| 1. Introduction | Motivate governed AI for engineering design and define the research gap beyond generic RAG. | Clear contribution list and research questions. |
| 2. S-Lay ILT Domain and Ontology | Teach enough mechanics to understand invalid topology, missing parameters, evidence scope, and failure consequences. | Shared Figures S1–S5; R7 and R8. |
| 3. Related Work | Position against engineering KGs, FBS/OAM, P-map/APF, neuro-symbolic systems, tool-using LLMs, human-in-the-loop learning, and automated problem formulation. | Completed literature matrix. |
| 4. Formal Knowledge Model | Define graph/record types, identifiers, constraints, provenance, and cross-layer interfaces. | Notation table and schema excerpts. |
| 5. Governed Reasoning Pipeline | Specify parse, retrieve, validate, solve, materialize, plot, inspect, and emit stages. | Algorithm/pseudocode and state diagram. |
| 6. Knowledge Evolution Loop | Formalize feedback decomposition, fingerprints, grouping, change requests, expert review, implementation, and reconciliation. | KEL schemas and lifecycle example. |
| 7. Experimental Design | Define tasks, baselines, ablations, metrics, prompt controls, and artifact capture. | Reproducible benchmark package. |
| 8. Results | Report validity, completeness, evidence traceability, refusal/gap quality, and feedback-processing results. | Tables with confidence intervals where repeated sampling is used. |
| 9. Case Analysis | Explain Q1 successes and failures in mechanical terms for AI readers. | Side-by-side outputs and trace paths. |
| 10. Discussion | Interpret generalizability, governance tradeoffs, symbolic maintenance cost, and the limits of deterministic gating. | Cross-domain implications. |
| 11. Limitations and Future Work | Bound current parser, dataset, evaluation size, expert review, FEA validation, and ML claims. | Explicit threat-to-validity table. |
| 12. Conclusion | State what the architecture demonstrates and what remains unproven. | No new claims. |

## Formalization Work

Before prose drafting of Sections 4–6, define:

1. Problem instance graph or record set (G_P) for EDPR.
2. Component knowledge graph (G_E) for EDES.
3. Assembly/topology graph (G_A) for EDAS.
4. Evidence and behavior graph (G_K) for EDIKB.
5. Tool transition function from validated EDPR and retrieved subgraphs to a candidate, gap, or clarification outcome.
6. KEL state transition from experience through feedback, review, implementation, and promotion.
7. Provenance relation linking output claims to repository artifacts and publication evidence.

Notation should remain compact and correspond directly to existing JSON schemas and executable tools.

## Experimental Plan

### Baselines

| Mode | Available capability |
|---|---|
| B0: Unguided LLM | Prompt and general language reasoning only. |
| B1: Retrieval-only | Prompt plus retrieved repository text, without enforced schemas or design gates. |
| B2: Ontology-constrained | EDPR/EDES/EDAS/EDIKB structure and validation, without the full KEL feedback lifecycle. |
| B3: Governed workflow | Full repository pipeline, plot/report gates, fail-closed outcomes, and KEL capture. |

### Benchmark task families

- Valid standard layouts with adequate inputs.
- Ambiguous connector orientation requiring clarification or deterministic topology selection.
- Missing EA-ST or EA-SB parameters.
- Unsupported valve-protection assumptions.
- Evidence-scope mismatch between component and assembly behavior.
- Two-branch-valve representation gap.
- Plot/report completeness and association exposure.
- Repeated or semantically duplicate expert feedback.

### Metrics

| Metric | Definition direction |
|---|---|
| Topology validity | Fraction satisfying EDAS rules and component-interface constraints. |
| Requirement fidelity | Fraction of explicit objectives/constraints preserved without invented objectives. |
| Parameter completeness | Required parameters exposed or explicitly reported missing. |
| Association completeness | Required component-to-structure and connector relations reported and plotted. |
| Evidence precision | Claims supported by compatible EDIKB evidence rather than keyword proximity alone. |
| Traceability coverage | Output claims linked to problem, knowledge, tool, and source evidence. |
| Calibrated gap behavior | Unsupported cases correctly emitted as clarification/evidence/representation gaps. |
| Feedback retention | Source issues preserved after atomic decomposition and grouping. |

### Ablations

- Remove EDAS topology gates.
- Remove EDIKB applicability filtering.
- Remove plot/report completeness checks.
- Remove fail-closed representation-gap handling.
- Remove feedback grouping and lifecycle reconciliation.

The final experiment design must prevent prompt, model, sampling, and reviewer differences from being confused with architecture effects.

## arXiv Preparation

Checked 2026-09-14 against official arXiv guidance:

- Provisional primary category: **cs.AI**, because the intended contribution concerns knowledge representation, expert systems, planning, and uncertainty-aware governed behavior.
- Consider **cs.CE** as a cross-list if the final paper contains a substantial computational-engineering and simulation connection. Consider **cs.SE** only if the evaluation makes the software/toolchain contribution central.
- Do not select cs.LG unless the final paper contributes or rigorously evaluates a learning method; future surrogate-model plans alone are insufficient.
- Maintain a clean LaTeX source package with all figures, bibliography files, and required local macros. arXiv prefers TeX/LaTeX and requires submitted figures to be included.
- Use portable file names without spaces and verify the arXiv-compiled PDF.
- Check author registration and possible category endorsement early.
- Prepare title, abstract, comments, category, cross-list, author metadata, ORCIDs, license choice, and repository link.

Official checks: [arXiv submission guidelines](https://info.arxiv.org/help/submit/index.html), [TeX submissions](https://info.arxiv.org/help/submit_tex.html), [category taxonomy](https://arxiv.org/category_taxonomy), and [endorsement](https://info.arxiv.org/help/endorsement.html).

## Execution Order

1. Freeze the research claims and contribution boundary against Paper 01A.
2. Complete the AI related-work matrix and R7/R8 domain evidence matrix.
3. Define the formal graph, transition, gap, and provenance notation from current schemas.
4. Produce the shared domain-to-ontology figures and an AI-oriented architecture diagram.
5. Expand the benchmark from Q1 into the planned task families.
6. Freeze baselines, prompts, model settings, review rubric, and metric definitions.
7. Run the comparative evaluation and ablations; preserve raw outputs and scripts.
8. Draft Sections 2 and 4–7 from the frozen technical artifacts.
9. Draft introduction, related work, results, discussion, and limitations.
10. Conduct AI-method, mechanical-domain, reproducibility, and arXiv-build reviews.

## Definition of Draft-Ready

Paper 01B may enter full prose drafting when the contribution matrix, formal notation, related-work matrix, benchmark specification, R7/R8 evidence matrix, figure storyboard, and reproducibility package structure have been reviewed.
