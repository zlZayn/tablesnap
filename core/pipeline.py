"""Workflow orchestration — ties capture, OCR, and export together."""

import time

from core.config import DEBOUNCE, HOTKEY
from core.hotkey import wait_for_hotkey
from ocr.engine import recognize_text
from output.excel import export_to_excel
from capture.selector import capture_region


def process_screenshot() -> None:
    """Select a screen region -> OCR -> export Excel."""
    try:
        print("请用鼠标拖拽选择要识别的区域（按 Esc 取消）...")
        image_path = capture_region()

        if image_path is None:
            print("已取消")
            return

        print("正在识别文字...")
        lines = recognize_text(image_path)
        print(f"识别到 {len(lines)} 行")

        print("正在导出 Excel...")
        excel_path = export_to_excel(lines)
        print(f"Excel 已保存到: {excel_path}")
        print("完成！")
    except Exception as exc:
        print(f"处理失败: {exc}")


def main_loop() -> None:
    """Print banner and enter the hotkey-polling loop."""
    print("=" * 40)
    print("      截图 OCR 转 Excel 工具")
    print("=" * 40)
    print(f"  快捷键：{HOTKEY}")
    print("  操作：拖拽选择要识别的屏幕区域")
    print("  保存：项目目录/outputs/")
    print("  退出：Ctrl+C")
    print("=" * 40)

    try:
        while True:
            wait_for_hotkey(HOTKEY)
            time.sleep(DEBOUNCE)
            process_screenshot()
    except KeyboardInterrupt:
        print("\n已退出")
