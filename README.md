# Slay-ILS-Designer

**Ontology-grounded, RAG-enabled expert design framework for subsea inline structures (ILS).**

Slay-ILS-Designer turns a natural-language design request about a subsea pipeline inline
structure — a branch/tee, an inline valve, a thick-wall section, a tapered transition, a
guide shroud, an external top or base structure — into a **traceable, evidence-cited
design recommendation**. It does this by forcing every request through a fixed pipeline
that makes the problem structure explicit *before* any retrieval or solving happens, grounds
the reasoning in a curated engineering knowledge base, and records a feedback candidate
after every run.

It is a **neuro-symbolic / compound AI system**: a curated symbolic knowledge base
(ontology + typed behaviour rules + numeric evidence) with LLM stages for parsing and
reasoning, wired together by an orchestrator with schema validators, a retriever, a
first-pass numeric solver, and a human-in-the-loop feedback loop.

---

## The five knowledge layers

| Layer | Name | Role |
|---|---|---|
| **EDPR** | Engineering Design **Problem** Representation | Converts the NL request into an APF / P-map JSON: objectives, constraints, candidate solution families, retrieval plan, evidence requirements. |
| **EDES** | Engineering Design **Equipment** Schema | Per-component / OAM part knowledge under the FBS-OAM framework (GD-B, GD-TP, GD-TT, GD-SH, GD-ST, GD-Con, …). |
| **EDAS** | Engineering Design **Assembly** Schema | Assembly-build rules, valid topology, interface logic, standard layout anchors. |
| **EDIKB** | Engineering Design **Intelligence** Knowledge Base | Behaviour knowledge graph (rules, guidance, uncertainty, interaction candidates) + a numeric evidence dataset for quantitative comparison. |
| **Knowloop** | **Feedback** Candidate Knowledge Base | Captures one feedback candidate after every query. Candidate knowledge is exploratory; official KB updates require human/expert review. |

---

## The process

Every design query runs through this nine-step sequence
(`framework_manifest.json` → `runtime_sequence`, orchestrated by
`tools/run_edpr_pipeline.py`):

```
1. read_manifest            Load framework_manifest.json — discover schemas, prompts,
                            knowledge sources, tools, examples, Knowloop policy.

2. parse_problem_to_edpr    NL request -> EDPR problem-map JSON, using
   (LLM step)               knowledge/edpr/EDPR_PARSER_PROMPT_RUNTIME.md.
                            The parse MUST express APF and P-map before retrieval:
                              request -> APF interpretation (Action / Product / Function)
                                      -> P-map nodes + links
                                      -> APF requirement tuples  r = (Z, M, C)
                                      -> retrieval plan
                                      -> solver plan

3. validate_edpr            tools/EDPR_VALIDATOR.py against schemas/EDPR_METASCHEMA.json.
   (gate)                   Full JSON-Schema Draft 2020-12 + EDPR-specific checks
                            (ID format, ontology links, retrieval-plan coverage).

4. check_pmap_apf           tools/check_pmap_apf.py --strict.
   (gate)                   Verifies the parse is not merely schema-valid but
                            structurally useful: enough P-map nodes, links, and
                            formalised requirement tuples to drive retrieval.

5. retrieve_context         tools/retrieve_context.py.
                            Loads the relevant EDES components, EDAS assembly rules,
                            standard layout anchors, EDIKB graph nodes/edges, and
                            EDIKB numeric rows named by the EDPR retrieval &
                            numericComparison plans.

6. reason_over_candidates   EDAS for topology/interface validity, EDES for component
   (LLM step)               constraints (roller contact, envelope, connections),
                            EDIKB graph for behaviour rules and guidance,
                            EDIKB dataset for quantitative evidence.

7. handle_feature_          Check EDIKB interaction nodes and combined-case rows.
   interactions             Do NOT assume simple superposition of isolated component
                            effects unless direct combined evidence supports it.

8. solve_and_explain        Rank options against the EDPR objectives / rankingCriteria,
                            cite graph + dataset evidence, state assumptions, and mark
                            weakly-supported conclusions as future FEA/ML study needs.
                            (tools/solve_problem.py is a first-pass numeric ranker;
                            objective-specific scoring from rankingCriteria is on the
                            roadmap.)

9. emit_knowloop_candidate  tools/generate_knowloop_candidate.py — ALWAYS, whether the
                            outcome was successful, partial, or failed. The candidate
                            goes to human/expert review; accepted ones are promoted
                            into the official KB.
```

**Why the two gates (steps 3–4) matter:** they stop a weak parse — where the LLM jumps
straight from user text to candidate components without making the problem structure
visible — from reaching retrieval. If a design answer is later found weak, the failure can
be localised to APF interpretation, P-map construction, retrieval, numeric ranking, or
solver judgement rather than being lost in an opaque prompt.

### APF requirement tuple

Requirements are formalised as `r = (Z, M, C)`:

| Item | Meaning | Example |
|---|---|---|
| **Z** | Zone / domain / option set / evaluation region / condition | L-shaped ILT candidate layouts, S-lay overbend |
| **M** | Metric / response / feature / validity measure | Peak nominal strain in the header pipeline |
| **C** | Constraint / comparison / objective / preference / verification | `minimize`, listwise rank; or `== 2.0`; or `>= 4` |

See `docs/EDPR_PMAP_APF_IMPLEMENTATION.md` for the full P-map node/link vocabulary and
`docs/EDPR_Problem_Map_Spec.md` for the problem-map specification.

---

## Repository layout

