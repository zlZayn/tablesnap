# Architecture

## What this tool does

Screenshots a screen region, sends it to a local vision-language model
(Ollama + qwen3-vl:4b-instruct), and saves the extracted table as an
`.xlsx` file.  Everything runs on one thread, one process.

## Why it looks the way it does

The core decision is **no OCR pipeline**.  There is no text extraction,
no column detection, no layout reconstruction.  Those are all things
the VLM handles in a single call.  The pipeline only does three things:
grab pixels, send them to the model, and write the result to disk.

This keeps the Python code small and the failure modes simple.  The
tradeoff is that table extraction quality depends entirely on the model
prompt — which is why `docs/PHILOSOPHY.md` exists.

## Runtime flow

```
run.bat → uv run python main.py → main_loop()

main_loop():
    1. _ensure_ollama()          # check API → auto-start if missing
    2. wait_for_hotkey() loop:
         │
         └─ process_screenshot():
              a) capture_region()
                 ├─ capture_screen()     # mss → Pillow RGB
                 ├─ RegionSelector.show() # tkinter overlay (blocking)
                 └─ save_temp(crop)       # temp PNG → return path
              b) OllamaClient.analyze(image_bytes)
                 └─ urllib POST → /api/generate → JSON → PSV text
              c) psv_to_xlsx(psv_text)
                 └─ csv.reader (pipe delimiter) → openpyxl → results/
```

Each cycle runs end-to-end on the main thread.  There are no background
workers, no thread pools, no async.

## Module map and call chain

```
main.py → core.pipeline.main_loop()
  → core.hotkey.wait_for_hotkey() (50 ms poll loop, main thread)
  → core.pipeline.process_screenshot()
       → capture.capture_region() (capture/selector.py:121)
            → capture.capture_screen() (capture/screen.py:17, mss → Pillow RGB)
            → RegionSelector.show() (tkinter overlay, blocks until user releases)
            → capture.save_temp() (capture/screen.py:29, crops and saves PNG)
       → vlm.OllamaClient.analyze() (vlm/client.py:49)
            builds the request body in _build_request_body()
            POSTs to {VLM_OLLAMA_URL}/api/generate
            parses JSON response, returns PSV text
       → export.psv_to_xlsx() (export/xlsx.py:104)
            fences extraction → csv.reader (pipe delimiter)
            → export_to_xlsx() → openpyxl → results/
```

### Cross-cutting concern: configuration

Everything tunable lives in `core/config.py`: paths, hotkey, overlay
settings, VLM model + URL + temperature + timeout.  No magic numbers
in any other module.

### Cross-cutting concern: error handling

Two layers:

1. **Stage level** — `process_screenshot()` wraps each stage in its own
   `try/except`; a failure in one stage prints a descriptive message and
   the hotkey loop continues so the user can retry immediately.
2. **Program level** — `main_loop()` wraps the entire body in
   `except KeyboardInterrupt` so Ctrl+C at any point exits cleanly
   (no stack trace, no batch-file prompt).

## The three stages in detail

### Stage 1: Capture

**Input:** live screen  →  **Output:** temp PNG path or `None` (cancelled)

`capture_region()` is the entry point.  It calls `capture_screen()` to
grab the entire primary monitor, then opens a `RegionSelector` tkinter
overlay.  The user drags a rectangle — the selected area shows at full
brightness while the rest stays dimmed.  On release, the region is
cropped and saved to a timestamped PNG in the OS temp directory.

Key numbers (from `core/config.py`):
| Constant | Value | Meaning |
| :--- | :--- | :--- |
| `DIM_ALPHA` | 0.3 | Background dimming level |
| `MIN_SIZE` | 10 px | Minimum selection width/height |
| `COLOR` | `#FF4444` | Selection rectangle colour |
| `LINE_W` | 2 px | Selection rectangle border width |
| `DASH` | `(4,2)` | Rectangle dash pattern |

Cancel is handled by `<Escape>` (returns `None`) and `MIN_SIZE` check
(selections < 10 px are rejected).

### Stage 2: VLM analysis

**Input:** PNG image bytes  →  **Output:** PSV text string (or error)

`OllamaClient.analyze()` (in `vlm/client.py`) base64-encodes the image
and POSTs it to `{VLM_OLLAMA_URL}/api/generate` with the request body
built in `_build_request_body()`:

- `model`: from config (`qwen3-vl:4b-instruct`)
- `temperature`: 0.1 (deterministic output)
- `num_predict`: 2048 (max tokens)
- `stream`: False (full response, no chunks)

Two prompts drive the model — defined in `vlm/prompts.py`:
- **SYSTEM_PROMPT**: role ("precise data-extraction assistant"),
  format rules (raw PSV, no markdown, no fences, pipe delimiter,
  equal columns, headers first row, empty cells blank, no quoting
  except when a cell contains `|`), and the `NO_TABLE` escape hatch.
- **USER_PROMPT**: short reminder to extract tabular data as PSV.

