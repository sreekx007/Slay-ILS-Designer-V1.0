# KEL v0.2 Implementation Plan

## Implementation progress

Steps 1 through 4 and Step 6 were implemented locally on 2026-09-14. Step 5
is implemented as a fail-closed representation gap because expert review has
not yet selected the intended two-valve topology. The grouped cycle, design
intent gates, L/Z branch anchoring to GD-ST, Z-anchor selection, GD-ST report coverage, GD-SB evidence gate,
implementation plans, migration, status reporting, and lifecycle reconciliation
are active. Q1 GCR 08 has one implemented authority and one superseded trace.

## Status and scope

This is the implementation plan for the first KEL v0.2 release. It turns the
Q1 feedback set and the 12-inch inline-valve design feedback into executable
workflow improvements.

KEL v0.2 keeps the v0.1 governance rule: generated feedback and graph-change
requests are candidates. They do not become official engineering knowledge
until an expert accepts them and the implementation is verified.

The implementation order is fixed because each later item depends on the
traceability and grouping introduced by the earlier work:

1. Feedback decomposition, grouping, de-duplication, and lifecycle repair.
2. EDPR/EDAS vertical-connector rule.
3. GD-B-to-GD-ST anchoring and GD-ST plotter/report exposure gate.
4. GD-SB valve-protection rule using real GD-SB geometry.
5. Two-branch-valve representation gap.
6. Implementation planning, migration, reporting, and release validation.

## Compatibility decisions

- Existing `*/0.1` records remain readable and valid.
- New v0.2 record shapes use new schema files and `*/0.2` schema identifiers;
  v0.1 schemas are not silently changed.
- Stable source IDs are preserved during splitting and grouping.
- Grouping never discards raw feedback or evidence links.
- Promotion remains expert-controlled.
- A layout that cannot be represented by EDAS and the repository plotter emits
  a machine-readable representation gap and is not presented as an authoritative
  design.

## Phase 0 - Baseline and regression fixtures

### Work

1. Create `tests/kel/fixtures/q1/` from the 11 Q1 feedback records and graph
   change requests.
2. Add the compound 12-inch valve feedback as a fixture. It contains five
   independent issues:
   - base depth and valve/roller clearance;
   - base length and strain-evidence basis;
   - P-S support selection and missing valve bending-moment evidence;
   - missing top-frame protection question;
   - missing connector-spacing basis.
3. Preserve Q1 GCR 08 in both its current pending and implemented locations as a
   lifecycle-conflict fixture.
4. Run and record the current KEL, EDPR, solver, builder, and plotter tests before
   changing behavior.

### Exit gate

- Fixtures reproduce the compound-feedback collapse and the duplicate-lifecycle
  conflict on the v0.1 tools.
- The current test baseline passes before implementation begins.

## Phase 1 - Feedback decomposition, grouping, and lifecycle repair

### Schemas

Add:

- `knowledge/kel/schemas/KEL_ATOMIC_FEEDBACK_SCHEMA.json`
  (`kel-atomic-feedback/0.2`)
- `knowledge/kel/schemas/KEL_FEEDBACK_GROUP_SCHEMA.json`
  (`kel-feedback-group/0.2`)

An atomic feedback record must contain one observed issue and one requested
action. It must retain the original feedback ID, the source text span, linked
experience ID, affected components, target layers, evidence references,
classification confidence, and a deterministic fingerprint.

A feedback group must contain a canonical issue, member feedback IDs, member
fingerprints, proposed target layer/change type, lifecycle status, and all source
evidence links.

### Tools

Add:

- `tools/kel/decompose_feedback.py`
- `tools/kel/group_feedback.py`
- `tools/kel/reconcile_lifecycle.py`

Update:

- `tools/kel/convert_feedback_to_pmap_apf.py`
- `tools/kel/generate_graph_change_request.py`
- `tools/kel/promote_accepted_kel_change.py`
- `tools/kel/run_kel_cycle.py`
- `tools/kel/validate_kel_record.py`

Use a deterministic fingerprint made from normalized target layer, change type,
affected component or assembly, and requested action. Exact fingerprints group
automatically. Near matches may be suggested for grouping, but are not merged
when their engineering scope, load case, topology, or evidence requirement
differs.

Generate one graph-change request per accepted group. The request must reference
all member feedback IDs rather than only one `linked_feedback_id`.

Lifecycle reconciliation must guarantee that one change-request ID has one
authoritative status. When a record is promoted, the source record is moved or
marked with `status: superseded` and a pointer to the authoritative record. The
operation must be idempotent and must never overwrite a conflicting record.

### Required regression behavior

- The valve feedback fixture produces five atomic feedback records.
- Q1 GD-ST feedback records 03, 05, and 11 can be grouped while preserving all
  three source IDs and their distinct requirements.
- Q1 GCR 08 resolves to the implemented record; the pending copy is moved or
  explicitly superseded.
- Running the cycle twice creates no duplicate IDs or files.

