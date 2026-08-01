# Architecture

Screenshots a region, sends it to a local VLM (Ollama +
qwen3-vl:4b-instruct), saves the extracted table as `.xlsx`.  One
thread, one process, **no OCR pipeline** — no text extraction, layout
reconstruction, or column detection.  The VLM handles all of that in a
single call.  The Python code does three things: grab pixels, POST to
the model, write the result.  Table quality depends entirely on the
prompt (`docs/PHILOSOPHY.md`).

## Runtime flow

```
Launch Tablesnap Tool.cmd → uv run python main.py → main()

main():  # two modes
  no args  → main_loop()
  file ... → _run_batch(image_paths)          # batch mode, no GUI

main_loop():
    1. spinner("checking Ollama")    # animated → cleared; result on next line
    2. print_banner()                # Rich Panel with hotkey, model, output dir
    3. wait_for_hotkey() loop:
         │
           └─ process_screenshot():            (core/pipeline.py)
                a) ts = datetime.now()         # shared timestamp
                b) print_stage("capture")       # bold cyan ▸
                c) capture_region(ts)           (capture/selector.py)
                   ├─ capture_screen()          (capture/screen.py, mss)
                   ├─ RegionSelector.show()     # tkinter overlay (blocking)
                   └─ save_temp(crop, ts)       # PNG under results/captures/
                d) _analyze_and_export(bytes, ts)  (core/pipeline.py)
                   ├─ print_stage("vlm")        # bold cyan ▸
                   ├─ OllamaClient.analyze()    (vlm/client.py)
                   │    └─ POST /api/generate → JSON → PSV text
                   ├─ print_stage("export")     # bold cyan ▸
                   └─ psv_to_xlsx(text, ts)     (export/xlsx.py)
                        └─ csv.reader (|) → openpyxl → results/{ts}.xlsx

_run_batch(image_paths):
    for path in image_paths:
        process_image_file(path)               (core/pipeline.py)
        ├─ validate: is_file + extension in _IMAGE_EXTS
        └─ _analyze_and_export(bytes, ts)      # same vlm/export stages
    → summary "N converted, M failed (T total)"  # exit code 1 if any failed
```

The capture stage exists only in the screenshot flow; batch mode feeds
`_analyze_and_export` directly from image files.  Both flows share the
VLM + export stages (and the per-stage timings), so the `vlm`/`export`
behaviour is identical.

All on one thread, no background workers, no thread pools, no async.

## Stage details

### Stage 1: Capture

**Input:** live screen  →  **Output:** PNG path under `results/captures/` or `None` (cancelled)

`capture_region()` is the entry point.  It calls `capture_screen()` to
grab the entire primary monitor, then opens a `RegionSelector` tkinter
overlay.  The user drags a rectangle — the selected area shows at full
brightness while the rest stays dimmed.  On release, the region is
cropped and saved to a timestamped PNG under `results/captures/`.

Key numbers (from `core/config.py`):
| Constant | Value | Meaning |
| :--- | :--- | :--- |
| `DIM_ALPHA` | 0.3 | Background dimming level |
| `MIN_SIZE` | 10 px | Minimum selection width/height |
| `COLOR` | `#00BCD4` | Corner-marker accent colour |
| `BORDER_COLOR` | `#666666` | Thin border line colour |
| `CORNER_SIZE` | 5 px | Corner-marker half-size |
| `LINE_W` | 1 px | Border line width |
| `LABEL_COLOR` | `#CCCCCC` | Dimension text colour |
| `LABEL_FONT` | `("Segoe UI", 10)` | Dimension text font |
| `LABEL_OFFSET` | 18 px | Gap between selection edge and label |

A dimension label (`W x H`) sits below the selection at its
bottom-right corner.

Cancel is handled by `<Escape>` (returns `None`) and `MIN_SIZE` check
(selections < 10 px are rejected).  A global Escape hook (registered via
the ``keyboard`` library) ensures Esc works even before the tkinter
window receives keyboard focus on Windows.  The "Esc 取消选择" hint
is shown in the startup banner (``output.print_banner()``) rather than
drawn on the overlay, because tkinter's font rendering for CJK
characters is unreliable across systems.

### Stage 2: VLM analysis

**Input:** PNG image bytes  →  **Output:** PSV text string (or error)

Before the stage begins the pipeline shows ``▸ vlm`` (via
``print_stage("vlm")``).  The blocking ``client.analyze()`` call is
wrapped in a transient spinner (``with spinner("vlm analyzing")``) —
an animated character rotates on the same line during the 5-20 second
Ollama call.  The character set is chosen by terminal encoding:
braille (``⠋`` and friends) on UTF-8 consoles, ASCII (``-/|\``) on
GBK / non-UTF-8 consoles, so the spinner never crashes with a
``UnicodeEncodeError``.  The spinner line is removed when the call
completes, replaced by the timing line.

