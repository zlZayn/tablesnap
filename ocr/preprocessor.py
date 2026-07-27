"""Image preprocessing to boost OCR accuracy on small or low-contrast text.

Pipeline
--------
1. **Upscale** — enlarges the image so fine details (``+``, ``%``, ``.``)
   occupy more pixels for the OCR model.
2. **CLAHE** — Contrast Limited Adaptive Histogram Equalisation to bring
   out text on low-contrast backgrounds.
3. **Sharpen** — unsharp-mask filter to enhance edge contrast.

Usage
-----
    from ocr.preprocessor import enhance
    from PIL import Image

    img = Image.open("shot.png")
    processed = enhance(img)        # returns a new PIL Image
"""

import cv2
import numpy as np
from PIL import Image

from core.config import (
    UPSCALE_FACTOR,
    CLAHE_CLIP,
    CLAHE_TILE,
    SHARPEN_AMOUNT,
)


def enhance(img: Image.Image, scale: float | None = None) -> Image.Image:
    """Upscale, apply CLAHE, and sharpen *img*.

    Args:
        img:   Input RGB image.
        scale: Upscaling factor (``None`` = use ``config.UPSCALE_FACTOR``).

    Returns:
        A new, preprocessed PIL Image (the original is not modified).
    """
    if scale is None:
        scale = UPSCALE_FACTOR

    # PIL → numpy (OpenCV operates on BGR, but we'll stay in RGB)
    arr = np.array(img, dtype=np.uint8)

    # 1. Upscale — cubic interpolation for smoother edges
    if scale != 1.0:
        h, w = arr.shape[:2]
        new_size = (int(w * scale), int(h * scale))
        arr = cv2.resize(arr, new_size, interpolation=cv2.INTER_CUBIC)

    # 2. CLAHE on the L channel of LAB (preserves colour info)
    lab = cv2.cvtColor(arr, cv2.COLOR_RGB2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=CLAHE_CLIP, tileGridSize=CLAHE_TILE)
    l = clahe.apply(l)
    lab = cv2.merge([l, a, b])
    arr = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)

    # 3. Sharpen
    kernel = np.array([
        [0,    -SHARPEN_AMOUNT * 0.5,  0],
        [-SHARPEN_AMOUNT * 0.5, SHARPEN_AMOUNT * 2 + 1, -SHARPEN_AMOUNT * 0.5],
        [0,    -SHARPEN_AMOUNT * 0.5,  0],
    ], dtype=np.float32)
    arr = cv2.filter2D(arr, -1, kernel)

    return Image.fromarray(arr)
