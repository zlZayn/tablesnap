"""Global-hotkey polling — non-blocking, main-thread safe.

The ``keyboard`` library's ``add_hotkey`` dispatches callbacks on a
background thread, which conflicts with GUI frameworks (tkinter, etc.)
that require all UI work to happen on the main thread.

This module uses **polling** instead: ``wait_for_hotkey()`` loops in the
*caller's* thread, so it is safe to use alongside tkinter.
"""

import time

import keyboard

_POLL_INTERVAL = 0.05  # seconds between key-state checks


def wait_for_hotkey(hotkey: str, poll_interval: float = _POLL_INTERVAL) -> None:
    """Block the current thread until *hotkey* is pressed.

    Args:
        hotkey: Key combination understood by ``keyboard.is_pressed``,
            e.g. ``"ctrl+alt+s"``.
        poll_interval: Seconds between key-state polls (default 50 ms).
    """
    while True:
        if keyboard.is_pressed(hotkey):
            return
        time.sleep(poll_interval)
