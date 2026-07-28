"""End-to-end batch test: VLM analyze -> CSV parse -> Excel export.

Iterates over all images in ``tests/test_table_pics/`` and runs the full
VLM pipeline on each one, saving results to ``tests/test_output/`` for
manual review.

Usage:
    uv run python tests/test_end_to_end.py             # run all (auto-cleans old xlsx)
    uv run python tests/test_end_to_end.py --dump      # run all + print Excel content
    uv run python tests/test_end_to_end.py --show      # show last results (no VLM)
    uv run python tests/test_end_to_end.py --image xxx.png  # single image
"""

import sys
import time
import json
from pathlib import Path

# Force UTF-8 for terminal display (Chinese filenames / content)
try:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
except Exception:
    pass

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEST_IMAGES  = PROJECT_ROOT / "tests" / "test_table_pics"
TEST_OUTPUT  = PROJECT_ROOT / "tests" / "test_output"

sys.path.insert(0, str(PROJECT_ROOT))


# ===================================================================
#  Display helpers
# ===================================================================

def _display_excel(ws, max_rows: int = 30) -> None:
    """Print an openpyxl worksheet as rows of lists."""
    for row in ws.iter_rows(
        min_row=1,
        max_row=min(ws.max_row or 0, max_rows),
        values_only=True,
    ):
        print(f"  {list(row)}")


def _display_report(entries: list[dict]) -> None:
    """Pretty-print a saved test report (from _report.json)."""
    for entry in entries:
        print(f"=== {entry['image']} ===")
        status = entry.get("status", "?")
        if status == "ok" and entry.get("excel_path"):
            # Load the Excel to show content
            xp = entry["excel_path"]
            from openpyxl import load_workbook
            wb = load_workbook(xp)
            ws = wb.active
            if ws is not None:
                print(f"  VLM: {entry['vlm_time_s']}s  "
                      f"| Excel: {ws.max_row}r x {ws.max_column}c"
                      f"  | CSV len: {entry['csv_len']}")
                _display_excel(ws)
        else:
            print(f"  STATUS: {status}", end="")
            if entry.get("error"):
                print(f"  | ERROR: {entry['error']}", end="")
            print()
        print()


def _print_header() -> None:
    hdr = f"{'Image':40s} {'Size':>8s} {'VLM(ms)':>8s} {'Rows':>6s} {'Status':12s}"
    print(hdr)
    print("-" * 80)


def _print_row(r: dict, rows_str: str) -> None:
    vlm_ms = f"{r['vlm_time_s']*1000:.0f}" if r["vlm_time_s"] else "-"
    name = r["image"]
    # Truncate long names for table alignment
    if len(name) > 38:
        name = name[:35] + "..."
    print(f"{name:40s} {r['size_bytes']:>8d} {vlm_ms:>8s} {rows_str:>6s} {r['status']:12s}")
    if r["status"] in ("error", "parse_error", "export_error"):
        print(f"  {'':40s} error: {r['error']}")


# ===================================================================
#  Core test logic
# ===================================================================

def run_one(image_path: Path) -> dict:
    """Run the full VLM->CSV->Excel pipeline on a single image.

    Returns a dict with stats and the output Excel path (or error).
    """
    result = {
        "image": image_path.name,
        "size_bytes": image_path.stat().st_size,
        "status": "ok",
        "vlm_time_s": None,
        "csv_len": None,
        "excel_path": None,
        "error": None,
    }

    from vlm.client import OllamaClient
    from export.excel import csv_to_excel
    from core.config import VLM_OLLAMA_URL, VLM_MODEL, VLM_TIMEOUT

    client = OllamaClient(
        base_url=VLM_OLLAMA_URL,
        model=VLM_MODEL,
        timeout=VLM_TIMEOUT,
    )

    image_bytes = image_path.read_bytes()
    t0 = time.perf_counter()
    csv_text = client.analyze(image_bytes)
    t1 = time.perf_counter()
    result["vlm_time_s"] = round(t1 - t0, 2)

    if csv_text.startswith("ERROR:"):
        result["status"] = "error"
        result["error"] = csv_text
        return result

    if csv_text.strip() == "NO_TABLE":
        result["status"] = "no_table"
        result["csv_len"] = 0
        return result

    result["csv_len"] = len(csv_text)

    try:
        excel_path = csv_to_excel(csv_text, output_dir=str(TEST_OUTPUT))
        result["excel_path"] = excel_path
    except ValueError as e:
        result["status"] = "parse_error"
        result["error"] = str(e)
    except Exception as e:
        result["status"] = "export_error"
        result["error"] = f"{type(e).__name__}: {e}"

    return result


