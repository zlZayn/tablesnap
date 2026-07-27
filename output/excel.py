"""Excel export functionality."""

from datetime import datetime
from pathlib import Path

from openpyxl import Workbook

from core.config import OUTPUT_DIR


def export_to_excel(
    data: list[list[str]],
    output_dir: str | None = None,
) -> str:
    """Export a 2-D grid of text data to an Excel file.

    Creates a timestamped ``.xlsx`` file under *output_dir* (defaults to
    ``config.OUTPUT_DIR``).  Column widths are auto-fitted with a 50-char
    cap.

    Args:
        data:       2-D list where ``data[row][col]`` is the cell text.
        output_dir: Override output directory.

    Returns:
        Absolute path to the generated Excel file.

    Raises:
        OSError:  If the directory cannot be created or the file written.
        ValueError: If *data* is empty.
    """
    if not data:
        raise ValueError("data must not be empty")

    if output_dir is None:
        output_dir = str(OUTPUT_DIR)

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    filename = f"{timestamp}.xlsx"
    filepath = output_path / filename

    wb = Workbook()
    ws = wb.active
    ws.title = "OCR Results"

    for row_idx, row in enumerate(data, start=1):
        for col_idx, cell_value in enumerate(row, start=1):
            ws.cell(row=row_idx, column=col_idx, value=cell_value)

    # Auto-fit column widths
    for column_cells in ws.columns:
        max_length = 0
        col_letter = column_cells[0].column_letter
        for cell in column_cells:
            if cell.value is not None:
                max_length = max(max_length, len(str(cell.value)))
        ws.column_dimensions[col_letter].width = min(max_length + 2, 50)

    wb.save(str(filepath))
    return str(filepath)
