"""Minimal JSON Schema (2020-12 subset) validator.

Supports exactly the keywords EDES_METASCHEMA.json uses: type, required,
properties, additionalProperties, enum, const, pattern, items, oneOf,
if/then, $ref (resolved against the document's own $defs). Nothing else --
this is a verification tool for one specific schema, not a general
implementation.
"""
import json
import re
import sys


def _resolve(ref, root):
    assert ref.startswith('#/'), f'only local $ref supported, got {ref}'
    node = root
    for part in ref[2:].split('/'):
        node = node[part]
    return node


def validate(instance, schema, root, path=''):
    """Returns a list of error strings. Empty list = valid."""
    errors = []

    if '$ref' in schema:
        return validate(instance, _resolve(schema['$ref'], root), root, path)

    if 'oneOf' in schema:
        # NOT an early return: 'oneOf' is one keyword among possibly several
        # siblings on this schema object (e.g. a top-level `required` next
        # to `oneOf`, both meant to be ANDed). An early return here would
        # silently skip every sibling keyword -- exactly the bug a prior
        # version of this validator had, caught only by deliberately
        # testing a schema shaped that way before trusting it.
        matches, sub_errors = [], []
        for i, sub in enumerate(schema['oneOf']):
            e = validate(instance, sub, root, path)
            if not e:
                matches.append(i)
            else:
                sub_errors.append(f'  branch {i}: {e[0]}')
        if len(matches) == 0:
            errors.append(f'{path}: matched NONE of {len(schema["oneOf"])} oneOf branches:\n' + '\n'.join(sub_errors))
        elif len(matches) > 1:
            errors.append(f'{path}: matched {len(matches)} oneOf branches (ambiguous): {matches}')

    if 'const' in schema:
        if instance != schema['const']:
            errors.append(f'{path}: expected const {schema["const"]!r}, got {instance!r}')

    if 'enum' in schema:
        if instance not in schema['enum']:
            errors.append(f'{path}: {instance!r} not in enum {schema["enum"]}')

    if 'type' in schema:
        t = schema['type']
        types = t if isinstance(t, list) else [t]
        ok = any(_check_type(instance, ty) for ty in types)
        if not ok:
            errors.append(f'{path}: expected type {types}, got {type(instance).__name__} ({instance!r})')
            return errors  # further checks meaningless if type is wrong

    if 'pattern' in schema and isinstance(instance, str):
        if not re.match(schema['pattern'], instance):
            errors.append(f'{path}: {instance!r} does not match pattern {schema["pattern"]!r}')

    if 'minimum' in schema and isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if instance < schema['minimum']:
            errors.append(f'{path}: {instance!r} is below minimum {schema["minimum"]!r}')

    if isinstance(instance, dict):
        props = schema.get('properties', {})
        for req in schema.get('required', []):
            if req not in instance:
                errors.append(f'{path}: missing required property {req!r}')
        if schema.get('additionalProperties') is False:
            extra = set(instance.keys()) - set(props.keys())
            if extra:
                errors.append(f'{path}: additional properties not allowed: {sorted(extra)}')
        for k, v in instance.items():
            if k in props:
                errors += validate(v, props[k], root, f'{path}.{k}')
        if 'if' in schema:
            cond_errors = validate(instance, schema['if'], root, path)
            branch = schema.get('then') if not cond_errors else schema.get('else')
            if branch:
                errors += validate(instance, branch, root, path)

    if isinstance(instance, list) and 'items' in schema:
        for i, item in enumerate(instance):
            errors += validate(item, schema['items'], root, f'{path}[{i}]')

    return errors


def _check_type(instance, ty):
    if ty == 'object': return isinstance(instance, dict)
    if ty == 'array': return isinstance(instance, list)
    if ty == 'string': return isinstance(instance, str)
    if ty == 'number': return isinstance(instance, (int, float)) and not isinstance(instance, bool)
    if ty == 'integer':
        # JSON Schema: an integer is a number with a zero fractional part --
        # 4000 and 4000.0 both qualify, "4000" and True do not. Missing
        # entirely until this fix; every def before this schema used
        # number/string/object/array/boolean, so nothing caught the gap
        # until 'integer' was used for the first time.
        if isinstance(instance, bool): return False
        if isinstance(instance, int): return True
        if isinstance(instance, float): return instance.is_integer()
        return False
    if ty == 'boolean': return isinstance(instance, bool)
    if ty == 'null': return instance is None
    return False


