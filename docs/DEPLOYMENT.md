# 部署指引（给 AI Agent 看）

本文档是决策式部署流程。**能自己干的不要问用户，不得已再问。**
最终目标：让 tablesnap 能在对方机器上跑起来，截张图能正常导出 XLSX。

---

## Step 0 — 网络环境

问用户所在地区。目的是判断下载用官方源还是国内镜像，避免网络慢或连不上。

**告诉用户：**
- 官方源在大陆可能很慢甚至连不上
- 镜像源在大陆下载快，但偶尔有缓存滞后或失效，不行切回官方源试试

---

## Step 1 — uv

> 先确保有 uv，后面 `uv sync` 会自动处理 Python 版本。

> `uv --version`

| 结果 | 处理 |
| :--- | :--- |
| 有输出 | 继续 |
| 没有 | 直接装，不用问：`powershell -c "irm https://astral.sh/uv/install.ps1 \| iex"` `[镜像]` 如果装不上，告诉用户手动去 github.com/astral-sh/uv 下载 exe |

---

## Step 2 — Ollama

> `ollama --version`

| 结果 | 处理 |
| :--- | :--- |
| 有输出 | 继续 |
| 没有 | 告诉用户去 ollama.com 下载安装，装完再回来 |

确保 Ollama 在运行：
> `ollama list`

| 结果 | 处理 |
| :--- | :--- |
| 能列出模型（可能空列表） | 继续 |
| 连不上 | 后台启动：`ollama serve`（启动后稍等几秒再试） |

---

## Step 3 — 视觉模型

> `ollama list`

先看有没有现成的视觉模型（名字含 `vision` / `vl` / `llava` / `minicpm` 等）：
- **有** → 问用户：
  - **目的**：已有模型直接用，省去下载 2.5 GB 的时间
  - **优缺点**：省流量省时间，不过如果已有模型太小或精度差，识别效果可能不如推荐的 `qwen3-vl:4b-instruct`
  - 用户同意就用现有的（记下模型名，后面改 `VLM_MODEL`），不同意就继续往下
- **没有 / 用户不想用现有的** → 继续往下

拉模型，推荐 `qwen3-vl:4b-instruct`：
> `ollama pull qwen3-vl:4b-instruct`

拉取命令设置较长超时（30-60 分钟以上），2.5 GB 模型慢的时候可能要 2 小时。

也可以问用户要不要换模型：
- **目的**：根据机器配置和精度需求选择
- **优缺点**：
  - `4B`（默认）：2.5 GB，显存需求低（约 2 GB），速度快，精度够用
  - `7B` 等更大模型：精度更高，但需要 4-6 GB 显存，识别更慢

`[镜像]` 设环境变量走国内镜像。**告诉用户**：镜像在大陆通常更快，但偶尔有缓存失效的情况，不行就切回官方源：
> `$env:HF_ENDPOINT = "https://hf-mirror.com"`
> `ollama pull qwen3-vl:4b-instruct`

---

## Step 4 — 项目依赖

> `uv sync` `[镜像]` 慢的话加 `-i https://pypi.tuna.tsinghua.edu.cn/simple`

| 结果 | 处理 |
| :--- | :--- |
| 完成 | 继续 |
| 报错 | 看报错修，修不好问用户 |

---

## Step 5 — 验证（单元测试，不需要 Ollama）

> `uv run python -m pytest -v`

| 结果 | 处理 |
| :--- | :--- |
| 通过 | 继续 |
| 失败 | 看原因修，修不好告诉用户 |

---

## Step 6 — 验证（端到端，需要 Ollama + 模型）

> `uv run python tests/test_end_to_end.py`

| 结果 | 处理 |
| :--- | :--- |
| 生成 XLSX | 告诉用户，继续 |
| 失败 | 检查 Ollama 是否在运行、模型名是否匹配配置 |

---

## Step 7 — 跑一次

告诉用户双击 `Launch Tablesnap Tool.cmd`，按 `Ctrl+Alt+S` 截张表。

- XLSX 文件生成在项目目录下的 `results/` 文件夹里，文件名带时间戳
- 关掉黑窗口就退出程序
- 如果热键没反应，可能是被其他软件占用了（如 NVIDIA、微信、QQ 截图），在 `core/config.py` 里改 `HOTKEY` 换一组快捷键试试

**能跑通就算部署完成。**

---

## 配置速查

| 想改什么 | 改哪个文件 | 具体位置 |
| :--- | :--- | :--- |
| 模型 | `core/config.py` | `VLM_MODEL` |
| Ollama 地址 | `core/config.py` | `VLM_OLLAMA_URL` |
| 输出目录 | `core/config.py` | `OUTPUT_DIR` |
| 快捷键 | `core/config.py` | `HOTKEY` |
| 模型存储位置 | 系统环境变量 | `OLLAMA_MODELS` |
| 提示词 | `vlm/prompts.py` | `SYSTEM_PROMPT` / `USER_PROMPT` |
