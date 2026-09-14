# Critical Update Notes

Defects in this repository's code or data that are **not caught by anything**
— no exception, no `validate()` finding, no test — and that let a wrong or
incomplete model build, validate and return a number.

Each note is reproducible against the head it was raised on, states what is
and is not affected, and carries a patch that has been run. A note stays open
until the fix lands; then it is marked RESOLVED with the commit that did it.

| ID | Raised | Area | Severity | Status |
|---|---|---|---|---|
| CUN-001 | 14 Sep 2026 | `plotters/ils_builder.py` | **Critical** | **OPEN** |

---

## CUN-001 — `P_gap` is required for a `D` connector, and nothing requires it

**Raised:** 14 Sep 2026, against `3356b65`
**Found by:** downstream use in `Slay-Overbend-analysis-program.-Version-1.5`,
building ILS-EAST on F2D for a deadband study.

### What is wrong

`component_spec.py` documents the rule and names its enforcement point:

```
    # DEADBAND GAP -- the free travel a 'D' connector allows before it
    # closes and begins restraining (Fig 16: Ty free while < GAP,
    # restrained at >= GAP). REQUIRED whenever the active connection system
    # contains a D, and meaningless otherwise, so it defaults to None
    # rather than to a number: the design knowledge base calls this a
    # CRITICAL tuning parameter, because a deadband REDISTRIBUTES strain
    # rather than removing it and the gap decides WHERE it goes. A silent
    # default would make that choice for the engineer.
    #
    # The component cannot enforce "required when D" itself -- the
    # connection system is an ILS-LEVEL choice supplied at query time -- so
    # that check lives in ils_builder.validate().
    P_gap: Optional[float] = None     # m, FREE -- deadband free travel
```
— `plotters/component_spec.py:2570-2582`

**That check is not in `ils_builder.validate()`.** It is nowhere in the file:

```
$ grep -n P_gap plotters/ils_builder.py
$                       # no output
```

The reasoning in the comment is right and the placement is right — it is the
same argument as the "active connectors must lie within their own component's
extent" check at `ils_builder.py:305-315`, which does exist and which already
reasons about F2 leaving slots 1 and 5 empty while F2D fills them. Only the
`P_gap` check was never written.

### Reproduction

```python
import json, sys, copy
sys.path.insert(0, 'plotters')
import ils_builder

A = {a['id']: a for a in json.load(
    open('knowledge/edas/standard_ils_layouts.json'))['archetypes']}
d = copy.deepcopy(A['ILS-EAST']['definition'])
d['ils']['connection_system'] = 'F2D'      # two D connectors, no P_gap anywhere

ils = ils_builder.build_ils(d)
print(ils.components[0].P_gap)             # None
print([e for e in ils.validate() if e.severity == 'error'])   # []
print(ils.connectors_of(ils.components[0]))
# (1, -2.1674666666666664, 'D', 0.6096, None)   <-- gap is None
# (2, -1.0837333333333332, 'F', 0.6096, None)
# (4,  1.0837333333333332, 'F', 0.6096, None)
# (5,  2.1674666666666664, 'D', 0.6096, None)
```

It builds. It validates clean (the only finding is an unrelated warning about
GD-Con parts). Two deadband connectors come out of `connectors_of` with
`gap = None`, and every downstream consumer is handed a deadband it cannot
evaluate.

### Why this is critical rather than cosmetic

A deadband does not remove strain, it **moves** it, and `P_gap` decides where
it goes. The gap is not a tolerance — it is the engineering choice the
connection system exists to make. `component_spec` says exactly this, which is
why the default is `None` and not a number.

Measured downstream, on ILS-EAST at 200 kN with the two outer `D` connectors
active, changing nothing but the gap:

| `P_gap` | outer D | pipe deflection | force per D | peak frame stress |
|---|---|---|---|---|
| 5.00 mm | open | 49.43 mm | 0 | 2.0 MPa |
| 3.50 mm | open | 49.43 mm | 0 | 2.0 MPa |
| 2.50 mm | **shut** | 47.51 mm | 64.0 kN | 19.4 MPa |
| 1.00 mm | **shut** | 41.81 mm | 254.6 kN | 82.9 MPa |
| 0.25 mm | **shut** | 38.95 mm | 349.8 kN | 114.7 MPa |

