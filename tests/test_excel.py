"""Unit tests for export.excel.csv_to_excel."""

import tempfile
import unittest
from pathlib import Path

from export.excel import csv_to_excel


class TestCsvToExcel(unittest.TestCase):
    """Verify csv_to_excel fence extraction and empty handling —
    all via temp directory isolation."""

    # ------------------------------------------------------------------
    # Test 1: basic CSV without fence
    # ------------------------------------------------------------------
    def test_basic_csv(self):
        csv = "Name,Age\nAlice,30\nBob,25"
        with tempfile.TemporaryDirectory() as tmpdir:
            path = csv_to_excel(csv, output_dir=tmpdir)
            self.assertTrue(Path(path).exists())
            self.assertTrue(path.endswith(".xlsx"))

    # ------------------------------------------------------------------
    # Test 2: CSV inside ```csv fence
    # ------------------------------------------------------------------
    def test_csv_fence_extraction(self):
        csv = (
            "Some text before\n"
            "```csv\n"
            "Name,Age\n"
            "Alice,30\n"
            "```\n"
            "Some text after"
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            path = csv_to_excel(csv, output_dir=tmpdir)
            self.assertTrue(Path(path).exists())
            self.assertTrue(path.endswith(".xlsx"))

    # ------------------------------------------------------------------
    # Test 3: empty string raises ValueError
    # ------------------------------------------------------------------
    def test_empty_raises(self):
        with self.assertRaises(ValueError):
            csv_to_excel("")


if __name__ == "__main__":
    unittest.main()
