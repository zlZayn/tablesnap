"""Centralised output formatting.

All user-facing output goes through this module so the visual style
is consistent and can be changed in one place.
"""

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

def print_banner(hotkey: str, output_dir: str) -> None:
    grid = Table.grid(padding=(0, 2))
    grid.add_column(width=8, justify="right", style="bold cyan")
    grid.add_column()
    grid.add_row("快捷键", hotkey.title())
    grid.add_row("操作", "拖拽选择屏幕区域")
    grid.add_row("取消截图", "Esc")
    grid.add_row("保存", output_dir)
    grid.add_row("退出程序", "Ctrl+C")
    panel = Panel(grid, title="截图 \u2192 XLSX", border_style="cyan", padding=(1, 2))
    console.print(panel)

# ---------------------------------------------------------------------------
# Status messages
# ---------------------------------------------------------------------------

def print_info(msg: str) -> None:
    """Plain text, no special colour."""
    console.print(f"{PAD}{msg}")

def print_check(msg: str) -> None:
    """Dim 'checking …' line for startup probes."""
    console.print(f"{PAD}[dim]{msg}[/dim]")

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
