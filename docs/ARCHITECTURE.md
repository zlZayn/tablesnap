# Architecture

## Overview

**tablesnap** is a single-user desktop tool that transforms a screenshot of
tabular data directly into an XLSX file.  It uses a Vision-Language Model
(VLM) call: the VLM reads the screenshot holistically and returns structured
PSV (pipe-separated values) text, which the tool parses and saves as an
`.xlsx` file.

No text-detection libraries, no bounding-box layout recovery,
no column-guessing heuristics.  The VLM handles all of that implicitly.

> **Design philosophy.**  The VLM is treated as an intelligent reader, not a
> formatter.  Debugging is done at the prompt level, never via regex
> post-processing — a prompt fix raises the ceiling for *all* images, while
> a regex fix just adds a new edge case.  See `docs/PHILOSOPHY.md`.

## Data Flow

The pipeline is a three-stage sequential chain with no branching.  Every
hotkey trigger runs one complete cycle on the main thread.

### Stage Sequence

1. **Capture stage** (`capture/selector.py` → `capture/screen.py`)
   - `capture_region()` calls `capture_screen()` to grab the full primary
     monitor as a Pillow RGB image via `mss`.
   - `RegionSelector` displays a dimmed full-screen tkinter window.  The
     user drags a rectangle; the selected area is shown at full brightness
     (non-dimmed pixels overlaid on the dimmed background).
   - On release, the rectangle coordinates are returned.  If the area
     is below 10 px or Escape was pressed, the pipeline stops.
   - `capture_region()` crops the full-screen image to those coordinates
     and saves the cropped PNG to a temp file.  The file path is returned.

2. **VLM stage** (`vlm/client.py`, `vlm/prompts.py`)
   - The pipeline reads the cropped PNG from disk into a `bytes` object
     and passes it to `OllamaClient.analyze()`, which base64-encodes it
     and POSTs to `http://localhost:11434/api/generate`.
   - The request includes the system prompt (`SYSTEM_PROMPT`), the
     user prompt (`USER_PROMPT`), `temperature=0.1`, and `num_predict=2048`.
   - Ollama returns a JSON response whose `"response"` field contains
     raw PSV text (or `"NO_TABLE"`).  On any HTTP/network error, the
     method returns a string starting with `"ERROR:"`.

3. **Export stage** (`export/xlsx.py`)
   - `psv_to_xlsx()` applies one safety net: if the VLM response is
     wrapped in a ` ```psv ``` markdown code fence, only the content inside
     the fence is used.  Each line is parsed with `csv.reader`.
   - `export_to_xlsx()` writes the parsed rows to a timestamped `.xlsx`
     file under `results/` with column-width autofit (50-char cap).

### Data Handoffs

The pipeline in `core/pipeline.py` coordinates three module boundaries:

| Step | Public API | Input | Output |
| :--- | :--- | :--- | :--- |
| Capture | `capture_region()` | *(none — live screen)* | Temp PNG file path or `None` |
| VLM | `OllamaClient.analyze(image_bytes)` | PNG bytes | PSV text string |
| Export | `psv_to_xlsx(psv_text)` | PSV text | `.xlsx` file path |

Internally, `capture_region()` (in `capture/selector.py`) orchestrates three
sub-steps: it calls `capture_screen()` (in `capture/screen.py`) to grab the
monitor, hands the image to `RegionSelector.show()` to get mouse coordinates,
then crops and saves via `save_temp()` (in `capture/screen.py`).

The pipeline runs on the main thread only — no background workers, no
thread pools.  Each hotkey trigger runs one full capture–VLM–export cycle.
GUI work (tkinter overlay) happens on the same thread thanks to polling
instead of callbacks (see Hotkey section).

## Module Boundaries

| Layer | Responsibility | Key Files |
| :--- | :--- | :--- |
| **Entry** | Parse CLI, start hotkey loop | `main.py` |
| **Config** | Single source of truth for all tunables | `core/config.py` |
| **Orchestration** | Sequence capture → VLM → export; timing logs | `core/pipeline.py` |
| **Hotkey** | Poll keyboard state in caller's thread (tkinter-safe) | `core/hotkey.py` |
| **Capture** | Full-screen mss grab, tkinter region overlay, crop | `capture/screen.py`, `capture/selector.py` |
| **VLM** | Base64-encode image, POST to Ollama, return PSV text | `vlm/client.py`, `vlm/prompts.py` |
| **Export** | Parse PSV (fence safety net), write xlsx | `export/xlsx.py` |
| **Tests** | Unit tests (mocked HTTP) + E2E batch (real VLM) + debug tool | `tests/` |

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
     `http://localhost:11434/api/generate` → parse JSON response → return PSV.
   - **Export**: `psv_to_xlsx(psv_text)` → fence detection → `csv.reader`
     parse → write timestamped `.xlsx` to `results/`.
