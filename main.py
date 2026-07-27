"""Screenshot OCR to Excel tool."""

from screenshot import capture_screen
from ocr_engine import recognize_text
from excel_export import export_to_excel


def main() -> None:
    path = capture_screen()
    print(f"Screenshot saved to: {path}")

    lines = recognize_text(path)
    print(f"Recognized {len(lines)} rows, {len(lines[0]) if lines else 0} columns")
    for i, line in enumerate(lines):
        print(f"Row {i + 1}: {' | '.join(line)}")

    excel_path = export_to_excel(lines)
    print(f"Excel saved to: {excel_path}")


if __name__ == "__main__":
    main()
