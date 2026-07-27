"""Workflow orchestration — ties capture, OCR, and export together."""

import time

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from core.config import DEBOUNCE, HOTKEY, OUTPUT_DIR
from core.hotkey import wait_for_hotkey
from ocr.engine import recognize_text
from output.excel import export_to_excel
from capture.selector import capture_region

console = Console()


def process_screenshot() -> None:
    """Select a screen region -> OCR -> export Excel."""
    try:
        console.print("[bold]请用鼠标拖拽选择要识别的区域（按 Esc 取消）[/bold]")
        image_path = capture_region()

        if image_path is None:
            console.print("[yellow]已取消[/yellow]")
            return

        with console.status("[cyan]正在识别文字..."):
            lines = recognize_text(image_path)
        if lines:
            console.print(f"[green]识别到 {len(lines)} 行[/green]")
        else:
            console.print("[yellow]未识别到文字[/yellow]")

        console.print("[cyan]正在导出 Excel...[/cyan]")
        excel_path = export_to_excel(lines)
        console.print(f"[green]Excel 已保存到:[/green] {excel_path}")
        console.print("[bold green]完成！[/bold green]")
    except Exception as exc:
        console.print(f"[red]处理失败:[/red] {exc}")


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
        title="截图 OCR → Excel",
        border_style="cyan",
        padding=(1, 2),
    )
    console.print(panel)

    try:
        while True:
            wait_for_hotkey(HOTKEY)
            time.sleep(DEBOUNCE)
            process_screenshot()
    except KeyboardInterrupt:
        console.print("\n[green]已退出[/green]")
