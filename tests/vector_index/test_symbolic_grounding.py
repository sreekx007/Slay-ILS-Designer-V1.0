from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.vector_index.build_chunks import build_chunks
from tools.vector_index.build_vector_index import build_vector_index
from tools.vector_index.ground_retrieval import ground_results
from tools.vector_index.query_vector_index import query_index


class SymbolicGroundingTests(unittest.TestCase):
    def test_grounding_returns_layered_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            index_dir = Path(tmp)
            build_chunks(None or [
                "knowledge/edes",
                "knowledge/edas",
                "knowledge/edikb/future_study_candidates",
                "knowledge/kel",
                "README.md",
                "framework_manifest.json",
            ], index_dir)
            build_vector_index(index_dir)
            query_payload = query_index("valve cannot ride rollers", index_dir, top_k=8)
            grounded = ground_results(query_payload)
            all_grounded = " ".join(" ".join(values) for values in grounded["grounded_candidates"].values())
            self.assertIn("GD-VLV", all_grounded)
            self.assertIn("GD-SB", all_grounded)
            self.assertIn("HEADER_VALVE_REQUIRES_GD_SB", all_grounded)
            self.assertEqual([], grounded["unresolved_chunks"])


if __name__ == "__main__":
    unittest.main()
