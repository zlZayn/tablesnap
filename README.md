# tablesnap

[English](README.md) | [简体中文](README_zh.md)

Take a screenshot, let a VLM identify it directly, and export to XLSX.

## Quick start

Double-click `run.bat`, or:

```bash
cd path\to\tablesnap
uv run python main.py
```

Once started, press ``Ctrl+Alt+S`` to take a screenshot (drag to select an area). The XLSX is saved to the ``results/`` directory automatically.

> Tip: Press ``Esc`` to cancel a selection in progress.

## Prerequisites

- Python 3.8+
- [Ollama](https://ollama.com/) installed and running
- VLM model pulled: `ollama pull qwen3-vl:4b-instruct`

## How it works

1. Open the content you want to capture (a stock table, for example).
2. Press ``Ctrl+Alt+S``.
3. The screen dims — drag to select the area to identify (the original image is visible inside the selection box). Release to start recognition.
4. The XLSX file appears in the ``results/`` directory.

## Installation

```bash
uv sync
```

## Tech stack

- Selection: tkinter full-screen overlay (drag-select)
- Screenshot: mss
- Recognition: Qwen3-VL vision-language model (local Ollama)
- Export: openpyxl
- Hotkey: keyboard

## Running tests

```bash
# All unit tests (no Ollama needed)
uv run python -m pytest -v

# End-to-end test (requires Ollama + model pulled)
uv run python tests/test_end_to_end.py
```

Test output goes to `tests/test_output/`; old `.xlsx` files are cleaned before each run.

### Debug tool

Read any XLSX file as text:

```bash
uv run python tests/read_xlsx.py path/to/file.xlsx
```

## Learn more

- `docs/ARCHITECTURE.md` — workflow, modules, data flow, error handling strategy
- `docs/PHILOSOPHY.md` — design rationale: why VLM over OCR pipeline
- `docs/DEPLOYMENT.md` — step-by-step setup guide with Ollama, model pull, and troubleshooting (for AI agents)
- `core/config.py` — all configurable parameters in one place
