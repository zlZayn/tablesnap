"""快捷键监听功能"""
import keyboard
from typing import Callable


def start_hotkey_listener(hotkey: str, callback: Callable) -> None:
    """启动快捷键监听

    Args:
        hotkey: 快捷键组合，如 'ctrl+alt+s'
        callback: 触发时调用的回调函数
    """
    print(f"快捷键已设置: {hotkey}")
    print("按 Ctrl+C 退出程序")

    keyboard.add_hotkey(hotkey, callback)
    keyboard.wait()  # 阻塞等待
