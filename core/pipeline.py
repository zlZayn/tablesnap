"""Workflow orchestration — ties capture, VLM analysis, and export together."""

import subprocess
import time
import urllib.request
from datetime import datetime
from pathlib import Path

from openpyxl import load_workbook

from core.config import DEBOUNCE, HOTKEY, OUTPUT_DIR, VLM_OLLAMA_URL, VLM_MODEL, VLM_TIMEOUT
from core.hotkey import wait_for_hotkey
from core.output import (
    console,
    print_banner,
    print_break,
    print_err,
    print_ok,
    print_rule,
    print_stage,
    print_timing,
    print_tip,
    print_warn,
    spinner,
)
from vlm.client import OllamaClient
from export.xlsx import psv_to_xlsx
from capture.selector import capture_region


def _log_stage(label: str, elapsed: float, detail: str = "") -> None:
    """Timing line (delegates to output module)."""
    print_timing(label, elapsed, detail)


def _xlsx_shape(path: str) -> str:
    """Read xlsx shape quickly — '3r x 5c' or '?'."""
    try:
        wb = load_workbook(path)
        ws = wb.active
        if ws is not None:
            return f"{ws.max_row}r x {ws.max_column}c"
    except Exception:
        pass
    return "?"


def _file_href(path_str: str) -> str:
    """Return path as-is; drive-letter paths are clickable in Warp and most terminals."""
    return path_str


def process_screenshot() -> None:
    """1. Capture region → 2. VLM analyze → 3. Export to XLSX."""
    try:
        # -- Step 1: Capture --
        print_stage("capture")
        t_cap = time.perf_counter()
        # Generate timestamp once — shared by screenshot and XLSX
        ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        try:
            image_path = capture_region(timestamp=ts)
        except Exception as exc:
            _log_stage("capture", time.perf_counter() - t_cap)
            print_err(f"capture failed: {exc}")
            print_tip("Check display and permissions, then try again")
            return
        t_cap = time.perf_counter() - t_cap

        if image_path is None:
            _log_stage("capture", t_cap, "cancelled")
            return

        _log_stage("capture", t_cap)

        # -- Step 2: VLM analysis --
        print_stage("vlm")
        t_vlm = time.perf_counter()
        image_bytes = Path(image_path).read_bytes()
        client = OllamaClient(
            base_url=VLM_OLLAMA_URL,
            model=VLM_MODEL,
            timeout=VLM_TIMEOUT,
        )
        with spinner("vlm analyzing"):
            psv_text = client.analyze(image_bytes)
        t_vlm = time.perf_counter() - t_vlm
        _log_stage("vlm analyze", t_vlm)

        raw_stripped = psv_text.strip()

        # -- Step 3: Export --
        print_stage("export")
        t_xport = time.perf_counter()
        if raw_stripped.startswith("ERROR:") or raw_stripped == "NO_TABLE":
            xlsx_path = None
        else:
            xlsx_path = psv_to_xlsx(psv_text, timestamp=ts)
        t_xport = time.perf_counter() - t_xport
        _log_stage("export", t_xport)

        # -- Summary --
        total = t_cap + t_vlm + t_xport
        print_break()
        _log_stage("total", total)

        if xlsx_path:
            shape = _xlsx_shape(xlsx_path)
            extras = []
            if "```" in psv_text:
                extras.append("fenced")
            hint = f"  ({shape})" + (f"  [{', '.join(extras)}]" if extras else "")
            href = _file_href(xlsx_path)
            print_ok(f"{href}  {hint}")
        elif raw_stripped == "NO_TABLE":
            print_warn("no table detected in the selected region")
            print_tip("Make sure the area has a table with column headers")
        elif raw_stripped.startswith("ERROR:"):
            print_err(raw_stripped)
    except ValueError:
        print_warn("VLM returned unparseable output")
        print_tip("Try again, or check Ollama model status")
    except Exception as exc:
        print_err(f"unexpected error: {exc}")
        print_tip("If this persists, check the logs")


def _ensure_ollama(url: str, wait: int = 4) -> bool:
    """Check Ollama reachability; auto-start if missing.

    Returns True if API is reachable within *wait* seconds.
    """
    # Already reachable?
    try:
        req = urllib.request.Request(f"{url}/api/tags")
        urllib.request.urlopen(req, timeout=2)
        return True
    except Exception:
        pass

    # Try to start Ollama server in background (no console window)
    try:
        subprocess.Popen(
            ["ollama", "serve"],
            creationflags=subprocess.CREATE_NO_WINDOW,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
        )
    except Exception:
        return False

    for _ in range(wait * 2):
        time.sleep(0.5)
        try:
            req = urllib.request.Request(f"{url}/api/tags")
            urllib.request.urlopen(req, timeout=1)
            return True
        except Exception:
            continue
    return False


def main_loop() -> None:
    """Print banner and enter the hotkey-polling loop."""
    # Check Ollama before showing the banner so the hotkey is ready immediately.
    with spinner("checking Ollama"):
        ok = _ensure_ollama(VLM_OLLAMA_URL)
    if ok:
        print_ok("ollama reachable")
    else:
        print_warn(f"ollama unreachable ({VLM_OLLAMA_URL})")
        print_tip("Auto-launch failed. Start manually:  ollama serve")
        console.print()

    print_banner(HOTKEY.title(), str(OUTPUT_DIR.resolve()), VLM_MODEL)

    try:
        while True:
            wait_for_hotkey(HOTKEY)
            time.sleep(DEBOUNCE)
            process_screenshot()
            print_rule()
    except KeyboardInterrupt:
        console.print("\n[green]exited[/green]")
