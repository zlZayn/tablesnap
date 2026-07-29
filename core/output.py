"""Centralised output formatting.

All user-facing output goes through this module so the visual style
is consistent and can be changed in one place.
"""

import itertools
import sys
import threading
import time
from contextlib import contextmanager

from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table

# ---------------------------------------------------------------------------
# Console (single shared instance for the whole app)
# ---------------------------------------------------------------------------
console = Console()

# ---------------------------------------------------------------------------
# Spacing constants — adjust these to tune the whole look
# ---------------------------------------------------------------------------
PAD = "  "           # normal indent for most lines
TIP = "       "      # deeper indent for hint / suggestion lines

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _elapsed(sec: float) -> str:
    return f"{sec:>6.2f}s"

# ---------------------------------------------------------------------------
# Banner — shown once at startup
# ---------------------------------------------------------------------------

def print_banner(hotkey: str, output_dir: str, model_name: str = "") -> None:
    grid = Table.grid(padding=(0, 2))
    grid.add_column(justify="right", no_wrap=True)
    grid.add_column(no_wrap=True)
    grid.add_row("框选表格区域:", f"[bold cyan]{hotkey}[/bold cyan]")
    grid.add_row("取消选择:", "[dim]Esc[/dim]")
    grid.add_row("退出程序:", "[dim]Ctrl+C[/dim]")
    if model_name:
        grid.add_row("模型:", model_name)
    grid.add_row("保存至:", output_dir)
    panel = Panel(grid, title="截图 \u2192 XLSX", border_style="cyan", padding=(1, 2))
    console.print(panel)

# ---------------------------------------------------------------------------
# Status messages
# ---------------------------------------------------------------------------

def print_ok(msg: str) -> None:
    console.print(f"{PAD}[green]{msg}[/green]")

def print_warn(msg: str) -> None:
    console.print(f"{PAD}[yellow]{msg}[/yellow]")

def print_err(msg: str) -> None:
    console.print(f"{PAD}[red]{msg}[/red]")

def print_tip(msg: str) -> None:
    """Hint / suggestion — deeper indent, dim, arrow-prefixed."""
    console.print(f"{TIP}[dim]> {msg}[/dim]")

# ---------------------------------------------------------------------------
# Timing
# ---------------------------------------------------------------------------

def print_stage(label: str) -> None:
    """Stage header — clearly separated from timing lines."""
    console.print(f"{PAD}[bold cyan]\u25b8 {label}[/bold cyan]")

def print_timing(label: str, sec: float, detail: str = "") -> None:
    """Timing line: ``label  elapsed  [detail]``."""
    line = f"{PAD}{label:<20s}{_elapsed(sec)}"
    if detail:
        line += f"  {detail}"
    console.print(line)

# ---------------------------------------------------------------------------
# Separators
# ---------------------------------------------------------------------------

def print_rule() -> None:
    """Thin rule between capture cycles."""
    console.print(Rule(style="bright_black"))

def print_break() -> None:
    """Forty-dash break line used inside the timing summary."""
    console.print(f"{PAD}{'─' * 40}")

# ---------------------------------------------------------------------------
# Loading spinner
# ---------------------------------------------------------------------------

_SPINNER_CHARS = ("⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏")


class _SpinnerState:
    """Mutable holder set by caller to replace the spinner line on exit.

    If ``done`` is left empty the spinner line is cleared; otherwise it
    is replaced with ``done`` (Rich markup rendered).
    """
    def __init__(self) -> None:
        self.done = ""


@contextmanager
def spinner(text: str):
    """Animated spinner during a blocking call.

    On exit the spinner line is cleared.  To replace it with completion
    text instead, set ``state.done`` to a Rich-markup string — it will
    be printed on the same line when the spinner stops.

    Usage::

        with spinner("vlm analyzing"):
            model.analyze(image)

        with spinner("checking…") as state:
            ok = check()
            state.done = "[green]OK[/green]" if ok else "[red]FAIL[/red]"
    """
    state = _SpinnerState()
    stop = threading.Event()
    chars = itertools.cycle(_SPINNER_CHARS)

    def _spin() -> None:
        while not stop.is_set():
            sys.stdout.write(f"\r{PAD}{next(chars)} {text}")
            sys.stdout.flush()
            time.sleep(0.08)

    t = threading.Thread(target=_spin, daemon=True)
    t.start()
    try:
        yield state
    finally:
        stop.set()
        t.join(0.5)
        if state.done:
            # Replace the spinner line with completion text (Rich markup rendered)
            console.print(f"\r{PAD}{state.done}")
        else:
            # Full clear so the next line stands alone
            sys.stdout.write("\r" + " " * 80 + "\r")
            sys.stdout.flush()
