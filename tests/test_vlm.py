"""Unit tests for vlm.client.OllamaClient."""

import json
import unittest
from unittest.mock import patch, MagicMock
import urllib.error
import urllib.request

from vlm.client import OllamaClient


class TestOllamaClient(unittest.TestCase):
    """Verify OllamaClient.analyze() handles HTTP responses, errors,
    and edge cases correctly — all via mocked urllib."""

    def setUp(self):
        self.client = OllamaClient(
            base_url="http://localhost:11434",
            model="qwen3-vl:4b-instruct",
            timeout=5,
        )
        self.sample_png = b"fake-png-bytes"

    # ------------------------------------------------------------------
    # Helper: build a mock response context manager
    # ------------------------------------------------------------------
    @staticmethod
    def _mock_response(json_body: dict, status: int = 200) -> MagicMock:
        resp = MagicMock()
        resp.__enter__.return_value = resp
        resp.__exit__.return_value = None
        resp.read.return_value = json.dumps(json_body).encode("utf-8")
        resp.status = status
        return resp

    # ------------------------------------------------------------------
    # Test 1: normal PSV response
    # ------------------------------------------------------------------
    @patch("urllib.request.urlopen")
    def test_analyze_returns_psv_response(self, mock_urlopen):
        psv_data = "Name|Age\nAlice|30\nBob|25\n"
        mock_urlopen.return_value = self._mock_response({"response": psv_data})

        result = self.client.analyze(self.sample_png)

        self.assertEqual(result, psv_data)

    # ------------------------------------------------------------------
    # Test 2: NO_TABLE response passed through
    # ------------------------------------------------------------------
    @patch("urllib.request.urlopen")
    def test_analyze_passes_no_table_through(self, mock_urlopen):
        mock_urlopen.return_value = self._mock_response({"response": "NO_TABLE"})

        result = self.client.analyze(self.sample_png)

        self.assertEqual(result, "NO_TABLE")

    # ------------------------------------------------------------------
    # Test 3: error prefix on HTTP 500
    # ------------------------------------------------------------------
    @patch("urllib.request.urlopen")
    def test_analyze_returns_error_prefix_on_http_error(self, mock_urlopen):
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="http://localhost:11434/api/generate",
            code=500,
            msg="Internal Server Error",
            hdrs={},  # type: ignore[arg-type]
            fp=None,
        )

        result = self.client.analyze(self.sample_png)

        self.assertTrue(result.startswith("ERROR:"))
        self.assertIn("500", result)

    # ------------------------------------------------------------------
    # Test 4: error prefix on connection refused
    # ------------------------------------------------------------------
    @patch("urllib.request.urlopen")
    def test_analyze_returns_error_prefix_on_connection_error(self, mock_urlopen):
        mock_urlopen.side_effect = urllib.error.URLError(
            reason="Connection refused"
        )

        result = self.client.analyze(self.sample_png)

        self.assertTrue(result.startswith("ERROR:"))
        self.assertIn("Cannot connect to Ollama", result)

    # ------------------------------------------------------------------
    # Test 5: malformed JSON response
    # ------------------------------------------------------------------
    @patch("urllib.request.urlopen")
    def test_analyze_handles_malformed_json(self, mock_urlopen):
        resp = MagicMock()
        resp.__enter__.return_value = resp
        resp.__exit__.return_value = None
        resp.read.return_value = b"not-json-at-all"

        mock_urlopen.return_value = resp
        result = self.client.analyze(self.sample_png)

        self.assertTrue(result.startswith("ERROR:"))

    # ------------------------------------------------------------------
    # Test 6: verify the POST payload is correctly structured
    # ------------------------------------------------------------------
    @patch("urllib.request.urlopen")
    def test_analyze_sends_correct_payload(self, mock_urlopen):
        mock_urlopen.return_value = self._mock_response({"response": "ok"})

        self.client.analyze(self.sample_png)

        # Extract the Request object that was passed to urlopen
        request = mock_urlopen.call_args[0][0]
        body = json.loads(request.data)

        self.assertEqual(body["model"], "qwen3-vl:4b-instruct")
        self.assertIs(body["stream"], False)
        self.assertEqual(body["temperature"], 0.1)
        self.assertEqual(body["num_predict"], 2048)
        self.assertIsInstance(body["images"], list)
        self.assertEqual(len(body["images"]), 1)


if __name__ == "__main__":
    unittest.main()
