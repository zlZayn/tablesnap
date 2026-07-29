# 部署指引（给 AI Agent 看）

本文档是给 AI Agent 的交互式部署流程。**不要自动执行，每步先问对方。**
最终目标：让 tablesnap 能在对方机器上跑起来，截张图能正常导出 XLSX。

---

## 流程总览

一共 4 步，顺序推进：

1. 确认环境（Python + uv 装好没）
2. 装 Ollama + 拉模型
3. 装项目依赖
4. 跑起来验证

---

## 第 1 步：确认环境

先问对方 Python 和 uv 是否已安装。不要自己直接跑命令。

检查项：

- **Python**：跑 `python --version`，需要 >= 3.8
- **uv**：跑 `uv --version`，看看有没有

缺哪个就问对方要不要装。装 Python 让对方自己去 python.org 下载，
装 uv 给这条命令让他自己跑：

```
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**确认没问题再继续。**

---

## 第 2 步：Ollama + 模型

### 2.1 检查 Ollama 是否已装

别直接下载。先查：

- 跑 `ollama --version` — 有输出说明已装
- 或者看看环境变量里有没有 `OLLAMA_HOST`、`OLLAMA_MODELS`
- 或者问对方："Ollama 装过吗？"

**没装** → 问对方是否要装。如果愿意，让他自己去 ollama.com 下载安装。

### 2.2 拉取模型

推荐使用默认模型（小、快、够用）：

```
ollama pull qwen3-vl:4b-instruct
```

可以向对方确认："默认用 qwen3-vl:4b-instruct，大概 2.5 GB，要换别的吗？"
如果要换更大的（如 7B），提醒他显存需要 4-6 GB。

**确认模型拉完再继续。**

---

## 第 3 步：项目依赖

在项目目录下跑（告诉对方要在哪个目录执行）：

```
uv sync
```

这会装好 `pyproject.toml` 里所有依赖。**等跑完，确认没报错。**

---

## 第 4 步：验证跑通

分三层验证，每一层确认没问题再做下一层。

### 4.1 单元测试（不需要 Ollama）

```
uv run python -m pytest -v
```

所有测试应该通过。如果有失败的，停下来修。

### 4.2 手动启动 ollama

先确保 Ollama 在运行：

- 看看任务管理器有没有 `ollama.exe`
- 或者跑 `ollama list` 看能不能连上
- 没跑的话，让对方开个终端跑 `ollama serve`

### 4.3 端到端测试（需要 Ollama + 模型）

```
uv run python tests/test_end_to_end.py
```

所有测试图片都应该正常识别并生成 XLSX。

### 4.4 真正跑一次

让用户双击项目目录下的 `run.bat`（不要用命令行跑，因为是交互式
截图工具，双击更方便）。启动后按 `Ctrl+Alt+S`，框选屏幕上的表格区域，
松开后应该自动生成 XLSX 到 `results/` 目录。

**到这里能跑通就算部署完成。**

---

## 如果过程中需要改配置

告诉对方位置，问要不要改，不要直接改文件：

| 想改什么 | 改哪个文件 | 改哪一行 |
| :--- | :--- | :--- |
| 模型 | `core/config.py` | 第 34 行 `VLM_MODEL` |
| Ollama 地址 | `core/config.py` | 第 35 行 `VLM_OLLAMA_URL` |
| 输出目录 | `core/config.py` | 第 14 行 `OUTPUT_DIR` |
| 快捷键 | `core/config.py` | 第 19 行 `HOTKEY` |
| 模型存储位置 | 系统环境变量 | `OLLAMA_MODELS` |
| 提示词 | `vlm/prompts.py` | `SYSTEM_PROMPT` / `USER_PROMPT` |

---

## 关键原则

1. **先问，再动** — 每一步先确认对方意愿，不要自己偷偷执行
2. **推荐默认** — 模型用 `qwen3-vl:4b-instruct`，路径用默认，少折腾
3. **逐层验证** — 每步确认没问题再走下一步
4. **不要替对方下载** — 给链接和命令让他自己操作
