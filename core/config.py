"""Centralised configuration for the screenshot-to-xlsx pipeline.

All tunable constants live here so that tweaking VLM parameters,
preprocessing parameters, or output paths never requires hunting
through multiple files.
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR   = PROJECT_ROOT / "results"

# ---------------------------------------------------------------------------
# Hotkey
# ---------------------------------------------------------------------------
HOTKEY         = "ctrl+alt+s"
DEBOUNCE       = 0.3    # seconds to ignore after a trigger
POLL_INTERVAL  = 0.05   # seconds between key-state checks

# ---------------------------------------------------------------------------
# Region selection overlay
# ---------------------------------------------------------------------------
DIM_ALPHA  = 0.3          # dimming level for overlay
MIN_SIZE   = 10            # minimum selection width/height (px)
DASH       = (4, 2)        # selection-rectangle dash pattern
COLOR      = "#FF4444"     # selection-rectangle colour
LINE_W     = 2             # selection-rectangle line width

# ---------------------------------------------------------------------------
# VLM (Vision Language Model)
VLM_MODEL      = "qwen3-vl:4b-instruct"            # Ollama model id
VLM_OLLAMA_URL = "http://localhost:11434"           # Ollama server base URL
VLM_TIMEOUT    = 30                                 # seconds per request
VLM_TEMPERATURE   = 0.1                             # generation temperature
VLM_NUM_PREDICT   = 2048                            # max output tokens


