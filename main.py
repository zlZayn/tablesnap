"""截图OCR转Excel工具"""

from screenshot import capture_screen


def main() -> None:
    path = capture_screen()
    print(f"截图保存到: {path}")


if __name__ == "__main__":
    main()
