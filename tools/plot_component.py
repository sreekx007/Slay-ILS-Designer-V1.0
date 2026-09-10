"""Render one component using defaults and optional parameter overrides."""
import argparse
from _plot_cli import execute, output_arguments, overrides


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--component', required=True, help='Component code, e.g. GD-TP')
    parser.add_argument('--set', action='append', default=[], metavar='NAME=VALUE', help='Repeatable component override; JSON arrays supported')
    parser.add_argument('--pipeline-set', action='append', default=[], metavar='NAME=VALUE', help='Repeatable pipeline override')
    parser.add_argument('--system', help='ILS connection system, e.g. F2')
    output_arguments(parser)
    args = parser.parse_args()
    def make_spec(builder):
        import config
        params = overrides(args.set)
        if {'code', 'id', 'pipe'} & params.keys():
            raise ValueError('--set accepts parameters, not code, id, or pipe')
        args.default_component_fields = [] if 'centre_x' in params else ['centre_x']
        params.setdefault('centre_x', 0.0)
        pipeline = {'OD_pipe': config.OD_PIPE_DEF, 't_pipe': config.T_WALL_DEF}
        supplied = overrides(args.pipeline_set)
        args.default_pipeline_fields = list(pipeline.keys() - supplied.keys())
        pipeline.update(supplied)
        meta = {'name': args.component, 'frame': 'local', 'ownership': 'strict'}
        if args.system:
            meta['connection_system'] = args.system
        return {'schema_version': 1, 'ils': meta, 'pipeline': pipeline, 'components': [{'code': args.component, **params}], 'associations': []}
    return execute(args, make_spec, component=True)


if __name__ == '__main__':
    raise SystemExit(main())
