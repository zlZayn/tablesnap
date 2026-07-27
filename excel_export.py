"""Excel export functionality."""

from pathlib import Path
from datetime import datetime

from openpyxl import Workbook


def export_to_excel(data: list[list[str]], output_dir: str | None = None) -> str:
    """Export a 2D grid of text data to an Excel file.

    Creates a timestamped .xlsx file under the given output directory
    (defaults to ``<project_root>/outputs/``).  Column widths are
    auto-fitted with a 50-character cap.

    Args:
        data: 2D list where ``data[row][col]`` is the cell text.
        output_dir: Output directory.  If ``None``, uses
            ``<project_root>/outputs/``.

    Returns:
        Absolute path to the generated Excel file.

    Raises:
        OSError: If the output directory cannot be created or the file
            cannot be written.
        ValueError: If ``data`` is empty.
    """
    if not data:
        raise ValueError("data must not be empty")

    if output_dir is None:
        output_dir = str(Path(__file__).resolve().parent / "outputs")

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

    for column_cells in ws.columns:
        max_length = 0
        col_letter = column_cells[0].column_letter
        for cell in column_cells:
            if cell.value is not None:
                max_length = max(max_length, len(str(cell.value)))
        ws.column_dimensions[col_letter].width = min(max_length + 2, 50)

    wb.save(str(filepath))
    return str(filepath)
