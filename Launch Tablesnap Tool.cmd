@echo off
pushd "%~dp0" || exit /b 1

uv run python main.py

if errorlevel 1 (
    echo.
    echo [Tablesnap] Failed - see output above.
    pause
)

exit /b %errorlevel%