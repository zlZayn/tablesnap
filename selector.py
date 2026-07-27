"""Region-selection overlay — lets the user drag a rectangle on a dimmed
full-screen preview and returns the cropped image.

Usage:
    path = capture_region()      # str | None  (None means cancelled)
"""

import tkinter as tk

from PIL import Image, ImageTk

from screenshot import capture_screen, save_temp

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_DIM_ALPHA = 0.3          # how much to darken the preview
_MIN_SIZE  = 10            # minimum selection width/height (px)
_DASH      = (4, 2)        # selection-rectangle dash pattern
_COLOR     = "#FF4444"     # selection-rectangle colour
_LINE_W    = 2             # selection-rectangle line width

# ---------------------------------------------------------------------------
# Overlay widget
# ---------------------------------------------------------------------------

class RegionSelector:
    """Full-screen, dimmed overlay that captures a mouse-drag rectangle.

    Instantiate with a PIL Image of the desktop, then call ``show()``.
    The overlay blocks (enters tkinter mainloop) until the user either
    selects a region or presses Escape.

    Returns:
        ``(left, top, right, bottom)`` pixel coordinates, or ``None``.
    """

    def __init__(self, background: Image.Image) -> None:
        self._bg = background
        self._result: tuple[int, int, int, int] | None = None
        self._rect_id: int | None = None
        self._sx: int | None = None
        self._sy: int | None = None

        self._root = tk.Tk()
        self._root.attributes("-fullscreen", True)
        self._root.attributes("-topmost", True)
        self._root.configure(cursor="crosshair")

        # Dimmed preview
        dimmed = Image.blend(
            background,
            Image.new("RGB", background.size, (0, 0, 0)),
            _DIM_ALPHA,
        )
        self._photo = ImageTk.PhotoImage(dimmed)

        self._canvas = tk.Canvas(
            self._root, highlightthickness=0, cursor="crosshair"
        )
        self._canvas.pack(fill=tk.BOTH, expand=True)
        self._canvas.create_image(0, 0, anchor=tk.NW, image=self._photo)

        self._canvas.bind("<ButtonPress-1>", self._on_press)
        self._canvas.bind("<B1-Motion>", self._on_drag)
        self._canvas.bind("<ButtonRelease-1>", self._on_release)
        self._root.bind("<Escape>", self._on_cancel)

    # -- public API -------------------------------------------------------

    def show(self) -> tuple[int, int, int, int] | None:
        self._root.mainloop()
        self._root.destroy()  # hide the overlay so the screen returns to normal
        return self._result

    # -- event handlers ---------------------------------------------------

    def _on_press(self, event: tk.Event) -> None:
        self._sx, self._sy = event.x, event.y
        if self._rect_id is not None:
            self._canvas.delete(self._rect_id)

    def _on_drag(self, event: tk.Event) -> None:
        if self._rect_id is not None:
            self._canvas.delete(self._rect_id)
        self._rect_id = self._canvas.create_rectangle(
            self._sx, self._sy, event.x, event.y,
            outline=_COLOR, width=_LINE_W, dash=_DASH,
        )

    def _on_release(self, event: tk.Event) -> None:
        x0, y0 = self._sx, self._sy
        x1, y1 = event.x, event.y

        left, top = min(x0, x1), min(y0, y1)
        right, bottom = max(x0, x1), max(y0, y1)

        if (right - left) < _MIN_SIZE or (bottom - top) < _MIN_SIZE:
            self._result = None
        else:
            self._result = (left, top, right, bottom)
        self._root.quit()

    def _on_cancel(self, event: tk.Event | None = None) -> None:
        self._result = None
        self._root.quit()


# ---------------------------------------------------------------------------
# Public convenience function
# ---------------------------------------------------------------------------

def capture_region() -> str | None:
    """Full-screen snapshot → user selects region → return cropped path.

    1. Captures the entire primary monitor.
    2. Shows a dimmed overlay where the user drags a rectangle.
    3. Crops to that rectangle and saves to a temp PNG file.

    Returns:
        Absolute path to the cropped image, or *None* if the user cancelled.
    """
    full = capture_screen()
    selector = RegionSelector(full)
    region = selector.show()

    if region is None:
        return None

    cropped = full.crop(region)
    return save_temp(cropped)
