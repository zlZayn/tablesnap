"""Screen capture — low-level :mod:`mss` wrapper.

Provides::

    capture_screen() -> Image.Image       # full-screen capture
    save_temp(image) -> str               # persist to a temp PNG file
"""

import tempfile
from datetime import datetime
from pathlib import Path

from mss import mss
from PIL import Image


def capture_screen() -> Image.Image:
    """Capture the full primary monitor.

    Returns:
        PIL RGB Image of the entire screen.
    """
    with mss() as sct:
        mon = sct.monitors[1]
        raw = sct.grab(mon)
        return Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")


def save_temp(image: Image.Image) -> str:
    """Write *image* to a timestamped temporary PNG file.

    Returns:
        Absolute path of the saved file.
    """
    tmp = Path(tempfile.gettempdir())
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = tmp / f"screenshot_{ts}.png"
    image.save(path)
    return str(path)
