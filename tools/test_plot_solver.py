import argparse
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import jsonschema
from solution_to_layout import materialize, LIBRARY
from generate_knowloop_candidate import build_candidate

ROOT = Path(__file__).resolve().parents[1]

class SolverPlotTests(unittest.TestCase):
    def test_anchor_overrides_and_source_immutable(self):
        library = json.loads(LIBRARY.read_text(encoding="utf-8"))
        before = copy.deepcopy(library)
        spec, report = materialize({"recommendation": {"recommended_candidate": "L-ST-PS"}}, library)
        self.assertEqual(library, before)
        branch = next(c for c in spec["components"] if c["id"] == "B")
        self.assertEqual(branch["support_connector"], "S")
        self.assertEqual(spec["associations"][0]["connection"], "S")
        self.assertEqual(spec["ils"]["connection_system"], "PS")
        self.assertNotIn("top_connector_x", spec["components"][0])
        self.assertTrue(report["expert_review_required"])

    def test_exact_anchor_and_unknown(self):
        spec, report = materialize({"recommendation": {"recommended_candidate": "TP-A1"}})
        self.assertEqual(spec["components"][0]["t_comp"], .032)
        self.assertFalse(report["derived_changes"])
        for name in ("unknown", None, "L-ST-PS-guess"):
            with self.assertRaises(ValueError):
                materialize({"recommendation": {"recommended_candidate": name}})

    def test_feedback_warning_failure_and_schema(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.json"
            for payload, status in [
                ({"warnings": ["overlapping labels"]}, "partial"),
                ({"errors": ["invalid geometry"]}, "failed"),
                ({"expert_review_required": True}, "partial"),
                ({"plot_status": "failed"}, "failed"),
            ]:
                path.write_text(json.dumps(payload), encoding="utf-8")
                args = argparse.Namespace(edpr_json=None, context_json=None, solution_json=None,
                    solution_md=None, outcome_status="auto", human_comment=None,
                    candidate_id=None, human_rating=None, human_reviewer=None,
                    plot_report=str(path), layout_report=None)
                candidate = build_candidate(args)
                self.assertEqual(candidate["outcome_summary"]["design_outcome_status"], status)
                self.assertFalse(candidate["promotion_policy"]["official_kb_update_allowed"])
                self.assertIsNone(candidate["human_feedback_rating"]["comment"])
                schema = json.loads((ROOT / "knowledge/knowloop/KNOWLOOP_FEEDBACK_SCHEMA.json").read_text(encoding="utf-8"))
                jsonschema.validate(candidate, schema)

    def test_edpr_pipeline_markdown_with_plot(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run([sys.executable, str(ROOT / "tools/run_edpr_pipeline.py"),
                "--edpr-json", str(ROOT / "knowledge/edpr/examples/EDPR_EXAMPLE_ILT_L_BRANCH_MIN_STRAIN.json"),
                "--output-dir", directory, "--solution-format", "md", "--plot"],
                capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            base = Path(directory)
            candidate = json.loads(next(base.glob("*.knowloop_candidate.json")).read_text())
            self.assertEqual(candidate["outcome_summary"]["recommended_candidate"], "L-ST-PS")
            self.assertEqual(candidate["outcome_summary"]["design_outcome_status"], "partial")
            self.assertTrue(next(base.glob("*.png")).stat().st_size > 1000)
            self.assertEqual(json.loads(next(base.glob("*.plot.report.json")).read_text())["errors"], [])
            jsonschema.validate(candidate, json.loads((ROOT / "knowledge/knowloop/KNOWLOOP_FEEDBACK_SCHEMA.json").read_text()))

    def test_bridge_failure_report(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source, layout, report = [base / n for n in ("solution.json", "layout.json", "report.json")]
            source.write_text('{"recommendation":{"recommended_candidate":"unknown"}}', encoding="utf-8")
            result = subprocess.run([sys.executable, str(ROOT / "tools/solution_to_layout.py"),
                "--solution", str(source), "--output", str(layout), "--report", str(report)], capture_output=True)
            self.assertEqual(result.returncode, 1)
            self.assertFalse(layout.exists())
            self.assertEqual(json.loads(report.read_text())["status"], "failed")

if __name__ == "__main__":
    unittest.main()
