"""截图OCR转Excel工具 - 主程序"""
from screenshot import capture_screen
from ocr_engine import recognize_text
from excel_export import export_to_excel
from hotkey import start_hotkey_listener


def process_screenshot():
    """处理截图：截图 -> OCR -> 导出Excel"""
    try:
        print("正在截图...")
        image_path = capture_screen()
        print(f"截图保存到: {image_path}")

        print("正在识别文字...")
        lines = recognize_text(image_path)
        print(f"识别到 {len(lines)} 行文字")

        print("正在导出Excel...")
        excel_path = export_to_excel(lines)
        print(f"Excel已保存到: {excel_path}")

        print("完成！")
    except Exception as e:
        print(f"处理失败: {e}")


def main():
    print("=" * 40)
    print("截图OCR转Excel工具")
    print("=" * 40)
    print("功能：按快捷键截图，自动识别并导出Excel")
    print("默认快捷键：Ctrl+Alt+S")
    print("保存位置：桌面/stock_screenshots/")
    print("=" * 40)

    start_hotkey_listener('ctrl+alt+s', process_screenshot)


if __name__ == "__main__":
    main()
