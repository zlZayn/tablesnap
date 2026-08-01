"""Centralised configuration for the screenshot-to-xlsx pipeline.

All tunable constants live here so that tweaking VLM parameters,
preprocessing parameters, or output paths never requires hunting
through multiple files.
"""

import json
import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR   = PROJECT_ROOT / "results"
CAPTURES_DIR = OUTPUT_DIR / "captures"

# Test paths (shared by test scripts)
TEST_IMAGES = PROJECT_ROOT / "tests" / "test_table_pics"
TEST_OUTPUT = PROJECT_ROOT / "tests" / "test_output"

# ---------------------------------------------------------------------------
# Hotkey
# ---------------------------------------------------------------------------
HOTKEY         = "ctrl+alt+s"
DEBOUNCE       = 0.3    # seconds to ignore after a trigger

# ---------------------------------------------------------------------------
# Region selection overlay
# ---------------------------------------------------------------------------
DIM_ALPHA    = 0.3          # dimming level for overlay
MIN_SIZE     = 10            # minimum selection width/height (px)
COLOR        = "#00BCD4"     # accent colour for corner markers
BORDER_COLOR = "#666666"     # thin border line colour
CORNER_SIZE  = 5             # half-size of corner markers (px)
LINE_W       = 1             # border line width (px)

# Dimension label on selection overlay
LABEL_COLOR  = "#CCCCCC"          # dimension text colour
LABEL_FONT   = ("Segoe UI", 10)   # dimension text font
LABEL_OFFSET = 18                 # px gap between selection edge and text

# ---------------------------------------------------------------------------
# VLM (Vision Language Model)
VLM_MODEL      = "qwen3-vl:4b-instruct"            # Ollama model id
VLM_OLLAMA_URL = "http://localhost:11434"           # Ollama server base URL
VLM_TIMEOUT    = 30                                 # seconds per request
VLM_TEMPERATURE   = 0.1                             # generation temperature
VLM_NUM_PREDICT   = 2048                            # max output tokens

# ---------------------------------------------------------------------------
# External overrides (config.json + TABLESNAP_* environment variables)
# ---------------------------------------------------------------------------
# Any whitelisted constant below can be overridden at import time without
# editing this file: create a `config.json` in the project root and/or export
# `TABLESNAP_<CONSTANT>` environment variables (e.g. `TABLESNAP_VLM_MODEL`).
# Precedence: environment variable > config.json > file defaults. Because the
# overrides run at module level, `from core.config import X` always binds the
# effective value.

# Overridable constants mapped to their declared type. LABEL_FONT (a tuple)
# and the path constants (PROJECT_ROOT, TEST_*) are intentionally excluded.
_OVERRIDABLE: dict[str, type] = {
    "HOTKEY": str,
    "DEBOUNCE": float,
    "DIM_ALPHA": float,
    "MIN_SIZE": int,
    "COLOR": str,
    "BORDER_COLOR": str,
    "CORNER_SIZE": int,
    "LINE_W": int,
    "LABEL_COLOR": str,
    "LABEL_OFFSET": int,
    "VLM_MODEL": str,
    "VLM_OLLAMA_URL": str,
    "VLM_TIMEOUT": int,
    "VLM_TEMPERATURE": float,
    "VLM_NUM_PREDICT": int,
    "OUTPUT_DIR": Path,
}


def _convert(value: object, caster: type) -> object:
    """Coerce a raw override value to the constant's original type.

    Raises TypeError/ValueError when the value cannot be converted;
    callers treat that as "ignore this override".
    """
    if caster is str:
        if isinstance(value, str):
            return value
        raise TypeError(f"expected str, got {type(value).__name__}")
    if caster is int and isinstance(value, (str, float, int)):
        if isinstance(value, bool):
            raise ValueError("bool is not a valid int override")
        if isinstance(value, float) and not value.is_integer():
            raise ValueError("expected a whole number")
        return int(value)
    if caster is float and isinstance(value, (str, float, int)):
        return float(value)
    if caster is bool:
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in ("1", "true")
    raise TypeError(f"unsupported override value: {value!r}")


# Where each override came from (for --print-config source markers).
_OVERRIDE_SOURCES: dict[str, str] = {}


def _apply_override(name: str, value: object, source: str) -> None:
    """Set one module constant (and derived CAPTURES_DIR) if overridable.

    ``source`` ("config.json" / "env:TABLESNAP_*") is recorded in
    ``_OVERRIDE_SOURCES`` when the override is applied.
    """
    if name == "OUTPUT_DIR":
        if not isinstance(value, (str, Path)):
            return  # non-path value: silently ignored
        output_dir = Path(value)
        if not output_dir.is_absolute():
            output_dir = PROJECT_ROOT / output_dir  # relative to project root
        globals()["OUTPUT_DIR"] = output_dir
        globals()["CAPTURES_DIR"] = output_dir / "captures"
        _OVERRIDE_SOURCES[name] = source
        return
    caster = _OVERRIDABLE.get(name)
    if caster is None or value is None:
        return  # not whitelisted / null value: silently ignored
    try:
        globals()[name] = _convert(value, caster)
    except (TypeError, ValueError):
        return  # bad value: silently ignored
    _OVERRIDE_SOURCES[name] = source


def effective_config() -> dict[str, tuple[object, str]]:
    """Return ``{name: (effective_value, source)}`` for every overridable key.

    ``source`` is ``"default"``, ``"config.json"`` or ``"env:TABLESNAP_<NAME>"``.
    """
    return {
        name: (globals()[name], _OVERRIDE_SOURCES.get(name, "default"))
        for name in _OVERRIDABLE
    }


def _load_json_config() -> dict[str, object]:
    """Read project-root config.json; return {} if absent or malformed."""
    config_file = PROJECT_ROOT / "config.json"
    try:
        with config_file.open(encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


# File overrides first, then environment overrides on top.
for _name, _value in _load_json_config().items():
    _apply_override(_name, _value, "config.json")

for _name in _OVERRIDABLE:
    _env_value = os.environ.get("TABLESNAP_" + _name)
    if _env_value is not None:
        _apply_override(_name, _env_value, "env:TABLESNAP_" + _name)


