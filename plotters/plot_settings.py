"""Validated presentation configuration, independent of engineering geometry.

Missing files/keys retain frozen defaults. Invalid supplied values fail explicitly.
Settings are loaded once per process; restart a plotting command after editing.
"""
import copy
import json
import math
from pathlib import Path
import warnings
import yaml
from matplotlib.colors import is_color_like
from _plot_defaults import STYLE as DEFAULT_STYLE, CATALOG as DEFAULT_CATALOG

CONFIG_DIR = Path(__file__).resolve().parent / 'config'


def _merge(default, supplied, path='style'):
    if not isinstance(supplied, dict):
        raise ValueError(f'{path} must be an object')
    result = copy.deepcopy(default)
    for key, value in supplied.items():
        if key not in default:
            if path == 'style.component_colors':
                if not is_color_like(value):
                    raise ValueError(f'Invalid color for {key}')
                result[key] = value
                continue
            raise ValueError(f'Unknown setting: {path}.{key}')
        prior = default[key]
        if isinstance(prior, dict):
            result[key] = _merge(prior, value, f'{path}.{key}')
        else:
            if isinstance(prior, (int, float)):
                minimum = 0 if path == 'style.line_widths' else 0.001
                if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < minimum:
                    raise ValueError(f'{path}.{key} must be a finite number >= {minimum}')
            elif not isinstance(value, str) or not value:
                raise ValueError(f'{path}.{key} must be a nonempty string')
            result[key] = value
    return result


def load_settings(directory=CONFIG_DIR):
    directory = Path(directory)
    style_path = directory / 'plot_style.yaml'
    catalog_path = directory / 'component_catalog.json'
    if style_path.exists():
        style = _merge(DEFAULT_STYLE, yaml.safe_load(style_path.read_text(encoding='utf-8-sig')))
    else:
        warnings.warn(f'{style_path} missing; using legacy presentation defaults', stacklevel=2)
        style = copy.deepcopy(DEFAULT_STYLE)
    for colors in [style['colors'], style['component_colors']]:
        for key, value in colors.items():
            if not is_color_like(value):
                raise ValueError(f'Invalid color: {key}={value!r}')
    for key in ['foreground', 'background']:
        if not is_color_like(style['connector'][key]):
            raise ValueError(f'Invalid connector {key}')
    if style['labels']['format'] not in ('code', 'display_name', 'code_and_name'):
        raise ValueError('labels.format must be code, display_name, or code_and_name')
    entries = {e['component_code']: copy.deepcopy(e) for e in DEFAULT_CATALOG['components']}
    if catalog_path.exists():
        supplied = json.loads(catalog_path.read_text(encoding='utf-8-sig'))
        if supplied.get('schema_version') != 1 or not isinstance(supplied.get('components'), list):
            raise ValueError('Catalog requires schema_version 1 and a components array')
        seen = set()
        for entry in supplied['components']:
            code = entry.get('component_code')
            if not isinstance(code, str) or code in seen:
                raise ValueError(f'Missing or duplicate catalog component: {code}')
            seen.add(code)
            merged = {**entries.get(code, {}), **entry}
            required = set(DEFAULT_CATALOG['components'][0])
            if set(merged) != required:
                raise ValueError(f'Invalid catalog fields for {code}')
            if merged['renderer'] not in (None, 'accessor_renderer'):
                raise ValueError(f'Unknown renderer for {code}')
            for key in ['display_name', 'ontology_source', 'component_family', 'default_style_key']:
                if not isinstance(merged[key], str) or not merged[key]:
                    raise ValueError(f'{code}.{key} must be a nonempty string')
            if merged['label_priority'] not in ('low', 'medium', 'high'):
                raise ValueError(f'Invalid label priority for {code}')
            for key in ['supports_component_plot', 'supports_assembly_plot']:
                if not isinstance(merged[key], bool):
                    raise ValueError(f'{code}.{key} must be boolean')
                if merged[key] and merged['renderer'] is None:
                    raise ValueError(f'{code} enables plotting without a renderer')
            entries[code] = merged
    else:
        warnings.warn(f'{catalog_path} missing; using legacy catalog defaults', stacklevel=2)
    return style, entries


STYLE, CATALOG = load_settings()


def component_label(code):
    name = CATALOG.get(code, {}).get('display_name', code)
    return {'code': code, 'display_name': name, 'code_and_name': f'{code} — {name}'}[STYLE['labels']['format']]


def body_color(code, fallback='0.5'):
    key = CATALOG.get(code, {}).get('default_style_key', code)
    return STYLE['component_colors'].get(key, fallback)


def connector_symbol(kind):
    return STYLE['connector']['symbols'].get(kind, kind)


def label_priority(code):
    return {'high': 0, 'medium': 1, 'low': 2}[CATALOG.get(code, {}).get('label_priority', 'medium')]


def require_renderer(code, assembly=False):
    entry = CATALOG.get(code)
    key = 'supports_assembly_plot' if assembly else 'supports_component_plot'
    if entry is not None and (not entry[key] or entry['renderer'] != 'accessor_renderer'):
        raise ValueError(f'{code} does not support this plot type in the component catalog')