A 21% change in pipe deflection and a **57x** change in frame stress, from the
one parameter nothing requires you to set. A layout that omits it is not
slightly under-specified; it is a different structure, and it is the one place
in the connector model where "it built and validated" carries no information
at all.

### What is NOT affected

The shipped library is clean. All 39 EDAS anchors build and validate with no
error, and all 10 that declare a `D` system (`ILS-EAST-F1D/F2D/PSD`,
`ILS-EASB-F1D/F2D/PSD`, `ILT-L-FT-F2D/PSD`, `ILT-Z-FT-F2D/PSD`) set
`P_gap = 0.05` — the EA-ST anchors in `overrides`, the ILT anchors in
`parts.ST`. **The invariant is currently held by convention in the data, not
by code.** Any hand-built layout, any anchor added without the same care, and
any downstream consumer constructing a definition directly gets no warning.

### Proposed fix — run, not sketched

Insert in `ils_builder.py` `validate()`, immediately after the "active
connectors must lie within their own component's extent" loop (after
`ils_builder.py:315`):

```python
        # A 'D' connector REQUIRES P_gap. `component_spec` says this check
        # lives here, and for the same reason as the one above: whether a
        # component's D slots are active is the ILS-level connection
        # system's choice, so the component cannot know. P_gap defaults to
        # None deliberately -- a deadband REDISTRIBUTES strain rather than
        # removing it and the gap decides WHERE, so a silent default would
        # make that choice for the engineer. Without this, F2D/F1D/PSD
        # builds and validates with gap = None and every consumer of
        # `connectors_of` gets a deadband it cannot evaluate.
        for cid, c in zip(self.ids, self.components):
            if c.code not in EA_CODES:
                continue
            slots = [slot for slot, _cx, ctype, _, gap
                     in self.connectors_of(c) if ctype == 'D' and gap is None]
            if slots:
                out.append(Finding('error', f'{cid}/{c.code}',
                    f'connection system activates a D connector at slot(s) '
                    f'{slots} but P_gap is not set. A deadband has no '
                    f'default: the gap decides where the redistributed '
                    f'strain goes, so it is an engineering choice, not a '
                    f'tolerance. Set P_gap on {cid}.'))
```

Verified on this head:

| Case | Result |
|---|---|
| ILS-EAST, F2D, no `P_gap` | `[ERROR] ST/GD-ST: connection system activates a D connector at slot(s) [1, 5] but P_gap is not set...` |
| ILS-EAST, F2D, `P_gap = 50 mm` | no errors |
| ILS-EAST, F2 (no D), no `P_gap` | no errors |
| all 7 archetypes | no errors |
| all 39 anchors, overrides + parts + ils applied | no errors |

`EA_CODES` and `Finding` are already in scope in that function; the patch adds
no import and no new concept.

### Suggested test

```python
def test_a_d_connector_requires_p_gap():
    """The gap decides where a deadband sends strain, so it has no default
    and no silent fallback. A D system with P_gap unset must not validate."""
    d = copy.deepcopy(ARCHETYPES['ILS-EAST']['definition'])
    d['ils']['connection_system'] = 'F2D'
    errs = [e for e in ils_builder.build_ils(d).validate()
            if e.severity == 'error']
    assert any('P_gap' in e.message for e in errs)

    d['components'][0]['P_gap'] = 0.05
    assert not [e for e in ils_builder.build_ils(d).validate()
                if e.severity == 'error']
```

### Downstream record

Carried in `Slay-Overbend-analysis-program.-Version-1.5` as build-lesson
**L026** (`docs/BUILD_LESSONS.yaml`). That repository mirrors
`component_spec.py` and `ils_builder.py` and does not edit them, so it works
around the gap by checking `Association.gap is not None` at every consumer of
a `D`. The measured table above is from `tools/study_east_f2d.py` there.
