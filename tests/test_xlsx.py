"""Unit tests for export.xlsx.psv_to_xlsx."""

import tempfile
import unittest
from pathlib import Path

from export.xlsx import psv_to_xlsx


class TestPsvToXlsx(unittest.TestCase):
    """Verify psv_to_xlsx fence extraction and empty handling —
    all via temp directory isolation."""

    # ------------------------------------------------------------------
    # Test 1: basic PSV without fence
    # ------------------------------------------------------------------
    def test_basic_psv(self):
        psv = "Name|Age\nAlice|30\nBob|25"
        with tempfile.TemporaryDirectory() as tmpdir:
            path = psv_to_xlsx(psv, output_dir=tmpdir)
            self.assertTrue(Path(path).exists())
            self.assertTrue(path.endswith(".xlsx"))

    # ------------------------------------------------------------------
    # Test 2: PSV inside ```psv fence
    # ------------------------------------------------------------------
    def test_psv_fence_extraction(self):
        psv = (
            "Some text before\n"
            "```psv\n"
            "Name|Age\n"
            "Alice|30\n"
            "```\n"
            "Some text after"
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            path = psv_to_xlsx(psv, output_dir=tmpdir)
            self.assertTrue(Path(path).exists())
            self.assertTrue(path.endswith(".xlsx"))

    # ------------------------------------------------------------------
    # Test 3: empty string raises ValueError
    # ------------------------------------------------------------------
    def test_empty_raises(self):
        with self.assertRaises(ValueError):
            psv_to_xlsx("")


if __name__ == "__main__":
    unittest.main()
