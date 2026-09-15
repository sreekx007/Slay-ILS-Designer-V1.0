"""Shared execution and reporting for the Phase 2 plotting commands."""
import dataclasses
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def direct_plot_governance(component=False):
    tool_name = Path(sys.argv[0]).name or ("plot_component.py" if component else "plot_design.py")
    return {
        "authority": f"tools/{tool_name}",
        "status": "unstamped_direct_plot",
        "allowed_output": "non_authoritative_plot",
        "blocking_gates": ["GOVERNED_WORKFLOW_NOT_RUN"],
        "human_remaining_actions": [
            "If this plot supports a design decision, rerun the request through tools/run_design_workflow.py and use only the authority-stamped governed report.",
            "Review the parameter CSV and plot report for warnings, defaulted dimensions, and unresolved gates before accepting the concept.",
        ],
    }

def required_connection_label_check(ils, labels):
    ids = getattr(ils, 'ids', [])
    codes = getattr(ils, 'codes', [])
    code_by_id = dict(zip(ids, codes))
    associations = getattr(ils, 'definition', {}).get('associations', []) or []
    present = {item.get('index') for item in labels or []}
    required = []
    missing = []
    for index, assoc in enumerate(associations):
        if assoc.get('type') != 'Connection' or assoc.get('connection') == 'W':
            continue
        ends = [
            (assoc.get('from') or {}).get('component'),
            (assoc.get('to') or {}).get('component'),
        ]
        if not any(code_by_id.get(component) in {'GD-ST', 'GD-SB'} for component in ends):
            continue
        record = {
            'index': index,
            'connection': assoc.get('connection'),
            'from': assoc.get('from'),
            'to': assoc.get('to'),
        }
        required.append(record)
        if index not in present:
            missing.append(record)
    return {
        'id': 'required_structure_connection_labels',
        'status': 'passed' if not missing else 'failed',
        'required': required,
        'missing': missing,
        'rule': 'Show connection type labels only for required non-weld GD-ST/GD-SB structural connections; connector component labels are not required and W welds are omitted.',
    }
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
              'warnings': [], 'errors': [], 'defaulted_parameters': [],
              'parameter_csv': None,
              'design_governance': direct_plot_governance(component)}
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
        report['design_workflow'] = ils.design_workflow_report()
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
        gate = report['design_workflow']
        report['checks'].append({'id': 'ea_exposure_gate', 'status': gate['status'], 'missing': gate['unresolved_or_inactive_slots']})
        if report['errors']:
            raise ValueError('Assembly validation failed; no image exported')
        if output.suffix.lower() not in ('.png', '.svg', '.pdf'):
            raise ValueError('Output extension must be .png, .svg, or .pdf')
        output.parent.mkdir(parents=True, exist_ok=True)
        import matplotlib.pyplot as plt
        from plot_settings import STYLE
        try:
            if not component:
                import ils_plotter
                parameter_csv = output.with_suffix('.parameters.csv')
                ils_plotter.write_parameter_csv(ils, parameter_csv)
                report['parameter_csv'] = str(parameter_csv)
                report['checks'].append({'id': 'parameter_csv_export', 'status': 'passed', 'path': str(parameter_csv)})
            fig = ils.plot_component(0, title=args.title) if component else ils.plot(title=args.title)
            from checkers.label_overlap_checker import correct_layout
            report['plot_qa_status'] = 'failed'
            correct_layout(fig)
            fig.savefig(output, dpi=STYLE['figure']['export_dpi'], bbox_inches='tight')
            from checkers.plot_checker import check_plot
            report['plot_qa_status'] = 'failed'
            qa = check_plot(fig, ils.components, output)
            report['plot_qa_status'] = qa['plot_qa_status']
            report['layout_qa'] = getattr(fig, '_layout_qa', {})
            report['connection_labels'] = getattr(fig, '_connection_labels', [])
            report['plot_annotations'] = getattr(fig, '_plot_annotations', [])
            annotation_failures = [item for item in report['plot_annotations'] if item.get('status') == 'failed']
            annotation_check = {'id': 'plot_annotation_anchors', 'status': 'passed' if not annotation_failures else 'failed', 'failed': annotation_failures}
            report['checks'].append(annotation_check)
            if annotation_failures:
                report['errors'].append('Requested plot annotations must resolve to model coordinates; failed anchors: ' + ', '.join(str(item.get('id')) for item in annotation_failures))
            required_label_check = required_connection_label_check(ils, report['connection_labels'])
            report['required_connection_labels'] = required_label_check
            report['checks'].append(required_label_check)
            if required_label_check['status'] == 'failed':
                report['errors'].append('Required GD-ST/GD-SB connection type labels are missing: ' + ', '.join(str(item.get('index')) for item in required_label_check['missing']))
            min_connection_font = getattr(__import__('plot_settings'), 'STYLE')['fonts'].get('connection_label', 0)
            label_check = {'id': 'connection_label_legibility', 'status': 'passed' if min_connection_font >= 9 else 'failed', 'minimum_font_pt': min_connection_font}
            report['checks'].append(label_check)
            if label_check['status'] == 'failed':
                report['errors'].append('Connection labels must be at least 9 pt for review plots')
            for key in ('checks', 'errors', 'warnings', 'corrections'):
                report[key].extend(qa[key])
        finally:
            plt.close('all')
        if not output.is_file() or output.stat().st_size == 0:
            raise ValueError('Image export did not produce a nonempty file')
        report['output_image'] = str(output)
        report['checks'].append({'id': 'image_export', 'status': 'passed'})
        report['plot_status'] = 'failed' if report['errors'] else 'warning' if report['warnings'] else 'passed_with_corrections' if report['corrections'] else 'passed'
    except Exception as exc:
        report['errors'].append(f'{type(exc).__name__}: {exc}')
    if report['plot_qa_status'] == 'not_applicable':
        report['checks'].append({'id': 'plot_qa', 'status': 'not_applicable', 'message': 'Build or export did not reach plot QA.'})
    try:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    except Exception as exc:
        print(f'Cannot save report: {exc}', file=sys.stderr)
        return 1
    print(json.dumps({'status': report['plot_status'], 'image': report['output_image'], 'report': str(report_path), 'errors': report['errors']}))
    return 1 if report['errors'] else 0
