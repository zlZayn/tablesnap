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

运行期参数不用改代码，按优先级 `环境变量 > config.json > 代码默认值`。
以下 16 个键均可覆盖（环境变量名 = `TABLESNAP_` + 键名）：

| 键 | 类型 | 默认值 | 作用 |
| :--- | :--- | :--- | :--- |
| `HOTKEY` | str | `ctrl+alt+s` | 截图快捷键 |
| `DEBOUNCE` | float | `0.3` | 触发后的防抖秒数 |
| `DIM_ALPHA` | float | `0.3` | 选区外变暗程度 |
| `MIN_SIZE` | int | `10` | 最小选框宽高（px） |
| `COLOR` | str | `#00BCD4` | 角标强调色 |
| `BORDER_COLOR` | str | `#666666` | 边框线颜色 |
| `CORNER_SIZE` | int | `5` | 角标半边长（px） |
| `LINE_W` | int | `1` | 边框线宽（px） |
| `LABEL_COLOR` | str | `#CCCCCC` | 尺寸文字颜色 |
| `LABEL_OFFSET` | int | `18` | 尺寸文字与选框间距（px） |
| `VLM_MODEL` | str | `qwen3-vl:4b-instruct` | Ollama 模型名 |
| `VLM_OLLAMA_URL` | str | `http://localhost:11434` | Ollama 服务地址 |
| `VLM_TIMEOUT` | int | `30` | 单次请求超时（秒） |
| `VLM_TEMPERATURE` | float | `0.1` | 生成温度 |
| `VLM_NUM_PREDICT` | int | `2048` | 最大输出 token 数 |
| `OUTPUT_DIR` | path | `results/` | 输出目录（`captures/` 自动跟随） |

### 覆盖方式

1. **复制模板**：项目根目录的 `config.example.json` 就是完整模板（16 键默认值，已提交到 git）。复制为 `config.json` 后改任意键：

   ```powershell
   Copy-Item config.example.json config.json
   ```

   或者直接新建 `config.json`，只写想改的键（未写的键用默认值）：

   ```json
   { "VLM_MODEL": "qwen3-vl:2b-instruct", "HOTKEY": "ctrl+alt+x" }
   ```

2. **环境变量**：`TABLESNAP_<键名>`，如 `TABLESNAP_VLM_MODEL`。优先级高于 `config.json`。

### 验证生效配置

改完配置后，用 `--print-config` 查看每个键的当前值和来源（`default` / `config.json` / `env:TABLESNAP_*`）：

```powershell
uv run python main.py --print-config
```

- `config.json` 已被 git 忽略，本地设置不会提交。
- `OUTPUT_DIR` 支持相对路径（基于项目根目录解析，如 `results`）和绝对路径。

### 不参与覆盖

- `LABEL_FONT`（元组类型）与路径常量 `PROJECT_ROOT` / `TEST_*`
- 提示词：写死在 `vlm/prompts.py` 的 `SYSTEM_PROMPT` / `USER_PROMPT`
- 模型存储位置：Ollama 自身配置（系统环境变量 `OLLAMA_MODELS`）

### 回退规则

非法值（类型不对、`None`、路径非字符串）会被静默忽略，回退到默认值。
完整覆盖机制见 `docs/ARCHITECTURE.md` 的 Configuration 章节。