def _excel_shape(excel_path: str) -> str:
    """Return 'rowsxcols' string for a given Excel file."""
    from openpyxl import load_workbook
    try:
        wb = load_workbook(excel_path)
        ws = wb.active
        if ws is not None:
            return f"{ws.max_row}x{ws.max_column}"
        return "?"
    except Exception:
        return "?"


def _clean_output() -> None:
    """Remove old Excel files from test output to avoid accumulation."""
    count = 0
    for f in TEST_OUTPUT.glob("*.xlsx"):
        f.unlink()
        count += 1
    if count:
        print(f"(cleaned {count} stale .xlsx files)\n")


def run_all() -> list[dict]:
    """Run the pipeline on every image in TEST_IMAGES."""
    TEST_OUTPUT.mkdir(parents=True, exist_ok=True)
    _clean_output()

    images = sorted(TEST_IMAGES.glob("*.*"))
    valid_exts = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp"}
    images = [i for i in images if i.suffix.lower() in valid_exts]

    if not images:
        print(f"No test images found in {TEST_IMAGES}")
        print("Place screenshot images there and re-run.")
        return []

    _print_header()
    results = []

    for img in images:
        r = run_one(img)
        rows_str = _excel_shape(r["excel_path"]) if r["excel_path"] else "-"
        _print_row(r, rows_str)
        results.append(r)

    ok_count = sum(1 for r in results if r["status"] == "ok")
    fail_count = sum(1 for r in results if r["status"] != "ok")
    print("-" * 80)
    print(f"Total: {len(results)}  OK: {ok_count}  Failed: {fail_count}")
    print(f"\nOutput: {TEST_OUTPUT.resolve()}")

    # Persist report
    report_path = TEST_OUTPUT / "_report.json"
    report_data = [
        {
            "image": r["image"],
            "size_bytes": r["size_bytes"],
            "status": r["status"],
            "vlm_time_s": r["vlm_time_s"],
            "csv_len": r["csv_len"],
            "excel_path": r["excel_path"],
            "error": r["error"],
        }
        for r in results
    ]
    report_path.write_text(
        json.dumps(report_data, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"Report: {report_path.resolve()}")

    return results


def show_last() -> None:
    """Display results from the last saved report (no VLM calls)."""
    report_path = TEST_OUTPUT / "_report.json"
    if not report_path.exists():
        print("No saved report found. Run without --show first.")
        return
    entries = json.loads(report_path.read_text("utf-8"))
    _display_report(entries)


# ===================================================================
#  CLI
# ===================================================================

def main():
    args = [a.lower() for a in sys.argv[1:]]

    if "--show" in args:
        show_last()
        return

    if "--image" in args:
        idx = args.index("--image")
        if idx + 1 < len(sys.argv):
            target = sys.argv[idx + 1]
            img_path = TEST_IMAGES / target
            if not img_path.exists():
                print(f"Image not found: {img_path}")
                return
            r = run_one(img_path)
            rows_str = _excel_shape(r["excel_path"]) if r["excel_path"] else "-"
            _print_header()
            _print_row(r, rows_str)
            print()
            # Also print content if success
            if r["status"] == "ok" and r["excel_path"]:
                from openpyxl import load_workbook
                wb = load_workbook(r["excel_path"])
                ws = wb.active
                if ws is not None:
                    _display_excel(ws)
        return

    if "--dump" in args:
        results = run_all()
        print()
        for r in results:
            if r["status"] == "ok" and r["excel_path"]:
                from openpyxl import load_workbook
                wb = load_workbook(r["excel_path"])
                ws = wb.active
                if ws is not None:
                    print(f"=== {r['image']} ===")
                    _display_excel(ws)
                    print()
        return

    # Default: run all
    run_all()


if __name__ == "__main__":
    main()
