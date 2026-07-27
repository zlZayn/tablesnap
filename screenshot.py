"""屏幕截图功能"""

import tempfile
from datetime import datetime
from pathlib import Path

from mss import mss
from PIL import Image


def capture_screen() -> str:
    """截取全屏并保存到临时文件.

    Returns:
        临时图片文件路径.

    Raises:
        RuntimeError: 截图或保存失败时抛出.
    """
    try:
        with mss() as sct:
            monitor = sct.monitors[1]
            screenshot = sct.grab(monitor)

            temp_dir = tempfile.gettempdir()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            temp_path = Path(temp_dir) / f"screenshot_{timestamp}.png"

            img = Image.frombytes(
                "RGB", screenshot.size, screenshot.bgra, "raw", "BGRX"
            )
            img.save(str(temp_path))

            return str(temp_path)
    except Exception as e:
        raise RuntimeError(f"截图失败: {e}") from e
