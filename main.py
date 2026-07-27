"""Screenshot OCR to Excel — entry point.

Launches the hotkey-polling loop.  All orchestration logic lives in
:mod:`core.pipeline`.
"""

from core.pipeline import main_loop


if __name__ == "__main__":
    main_loop()
