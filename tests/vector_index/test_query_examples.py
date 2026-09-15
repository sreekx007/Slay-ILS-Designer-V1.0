from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.vector_index.build_chunks import build_chunks
from tools.vector_index.build_vector_index import build_vector_index
from tools.vector_index.query_vector_index import query_index


class QueryExamplesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tmpdir = tempfile.TemporaryDirectory()
        cls.index_dir = Path(cls.tmpdir.name)
        build_chunks([
            "knowledge/edes",
            "knowledge/edas",
            "knowledge/edikb/future_study_candidates",
            "knowledge/kel",
            "knowledge/edpr",
            "docs",
            "README.md",
            "framework_manifest.json",
        ], cls.index_dir)
        build_vector_index(cls.index_dir)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.tmpdir.cleanup()

    def assert_query_has(self, query: str, expected: list[str]) -> None:
        payload = query_index(query, self.index_dir, top_k=10)
        haystack = "\n".join(
            " ".join([
                result.get("source_file") or "",
                result.get("title") or "",
                " ".join(result.get("symbolic_targets", [])),
                result.get("excerpt") or "",
            ])
            for result in payload["results"]
        )
        for item in expected:
            self.assertIn(item, haystack, msg=f"{item!r} missing for query {query!r}\n{haystack}")

    def test_minimum_plan_queries(self) -> None:
        cases = [
            ("valve cannot ride rollers", ["GD-VLV", "GD-SB", "HEADER_VALVE_REQUIRES_GD_SB"]),
            ("strongback support for branch connector", ["GD-ST", "GD-B", "GD-Con", "BRANCH_TO_GD_ST_ASSOCIATION"]),
            ("vertical connector branch", ["GD_B_VERTICAL_CONNECTOR_TO_Z_BRANCH", "ILT-Z"]),
            ("base frame too large for valve", ["GD_SB_GD_ST_SUPPORT_SIZING_GATE", "GD-SB"]),
            ("similar previous plot label issue", ["PLOT_LABEL_ANNOTATION_GATE"]),
            ("is connector spacing optimized", ["GDST_PS_SPACING_CORRELATION_GAP", "future_study:GDST_PS_SPACING_BRANCH_VALVE_STRAIN_01"]),
        ]
        for query, expected in cases:
            with self.subTest(query=query):
                self.assert_query_has(query, expected)


if __name__ == "__main__":
    unittest.main()
