"""Presentation configuration behavior and geometry preservation."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import warnings

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'plotters'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import plot_settings as settings
from ils_builder import build_ils, CLS


class PlotSettingsTests(unittest.TestCase):
    def test_catalog_covers_builder_and_includes_boss(self):
        self.assertTrue(set(CLS) <= settings.CATALOG.keys())
        self.assertTrue(settings.CATALOG['GD-BOSS']['supports_component_plot'])
        for entry in settings.CATALOG.values():
            self.assertTrue((Path(__file__).resolve().parents[1] / entry['ontology_source']).is_file())

    def test_missing_files_use_legacy_defaults(self):
        with tempfile.TemporaryDirectory() as directory, warnings.catch_warnings(record=True) as caught:
            style, catalog = settings.load_settings(directory)
        self.assertEqual(style, settings.DEFAULT_STYLE)
        self.assertEqual(len(caught), 2)
        self.assertIn('GD-TP', catalog)

    def test_partial_custom_style_and_invalid_values(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory)
            (p / 'component_catalog.json').write_text(json.dumps(settings.DEFAULT_CATALOG))
            (p / 'plot_style.yaml').write_text('figure:\n  export_dpi: 72\n')
            style, _ = settings.load_settings(p)
            self.assertEqual(style['figure']['export_dpi'], 72)
            self.assertEqual(style['fonts'], settings.DEFAULT_STYLE['fonts'])
            for text in ['figure:\n  export_dpi: -1\n', 'colors:\n  PIPE: invalid-color\n', 'unknown: 1\n']:
                (p / 'plot_style.yaml').write_text(text)
                with self.assertRaises(ValueError):
                    settings.load_settings(p)

    def test_custom_names_colors_and_width_preserve_geometry(self):
        spec = {'schema_version': 1, 'pipeline': {'OD_pipe': 0.4064, 't_pipe': 0.021},
                'components': [{'code': 'GD-TP', 'centre_x': 0.0}]}
        ils = build_ils(spec)
        before = copy.deepcopy(ils.components[0].geometry_nodes())
        definition = copy.deepcopy(ils.definition)
        custom = copy.deepcopy(settings.STYLE)
        custom['figure']['component_width'] = 10
        custom['labels']['format'] = 'display_name'
        custom['component_colors']['GD-TP'] = '#00ff00'
        with patch.dict(settings.STYLE, custom):
            # Explicit width tests the public override; defaults load at process start.
            fig = ils.plot_component(0, width=settings.STYLE['figure']['component_width'])
            self.addCleanup(plt.close, fig)
            self.assertEqual(fig.get_size_inches()[0], 10)
            self.assertIn('Thick Pipe', fig.axes[0].get_title())
            self.assertEqual(settings.body_color('GD-TP'), '#00ff00')
        self.assertEqual(ils.components[0].geometry_nodes(), before)
        self.assertEqual(ils.definition, definition)


if __name__ == '__main__':
    unittest.main()
