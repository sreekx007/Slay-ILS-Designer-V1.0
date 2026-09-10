"""Shared execution and reporting for the Phase 2 plotting commands."""
import dataclasses
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def overrides(items):
    result = {}
    for item in items:
        key, separator, raw = item.partition('=')
        key = key.strip()
        if not separator or not key or not raw.strip():
            raise ValueError(f'Expected NAME=VALUE, got {item!r}')
        if key in result:
            raise ValueError(f'Duplicate override: {key}')
        try:
            result[key] = json.loads(raw)
        except json.JSONDecodeError:
            result[key] = raw
    return result


def validate_input(spec, builder):
    if not isinstance(spec, dict) or spec.get('schema_version') != 1:
        raise ValueError('Layout must be an object with schema_version 1')
    if spec.get('ils', {}).get('ownership', 'strict') not in ('strict', 'lowest'):
        raise ValueError('ownership must be strict or lowest')
    if not isinstance(spec.get('pipeline'), dict) or not {'OD_pipe', 't_pipe'} <= spec['pipeline'].keys():
        raise ValueError('pipeline requires OD_pipe and t_pipe')
    if not isinstance(spec.get('components'), list) or not spec['components']:
        raise ValueError('components must be a nonempty array')
    ids = []
    for i, entry in enumerate(spec['components']):
        if not isinstance(entry, dict) or entry.get('code') not in builder.CLS:
            raise ValueError(f'Unknown or missing component code at index {i}')
        if 'centre_x' not in entry:
            raise ValueError(f'Component {i} requires centre_x')
        allowed = {f.name for f in dataclasses.fields(builder.CLS[entry['code']]) if f.init and f.name != 'pipe'} | {'code', 'id'}
        if entry.keys() - allowed:
            raise ValueError(f'Unknown component parameters: {sorted(entry.keys() - allowed)}')
        cid = entry.get('id', f'C{i+1}')
        if not isinstance(cid, str) or not cid:
            raise ValueError('Component ids must be nonempty strings')
        ids.append(cid)
    if len(ids) != len(set(ids)):
        raise ValueError('Component ids must be unique')
    def finite(value):
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError('Non-finite numeric values are not supported')
        if isinstance(value, dict):
            for v in value.values():
                finite(v)
        elif isinstance(value, list):
            for v in value:
                finite(v)
    finite(spec)


def output_arguments(parser):
    parser.add_argument('--output', required=True, help='Image destination (.png, .svg, .pdf)')
    parser.add_argument('--report', help='JSON report destination (default: OUTPUT stem.report.json)')
    parser.add_argument('--title', help='Override figure title')


def execute(args, make_spec, component=False):
    report = {'plot_status': 'failed', 'plot_qa_status': 'not_applicable',
              'output_image': None, 'checks': [], 'corrections': [],
              'warnings': [], 'errors': [], 'defaulted_parameters': []}
    output = Path(args.output)
    report_path = Path(args.report) if args.report else output.with_suffix('.report.json')
    protected = [Path(args.input).resolve()] if getattr(args, 'input', None) else []
    if output.resolve() == report_path.resolve() or any(p in protected for p in (output.resolve(), report_path.resolve())):
        print('Output, report, and input paths must be distinct', file=sys.stderr)
        return 1
    try:
        sys.path.insert(0, str(ROOT / 'plotters'))
        import matplotlib
        matplotlib.use('Agg')
        import ils_builder as builder
        spec = make_spec(builder)
        validate_input(spec, builder)
        ils = builder.build_ils(spec)
        report['input_file'] = getattr(args, 'input', None)
        report['archetype'] = getattr(args, 'archetype', None)
        report['resolved_assembly_settings'] = {'header_half_length': ils.header_half, 'header_auto_extended': ils.header_auto, 'connection_system': ils.connection_system, 'ownership': ils.ownership.value}
        report['findings'] = [dataclasses.asdict(f) for f in ils.findings]
        for f in ils.findings:
            if f.severity in ('error', 'warning'):
                report[f.severity + 's'].append(str(f))
        supplied_pipeline = set(spec['pipeline']) - set(getattr(args, 'default_pipeline_fields', []))
        records = [('pipeline', ils.pipe, supplied_pipeline)] + [
            (f'components.{cid}', obj, set(entry) - set(getattr(args, 'default_component_fields', [])))
            for cid, obj, entry in zip(ils.ids, ils.components, spec['components'])]
        for prefix, obj, supplied in records:
            for field in dataclasses.fields(obj):
                if field.init and field.name not in supplied and field.name != 'pipe':
                    value = getattr(obj, field.name)
                    report['defaulted_parameters'].append({'path': f'{prefix}.{field.name}', 'value': getattr(value, 'name', value)})
        report['checks'].append({'id': 'assembly_validation', 'status': 'failed' if report['errors'] else ('warning' if report['warnings'] else 'passed')})
        if report['errors']:
            raise ValueError('Assembly validation failed; no image exported')
        if output.suffix.lower() not in ('.png', '.svg', '.pdf'):
            raise ValueError('Output extension must be .png, .svg, or .pdf')
        output.parent.mkdir(parents=True, exist_ok=True)
        import matplotlib.pyplot as plt
        try:
            fig = ils.plot_component(0, title=args.title) if component else ils.plot(title=args.title)
            fig.savefig(output, dpi=150, bbox_inches='tight')
        finally:
            plt.close('all')
        if not output.is_file() or output.stat().st_size == 0:
            raise ValueError('Image export did not produce a nonempty file')
        report['output_image'] = str(output)
        report['checks'].append({'id': 'image_export', 'status': 'passed'})
        report['plot_status'] = 'warning' if report['warnings'] else 'passed'
    except Exception as exc:
        report['errors'].append(f'{type(exc).__name__}: {exc}')
    report['checks'].append({'id': 'visual_plot_qa', 'status': 'not_applicable', 'message': 'Automated visual QA is not implemented in Phase 2.'})
    try:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    except Exception as exc:
        print(f'Cannot save report: {exc}', file=sys.stderr)
        return 1
    print(json.dumps({'status': report['plot_status'], 'image': report['output_image'], 'report': str(report_path), 'errors': report['errors']}))
    return 1 if report['errors'] else 0
