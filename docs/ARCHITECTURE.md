# Architecture

## Overview

Screenshot-to-excel is a single-user desktop tool that transforms a
screenshot of tabular data directly into an Excel file.  It uses a
Vision-Language Model (VLM) call: the VLM reads the screenshot holistically
and returns structured CSV text, which the tool parses and saves as an
`.xlsx` file.

No text-detection libraries, no bounding-box layout recovery,
no column-guessing heuristics.  The VLM handles all of that implicitly.

## Data Flow

The pipeline is a three-stage sequential chain with no branching.  Every
hotkey trigger runs one complete cycle on the main thread.

### Stage Sequence

1. **Capture stage** (`capture/screen.py` → `capture/selector.py`)
   - `capture_screen()` grabs the full primary monitor as a Pillow RGB
     image via `mss`.
   - `RegionSelector` displays a dimmed full-screen tkinter window.  The
     user drags a rectangle; the selected area is shown at full brightness
     (non-dimmed pixels overlaid on the dimmed background).
   - On release, the rectangle coordinates are returned.  If the area
     is below 10 px or Escape was pressed, the pipeline stops.
   - `capture_region()` crops the full-screen image to those coordinates
     and saves the cropped PNG to a temp file.  The file path is passed
     to the VLM stage.

2. **VLM stage** (`vlm/client.py`, `vlm/prompts.py`)
   - `OllamaClient.analyze()` reads the cropped PNG from disk, base64-
     encodes it, and POSTs to `http://localhost:11434/api/generate`.
- The request includes the system prompt (`SYSTEM_PROMPT`), the
user prompt (`USER_PROMPT`), and `temperature=0.1`.
   - Ollama returns a JSON response whose `"response"` field contains
     raw CSV text (or `"NO_TABLE"`).  On any HTTP/network error, the
     method returns a string starting with `"ERROR:"`.

3. **Export stage** (`export/excel.py`)
   - `csv_to_excel()` extracts CSV from the VLM text (fence detection
     safety net, then `csv.reader`).  If the text is empty, `ValueError`
     is raised.
   - `export_to_excel()` writes the parsed rows to a timestamped `.xlsx`
      file under `results/` with column-width autofit.

### Data Handoffs

| From | To | Payload |
| :--- | :--- | :--- |
| `selector.py` | `screen.py` | Region bounds (left, top, right, bottom) — passed as arguments for the crop call |
| `screen.py` | `selector.py` | Full-screen Pillow image — used both for the dimmed overlay and for the crop |
| `selector.py` | `vlm/client.py` | Cropped PNG file path — `client.analyze()` reads this from disk |
| `vlm/client.py` | `export/excel.py` | Raw CSV text string — parsed by `csv_to_excel()` |
| `export/excel.py` | `results/` directory | `.xlsx` file path — final output on disk |

The pipeline runs in the main thread only — no background workers, no
thread pools.  Each hotkey trigger runs one full capture-VLM-export cycle.

## Module Boundaries

| Layer | Responsibility | Key Files |
| :--- | :--- | :--- |
| **Entry** | Parse CLI, start hotkey loop | `main.py` |
| **Config** | Single source of truth for all tunables | `core/config.py` |
| **Orchestration** | Sequence capture → VLM → export; timing logs | `core/pipeline.py` |
| **Hotkey** | Poll keyboard state in caller's thread (tkinter-safe) | `core/hotkey.py` |
| **Capture** | Full-screen mss grab, tkinter region overlay, crop | `capture/screen.py`, `capture/selector.py` |
| **VLM** | Base64-encode image, POST to Ollama, return CSV text | `vlm/client.py`, `vlm/prompts.py` |
| **Export** | Parse CSV (fence safety net), write xlsx | `export/excel.py` |
| **Tests** | Unit tests (mocked HTTP) + E2E batch (real VLM) | `tests/` |

## Workflows

### Interactive Mode (the main use case)

1. The user double-clicks `run.bat` (or runs `uv run python main.py`).
2. `main_loop()` prints a banner with the hotkey binding (`Ctrl+Alt+S` by
   default), the output directory, and enters a `wait_for_hotkey()` loop.
