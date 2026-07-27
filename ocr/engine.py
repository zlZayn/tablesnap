"""OCR text recognition with automatic row/column detection.

Pipeline
--------
1. **Preprocess** — upscale + CLAHE + sharpen via :mod:`ocr.preprocessor`.
2. **Recognise** — run EasyOCR on the enhanced image.
3. **Cluster** — group bounding boxes into rows (y-clustering) and columns
   (x-gap analysis).
4. **Correct** — apply column-aware post-processing via :mod:`ocr.corrector`.
"""

from typing import Any, TypedDict

import numpy as np
from PIL import Image
from easyocr import Reader

from core.config import (
    COLUMN_GAP_MIN,
    OCR_CONFIDENCE_THRESHOLD,
    ROW_GAP_MIN,
    ROW_GAP_MULTIPLIER,
)
from ocr.corrector import correct_grid
from ocr.preprocessor import enhance


class _OcrItem(TypedDict):
    """Typed item returned by :func:`_extract_items`."""
    text: str
    x: float
    y: float


_reader: Reader | None = None


def get_reader() -> Reader:
    """Get the global EasyOCR Reader singleton (lazy-init)."""
    global _reader
    if _reader is None:
        _reader = Reader(["ch_sim", "en"], gpu=True)
    return _reader


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def recognize_text(image_path: str) -> list[list[str]]:
    """Recognise text in an image and return a 2-D grid with auto-detected
    rows and columns.

    Args:
        image_path: Path to the input image file.

    Returns:
        A 2-D list where ``grid[row][col]`` contains the text at that
        position, or an empty list if no text is found.
    """
    reader = get_reader()

    # 1. Preprocess
    img = Image.open(image_path).convert("RGB")
    img = enhance(img)
    img_array: np.ndarray = np.array(img)

    # 2. OCR — EasyOCR returns list of [(bbox, text, confidence), ...]
    raw_result: list[Any] = reader.readtext(img_array)

    if not raw_result:
        return []

    # 3. Build item list with centre-of-mass coordinates
    items = _extract_items(raw_result)
    if not items:
        return []

    # 4. Row clustering
    rows_grouped = _cluster_rows(items)

    # 5. Column detection
    boundaries = _detect_columns(rows_grouped)

    # 6. Assemble grid
    grid = _assemble_grid(rows_grouped, boundaries)

    # 7. Column-aware post-processing
    grid = correct_grid(grid)

    return grid


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _extract_items(
    raw_result: list[Any],
) -> list[_OcrItem]:
    """Convert EasyOCR output into a list of ``{text, x, y}``
    dicts sorted by y-coordinate.

    EasyOCR returns ``(bbox, text, confidence)`` per detection where
    ``bbox = [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]`` (corners in order).
    """
    items: list[_OcrItem] = []
    for entry in raw_result:
        box = entry[0]      # four-corner polygon
        text: str = entry[1]  # recognised string
        conf: float = entry[2]  # confidence score

        if conf < OCR_CONFIDENCE_THRESHOLD:
            continue

        # Use top-left + bottom-right for centre (same as original code)
        x_center = float(box[0][0] + box[2][0]) / 2
        y_center = float(box[0][1] + box[2][1]) / 2
        items.append({"text": text, "x": x_center, "y": y_center})

    items.sort(key=lambda i: i["y"])
    return items


def _cluster_rows(
    items: list[_OcrItem],
) -> list[list[_OcrItem]]:
    """Group items into rows via adaptive y-gap thresholding.

    The threshold is ``max(median_gap × multiplier, min_gap)`` so it
    adapts to both dense and sparse tables.
    """
    y_gaps = [
        items[i + 1]["y"] - items[i]["y"]
        for i in range(len(items) - 1)
    ]
    if y_gaps:
        y_gaps.sort()
        median_gap = y_gaps[len(y_gaps) // 2]
        row_threshold = max(median_gap * ROW_GAP_MULTIPLIER, ROW_GAP_MIN)
    else:
        row_threshold = float(ROW_GAP_MIN)

    rows = []
    current = [items[0]]
    for item in items[1:]:
        if item["y"] - current[-1]["y"] > row_threshold:
            rows.append(current)
            current = [item]
        else:
            current.append(item)
    if current:
        rows.append(current)
    return rows


def _detect_columns(
    rows_grouped: list[list[_OcrItem]],
) -> list[float]:
    """Find natural column boundaries by analysing x-gaps across all rows.

    Uses the average number of items per row to determine how many
    separators to pick (largest gaps win).
    """
    all_x = sorted(
        item["x"]
        for row in rows_grouped
        for item in row
    )

    if len(all_x) < 2:
        return []

    # Collect gaps larger than COLUMN_GAP_MIN
    x_gaps_with_pos: list[tuple[float, float, float]] = []
    for i in range(1, len(all_x)):
        gap = all_x[i] - all_x[i - 1]
        if gap > COLUMN_GAP_MIN:
            x_gaps_with_pos.append((gap, all_x[i - 1], all_x[i]))

    total_items = sum(len(row) for row in rows_grouped)
    num_rows = len(rows_grouped)
    avg_per_row = total_items / max(num_rows, 1)
    num_cols = max(1, round(avg_per_row))
    num_separators = num_cols - 1

    if num_separators > 0 and len(x_gaps_with_pos) >= num_separators:
        x_gaps_with_pos.sort(key=lambda g: g[0], reverse=True)
        boundaries = sorted(g[2] for g in x_gaps_with_pos[:num_separators])
    else:
        boundaries = []

    return boundaries


def _assemble_grid(
    rows_grouped: list[list[_OcrItem]],
    boundaries: list[float],
) -> list[list[str]]:
    """Place items into a 2-D string grid according to column boundaries."""
    grid: list[list[str]] = []
    for row_items in rows_grouped:
        row_items.sort(key=lambda i: i["x"])
        row_data = [""] * (len(boundaries) + 1)

        for item in row_items:
            col_idx = 0
            for b in boundaries:
                if item["x"] >= b:
                    col_idx += 1
                else:
                    break
            if col_idx < len(row_data):
                text: str = item["text"]
                prev = row_data[col_idx]
                row_data[col_idx] = (
                    (prev + " " + text).strip() if prev else text
                )

        while row_data and row_data[-1] == "":
            row_data.pop()
        if row_data:
            grid.append(row_data)

    return grid
