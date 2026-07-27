@echo off
chcp 65001 >nul
echo Building ScreenshotOCR executable...
.venv\Scripts\python.exe -m PyInstaller --onefile --windowed --name "ScreenshotOCR" --hidden-import rapidocr_onnxruntime main.py
echo Done. File: dist\ScreenshotOCR.exe
pause