### Exit gate

- Schema, unit, and full-cycle tests pass.
- No source feedback or evidence reference is lost.
- The pending queue contains no second authoritative copy of an implemented ID.

## Phase 2 - Vertical connector to GD-B Z / ILT-Z rule

### EDPR changes

Update the EDPR parse and validation path so connector direction/orientation is
an explicit field. The parse must distinguish a vertical connector requirement
from branch routing, branch take-off direction, and drawing orientation.

### EDAS and solver changes

Add a rule to `knowledge/edas/EDAS_SHARED_KNOWLEDGE.json` and the solution/layout
selection code:

```text
required connector orientation = vertical
    -> GD-B variant = Z
    -> eligible standard-layout anchors = ILT-Z-*
```

If no compatible Z anchor satisfies the remaining constraints, return an
unresolved layout/representation gap. Do not substitute an L-shaped branch.

### Tests

- EDPR extracts the vertical connector constraint from the Q1 wording.
- The layout selector filters out `ILT-L-*` anchors.
- The emitted layout contains a Z-shaped GD-B and cites its `ILT-Z-*` anchor.
- An intentionally incompatible L output fails validation before plotting.

### Exit gate

Q1 vertical-connector input deterministically produces a Z candidate or an
explicit gap, never an L candidate.

## Phase 3 - GD-B anchoring and GD-ST plotter/report exposure gate

### Required output

Every GD-B branch in an emitted ILS must terminate at GD-ST through an
explicit association. An L branch has a horizontal terminal and a Z branch has
a vertical terminal; the selected anchor defines the compatible GD-ST feature.
The issue first surfaced in a Z-branch trial, but the gate
is branch-family independent. Whenever GD-ST is active, the machine-readable
report and plotted design must expose:

- the canonical GD-ST parameters, including applicable centre position,
  top-frame length, top-frame height, and connector positions;
- every active connector slot and its connector type;
- every pipe-side GD-Con/GD-TP landing;
- the association from each connector to the header, branch, top, or side member;
- the branch-to-top or branch-to-side connection used by the layout;
- unresolved or inactive slots without drawing them as active connections.

Parameter names must be taken from the canonical EDES/plotter component
specification; aliases may be shown in the report but cannot replace canonical
keys.

### Implementation touchpoints

- `plotters/ils_builder.py`: build-time coverage and association findings.
- `plotters/ils_plotter.py`: labels and association rendering.
- `plotters/component_spec.py`: canonical GD-ST parameters and slot metadata.
- `tools/solution_to_layout.py`: solver-to-layout field preservation.
- plot report schema/validator: fail-closed completeness gate.

### Tests

- Reviewed L-horizontal and Z-vertical anchors each pass with a declared
  GD-B-to-GD-ST terminal association.
- Removing GD-ST or the terminal association fails the branch gate.
- Complete GD-ST example passes and lists each parameter, slot, connector,
  landing, and association.
- Removing one association fails the gate with its component/slot ID.
- A label-overlap regression verifies that required labels do not obscure the
  structure; unresolved placement is a plot finding.
- Simplified paper-reproduction plots are explicitly marked and cannot satisfy
  the complete-design gate.

### Exit gate

Q1 feedback 03, 05, and 11 is satisfied by one traceable GD-ST report and plot, and both L and Z branches satisfy the generalized anchoring gate.

## Phase 4 - GD-SB valve protection using GD-SB geometry

### EDPR clarification gate

Before selecting protection, EDPR must capture or ask for:

- whether installation roller passage is part of the design case;
- whether the valve requires underside support only or a protective top frame;
- valve body, actuator, flange, and local thick-section envelopes;
- roller/contact geometry and required clearances;
- design load case and acceptance measure;
- valve bending-moment capacity relative to the pipeline.

An 80 percent valve capacity is a constraint. It does not by itself establish a
support topology or a strain-optimization objective.

### EDAS geometry rule

When a valve cannot pass over the installation rollers and protection is in
scope, select a GD-SB candidate or emit an unresolved assumption. A valid GD-SB
candidate must use the EDES GD-SB component geometry, contact ownership,
connections, and associations. A generic rectangle or freehand frame cannot
satisfy the rule.

If a protective top frame is required, represent it with GD-ST and its
declared associations; do not distort GD-SB to stand in for a top structure.

Derive base depth and length from the equipment envelope, roller clearance,
weld/service clearances, connector geometry, and applicable load path. Record
each input and derivation in the report. Ask for missing values; do not invent a
default dimension.

### Evidence and acceptance rule

Do not infer valve bending-moment compliance from the existing 16-inch GD-SB
strain study. That evidence does not contain a combined GD-VLV + GD-SB valve
moment result. P-S, F, D, or mixed connector selection must cite in-domain EDIKB
evidence or create a `needs_evidence` FEA candidate.

When analysis evidence is available, evaluate:

```text
utilization = maximum valve bending moment
              / (valve capacity ratio * pipeline allowable bending moment)
```

