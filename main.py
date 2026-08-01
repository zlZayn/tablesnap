"""Screenshot to Excel — entry point.

Two modes:

- No arguments:  launch the hotkey-polling loop (interactive capture).
- ``file`` subcommand:  batch-convert image files to XLSX without the GUI::

      uv run python main.py file a.png b.jpg
- ``--print-config``:  show the effective configuration and its sources.

All orchestration logic lives in :mod:`core.pipeline`.
"""

import sys
from pathlib import Path

from core.config import PROJECT_ROOT, VLM_OLLAMA_URL, effective_config
from core.output import (
    console,
    print_ok,
    print_rule,
    print_tip,
    print_warn,
    spinner,
)
from core.pipeline import _ensure_ollama, main_loop, process_image_file


_USAGE = (
    "Usage:\n"
    "  uv run python main.py                       hotkey screenshot loop\n"
    "  uv run python main.py file <img> [<img>...]  convert images to XLSX\n"
    "  uv run python main.py --print-config        show effective configuration"
)


def _print_config() -> int:
    """Show every overridable key with its effective value and source."""
    for name, (value, source) in effective_config().items():
        display = str(value) if isinstance(value, Path) else repr(value)
        console.print(f"{name:<20} {display:<40} {source}")
    print_tip(
        "configure via config.json (copy config.example.json) "
        "or TABLESNAP_<NAME> environment variables"
    )
    return 0


def _run_batch(image_paths: list[str]) -> int:
    """Run the batch pipeline over *image_paths*; returns process exit code."""
    with spinner("checking Ollama"):
        ok = _ensure_ollama(VLM_OLLAMA_URL)
    if ok:
        print_ok("ollama reachable")
    else:
        print_warn(f"ollama unreachable ({VLM_OLLAMA_URL})")
        print_tip("Auto-launch failed. Start manually:  ollama serve")
        console.print()

    ok_count = 0
    fail_count = 0
    for path in image_paths:
        print_rule()
        if process_image_file(path) is not None:
            ok_count += 1
        else:
            fail_count += 1

    print_rule()
    console.print(
        f"{ok_count} converted, {fail_count} failed "
        f"({len(image_paths)} total)"
    )
    return 1 if fail_count else 0


def main() -> int:
    """Dispatch on argv; returns the process exit code."""
    args = sys.argv[1:]

    if args and args[0] == "--print-config":
        return _print_config()

    if not args:
        if not (PROJECT_ROOT / "config.json").exists():
            print_tip(
                "no config.json — copy config.example.json to customize settings"
            )
        main_loop()
        return 0

    if args[0] == "file":
        if len(args) < 2:
            console.print(_USAGE)
            return 1
        return _run_batch(args[1:])

    console.print(f"[red]unknown command: {args[0]}[/red]")
    console.print(_USAGE)
    return 1


if __name__ == "__main__":
    sys.exit(main())
