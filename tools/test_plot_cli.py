"""CLI integration checks: run with python -m unittest discover -s tools -p test_plot_cli.py."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PlotCommands(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)

    def run_cli(self, tool, *args, expected=0):
        env = os.environ.copy()
        env.pop('PYTHONPATH', None)
        result = subprocess.run([sys.executable, str(ROOT / 'tools' / tool), *map(str, args)],
                                cwd=self.directory, env=env, text=True, capture_output=True)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return result

    def test_component_defaults_overrides_and_png(self):
        from PIL import Image
        output = self.directory / 'component.png'
        self.run_cli('plot_component.py', '--component', 'GD-TP', '--set', 't_comp=0.042', '--output', output)
        with Image.open(output) as image:
            image.verify()
        report = json.loads(output.with_suffix('.report.json').read_text())
        defaults = {item['path'] for item in report['defaulted_parameters']}
        self.assertIn('pipeline.OD_pipe', defaults)
        self.assertNotIn('components.C1.t_comp', defaults)
        self.assertEqual(report['plot_qa_status'], 'passed')

    def test_archetype_warning_is_preserved(self):
        output = self.directory / 'ilt.png'
        self.run_cli('plot_design.py', '--input', ROOT / 'knowledge/edas/standard_ils_layouts.json',
                     '--archetype', 'ILS-ILT', '--output', output)
        report = json.loads(output.with_suffix('.report.json').read_text())
        self.assertEqual(report['plot_status'], 'warning')
        self.assertTrue(report['warnings'])

    def test_direct_layout_and_explicit_report(self):
        output = self.directory / 'valve.svg'
        report = self.directory / 'report.json'
        self.run_cli('plot_design.py', '--input', ROOT / 'plotters/examples/example_valve_layout.json',
                     '--output', output, '--report', report)
        self.assertIn('<svg', output.read_text())
        self.assertEqual(json.loads(report.read_text())['errors'], [])

    def test_invalid_requests_fail_without_images(self):
        cases = [
            ('plot_component.py', ['--component', 'GD-BOSS']),
            ('plot_component.py', ['--component', 'GD-TP', '--set', 't_comp=-1']),
            ('plot_component.py', ['--component', 'GD-TP', '--set', 'unknown=1']),
            ('plot_component.py', ['--component', 'GD-TP', '--set', 'centre_x=NaN']),
            ('plot_design.py', ['--input', ROOT / 'knowledge/edas/standard_ils_layouts.json']),
            ('plot_design.py', ['--input', ROOT / 'knowledge/edas/standard_ils_layouts.json', '--archetype', 'missing'])]
        for i, (tool, args) in enumerate(cases):
            with self.subTest(args=args):
                output = self.directory / f'invalid{i}.png'
                self.run_cli(tool, *args, '--output', output, expected=1)
                self.assertFalse(output.exists())
                self.assertTrue(json.loads(output.with_suffix('.report.json').read_text())['errors'])

    def test_validation_findings_block_export_and_input_is_preserved(self):
        spec = json.loads((ROOT / 'plotters/examples/example_valve_layout.json').read_text())
        spec['header'] = {'half_length': 0.1}
        source = self.directory / 'input.json'
        original = json.dumps(spec)
        source.write_text(original)
        output = self.directory / 'invalid.png'
        self.run_cli('plot_design.py', '--input', source, '--output', output, expected=1)
        self.assertFalse(output.exists())
        self.run_cli('plot_design.py', '--input', source, '--output', source, expected=1)
        self.assertEqual(source.read_text(), original)


if __name__ == '__main__':
    unittest.main()