The candidate passes only when utilization is no greater than 1.0 for every
required load case.

### Tests

- The current 12-inch valve query stops at the clarification/evidence gate when
  envelope, roller, top-frame, connector-spacing, and moment evidence are absent.
- A complete fixture builds actual GD-SB geometry and reports every dimensional
  basis.
- A generic frame fails the GD-SB gate.
- P-S selection without compatible evidence emits `needs_evidence` and an FEA
  study candidate.
- No strain-minimization objective is added unless the user requested it.

### Exit gate

The workflow can issue a supported GD-SB concept or a precise evidence gap. It
cannot emit the earlier unsupported P-S concept as a suitable design.

## Phase 5 - Two-branch-valve representation gap

### Formalize the gap first

Create one atomic feedback record and one graph-change request defining the
required topology. Expert review must confirm whether the intended case is two
valves on one branch path, one valve on each of two branches, or another
configuration. Until that topology is fixed, the tool emits a representation
gap rather than guessing.

### Representation changes

Once accepted, extend EDPR, EDAS, layout JSON, builder, plotter, and report with:

- stable, distinct valve instance IDs;
- parent piping path/branch ownership;
- branch-local station and orientation;
- upstream/downstream piping associations;
- independent equipment envelopes and protection requirements;
- collision and label-clearance checks;
- complete topology in the machine-readable report.

### Tests

- Both valve instances survive EDPR-to-layout conversion with distinct IDs.
- Each valve is attached to the correct branch-local pipe chain.
- Plot and report show both valves and their associations unambiguously.
- Coincident placement, ambiguous ownership, or missing connections fail closed.
- Unsupported topology produces a representation-gap record linked to its KEL
  feedback and graph-change request.

### Exit gate

The accepted two-valve topology is buildable and plottable, or the workflow emits
a complete machine-readable gap without a misleading plot.

## Phase 6 - Implementation plans, migration, and release

### Target-layer implementation plans

Add `knowledge/kel/schemas/KEL_IMPLEMENTATION_PLAN_SCHEMA.json` and
`tools/kel/create_implementation_plan.py`. An expert-accepted graph-change group
must produce a checklist appropriate to EDPR, EDES, EDAS, EDIKB, Plotters, Tools,
Datasets, or Docs. The plan links requirements, changed paths, evidence, tests,
review, and completion status.

### Status report

Add `tools/kel/summarize_kel_status.py` to emit JSON and Markdown counts for
atomic feedback, groups, pending changes, needs-evidence items, accepted changes,
implemented changes, superseded records, and lifecycle conflicts.

### Migration

1. Validate every v0.1 record before migration.
2. Generate v0.2 atomic records and groups without modifying the v0.1 source.
3. Reconcile lifecycle duplicates and preserve supersession pointers.
4. Re-run migration and confirm byte-stable/idempotent results apart from declared
   timestamps.
5. Update KEL docs, templates, the root README, `framework_manifest.json`, and
   `UPLOAD_MAP.md`.

### Release validation

Run:

1. KEL schema and governance tests.
2. EDPR parser and pipeline tests.
3. Solver-to-layout tests.
4. Plotter/builder regression tests.
5. JSON validation for all KEL records, examples, and templates.
6. End-to-end reruns of Q1 and the 12-inch valve query.

KEL v0.2 is ready only when both end-to-end runs produce repository-backed
outputs, explicit assumptions, evidence citations, and machine-readable gaps.

## Delivery sequence

Use small reviewable changes in this order:

1. Baseline fixtures and v0.2 schemas.
2. Atomic decomposition, grouping, and de-duplication.
3. Lifecycle reconciliation and idempotency.
4. Vertical connector EDPR/EDAS rule.
5. GD-B-to-GD-ST anchoring and GD-ST completeness gate.
6. GD-SB valve-protection clarification, geometry, and evidence gate.
7. Two-branch-valve gap record and accepted representation.
8. Implementation-plan/status tools, migration, docs, and full release run.

Each change must include its own focused regression tests. The final release run
then verifies the integrated workflow once, avoiding repeated broad test runs
after every small edit.

## Definition of done

KEL v0.2 is complete when:

- compound feedback is decomposed into atomic traceable issues;
- equivalent feedback is grouped without losing source IDs or evidence;
- one change-request ID has one authoritative lifecycle state;
- every GD-B branch terminates at GD-ST through the terminal association defined by the selected L or Z anchor;
- a vertical connector selects GD-B Z and `ILT-Z-*` or emits a gap;
- GD-ST plots and reports expose all parameters, active connectors, and
  associations;
- GD-SB valve protection uses real GD-SB geometry and a documented dimensional
  and evidence basis;
- the accepted two-branch-valve topology is represented end to end, or remains a
  machine-readable gap;
- accepted changes produce target-layer implementation plans;
- Q1 and the 12-inch valve regression scenarios pass the full workflow;
- all generated knowledge remains subject to expert review and promotion.