# ============================================================================
# Cross-file reference check -- merged from check_dangling_refs.py.
# Deliberately kept as separate functions below, not folded into validate()
# above: per-file shape checking and cross-file reference resolution are
# genuinely different operations (one file vs the whole set; schema-driven
# vs id-matching), proven independent by dedicated negative tests -- an
# earlier check found a file with five real metaschema violations that this
# reference check still reported clean, since none of those violations
# happened to touch an edes: reference. Merged into one importable module
# for convenience; kept as two capabilities, not blended into one.
# ============================================================================
def declared_ids(shared, component_docs):
    ids = {shared['id']}
    for key in ('nodes', 'futureComponents', 'proposedFunctions', 'metaTypes'):
        for n in shared.get(key, []):
            ids.add(n['id'])
    for d in component_docs:
        ids.add(d['id'])
    return ids


def referenced_ids(shared, component_docs):
    """Extract every edes: reference, excluding documentation placeholders.

    refConventions in EDES_SHARED.json uses 'edes:NODE' as prose describing
    the pointer SYNTAX, not an actual reference -- a real id never appears
    in all-caps (every genuine id observed so far is a CURIE like GD-TP,
    Func2, GD-BOSS: mixed case or a short all-caps CODE, never a bare
    English word standing in for 'some node'). Excluding bare all-caps
    single-word tokens removes that false positive without also excluding
    real ids like GD-BOSS or ComponentType, which are not single words.
    """
    refs = set()
    for doc in [shared] + component_docs:
        for m in re.finditer(r'edes:([A-Za-z0-9_-]+)', json.dumps(doc)):
            token = m.group(1)
            if re.fullmatch(r'[A-Z]+', token):
                continue  # e.g. 'NODE' in explanatory prose, not a real id
            refs.add('edes:' + token)
    return refs


def check(shared_path, component_paths):
    shared = json.load(open(shared_path))
    components = [json.load(open(p)) for p in component_paths]
    declared = declared_ids(shared, components)
    referenced = referenced_ids(shared, components)
    dangling = sorted(referenced - declared)
    return dangling


def run_all(metaschema_path, shared_path, component_paths):
    """Both checks together: per-file shape (validate) against every file,
    then the cross-file reference check. Returns (shape_ok, dangling_ok)."""
    schema = json.load(open(metaschema_path))
    all_paths = [shared_path] + list(component_paths)

    print('=== per-file shape check (validate vs metaschema) ===')
    shape_ok = True
    for p in all_paths:
        doc = json.load(open(p))
        errors = validate(doc, schema, schema)
        name = p.split('/')[-1]
        status = 'PASS' if not errors else f'FAIL ({len(errors)})'
        print(f'  {name:22} {status}')
        if errors:
            shape_ok = False
            for e in errors:
                print('     ', e)

    print()
    print('=== cross-file reference check ===')
    dangling = check(shared_path, component_paths)
    dangling_ok = not dangling
    if dangling:
        print('  DANGLING REFERENCES (declared nowhere):')
        for d in dangling:
            print('   ', d)
    else:
        print('  OK -- every edes: reference resolves to a declared node')

    return shape_ok, dangling_ok


if __name__ == '__main__':
    # Resolve relative to THIS script's own directory, not a fixed
    # absolute path. Was hard-coded to '/mnt/user-data/outputs/', which
    # meant the validator only ran in the one place it was authored --
    # a backup copy of the schema set could not be checked where it
    # actually sat. An explicit first argument still overrides.
    import os, sys
    base = (sys.argv[1].rstrip('/') + '/') if len(sys.argv) > 1 \
        else os.path.dirname(os.path.abspath(__file__)) + '/'
    metaschema_path = base + 'EDES_METASCHEMA.json'
    shared_path = base + 'EDES_SHARED_KNOWLEDGE.json'
    component_paths = [base + f'EDES_{c}_KNOWLEDGE.json' for c in
                        ('GD-TP', 'GD-TT', 'GD-PIP', 'GD-VLV', 'GD-SH', 'GD-ST', 'GD-SB', 'GD-B', 'GD-BOSS', 'GD-HdPipe', 'GD-BrPipe', 'GD-Con')]

    shape_ok, dangling_ok = run_all(metaschema_path, shared_path, component_paths)
    print()
    print('ALL CHECKS PASS:', shape_ok and dangling_ok)
    sys.exit(0 if (shape_ok and dangling_ok) else 1)