`OllamaClient.analyze()` (in `vlm/client.py`) base64-encodes the image
and POSTs it to `{VLM_OLLAMA_URL}/api/generate` with the request body
built in `_build_request_body()`:

- `model`: from config (`qwen3-vl:4b-instruct`)
- `temperature`: 0.1 (deterministic output)
- `num_predict`: 2048 (max tokens)
- `stream`: False (full response, no chunks)

Two prompts drive the model — defined in `vlm/prompts.py`:
- **SYSTEM_PROMPT**: role ("precise data-extraction assistant"),
  format rules (pipe | between columns, no pipe at row start/end,
  copy every cell exactly, include ALL visible data, skip dash-only
  rows, `NO_TABLE` escape hatch), and a concrete PSV example.
- **USER_PROMPT**: short reminder to extract tabular data as PSV.

Possible return values:
| Response | Meaning | Pipeline action |
| :--- | :--- | :--- |
| Normal PSV text | Model extracted a table | Pass to export stage |
| `"NO_TABLE"` | Model found no table in the image | Yellow warning message |
| `"ERROR: ..."` | HTTP error, connection failure, or bad JSON | Red error message |

### Stage 3: Export to XLSX

**Input:** PSV text  →  **Output:** absolute path to `.xlsx` file

``▸ export`` (via ``print_stage("export")``) appears before the export
stage so the user sees that capture + analysis succeeded and writing
has begun.

`psv_to_xlsx()` (in `export/xlsx.py`) applies one safety net: if the
VLM wrapped its output in a ` ```psv ``` markdown fence, the content
inside the fence is extracted.  The text is then split into lines,
empty lines are dropped, and each line is parsed by `csv.reader` with
`|` as delimiter.  An optional `timestamp` parameter lets the caller
pass a pre-generated timestamp so the XLSX shares the same filename
stem as the screenshot PNG.

`export_to_xlsx()` writes the parsed rows to a timestamped `.xlsx` file
under `config.OUTPUT_DIR` (`results/` by default).  If a `timestamp`
is provided, it is used as the filename stem; otherwise one is
generated from the current time.  Column widths are autofitted to the
longest cell value (CJK-aware: full-width chars are counted as 2 via
`unicodedata.east_asian_width`; capped at 50 characters; `MergedCell`
objects are skipped to avoid openpyxl errors).

If `psv_to_xlsx()` receives empty text after cleaning, it raises
`ValueError` — the pipeline catches this in the export-stage
`try/except` and reports it clearly.

## Cross-cutting

### Configuration

Everything tunable lives in `core/config.py`: paths, hotkey, overlay
settings, VLM model + URL + temperature + timeout.  One exception:
the hotkey poll interval (50 ms) is a function default in
`core/hotkey.py` rather than a config constant.

**External overrides** — any whitelisted constant can be overridden at
import time without editing the file:

- `config.json` in the project root (keys must be whitelisted)
- Environment variables `TABLESNAP_<CONSTANT>` (e.g.
  `TABLESNAP_VLM_MODEL=qwen3-vl:2b-instruct`)

Precedence: **environment variable > config.json > file default.**
Because the overrides run at module level, `from core.config import X`
always binds the effective value.

Whitelisted keys (in `_OVERRIDABLE`, with their types): `HOTKEY`,
`DEBOUNCE`, `DIM_ALPHA`, `MIN_SIZE`, `COLOR`, `BORDER_COLOR`,
`CORNER_SIZE`, `LINE_W`, `LABEL_COLOR`, `LABEL_OFFSET`, `VLM_MODEL`,
`VLM_OLLAMA_URL`, `VLM_TIMEOUT`, `VLM_TEMPERATURE`, `VLM_NUM_PREDICT`,
`OUTPUT_DIR`.  `LABEL_FONT` (a tuple) and the path constants
(`PROJECT_ROOT`, `TEST_*`) are intentionally excluded.

When `OUTPUT_DIR` is overridden, `CAPTURES_DIR` is recomputed to
`<output_dir>/captures` automatically.  Invalid values (wrong type,
unparseable numbers, `None`) are silently ignored and the file default
stands.

### Console output

All user-facing output goes through `core/output.py`.  Every
`print_*()` call uses a consistent indent (`PAD` / `TIP`) and Rich
markup colour.  Other modules never import `rich` directly —
changing the look means editing one file.

```
output.py
├── print_banner()    # Rich Panel (startup); shows hotkey, model, save-path
├── print_ok()        # green (success)
├── print_warn()      # yellow (warning)
├── print_err()       # red (error)
├── print_tip()       # dim + indent + ">" (hint / suggestion)
├── print_stage()     # bold cyan ▸ (stage header)
├── print_timing()    # "label  12.34s" (elapsed time)
├── print_rule()      # Rich Rule (separator between cycles; "─" on UTF-8, "-" on GBK)
├── print_break()     # "────" (separator inside timing summary)
└── spinner()         # context manager: animated (braille on UTF-8, ASCII fallback)
```

### Error handling

Two layers:

1. **Stage level** — Capture has a dedicated inner ``try/except``;
   VLM and export rely on the outer ``try`` in ``process_screenshot()``.
   Either way, a failure prints a descriptive message (via
   ``output.print_err()`` / ``output.print_warn()``) and the hotkey loop
   continues so the user can retry immediately.
2. **Program level** — `main_loop()` wraps the entire body in
   `except KeyboardInterrupt` so Ctrl+C cleans up without a stack
   trace or batch-file prompt.

### Ollama auto-start

`_ensure_ollama()` runs once at startup, wrapped in a ``spinner()``
context manager so the user sees an animated indicator during the
check.  After the spinner exits (line cleared), a status line is
printed — matching the same pattern used for ``vlm analyze``:

```python
with spinner("checking Ollama"):
    ok = _ensure_ollama(VLM_OLLAMA_URL)
