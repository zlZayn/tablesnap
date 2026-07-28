"""Ollama API client for vision-language model inference.

Sends image bytes to a locally running Ollama instance running
a vision-language model (e.g. qwen3-vl:4b-instruct) and returns
the generated text response.
"""

from __future__ import annotations

import base64
import json
import urllib.error
import urllib.request
from typing import Final

from vlm.prompts import SYSTEM_PROMPT, USER_PROMPT
from core.config import VLM_NUM_PREDICT, VLM_TEMPERATURE


class OllamaClient:
    """A lightweight client that sends images to Ollama's /api/generate endpoint.

    Uses only the Python stdlib — no third-party HTTP dependencies.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "qwen3-vl:4b-instruct",
        timeout: int = 30,
    ) -> None:
        """Initialise the Ollama client.

        Args:
            base_url: Base URL of the running Ollama server
                      (e.g. ``"http://localhost:11434"``).
            model:   The vision-language model tag to use
                      (e.g. ``"qwen3-vl:4b-instruct"``).
            timeout: Maximum time in seconds to wait for a response.
        """
        self.base_url: Final[str] = base_url.rstrip("/")
        self.model: Final[str] = model
        self.timeout: Final[int] = timeout

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze(self, image_bytes: bytes) -> str:
        """Send a PNG image to Ollama and return the model's text response.

        The image is base64-encoded and sent inside the ``images`` array of
        the ``/api/generate`` request body together with the system and user
        prompts from ``vlm.prompts``.

        Args:
            image_bytes: Raw PNG image bytes (e.g. from an ``mss`` screenshot).

        Returns:
            The raw response text — either a CSV string or ``"NO_TABLE"``.
            If the API call fails entirely, returns ``"ERROR: <brief message>"``.
        """
        # ---------- encode payload ----------
        body = self._build_request_body(image_bytes)
        data = json.dumps(body).encode("utf-8")

        # ---------- send request ----------
        try:
            req = urllib.request.Request(
                url=f"{self.base_url}/api/generate",
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                response_bytes = resp.read()
        except urllib.error.HTTPError as e:
            return (
                f"ERROR: Ollama returned HTTP {e.code} ({e.reason})\n"
                f"       → Check Ollama:  ollama serve"
            )
        except urllib.error.URLError as e:
            return (
                f"ERROR: Cannot connect to Ollama at {self.base_url}\n"
                f"       → Start Ollama:  ollama serve"
            )
        except Exception as e:
            return f"ERROR: {type(e).__name__}: {e}\n       → Try again, or check Ollama logs"

        # ---------- parse response ----------
        try:
            result = json.loads(response_bytes)
            return result.get("response", "")
        except (json.JSONDecodeError, KeyError) as e:
            return f"ERROR: Ollama returned unexpected response\n       → Try again, or check Ollama logs"

    def __repr__(self) -> str:
        return f"OllamaClient(model={self.model})"

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_request_body(self, image_bytes: bytes) -> dict:
        """Build the JSON body for the ``/api/generate`` endpoint.

        Args:
            image_bytes: Raw PNG image bytes.

        Returns:
            A dictionary ready to be serialised as the request body.
        """
        b64_image = base64.b64encode(image_bytes).decode("utf-8")
        return {
            "model": self.model,
            "prompt": USER_PROMPT,
            "system": SYSTEM_PROMPT,
            "stream": False,
            "temperature": VLM_TEMPERATURE,
            "num_predict": VLM_NUM_PREDICT,
            "images": [b64_image],
        }
