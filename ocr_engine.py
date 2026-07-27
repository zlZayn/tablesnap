"""OCR text recognition with automatic row/column detection."""

from rapidocr_onnxruntime import RapidOCR


_ocr: RapidOCR | None = None


def get_ocr() -> RapidOCR:
    """Get the global OCR engine singleton."""
    global _ocr
    if _ocr is None:
        _ocr = RapidOCR()
    return _ocr


def recognize_text(image_path: str) -> list[list[str]]:
    """Recognize text in an image and return a 2D grid with auto-detected rows and columns.

    Uses OCR bounding-box coordinates to cluster text blocks into
    rows (via y-coordinate clustering with adaptive threshold) and columns
    (via x-gap analysis to find natural column boundaries).

    Args:
        image_path: Path to the input image file.

    Returns:
        A 2D list where grid[row][col] contains the text at that position,
        or an empty list if no text is found.
    """
    ocr = get_ocr()
    result, _ = ocr(image_path)

    if not result:
        return []

    items = []
    for item in result:
        box = item[0]
        text = item[1]
        x_center = (box[0][0] + box[2][0]) / 2
        y_center = (box[0][1] + box[2][1]) / 2
        items.append({'text': text, 'x': x_center, 'y': y_center})

    if not items:
        return []

    items.sort(key=lambda i: i['y'])

    y_gaps = [items[i + 1]['y'] - items[i]['y'] for i in range(len(items) - 1)]
    if y_gaps:
        y_gaps.sort()
        median_gap = y_gaps[len(y_gaps) // 2]
        row_threshold = max(median_gap * 2.5, 15)
    else:
        row_threshold = 20

    rows_grouped = []
    current_row = [items[0]]
    for item in items[1:]:
        if item['y'] - current_row[-1]['y'] > row_threshold:
            rows_grouped.append(current_row)
            current_row = [item]
        else:
            current_row.append(item)
    if current_row:
        rows_grouped.append(current_row)

    all_x = sorted([item['x'] for row in rows_grouped for item in row])

    if len(all_x) < 2:
        return [[item['text'] for item in row] for row in rows_grouped]

    x_gaps_with_pos = []
    for i in range(1, len(all_x)):
        gap = all_x[i] - all_x[i - 1]
        if gap > 20:
            x_gaps_with_pos.append((gap, all_x[i - 1], all_x[i]))

    avg_per_row = len(items) / max(len(rows_grouped), 1)
    num_cols = max(1, round(avg_per_row))
    num_separators = num_cols - 1

    if num_separators > 0 and len(x_gaps_with_pos) >= num_separators:
        x_gaps_with_pos.sort(key=lambda g: g[0], reverse=True)
        boundaries = sorted([g[2] for g in x_gaps_with_pos[:num_separators]])
    else:
        boundaries = []

    grid = []
    for row_items in rows_grouped:
        row_items.sort(key=lambda i: i['x'])
        row_data = [''] * (len(boundaries) + 1)

        for item in row_items:
            col_idx = 0
            for b in boundaries:
                if item['x'] >= b:
                    col_idx += 1
                else:
                    break
            if col_idx < len(row_data):
                prev = row_data[col_idx]
                row_data[col_idx] = (prev + ' ' + item['text']).strip() if prev else item['text']

        while row_data and row_data[-1] == '':
            row_data.pop()

        if row_data:
            grid.append(row_data)

    return grid