3. `wait_for_hotkey()` polls `keyboard.is_pressed()` every 50 ms on the
   main thread.  When the hotkey is detected, it waits for *release* before
   returning (this prevents the debounce from immediately re-triggering).
4. `process_screenshot()` runs the three steps:
   - **Capture**: `capture_region()` → `capture_screen()` (full-screen via
     `mss`) → `RegionSelector.show()` (tkinter overlay) → crop + `save_temp()`.
   - **VLM**: `OllamaClient.analyze(image_bytes)` → base64-encode → POST to
     `http://localhost:11434/api/generate` → parse JSON response → return CSV.
   - **Export**: `csv_to_excel(csv_text)` → three-layer parse → write
      timestamped `.xlsx` to `results/`.
5. Timing for each stage is printed, along with the final file path.
6. The loop returns to hotkey polling.  `Ctrl+C` exits.

### Batch Test Mode

The test suite (`tests/test_end_to_end.py`) runs the same
`OllamaClient.analyze()` → `csv_to_excel()` path, but substitutes a
statically-saved test image for the live screen capture.

- `uv run python tests/test_end_to_end.py` iterates over every image in
  `tests/test_table_pics/`, runs the full pipeline on each, prints a
  summary table, and saves the Excel files to `tests/test_output/`.
- `--dump` adds per-file content printing after the run.
- `--show` skips VLM and re-displays the last run's `_report.json`.
- Old `.xlsx` files in `test_output/` are cleaned at the start of every
  `run_all()` call.

## Capture Subsystem

### screen.py (mss wrapper)

`capture_screen()` uses `mss` to grab the full primary monitor (index 1)
as a BGRA byte buffer and converts it to a Pillow RGB image.  `save_temp()`
writes the image to the OS temp directory with a timestamp filename.

### selector.py (tkinter overlay)

`RegionSelector` creates a full-screen, always-on-top tkinter window:

1. A dimmed copy of the desktop (original blended with black at `DIM_ALPHA`)
   is painted as the base layer.  This signals to the user that the tool is
   waiting for input.
2. On mouse press (`<ButtonPress-1>`), the origin is recorded.
3. During drag (`<B1-Motion>`):
   - A dashed rectangle is drawn between origin and current cursor position.
   - **The original (non-dimmed) pixels** inside the rectangle are overlaid
     on top of the dimmed background.  This means the selected area shows
     with full brightness while everything outside remains dimmed — the
     user sees exactly what will be captured.
4. On release (`<ButtonRelease-1>`), if the area is below `MIN_SIZE`
   (10 px), the selection is treated as cancelled.  Otherwise the cropped
   region is saved and the file path is returned.
5. `Escape` cancels at any time (returns `None`).

This inverted overlay (dimmed outer, bright inner) avoids the visual
confusion of a dark rectangle over the user's content — the selected
content is always readable at full resolution.

## VLM Subsystem

### Client Design

`OllamaClient` uses only the Python standard library (`urllib` + `json` +
`base64`).  No third-party HTTP library is needed.  Key design points:

- **Single-shot, no streaming.**  The `response` field of Ollama's
  `/api/generate` JSON is read in full.  Streaming would add complexity
  with no benefit at `num_predict=2048`.
- **No retry/backoff.**  A failure returns `"ERROR: <message>"` and the
  pipeline surfaces it to the user.  Retries belong at the user level
  (press the hotkey again).
- **Low temperature (0.1).**  Keeps the model deterministic — the same
  screenshot should produce the same (or very similar) CSV every time.
- **No structured output / JSON mode.**  The model is instructed to return
  raw CSV text.  `temperature=0.1` and `system` / `user` prompt design are
  the only steering mechanisms.

### Prompt Design

Two prompts in `vlm/prompts.py`:

- **`SYSTEM_PROMPT`** (system message): Defines the assistant's role
  ("precise data-extraction assistant"), output format (raw CSV only, no
  markdown fences), quoting rules, empty-cell handling, and the
  `NO_TABLE` contract.
