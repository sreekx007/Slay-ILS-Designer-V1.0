"""Render a layout definition or one archetype from a layout collection."""
import argparse
import json
from pathlib import Path
from _plot_cli import execute, output_arguments


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, help='Layout JSON or archetype collection')
    parser.add_argument('--archetype', help='Exact archetype id to select')
    output_arguments(parser)
    args = parser.parse_args()
    def make_spec(builder):
        data = json.loads(Path(args.input).read_text(encoding='utf-8-sig'))
        if args.archetype:
            if not isinstance(data, dict) or not isinstance(data.get('archetypes'), list):
                raise ValueError('--archetype requires an archetypes collection')
            matches = [a for a in data['archetypes'] if a.get('id') == args.archetype]
            if len(matches) != 1:
                raise ValueError(f'Expected one archetype matching {args.archetype!r}; found {len(matches)}')
            return matches[0]['definition']
        if isinstance(data, dict) and 'archetypes' in data:
            raise ValueError('Select an archetype with --archetype ID')
        return data
    return execute(args, make_spec)


if __name__ == '__main__':
    raise SystemExit(main())
