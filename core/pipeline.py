"""Workflow orchestration — ties capture, VLM analysis, and export together."""

import time
from datetime import datetime
from pathlib import Path

from openpyxl import load_workbook
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from core.config import DEBOUNCE, HOTKEY, OUTPUT_DIR, VLM_OLLAMA_URL, VLM_MODEL, VLM_TIMEOUT
from core.hotkey import wait_for_hotkey
from vlm.client import OllamaClient
from export.xlsx import psv_to_xlsx
from capture.selector import capture_region

console = Console()


def _log_stage(label: str, elapsed: float, detail: str = "") -> None:
    """Timing line."""
    padded = f"{label:<20s}"
    rest = f"{elapsed:>6.2f}s"
    if detail:
        rest += f"  {detail}"
    print(f"  {padded}{rest}")


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


def process_screenshot() -> None:
    """1. Capture region → 2. VLM analyze → 3. Export to XLSX."""
    try:
        # -- Step 1: Capture --
        print(f"  [{'capture'.center(18)}]")
        t_cap = time.perf_counter()
        image_path = capture_region()
        t_cap = time.perf_counter() - t_cap

        if image_path is None:
            _log_stage("capture", t_cap, "cancelled")
            return

        _log_stage("capture", t_cap)

        # -- Step 2: VLM analysis --
        t_vlm = time.perf_counter()
        image_bytes = Path(image_path).read_bytes()
        client = OllamaClient(
            base_url=VLM_OLLAMA_URL,
            model=VLM_MODEL,
            timeout=VLM_TIMEOUT,
        )
        psv_text = client.analyze(image_bytes)
        t_vlm = time.perf_counter() - t_vlm

        raw_stripped = psv_text.strip()

        # -- Step 3: Export --
        t_xport = time.perf_counter()
        if raw_stripped.startswith("ERROR:") or raw_stripped == "NO_TABLE":
            xlsx_path = None
        else:
            xlsx_path = psv_to_xlsx(psv_text)
        t_xport = time.perf_counter() - t_xport

        # -- Summary --
        total = t_cap + t_vlm + t_xport
        _log_stage("vlm analyze", t_vlm)
        _log_stage("export", t_xport)
        print(f"  {'─' * 40}")
        _log_stage("total", total)

        if xlsx_path:
            shape = _xlsx_shape(xlsx_path)
            extras = []
            if "```" in psv_text:
                extras.append("fenced")
            hint = f"  ({shape})" + (f"  [{', '.join(extras)}]" if extras else "")
            console.print(f"\n  [green]  {xlsx_path}  {hint}[/green]")
        elif raw_stripped == "NO_TABLE":
            console.print("\n  [yellow]no table detected in the selected region[/yellow]")
            console.print("       [dim]→ Make sure the area has a table with column headers[/dim]")
        elif raw_stripped.startswith("ERROR:"):
            console.print(f"\n  [red]{raw_stripped}[/red]")
    except ValueError as exc:
        console.print(f"\n  [yellow]VLM returned no recognizable table data[/yellow]")
        console.print(f"       [dim]→ Select a region that contains a table with column headers[/dim]")
    except Exception as exc:
        console.print(f"\n  [red]error:[/red] {exc}")


def main_loop() -> None:
    """Print banner and enter the hotkey-polling loop."""
    grid = Table.grid(padding=(0, 2))
    grid.add_column(width=8, justify="right", style="bold cyan")
    grid.add_column()
    grid.add_row("快捷键", HOTKEY.title())
    grid.add_row("操作", "拖拽选择屏幕区域")
    grid.add_row("保存", str(OUTPUT_DIR.resolve()))
    grid.add_row("退出", "Ctrl+C")

    panel = Panel(
        grid,
        title="截图 \u2192 XLSX",
        border_style="cyan",
        padding=(1, 2),
    )
    console.print(panel)

    try:
        while True:
            wait_for_hotkey(HOTKEY)
            time.sleep(DEBOUNCE)
            process_screenshot()
            console.rule(style="bright_black")
    except KeyboardInterrupt:
        console.print("\n[green]已退出[/green]")
