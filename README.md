# 截图 → Excel（VLM 版）

截图 → VLM 视觉语言模型直接识别 → 导出 Excel。

## 快速开始

双击 `run.bat`，或：

```bash
cd D:\PythonDirectory\screenshot_ocr
uv run python main.py
```

启动后按 ``Ctrl+Alt+S`` 截图（拖拽选择区域），Excel 自动保存到项目内 ``results/`` 目录。

## 使用说明

1. 打开需要截图的画面（如股票行情列表）
2. 按 ``Ctrl+Alt+S``
3. 屏幕变暗 → 鼠标拖拽框选要识别的区域（框内显示原图）→ 松开自动识别并导出 Excel
4. 去项目内 ``results/`` 目录查看生成的 Excel 文件

> 提示：按下 ``Esc`` 可取消本次截图。

## 项目结构

 ```
screenshot_ocr/
├── main.py                  # 入口（薄）
├── core/
│   ├── config.py            # 统一配置（路径、参数、VLM）
│   ├── hotkey.py            # 全局热键轮询（主线程安全）
│   └── pipeline.py          # 工作流编排（capture → VLM → export）
├── capture/
│   ├── screen.py            # 底层截图（mss）
│   └── selector.py          # 选区覆盖层（tkinter, 框内显示原图）
├── vlm/
│   ├── client.py            # Ollama VLM API 客户端
│   └── prompts.py           # 提示词模板
├── export/
│   └── excel.py             # CSV → Excel 导出（fence 解析兜底）
├── tests/
│   ├── test_vlm.py          # VLM 客户端单测（mock HTTP）
│   ├── test_excel.py        # CSV 解析单测
│   ├── test_end_to_end.py   # 端到端批量测试
│   ├── read_excel.py        # 调试工具：读取 xlsx 打印为文本
│   ├── test_table_pics/     # 测试用截图（test_data_01~06.png）
│   └── test_output/         # 测试输出（每次自动清理旧 xlsx）
├── results/                 # 识别结果存放目录
├── docs/
│   └── ARCHITECTURE.md      # 架构文档（工作流、模块关系、算法逻辑）
├── pyproject.toml           # 项目依赖
├── run.bat                  # 双击启动脚本
└── README.md
```

## 技术栈

- 选区：tkinter 全屏叠加层（拖拽选择）
- 截图：mss
- 识别：Qwen3-VL 视觉语言模型（本地 Ollama）
- 导出：openpyxl
- 快捷键：keyboard

## 配置

所有可调参数集中在 ``core/config.py``：

| 分类 | 参数 | 默认值 | 说明 |
| :--- | :--- | :---: | :--- |
| 热键 | ``HOTKEY`` | ``ctrl+alt+s`` | 截图快捷键 |
| | ``DEBOUNCE`` | ``0.3`` | 防抖间隔（秒） |
| 选区 | ``DIM_ALPHA`` | ``0.3`` | 遮罩透明度 |
| | ``COLOR`` | ``#FF4444`` | 选取框颜色 |
| VLM | ``VLM_MODEL`` | ``qwen3-vl:4b-instruct`` | Ollama 模型名 |
| | ``VLM_OLLAMA_URL`` | ``http://localhost:11434`` | Ollama 服务地址 |
| | ``VLM_TIMEOUT`` | ``30`` | 请求超时（秒） |

## 前置要求

需在本地运行 Ollama 并加载 VLM 模型：

```bash
ollama pull qwen3-vl:4b-instruct
```

程序启动后：
1. 截图数据直接发送给 VLM 模型，模型返回结构化 CSV
2. CSV 写入 Excel（如果 VLM 用 ```csv 代码块包裹了结果会自动提取）
3. 若模型输出 ``NO_TABLE`` 或返回错误，程序给出提示和下一步建议

## 安装

```bash
uv sync
# （可选）安装静态检查工具
uv sync --group dev
```

## 端到端测试

```bash
# 批量测试全部测试图片（自动清理旧 xlsx）
uv run python tests/test_end_to_end.py

# 批量测试 + 打印每个 Excel 的文本内容
uv run python tests/test_end_to_end.py --dump

# 查看上次测试结果（不调 VLM）
uv run python tests/test_end_to_end.py --show

# 单张测试
uv run python tests/test_end_to_end.py --image test_data_01.png
```

测试输出位于 `tests/test_output/`，每次运行前自动清理旧 `.xlsx` 文件，
仅保留最新结果。

### 调试工具：直接查看 Excel 内容

调试时可随时用 `read_excel.py` 读取任意 Excel 文件：

```bash
# 读取全部行
uv run python tests/read_excel.py tests/test_output/file.xlsx

# 只读前 5 行
uv run python tests/read_excel.py tests/test_output/file.xlsx --rows 5
```