Possible return values:
| Response | Meaning | Pipeline action |
| :--- | :--- | :--- |
| Normal PSV text | Model extracted a table | Pass to export stage |
| `"NO_TABLE"` | Model found no table in the image | Yellow warning message |
| `"ERROR: ..."` | HTTP error, connection failure, or bad JSON | Red error message |

### Stage 3: Export to XLSX

**Input:** PSV text  →  **Output:** absolute path to `.xlsx` file

`psv_to_xlsx()` (in `export/xlsx.py`) applies one safety net: if the
VLM wrapped its output in a ` ```psv ``` markdown fence, the content
inside the fence is extracted.  The text is then split into lines,
empty lines are dropped, and each line is parsed by `csv.reader` with
`|` as delimiter.

`export_to_xlsx()` writes the parsed rows to a timestamped `.xlsx` file
under `config.OUTPUT_DIR` (`results/` by default).  Column widths are
autofitted to the longest cell value (capped at 50 characters;
`MergedCell` objects are skipped to avoid openpyxl errors).

If `psv_to_xlsx()` receives empty text after cleaning, it raises
`ValueError` — the pipeline catches this in the export-stage
`try/except` and reports it clearly.

## Ollama auto-start

`_ensure_ollama()` in `core/pipeline.py` runs once at startup:

1. Tries `GET {VLM_OLLAMA_URL}/api/tags` with a 2-second timeout.
   If reachable, returns `True` immediately.
2. If not reachable, launches `ollama serve` via `subprocess.Popen`
   with `CREATE_NO_WINDOW` (no visible console on Windows) and redirects
   stdout/stderr/stdin to `DEVNULL`.
3. Polls the same endpoint every 500 ms for up to 4 seconds.
4. Returns `True` if the API becomes reachable, `False` otherwise.

When `_ensure_ollama()` returns `False`, the banner is printed with a
yellow warning and a manual-start instruction.  The tool does **not**
block — the user can start Ollama in another window and continue using
tablesnap.

## Hotkey system

`core/hotkey.wait_for_hotkey()` polls `keyboard.is_pressed()` every
50 ms on the caller's thread (the main thread).  When the hotkey is
pressed, it waits for the key to be **released** before returning —
this prevents the debounce from immediately re-triggering the same
capture cycle.

Using polling instead of keyboard library callbacks is deliberate:
callbacks fire on background threads, which conflicts with tkinter
(which requires all UI work on the main thread).  Polling keeps
everything on one thread with no synchronization needed.

## Entry point

`main.py` (11 lines): imports `main_loop` from `core.pipeline` and
calls it under `if __name__ == "__main__"`.

`run.bat` runs `uv run python main.py` and uses `exit /b` (not
`pause`) so Ctrl+C exits cleanly without a "终止批处理操作吗" prompt.

## Dependencies

| Package | Role | Why this one |
| :--- | :--- | :--- |
| Pillow | Image blend, crop, save | Standard imaging library |
| mss | Screen capture | Fastest cross-platform option |
| keyboard | Global hotkey polling | Polling works on main thread; `pynput` uses callbacks that conflict with tkinter |
| openpyxl | XLSX read/write | Can read existing files (unlike xlsxwriter) |
| rich | Coloured console output | Structured markup for terminal |

All five are pure Python or have pre-built wheels for Windows.  No
model weights live in Python — Ollama manages the model as a separate
process.

## Tests

Three files, each with a distinct scope:

| File | Scope | Needs VLM? |
| :--- | :--- | :--- |
| `tests/test_vlm.py` | `OllamaClient.analyse()` with mocked urllib | No |
| `tests/test_xlsx.py` | `psv_to_xlsx()` PSV parsing + export | No |
| `tests/test_end_to_end.py` | Full pipeline on 6 sample images | Yes |
| `tests/read_xlsx.py` | Standalone debug tool: dump XLSX rows | No |

The E2E tests (`test_end_to_end.py`) run every image in
`tests/test_table_pics/`, save results to `tests/test_output/`,
and write a `_report.json` for reproducible `--show` mode.

## Project file map

```
tablesnap/
├── main.py                  # entry point
├── run.bat                  # launcher (exit /b)
├── pyproject.toml           # project config + dependencies
├── core/
│   ├── config.py            # all tunable parameters
│   ├── hotkey.py            # polling-based hotkey wait
│   └── pipeline.py          # main_loop + process_screenshot + _ensure_ollama
├── capture/
│   ├── __init__.py
│   ├── screen.py            # mss capture + temp PNG save
│   └── selector.py          # tkinter dimmed overlay + RegionSelector
├── vlm/
│   ├── __init__.py
│   ├── client.py            # Ollama HTTP client (stdlib only)
│   └── prompts.py           # SYSTEM_PROMPT + USER_PROMPT
├── export/
│   ├── __init__.py
│   └── xlsx.py              # psv_to_xlsx + export_to_xlsx
├── tests/
│   ├── test_vlm.py          # mocked VLM client tests
│   ├── test_xlsx.py         # PSV parsing tests
│   ├── test_end_to_end.py   # integration test on sample images
│   └── read_xlsx.py         # debug tool
└── results/                 # output XLSX directory
```