if ok:
    print_ok("ollama reachable")
else:
    print_warn(f"ollama unreachable ({VLM_OLLAMA_URL})")
```

``_ensure_ollama()`` probes ``GET {VLM_OLLAMA_URL}/api/tags``:

1. **Reachable** (2 s timeout) → return ``True``.
2. **Not reachable** → launch ``ollama serve`` (hidden, ``CREATE_NO_WINDOW``).
3. Poll every 500 ms for up to 4 s → if reachable now, return ``True``.
4. Otherwise return ``False``.

The tool does **not** block on a failure; a tip suggests manually
starting ``ollama serve`` and the banner is shown so the user can
retry at any time.

### Hotkey system

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

`main.py` dispatches on argv:

- no arguments → `main_loop()` (hotkey screenshot loop)
- `file <img> [<img>...]` → `_run_batch()` (batch conversion, no GUI)
- anything else → usage message, exit code 1

`Launch Tablesnap Tool.cmd` runs `uv run python main.py` and uses
`exit /b` (not `pause`) so Ctrl+C exits cleanly without a
"终止批处理操作吗" prompt.

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

Four files, each with a distinct scope:

| File | Scope | Needs VLM? |
| :--- | :--- | :--- |
| `tests/test_vlm.py` | `OllamaClient.analyze()` — 6 mocked cases | No |
| `tests/test_xlsx.py` | `psv_to_xlsx()` — PSV parsing, fence extraction, timestamp | No |
| `tests/test_end_to_end.py` | Full pipeline on 5 sample images | Yes |
| `tests/read_xlsx.py` | Standalone debug tool: dump XLSX rows | No |

The E2E tests (`test_end_to_end.py`) run every image in
`tests/test_table_pics/`, save results to `tests/test_output/`,
and write a `_report.json` (includes `psv_raw` + `xlsx_content`
snapshots for offline replay).  Default mode is **dump** — shows VLM
raw output side-by-side with XLSX content.  `--show` replays the last
report without calling VLM.  Running cleans stale `.xlsx` and `.json`
files first.

## Project file map

```
tablesnap/
├── main.py                  # entry point (loop / file batch dispatch)
├── Launch Tablesnap Tool.cmd  # launcher (exit /b)
├── pyproject.toml           # project config + dependencies
├── config.json              # optional runtime overrides (gitignored)
├── core/
│   ├── __init__.py          # docstring only
│   ├── config.py            # all tunable parameters + override loading
│   ├── hotkey.py            # polling-based hotkey wait
│   ├── output.py            # centralised console output (all print_*)
│   └── pipeline.py          # main_loop + process_screenshot + process_image_file + _ensure_ollama
├── capture/
│   ├── __init__.py
│   ├── screen.py            # mss capture + PNG save to captures/
│   └── selector.py          # tkinter dimmed overlay + RegionSelector
├── vlm/
│   ├── __init__.py
│   ├── client.py            # Ollama HTTP client (stdlib only)
│   └── prompts.py           # SYSTEM_PROMPT + USER_PROMPT
├── export/
│   ├── __init__.py
│   └── xlsx.py              # psv_to_xlsx + export_to_xlsx
├── tests/
│   ├── __init__.py
│   ├── test_vlm.py          # mocked VLM client tests
│   ├── test_xlsx.py         # PSV parsing tests
│   ├── test_end_to_end.py   # integration test on sample images
│   ├── read_xlsx.py         # debug tool
│   └── test_table_pics/     # 5 sample table images (139 KB compressed)
│       ├── test_data_01.png
│       ├── test_data_02.png
│       ├── test_data_03.png
│       ├── test_data_04.png
│       └── test_data_05.png
└── results/                 # output XLSX directory
    └── captures/            # screenshot PNGs (timestamped, paired with XLSX)
```
