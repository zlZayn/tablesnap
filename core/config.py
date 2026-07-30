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

# Test paths (shared by test scripts)
TEST_IMAGES = PROJECT_ROOT / "tests" / "test_table_pics"
TEST_OUTPUT = PROJECT_ROOT / "tests" / "test_output"

# ---------------------------------------------------------------------------
# Hotkey
# ---------------------------------------------------------------------------
HOTKEY         = "ctrl+alt+s"
DEBOUNCE       = 0.3    # seconds to ignore after a trigger
POLL_INTERVAL  = 0.05   # seconds between key-state checks

# ---------------------------------------------------------------------------
# Region selection overlay
# ---------------------------------------------------------------------------
DIM_ALPHA    = 0.3          # dimming level for overlay
MIN_SIZE     = 10            # minimum selection width/height (px)
COLOR        = "#00BCD4"     # accent colour for corner markers
BORDER_COLOR = "#666666"     # thin border line colour
CORNER_SIZE  = 5             # half-size of corner markers (px)
LINE_W       = 1             # border line width (px)

# Dimension label on selection overlay
LABEL_COLOR  = "#CCCCCC"          # dimension text colour
LABEL_FONT   = ("Segoe UI", 10)   # dimension text font
LABEL_OFFSET = 18                 # px gap between selection edge and text

# ---------------------------------------------------------------------------
# VLM (Vision Language Model)
VLM_MODEL      = "qwen3-vl:4b-instruct"            # Ollama model id
VLM_OLLAMA_URL = "http://localhost:11434"           # Ollama server base URL
VLM_TIMEOUT    = 30                                 # seconds per request
VLM_TEMPERATURE   = 0.1                             # generation temperature
VLM_NUM_PREDICT   = 2048                            # max output tokens


