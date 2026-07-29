"""Region-selection overlay.

Shows a dimmed full-screen preview and lets the user drag a rectangle to
select the region of interest.

Usage::

    from capture.selector import capture_region
    path = capture_region()          # str | None  (None == cancelled)
"""

import tkinter as tk

import keyboard
from PIL import Image, ImageTk

from capture.screen import capture_screen, save_temp
from core.config import COLOR, DASH, DIM_ALPHA, LINE_W, MIN_SIZE


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
        self._hl_id: int | None = None        # "highlight" image item
        self._hl_photo: ImageTk.PhotoImage | None = None
        self._sx: int | None = None
        self._sy: int | None = None

        self._root = tk.Tk()
        self._root.attributes("-fullscreen", True)
        self._root.attributes("-topmost", True)
        self._root.configure(cursor="crosshair")

        # Dimmed full-screen preview (always the base layer)
        dimmed = Image.blend(
            background,
            Image.new("RGB", background.size, (0, 0, 0)),
            DIM_ALPHA,
        )
        self._photo_dimmed = ImageTk.PhotoImage(dimmed)

        self._canvas = tk.Canvas(
            self._root, highlightthickness=0, cursor="crosshair"
        )
        self._canvas.pack(fill=tk.BOTH, expand=True)
        self._canvas.create_image(0, 0, anchor=tk.NW, image=self._photo_dimmed)

        self._canvas.bind("<ButtonPress-1>", self._on_press)
        self._canvas.bind("<B1-Motion>", self._on_drag)
        self._canvas.bind("<ButtonRelease-1>", self._on_release)
        self._canvas.bind("<Escape>", self._on_cancel)
        self._root.bind("<Escape>", self._on_cancel)

        # 提示写在终端的横幅里，不在画布上叠加

    # -- public API -------------------------------------------------------

    def show(self) -> tuple[int, int, int, int] | None:
        self._root.focus_force()
        self._root.grab_set()
        # Global Escape listener (tkinter window may not have keyboard focus
        # on Windows until the user clicks — this ensures Esc works always)
        hook = keyboard.on_press_key("esc", self._on_global_esc)
        self._root.mainloop()
        keyboard.unhook_key(hook)
        self._root.destroy()
        return self._result

    def _on_global_esc(self, _event) -> None:
        """Called from the keyboard hook thread; schedule quit in the GUI thread."""
        self._root.after(0, self._on_cancel)

    # -- event handlers ---------------------------------------------------

    def _on_press(self, event: tk.Event) -> None:
        self._sx, self._sy = event.x, event.y
        if self._rect_id is not None:
            self._canvas.delete(self._rect_id)

    def _on_drag(self, event: tk.Event) -> None:
        assert self._sx is not None and self._sy is not None
        # -- Draw the dashed outline --
        if self._rect_id is not None:
            self._canvas.delete(self._rect_id)
        self._rect_id = self._canvas.create_rectangle(
            self._sx, self._sy, event.x, event.y,
            outline=COLOR, width=LINE_W, dash=DASH,
        )

        # -- Overlay the ORIGINAL (non-dimmed) pixels on the selection --
        x0, y0 = self._sx, self._sy
        x1, y1 = event.x, event.y
        left, top = min(x0, x1), min(y0, y1)
        right, bottom = max(x0, x1), max(y0, y1)

        region = self._bg.crop((left, top, right, bottom))
        self._hl_photo = ImageTk.PhotoImage(region)

        if self._hl_id is not None:
            self._canvas.delete(self._hl_id)
        self._hl_id = self._canvas.create_image(
            left, top, anchor=tk.NW, image=self._hl_photo,
        )

    def _on_release(self, event: tk.Event) -> None:
        if self._sx is None or self._sy is None:
            return  # stale release event after Esc-cancel
        x0, y0 = self._sx, self._sy
        x1, y1 = event.x, event.y
        left, top = min(x0, x1), min(y0, y1)
        right, bottom = max(x0, x1), max(y0, y1)

        if (right - left) < MIN_SIZE or (bottom - top) < MIN_SIZE:
            self._result = None
        else:
            self._result = (left, top, right, bottom)
        self._root.quit()

    def _on_cancel(self, event: tk.Event | None = None) -> None:
        self._result = None
        self._root.quit()


def capture_region() -> str | None:
    """Full-screen snapshot -> user selects region -> return cropped path.

    1. Captures the entire primary monitor.
    2. Shows a dimmed overlay where the user drags a rectangle.
    3. Crops to that rectangle and saves to a temp PNG file.

    Returns:
        Absolute path to the cropped image, or ``None`` if cancelled.
    """
    full = capture_screen()
    selector = RegionSelector(full)
    region = selector.show()

    if region is None:
        return None

    cropped = full.crop(region)
    return save_temp(cropped)
