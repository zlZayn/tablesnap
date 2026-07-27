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

## 快速启动

```powershell
.\run.ps1
```

## 项目结构

```
screenshot_ocr/
├── main.py              # 入口（薄）
├── core/
│   ├── config.py        # 统一配置（路径、参数、常量）
│   ├── hotkey.py        # 全局热键轮询（主线程安全）
│   └── pipeline.py      # 工作流编排
├── capture/
│   ├── screen.py        # 底层截图（mss）
│   └── selector.py      # 选区覆盖层（tkinter）
├── ocr/
│   ├── preprocessor.py  # 图像预处理（3x放大 + CLAHE + 锐化）
│   ├── engine.py        # EasyOCR 识别 + 坐标聚类列检测
│   └── corrector.py     # 轻量后处理纠错（字符替换，不启发式重建）
├── output/
│   └── excel.py         # Excel 导出
├── outputs/             # 识别结果存放目录
├── pyproject.toml       # 项目依赖
├── run.ps1              # 一键启动脚本
└── README.md
```

## 技术栈

- 选区：tkinter 全屏叠加层（拖拽选择）
- 截图：mss
- 预处理：OpenCV（CLAHE 对比度增强 + 3x 放大 + 锐化）
- OCR：EasyOCR（中文 + 英文，PyTorch 后端，支持 GPU 加速）
- 后处理：轻量字符替换纠错（仅做字符映射，不进行启发式数字重建）
- 列检测：坐标聚类算法，自动识别表格列边界
- 导出：openpyxl
- 快捷键：keyboard

## 依赖

```bash
uv sync
```

> **注意**：默认安装 CPU 版 PyTorch。如果有 NVIDIA GPU（CUDA），需手动替换为 CUDA 版以加速：
> ```bash
> uv pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124
> ```

