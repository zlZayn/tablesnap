"""Centralised configuration for the screenshot-ocr pipeline.

All tunable constants live here so that tweaking OCR behaviour,
preprocessing parameters, or output paths never requires hunting
through multiple files.
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR   = PROJECT_ROOT / "outputs"

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
# Image preprocessing
# ---------------------------------------------------------------------------
UPSCALE_FACTOR = 3.0       # enlarge image before OCR (helps small text)
CLAHE_CLIP     = 2.0       # contrast limit for CLAHE
CLAHE_TILE     = (8, 8)    # tile grid size for CLAHE
SHARPEN_AMOUNT = 1.5       # sharpening kernel centre weight

# ---------------------------------------------------------------------------
# OCR engine
# ---------------------------------------------------------------------------
OCR_CONFIDENCE_THRESHOLD = 0.0   # minimum confidence (0 = keep all)

# ---------------------------------------------------------------------------
# Column detection
# ---------------------------------------------------------------------------
ROW_GAP_MULTIPLIER = 2.5        # adaptive row-threshold multiplier
ROW_GAP_MIN       = 15          # minimum row gap (px)
COLUMN_GAP_MIN    = 20          # minimum x-gap to be a column boundary