- **`USER_PROMPT`** (user message): A short, direct instruction
  restating the constraints.  Having the key rules in both the system and
  user message acts as a defence against the model "forgetting" to follow
  the format.

The user message explicitly says "Do NOT wrap in ```csv markdown fences",
which contradicts `csv_to_excel()`'s first parsing layer (fence detection).
This is intentional: the E2E tests show that the model sometimes ignores
this instruction, so the parser's fence extraction serves as a safety net.

## Export Subsystem

### CSV Parsing (`csv_to_excel()`)

The parser applies one safety net: if the VLM response is wrapped inside
a ```` ```csv ```` markdown code fence, only the content inside the fence
is used.  Otherwise the entire text is parsed as CSV.  Empty lines are
dropped before parsing.

No disclaimer filtering, no column-count validation, no formula-injection
transformation — the VLM's output is written as-is (modulo fence extraction).

### Column Width Autofit

After writing all cells, the exporter iterates every column, measures the
longest cell value (skipping `MergedCell` objects to avoid openpyxl
errors), and sets the column width to `min(max_length + 2, 50)` characters.

## Configuration Hub

`core/config.py` is the single source of truth for all tunable parameters:

| Domain | Parameter | Purpose |
| :--- | :--- | :--- |
| **Paths** | `PROJECT_ROOT`, `OUTPUT_DIR` | Where to save Excel files |
| **Hotkey** | `HOTKEY`, `DEBOUNCE`, `POLL_INTERVAL` | Key binding, debounce guard, poll rate |
| **Overlay** | `DIM_ALPHA`, `MIN_SIZE`, `DASH`, `COLOR`, `LINE_W` | Visual properties of the region selector |
| **VLM** | `VLM_MODEL`, `VLM_OLLAMA_URL`, `VLM_TIMEOUT` | Which model, where, and how long to wait |

No magic numbers appear in any other file — every tunable constant is
imported from `config.py`.

## Test Infrastructure

Three test files, each with a distinct scope:

| File | Scope | VLM required? |
| :--- | :--- | :---: |
| `test_vlm.py` | `OllamaClient.analyze()` with mocked `urllib` | No |
| `test_excel.py` | `csv_to_excel()` CSV parsing + export | No |
| `test_end_to_end.py` | Full pipeline on real images | Yes |

### Unit Tests

`test_vlm.py` patches `urllib.request.urlopen` and verifies:
- Normal CSV is returned as-is.
- `NO_TABLE` is passed through.
- HTTP 500 → `"ERROR:"` prefix.
- Connection refused → client-specific error message.
- Malformed JSON → `"ERROR:"` prefix.
- The POST payload structure (model, temperature, base64 image array).

`test_excel.py` writes to `tempfile.TemporaryDirectory` and verifies:
- Basic CSV produces an `.xlsx` file.
- Markdown fence extraction works.
- Empty input raises `ValueError`.

### End-to-End Tests

`test_end_to_end.py` runs the real `OllamaClient.analyze()` + `csv_to_excel()`
on the images in `tests/test_table_pics/`.  Results go to
`tests/test_output/` and a `_report.json` is written for the `--show` mode.

Six test images (`test_data_01.png` through `test_data_06.png`) exercise
different table shapes and domains: eurostat cross-tab, product inventory,
R data.frame, vegetable sales, stock prices, and student records.

## Dependencies

Five runtime dependencies, chosen for minimal footprint and no GPU
requirement (the GPU work happens in the separate Ollama process):

| Package | Role | Alternative considered |
| :--- | :--- | :--- |
| `Pillow` | Image blend, crop, save in selector | N/A (standard) |
| `mss` | Fast cross-platform screen capture | `pyautogui` (slower, no perf gain) |
| `keyboard` | Global hotkey state polling | `pynput` (callback-based, thread conflict with tkinter) |
| `openpyxl` | Excel read/write | `xlsxwriter` (cannot read existing files) |
| `rich` | Coloured console output in hotkey loop | `colorama` (less structured output) |

The VLM (Qwen3-VL) runs as a separate Ollama process.  The client
communicates over HTTP — no Python ML libraries or GPU dependencies
are required in the Python process.
