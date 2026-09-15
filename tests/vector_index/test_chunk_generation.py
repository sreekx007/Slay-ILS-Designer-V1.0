from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.vector_index.build_chunks import build_chunks


class VectorChunkGenerationTests(unittest.TestCase):
    def test_chunk_generation_covers_core_layers_and_future_studies(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            metadata = build_chunks([
                "knowledge/edes",
                "knowledge/edas",
                "knowledge/edikb/future_study_candidates",
                "knowledge/kel",
                "knowledge/edpr",
                "docs",
                "README.md",
                "framework_manifest.json",
            ], Path(tmp))
            self.assertGreater(metadata["chunk_count"], 50)
            chunks_text = (Path(tmp) / "chunks.jsonl").read_text(encoding="utf-8")
            self.assertIn("GDST_PS_SPACING_BRANCH_VALVE_STRAIN_01", chunks_text)
            self.assertIn("Q2_02_HEADER_VALVE_REQUIRES_GD_SB", chunks_text)
            self.assertIn("GD-ST", chunks_text)
            self.assertIn("EDPR", chunks_text)


if __name__ == "__main__":
    unittest.main()
