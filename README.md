# 截图OCR转Excel工具

快捷键截图 → 自动识别文字 → 检测分列结构 → 导出 Excel。

## 快速开始

```bash
cd D:\PythonDirectory\screenshot_ocr
uv run python main.py
```

启动后按 `Ctrl+Alt+S` 截图（拖拽选择区域），Excel 自动保存到项目内 `outputs/` 目录。

## 使用说明

1. 打开需要截图的画面（如股票行情列表）
2. 按 `Ctrl+Alt+S`
3. 屏幕变暗 → 鼠标拖拽框选要识别的区域 → 松开自动识别
4. 去项目内 `outputs/` 目录查看生成的 Excel 文件

## 打包版

```bash
dist\ScreenshotOCR.exe
```

无需 Python 环境，双击运行即可。

## 项目结构

```
screenshot_ocr/
├── main.py           # 入口：热键轮询 + 工作流编排
├── selector.py       # 选区覆盖层：全屏变暗, 拖拽选区域
├── screenshot.py     # 底层截图：全屏截图 + 临时文件保存
├── ocr_engine.py     # OCR 识别 + 坐标聚类列检测
├── excel_export.py   # Excel 导出
├── hotkey.py         # 全局热键轮询（主线程安全）
├── outputs/          # 识别结果存放目录
├── pyproject.toml    # 项目依赖
├── build.bat         # 打包脚本
└── README.md
```

## 技术栈

- 选区：tkinter 全屏叠加层（拖拽选择）
- 截图：mss
- OCR：RapidOCR（基于 ONNX Runtime，中文识别优化）
- 列检测：坐标聚类算法，自动识别表格列边界
- 导出：openpyxl
- 快捷键：keyboard

## 依赖

```bash
uv sync
```

## 打包

```bash
build.bat
```