5. Timing for each stage is printed, along with the final file path
   (with shape and fence markers if applicable).  `ERROR:` and `NO_TABLE`
   responses are shown in distinct colours (red / yellow).
6. The loop returns to hotkey polling.  `Ctrl+C` exits.

### Batch Test Mode

The test suite (`tests/test_end_to_end.py`) runs the same
`OllamaClient.analyze()` → `psv_to_xlsx()` path, but substitutes a
statically-saved test image for the live screen capture.

- `uv run python tests/test_end_to_end.py` iterates over every image in
  `tests/test_table_pics/`, runs the full pipeline on each, prints a
  summary table, and saves the XLSX files to `tests/test_output/`.
- `--dump` runs all images then prints the full data flow per image:
  raw VLM output (verbatim) followed by the parsed XLSX content.
- `--image xxx.png` runs a single image and prints its XLSX content.
- `--show` skips VLM and re-displays the last run's `_report.json`.
- Old `.xlsx` files in `test_output/` are cleaned at the start of every
  `run_all()` call.
- Use `tests/read_xlsx.py` to inspect any XLSX file outside the test run
  (e.g. `uv run python tests/read_xlsx.py path/to/file.xlsx`).

### Six Test Images

| Image | Table shape | Domain |
| :--- | :--- | :--- |
| `test_data_01.png` | ~34 rows | Eurostat cross-tab (countries x years) |
| `test_data_02.png` | 6x7 | Product inventory (Chinese) |
| `test_data_03.png` | 11x2 | R data.frame listing |
| `test_data_04.png` | 18x7 | Vegetable sales records |
| `test_data_05.png` | 4x3 | Stock prices (Chinese) |
| `test_data_06.png` | 7x5 | Student records (English) |

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

`capture_region()` orchestrates all of the above: it calls
`capture_screen()`, hands the image to `RegionSelector`, then crops
and saves once the user releases the mouse.

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
  screenshot should produce the same (or very similar) PSV every time.
- **No structured output / JSON mode.**  The model is instructed to return
  raw PSV text.  `temperature=0.1` and `system` / `user` prompt design are
  the only steering mechanisms.

### Prompt Design

Two prompts in `vlm/prompts.py`, each with a clear role:

- **`SYSTEM_PROMPT`** (system message): Defines the assistant's role
  ("precise data-extraction assistant"), the output format (raw PSV only,
  no markdown, no code fences), and the structural rules: pipe delimiter
  (no leading/trailing pipes), equal column count per row, first row =
  headers, empty cells blank, preserve all visible rows, and no quoting
  unless the cell contains a `|` character.
- **`USER_PROMPT`** (user message): A short, direct instruction that
  restates the task.  Keeping it brief lets the system prompt carry
  the detailed rules while the user message anchors the model on the
  current image.

The prompts explicitly instruct *not* to wrap PSV in ` ```psv ` fences,
yet `psv_to_xlsx()` still checks for fences.  This is intentional: the
E2E tests show that the model sometimes adds fences despite the
instruction, so the parser's fence extraction serves as a safety net for
a rule the model occasionally ignores.

**Philosophy.**  The prompts avoid prescribing quoting rules, escaping
conventions, or any formatting logic the model has to "get right"
syntactically.  The VLM is trusted to understand what it reads and
separate columns correctly.  When output is malformed, the fix is always
a better prompt — never a regex post-processing layer.  See
`docs/PHILOSOPHY.md` for the full rationale.

## Export Subsystem

### PSV Parsing (`psv_to_xlsx()`)

The parser applies one safety net: if the VLM response is wrapped inside
a ` ```psv ``` markdown code fence, only the content inside the fence
is used.  Otherwise the entire text is parsed as PSV.  Empty lines are
dropped before parsing.

Each line is parsed with Python's `csv.reader` using `|` as the delimiter.
No column-count validation, no formula-injection transformation, no
quoting repair — the VLM's output is written as-is (modulo fence extraction).

### Column Width Autofit

After writing all cells, the exporter iterates every column, measures the
longest cell value (skipping `MergedCell` objects to avoid openpyxl
errors), and sets the column width to `min(max_length + 2, 50)` characters.

## Configuration Hub

`core/config.py` is the single source of truth for all tunable parameters:

| Domain | Parameter | Default | Purpose |
| :--- | :--- | :---: | :--- |
| **Paths** | `PROJECT_ROOT` | *auto* | Project root (used for relative paths) |
| | `OUTPUT_DIR` | `results/` | Where to save XLSX files |
| **Hotkey** | `HOTKEY` | `ctrl+alt+s` | Key binding |
| | `DEBOUNCE` | `0.3` | Debounce guard (seconds) |
| | `POLL_INTERVAL` | `0.05` | Key-state poll rate (seconds) |
| **Overlay** | `DIM_ALPHA` | `0.3` | Dimming level outside selection |
| | `MIN_SIZE` | `10` | Minimum selection width/height (px) |
| | `DASH` | `(4, 2)` | Selection-rectangle dash pattern |
| | `COLOR` | `#FF4444` | Selection-rectangle colour |
| | `LINE_W` | `2` | Selection-rectangle line width |
| **VLM** | `VLM_MODEL` | `qwen3-vl:4b-instruct` | Ollama model id |
| | `VLM_OLLAMA_URL` | `http://localhost:11434` | Ollama server base URL |
| | `VLM_TIMEOUT` | `30` | Request timeout (seconds) |
| | `VLM_TEMPERATURE` | `0.1` | Generation temperature |
| | `VLM_NUM_PREDICT` | `2048` | Max output tokens |

No magic numbers appear in any other module — every tunable constant is
imported from `config.py`.

## Test Infrastructure

Three test files, each with a distinct scope, plus a debugging utility:

| File | Scope | VLM required? |
| :--- | :--- | :---: |
| `test_vlm.py` | `OllamaClient.analyze()` with mocked `urllib` | No |
| `test_xlsx.py` | `psv_to_xlsx()` PSV parsing + export | No |
| `test_end_to_end.py` | Full pipeline on real images | Yes |
| `read_xlsx.py` | Debugging: dump any XLSX as rows of lists | (standalone) |

### Unit Tests

`test_vlm.py` patches `urllib.request.urlopen` and verifies:
- Normal PSV is returned as-is.
- `NO_TABLE` is passed through.
- HTTP 500 → `"ERROR:"` prefix.
- Connection refused → client-specific error message.
- Malformed JSON → `"ERROR:"` prefix.
- The POST payload structure (model, temperature, `num_predict`, base64
  image array).

`test_xlsx.py` writes to `tempfile.TemporaryDirectory` and verifies:
- Basic PSV produces an `.xlsx` file.
- Markdown fence extraction works.
- Empty input raises `ValueError`.

### End-to-End Tests

`test_end_to_end.py` runs the real `OllamaClient.analyze()` +
`psv_to_xlsx()` on the images in `tests/test_table_pics/`.  Results go to
`tests/test_output/` and a `_report.json` is written for the `--show` mode.

| Flag | Behaviour |
| :--- | :--- |
| *(none)* | Run all images, print summary table |
| `--dump` | Run all + print VLM raw output and XLSX content per image |
| `--image xxx.png` | Run single image + print XLSX content |
| `--show` | Display last run's `_report.json` (no VLM calls) |

Old `.xlsx` files in `test_output/` are cleaned at the start of every
`run_all()` call.

### Debug Tool

`tests/read_xlsx.py` is a standalone script that reads any XLSX file and
prints its content as rows of lists.  Supports `--rows N` to limit output:

```bash
uv run python tests/read_xlsx.py results/2026-07-28_193546.xlsx --rows 5
```

## Dependencies

Five runtime dependencies, chosen for minimal footprint and no GPU
requirement (the GPU work happens in the separate Ollama process):

| Package | Role | Alternative considered |
| :--- | :--- | :--- |
| `Pillow` | Image blend, crop, save in selector | N/A (standard) |
| `mss` | Fast cross-platform screen capture | `pyautogui` (slower, no perf gain) |
| `keyboard` | Global hotkey state polling | `pynput` (callback-based, thread conflict with tkinter) |
| `openpyxl` | XLSX read/write | `xlsxwriter` (cannot read existing files) |
| `rich` | Coloured console output in hotkey loop | `colorama` (less structured output) |

The VLM (Qwen3-VL) runs as a separate Ollama process.  The client
communicates over HTTP — no Python ML libraries or GPU dependencies
are required in the Python process.

## Related Documents

| File | Content |
| :--- | :--- |
| `README.md` | Quick start, usage, install, test commands |
| `docs/PHILOSOPHY.md` | Design philosophy: debugging for generality |
