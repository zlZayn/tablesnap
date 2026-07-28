"""Global-hotkey polling — non-blocking, main-thread safe.

The ``keyboard`` library's ``add_hotkey`` dispatches callbacks on a
background thread, which conflicts with GUI frameworks (tkinter, etc.)
that require all UI work to happen on the main thread.

This module uses **polling** instead: ``wait_for_hotkey()`` loops in the
*caller's* thread, so it is safe to use alongside tkinter.
"""

import time

import keyboard


def wait_for_hotkey(hotkey: str, poll_interval: float = 0.05) -> None:
    """Block the current thread until *hotkey* is pressed.

    Waits for the hotkey to be *released* before returning so that the
    caller's debounce / re-entry guard does not immediately re-trigger.

    Args:
        hotkey:       Key combination understood by ``keyboard.is_pressed``,
                      e.g. ``"ctrl+alt+s"``.
        poll_interval: Seconds between key-state polls (default 50 ms).
    """
    while True:
        if keyboard.is_pressed(hotkey):
            # Wait for release to prevent immediate re-trigger
            while keyboard.is_pressed(hotkey):
                time.sleep(poll_interval)
            return
        time.sleep(poll_interval)
