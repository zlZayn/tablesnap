> **ARCHIVED — Historical design document only.**  
> This spec describes the original VLM refactor (EasyOCR → VLM) and is kept for reference.
> The live codebase has since diverged: see `docs/ARCHITECTURE.md` and `README.md` for current state.

# screenshot-ocr VLM 重构设计

## 背景

原项目使用 EasyOCR + OpenCV 预处理 + 视觉列检测 + 多步纠错链来做截图表格提取，
pipeline 过长（5 步），依赖沉重（easyocr, torch, torchvision, opencv）。
重构为 VLM（Visual Language Model）直出方案，让 qwen3-vl:4b-instruct 一次性完成
"看图 → 识别文字 → 理解表格结构 → 输出 CSV"。

## 架构

```
main.py  (入口)
  │
  └── core/pipeline.py  (工作流编排)
        ├── capture/selector.py  — tkinter 选区覆盖层 + mss 截图
        ├── vlm/client.py        — Ollama API 调用（传 base64 图片 → 收文本）
        │     └── vlm/prompts.py — 所有提示词模板统一管理
        └── output/excel.py      — CSV → openpyxl Excel 导出
```

## 数据流

```
Ctrl+Alt+S
  → tkinter 全屏暗化 + 鼠标拖拽选区域
  → mss 截图裁剪为 PNG
  → base64 编码发 Ollama (qwen3-vl:4b-instruct)
  → 模型返回 CSV 文本 (```csv ... ```)
  → CSV 解析器提取结构化数据
  → openpyxl 写入 .xlsx → outputs/
  → 终端打印摘要
```

## 模块职责

| 模块 | 职责 | 文件数 |
|------|------|--------|
| `core/config.py` | 统一配置（路径、模型名、超时、温度） | 1 |
| `core/hotkey.py` | Ctrl+Alt+S 全局热键轮询（不变） | 1 |
| `core/pipeline.py` | 流程编排（3 步：capture → vlm → excel） | 1 |
| `capture/screen.py` | mss 底层全屏截图 | 1 |
| `capture/selector.py` | tkinter 选区覆盖层 | 1 |
| `vlm/client.py` | Ollama API 封装（请求/重试/超时/解析） | 1 |
| `vlm/prompts.py` | 所有提示词集中管理 + 版本注释 | 1 |
| `output/excel.py` | CSV → openpyxl 导出 | 1 |

## 命名变更

| 旧 | 新 | 理由 |
|----|----|------|
| `ocr/` | `vlm/` | 不再 OCR，是 VLM 看图理解 |
| `ocr/engine.py` | 删除 → 拆为 `vlm/client.py` + `vlm/prompts.py` | engine 职责模糊 |
| `ocr/preprocessor.py` | 删除 | VLM 不需要预处理 |
| `ocr/features.py` | 删除 | VLM 自带视觉理解 |
| `ocr/layout.py` | 删除 | VLM 自带布局理解 |
| `ocr/filters.py` | 删除 | 垃圾行由 VLM 自行过滤 |
| `ocr/correction/` | 删除 | 后纠错不再需要 |

## CSV 输出可靠性

模型输出不稳定会直接破坏 CSV 解析。防御策略：

### 分层解析

1. 优先提取 ` ```csv ... ``` ` 代码块内容
2. 无代码块时尝试将全文按 CSV 解析
3. 空响应/解析失败 → 不崩溃，保存原始响应到文件供人工查看

### 数据校验

- 行数不足（无表头或空结果）→ 不写 Excel，打印警告
- 列数不一致 → 补齐/截断至大多数行的列数
- 单元格含逗号/引号 → `csv.reader` 标准解析

### 提示词稳定性

- system prompt 使用强约束（零废话、唯一CSV格式）
- temperature = 0.1（高确定性）
- num_predict = 2048（足够容纳绝大多数表格）
- 统一在 `vlm/prompts.py` 管理，可版本化

## 依赖变更

```
删除: easyocr, opencv-python-headless, torch, torchvision
保留: openpyxl, Pillow, mss, keyboard, numpy, rich
新增: 无（标准库 urllib 调 Ollama API）
```

## 旧模型缓存清理

| 缓存 | 大小 | 状态 |
|------|------|------|
| `~/.cache/torch/` | ~569 MB | 已清除 |
| `~/.EasyOCR/` | ~100 MB | 已清除 |
| Ollama: qwen3-vl:4b-instruct | 3.3 GB | 保留（主力） |
| Ollama: qwen3.5-vision | 6.5 GB | 保留（备选） |
