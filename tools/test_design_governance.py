"""Governed design workflow regression checks."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class GovernedDesignWorkflow(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)

    def run_tool(self, *args, expected=0):
        env = os.environ.copy()
        env.pop('PYTHONPATH', None)
        result = subprocess.run([sys.executable, str(ROOT / 'tools' / 'run_design_workflow.py'), *map(str, args)],
                                cwd=ROOT, env=env, text=True, capture_output=True)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return result

    def test_unconfirmed_edpr_blocks_before_pipeline_outputs(self):
        edpr = self.directory / 'unconfirmed.json'
        edpr.write_text(json.dumps({'sourceRequest': {'rawText': 'Design an ILS with a valve on the header line.'}}), encoding='utf-8')
        out = self.directory / 'out'
        self.run_tool('--edpr-json', edpr, '--output-dir', out, '--solution-format', 'json', '--plot', expected=1)
        governance = json.loads((out / 'unconfirmed.design_governance.json').read_text(encoding='utf-8'))
        self.assertEqual(governance['authority'], 'tools/run_design_workflow.py')
        self.assertEqual(governance['status'], 'blocked')
        self.assertEqual(governance['allowed_output'], 'gap_report_only')
        codes = {item['code'] for item in governance['blocking_gates']}
        self.assertIn('EDPR_CONFIRMATION_REQUIRED', codes)
        self.assertFalse((out / 'unconfirmed.solution.json').exists())
        self.assertTrue(governance['stage_reports'][0]['human_remaining_actions'])
        self.assertTrue(governance['stage_reports'][-1]['human_remaining_actions'])


if __name__ == '__main__':
    unittest.main()