```
framework_manifest.json          Active manifest (v0.4). READ THIS FIRST.
framework_manifest_v0_*.json     Version history.

schemas/                         Metaschemas: EDPR, EDES, EDAS, EDIKB.

knowledge/
  edpr/
    EDPR_PARSER_PROMPT_RUNTIME.md    Runtime parser prompt (APF/P-map mandatory).
    EDPR_APF_PARSER_PROMPT.md        Full APF parser prompt.
    examples/                        Validated worked EDPR problem maps.
  edes/                          14 component knowledge files + EDES_SHARED.
  edas/                          EDAS_SHARED_KNOWLEDGE.json + standard_ils_layouts.json.
  edikb/                         EDIKB_FULL_KNOWLEDGE_GRAPH.json + EDIKB_FULL_DATASET.csv.
  knowloop/
    KNOWLOOP_FEEDBACK_SCHEMA.json
    templates/  candidates/  accepted/  rejected/

tools/
  EDPR_VALIDATOR.py  EDES_VALIDATOR.py  EDAS_VALIDATOR.py
  check_pmap_apf.py                  P-map/APF semantic completeness checker.
  retrieve_context.py               Context package builder.
  solve_problem.py                  First-pass numeric ranker.
  generate_knowloop_candidate.py    Feedback candidate emitter.
  run_edpr_pipeline.py              Orchestrator for steps 3-9.

plotters/                        ILS geometry plotters (component_spec, ils_builder,
                                 ils_plotter, …). Draw an ILS on its header with the
                                 roller-contact envelope; ILS-tier only (no stinger/rollers).

docs/                            EDPR_Problem_Map_Spec, ONTOLOGY_CROSSWALK,
                                 EDPR_PMAP_APF_IMPLEMENTATION, KNOWLOOP_FEEDBACK_WORKFLOW.

Reference Papers/                Source papers (APF-via-LLM, Problem-Map, ontology, NIST).
```

---

## Setup

Requires Python 3.10+.

```bash
pip install jsonschema            # required for full validation in the validators
pip install matplotlib numpy pyyaml   # only for the plotters/ tools
```

The validators still run without `jsonschema` (they fall back to their own structural
checks and skip full JSON-Schema validation).

---

## Running it

All commands are run from the repository root. Globs (`*.json`) assume a POSIX shell;
on Windows PowerShell, expand the file list yourself or use `Get-ChildItem`.

### Validate the knowledge base

```bash
python tools/EDPR_VALIDATOR.py --schema schemas/EDPR_METASCHEMA.json knowledge/edpr/examples/*.json
python tools/check_pmap_apf.py --strict knowledge/edpr/examples/*.json
python tools/EDES_VALIDATOR.py tools/          # metaschema + EDES_*_KNOWLEDGE.json in one dir
python tools/EDAS_VALIDATOR.py tools/          # metaschema + EDAS_SHARED + EDES files in one dir
```

> The EDES/EDAS validators expect the metaschema and knowledge files to sit in one
> directory (default: the script's own `tools/`); pass a directory argument to point
> elsewhere.

### Run the full pipeline on an example

```bash
python tools/run_edpr_pipeline.py \
  --edpr-json knowledge/edpr/examples/EDPR_EXAMPLE_ILT_L_BRANCH_MIN_STRAIN.json \
  --output-dir runs/test_ilt \
  --solution-format md
```

Expected:

- EDPR validation passes.
- P-map/APF check passes.
- The ILT L-branch solution recommends **`L-ST-PS`** (L-shaped branch, slotted support,
  PS top-frame connection system).
- `runs/test_ilt/` contains the retrieval context, the solution summary, and a Knowloop
  candidate JSON.

`runs/` is git-ignored.

---

## Knowloop feedback loop

```
design query -> EDPR parse -> retrieval -> solution
             -> Knowloop candidate JSON  (tools/generate_knowloop_candidate.py)
             -> human / expert review
             -> accepted updates promoted to the official KB
```

Candidate types: `confirmation`, `improvement`, `correction`, `new_knowledge_candidate`,
`future_study_candidate`, `failure_record`.
Status flow: `generated` → `human_reviewed` / `needs_evidence` → `expert_accepted` /
`expert_rejected` → `implemented` / `superseded`.

An accepted candidate is promoted to a specific target: a wrong parse → EDPR prompt/schema/
examples; missing component info → EDES; missing assembly logic → EDAS; missing behaviour
rule → EDIKB graph; missing numbers → EDIKB dataset or the FEA/ML study queue; missing
archetype → standard layouts; tool failure → runtime tools. See
`docs/KNOWLOOP_FEEDBACK_WORKFLOW.md`.

The Knowloop KB never modifies EDPR/EDES/EDAS/EDIKB directly. Candidate knowledge is
exploratory until expert acceptance.

---

## Status & limitations

- **Prototype / working-batch.** Manifest schema v0.4.
- `solve_problem.py` is a **first-pass numeric ranker** — it treats lower strain / moment
  values as better and does not yet apply objective-specific weighting from the EDPR
  `rankingCriteria`, so its raw output can mix response types. Treat its ranking as a
  retrieval-sanity check, not the final answer; the reasoning (step 6–8) is where options
  are actually weighed.
- The LLM steps (parse, reason) are **specified but not wired into the orchestrator** —
  `run_edpr_pipeline.py` runs the deterministic tools; NL→EDPR conversion is a manual or
  external-LLM step. Connecting an LLM API is on the roadmap.
- All EDIKB numeric evidence is from a **bounded parametric study domain** (S-lay overbend,
  one pipe geometry, fixed roller spacing). Use it for relative concept ranking and feature
  selection; a project outside that domain needs its own FEA/ML verification case.
- No vector-index retrieval yet — retrieval is structured lookup driven by the EDPR
  retrieval plan (planned enhancement once P-map/APF and Knowloop behaviour are stable).
