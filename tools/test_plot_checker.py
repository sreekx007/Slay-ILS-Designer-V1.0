"""Adversarial checks for the basic Phase 4 QA layer."""
import copy
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'plotters'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image
from ils_builder import build_ils
from checkers.plot_checker import check_plot


class PlotCheckerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.addCleanup(plt.close, 'all')
        self.output = Path(self.temp.name) / 'plot.png'
        self.ils = build_ils({'schema_version': 1, 'pipeline': {'OD_pipe': 0.4064, 't_pipe': 0.021}, 'components': [{'code': 'GD-TP', 'centre_x': 0}]})

    def statuses(self, fig):
        return {c['id']: c['status'] for c in check_plot(fig, self.ils.components, self.output)['checks']}

    def test_valid_plot_and_geometry_unchanged(self):
        before = copy.deepcopy(self.ils.components[0].geometry_nodes())
        fig = self.ils.plot_component(0)
        fig.savefig(self.output)
        result = check_plot(fig, self.ils.components, self.output)
        self.assertEqual(result['plot_qa_status'], 'passed')
        self.assertEqual(result['corrections'], [])
        self.assertEqual(before, self.ils.components[0].geometry_nodes())

    def test_missing_and_corrupt_export(self):
        fig = self.ils.plot_component(0)
        self.assertEqual(self.statuses(fig)['output_exists'], 'failed')
        self.output.write_bytes(b'not a PNG')
        self.assertEqual(self.statuses(fig)['export_integrity'], 'failed')

    def test_blank_export_and_empty_axes(self):
        fig, ax = plt.subplots()
        Image.new('RGB', (100, 100), 'white').save(self.output)
        result = self.statuses(fig)
        self.assertEqual(result['export_nonblank'], 'failed')
        self.assertEqual(result['figure_content'], 'failed')

    def test_clipping_and_wrong_scale_warn(self):
        fig = self.ils.plot_component(0)
        ax = fig.axes[0]
        ax.set_xlim(-0.1, 0.1)
        ax.set_aspect('auto')
        fig.savefig(self.output)
        result = self.statuses(fig)
        self.assertEqual(result['geometry_clipping'], 'warning')
        self.assertEqual(result['physical_scale'], 'warning')

    def test_vector_exports_state_raster_limit(self):
        fig = self.ils.plot_component(0)
        for extension in ['svg', 'pdf']:
            self.output = self.output.with_suffix('.' + extension)
            fig.savefig(self.output)
            result = self.statuses(fig)
            self.assertEqual(result['export_integrity'], 'passed')
            self.assertEqual(result['export_nonblank'], 'not_applicable')


if __name__ == '__main__':
    unittest.main()
