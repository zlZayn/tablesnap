"""Post-processing correction for common OCR errors on financial data.

Strategy
--------
1. **Validate** — if the text already matches the expected format for its
   column, pass it through unchanged.
2. **Light fix** — substitute common OCR confusions (``'`` → ``.``,
   ``O`` → ``0``, etc.) and re-check.
3. **Reject** — if still invalid, return the original text.  Do **not**
   attempt heuristic reconstruction: with PaddleOCR's strong accuracy on
   financial tables, a garbled output is more likely a genuine recognition
   failure than a simple character-swap problem, and siloed reconstruction
   risks introducing silent data errors.

The column index is used as a hint:
  - Column 0 → text (stock name) — pass through.
  - Column 1 → percentage (e.g. ``+10.02%``).
  - Column 2 → price (e.g. ``35.26``).
"""

import re

# ---------------------------------------------------------------------------
# Pattern cache
# ---------------------------------------------------------------------------
# Valid percentage:  +10.02%  -3.50%  5.00%  +0.01%
_VALID_PERCENT = re.compile(r"^[+-]?\d+\.\d+%$")
# Valid price:  35.26  169.35  5.73  100.00
_VALID_PRICE   = re.compile(r"^\d+\.\d{1,2}$")
# Chinese stock name (2-4 Han characters)
_CHINESE       = re.compile(r"^[\u4e00-\u9fff]{2,4}$")


def correct_grid(grid: list[list[str]]) -> list[list[str]]:
    """Apply :func:`correct_cell` to every cell in a 2-D grid.

    Column index is derived from position so that per-format corrections
    (percentage, price) are applied correctly.
    """
    return [
        [correct_cell(cell, col_idx) for col_idx, cell in enumerate(row)]
        for row in grid
    ]


def correct_cell(text: str, column_index: int = -1) -> str:
    """Attempt to fix a single OCR-recognised cell.

    Args:
        text:         Raw OCR output for this cell.
        column_index: Position in the row (0 = name, 1 = percent, …).

    Returns:
        Corrected text, or the original if no correction could be applied.
    """
    text = text.strip()
    if not text:
        return text

    # Column 0 — stock name: light cleanup only
    if column_index == 0:
        return _fix_name(text)

    # Column 1 — percentage
    if column_index == 1 or _has_percent_sign(text):
        return _fix_percentage(text)

    # Column 2 — price
    if column_index == 2 or _looks_like_price(text):
        return _fix_price(text)

    # Generic cleanup for any column
    return _generic_cleanup(text)


# ---------------------------------------------------------------------------
# Per-type fixers
# ---------------------------------------------------------------------------

def _fix_name(text: str) -> str:
    """Light cleanup for stock names (remove stray non-Chinese chars)."""
    cleaned = re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]", "", text)
    return cleaned or text


def _fix_percentage(text: str) -> str:
    """Apply light character substitutions to percentage strings.

    Returns the validated result, or the **original** text if the fix
    doesn't produce valid output.  No heuristic reconstruction is
    attempted — a garbled OCR output is returned as-is rather than
    silently inventing data.
    """
    text = text.strip()
    if not text:
        return text

    # Already valid
    if _VALID_PERCENT.match(text):
        return text

    # Light fix: substitute common confusions
    fixed = _substitute_confusions(text)
    return fixed if _VALID_PERCENT.match(fixed) else text


def _fix_price(text: str) -> str:
    """Apply light character substitutions to price strings."""
    text = text.strip()
    if not text:
        return text

    if _VALID_PRICE.match(text):
        return text

    fixed = _substitute_confusions(text)
    return fixed if _VALID_PRICE.match(fixed) else text


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _has_percent_sign(text: str) -> bool:
    return "%" in text


def _looks_like_price(text: str) -> bool:
    """Heuristic: contains a dot and consists mostly of digits."""
    cleaned = re.sub(r"[^\d.]", "", text)
    return bool(cleaned) and "." in cleaned


_COMMON_SUBSTITUTIONS = str.maketrans({
    "'": ".",
    "’": ".",
    "′": ".",
    "，": ".",
    ",": ".",
    "·": ".",
    "O": "0",
    "o": "0",
    "S": "5",
    "I": "1",
    "l": "1",
    "|": "1",
})


def _substitute_confusions(text: str) -> str:
    """Apply common OCR character substitutions."""
    return text.translate(_COMMON_SUBSTITUTIONS)


def _generic_cleanup(text: str) -> str:
    """Remove stray control characters and trim."""
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text).strip()
