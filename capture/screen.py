"""Screen capture — low-level :mod:`mss` wrapper.

Provides::

    capture_screen() -> Image.Image       # full-screen capture
    save_temp(image) -> str               # persist to a PNG under CAPTURES_DIR
"""

from datetime import datetime
from pathlib import Path

from mss import mss
from PIL import Image

from core.config import CAPTURES_DIR


def capture_screen() -> Image.Image:
    """Capture the full primary monitor.

    Returns:
        PIL RGB Image of the entire screen.
    """
    with mss() as sct:
        mon = sct.monitors[1]
        raw = sct.grab(mon)
        return Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")


def save_temp(image: Image.Image, timestamp: str | None = None) -> str:
    """Write *image* to a timestamped PNG file under ``CAPTURES_DIR``.

    Args:
        image:     PIL Image to save.
        timestamp: Optional pre-generated timestamp string (format
                   ``YYYY-MM-DD_HHMMSS``).  When ``None`` a new one is
                   generated from the current time.

    Returns:
        Absolute path of the saved file.
    """
    CAPTURES_DIR.mkdir(parents=True, exist_ok=True)
    ts = timestamp or datetime.now().strftime("%Y-%m-%d_%H%M%S")
    path = CAPTURES_DIR / f"{ts}.png"
    image.save(path)
    return str(path)
