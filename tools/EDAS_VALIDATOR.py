"""EDAS validator -- shape check plus a CROSS-LAYER reference check.

Run:  python3 EDAS_VALIDATOR.py [directory]

Two checks, and the second is the one that could not exist before EDAS was
split out:

  1. SHAPE. EDAS_SHARED_KNOWLEDGE.json against EDAS_METASCHEMA.json. Section
     bodies are loose while they settle; what is enforced is the document
     kind and that no section has been silently dropped.

  2. CROSS-LAYER REFERENCES. EDAS names EDES components and nodes constantly
     -- edes:GD-TP, edes:GD-SH, edes:shared#/oam/connectionClassMap -- and
     nothing checked that any of them exist. That is the reference class this
     project has already been bitten by twice INSIDE EDES: a wildcard written
     as `edes:GD-*` reads as a node id, and placeholder ids like `edes:FuncN`
     look real. Across two layers with no shared validator the risk is worse,
     because a component can be renamed in EDES with nothing in EDAS
     noticing.

Deliberately reuses the EDES validator's `validate()` rather than
reimplementing it: two JSON-Schema checkers drifting apart would be a worse
problem than the one this file solves.
"""

import json
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

try:
    from EDES_VALIDATOR import validate
except ImportError:                       # pragma: no cover
    sys.exit('EDAS_VALIDATOR needs EDES_VALIDATOR.py alongside it: it reuses '
             'that module\'s validate() so the two layers cannot drift into '
             'two different notions of "valid".')


def edes_declared_ids(base):
    """Every id an EDES file declares: the node ids themselves plus the
    Function / ProposedFunction / FutureComponent entries inside shared."""
    ids = set()
    for name in sorted(os.listdir(base)):
        if not (name.startswith('EDES_') and name.endswith('KNOWLEDGE.json')):
            continue
        doc = json.load(open(os.path.join(base, name)))
        if 'id' in doc:
            ids.add(doc['id'])
        for key in ('nodes', 'proposedFunctions', 'futureComponents'):
            for item in doc.get(key, []) or []:
                if isinstance(item, dict) and 'id' in item:
                    ids.add(item['id'])
    return ids


def edas_references(doc):
    """`edes:` tokens appearing anywhere in the document, including inside
    prose -- which is exactly where the bad ones have historically hidden.
    A fragment after '#' is dropped: the target is the NODE."""
    raw = re.findall(r'edes:[A-Za-z0-9_.\-]+', json.dumps(doc))
    return {r.rstrip('.').split('#')[0] for r in raw}


def run(base=None):
    base = base or _HERE
    schema_path = os.path.join(base, 'EDAS_METASCHEMA.json')
    doc_path = os.path.join(base, 'EDAS_SHARED_KNOWLEDGE.json')
    for p in (schema_path, doc_path):
        if not os.path.exists(p):
            sys.exit(f'not found: {p}\nPass the directory as an argument if '
                     'the files are elsewhere.')

    schema = json.load(open(schema_path))
    doc = json.load(open(doc_path))

    print('=== shape check (EDAS_SHARED vs EDAS_METASCHEMA) ===')
    errors = validate(doc, schema, schema)
    shape_ok = not errors
    print('  EDAS_SHARED_KNOWLEDGE.json',
          'PASS' if shape_ok else f'FAIL ({len(errors)})')
    for e in errors:
        print('     ', e)

    print()
    print('=== cross-layer reference check (EDAS -> EDES) ===')
    declared = edes_declared_ids(base)
    if not declared:
        print('  SKIPPED -- no EDES_*KNOWLEDGE.json files alongside. The '
              'reference check needs both layers present.')
        return shape_ok, True
    refs = edas_references(doc)
    dangling = sorted(r for r in refs if r not in declared)
    ref_ok = not dangling
    if ref_ok:
        print(f'  OK -- all {len(refs)} edes: references resolve '
              f'({len(declared)} ids declared across EDES)')
    else:
        print('  DANGLING (named in EDAS, declared nowhere in EDES):')
        for r in dangling:
            print('   ', r)
        print('  NOTE a wildcard such as edes:GD-* will land here. Write it as '
              'a file glob (EDES_GD-*.json) so it does not read as a node id.')

    print()
    print('ALL CHECKS PASS:', shape_ok and ref_ok)
    return shape_ok, ref_ok


if __name__ == '__main__':
    ok = run(sys.argv[1] if len(sys.argv) > 1 else None)
    sys.exit(0 if all(ok) else 1)
