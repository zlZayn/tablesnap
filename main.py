"""Screenshot OCR to Excel tool."""

from screenshot import capture_screen
from ocr_engine import recognize_text


def main() -> None:
    path = capture_screen()
    print(f"Screenshot saved to: {path}")

    lines = recognize_text(path)
    print(f"Recognized {len(lines)} rows, {len(lines[0]) if lines else 0} columns")
    for i, line in enumerate(lines):
        print(f"Row {i + 1}: {' | '.join(line)}")


if __name__ == "__main__":
    main()
