# tablesnap — 维护索引

## 全局规则（3-5 条，本项目特有）
- 只改文档与结构，不动功能逻辑；分层约定：AGENTS.md 只写规则，README.md 只写是什么/怎么改（双语文档见 [README_zh.md](README_zh.md)）
- 新可调常量必须登记进 core/config.py 的 _OVERRIDABLE 白名单，否则无法外部覆盖（见 [core/README.md](core/README.md)）
- 用户可见输出一律走 core/output.py，不得在别处直接 import rich（见 [core/README.md](core/README.md)）
- 结构性取舍必须写决策记录，含 Alternatives considered（见 [.agents/notes/](.agents/notes/)）
- 文档改动后跑链接校验，断链必修（check-links.py 位于 maintenance-flow 技能目录）

## 常用命令（可执行规范）
- 单测（无需 Ollama）：uv run python -m pytest -q
- 端到端（需 Ollama + qwen3-vl:4b-instruct）：uv run python tests/test_end_to_end.py
- 生效配置：uv run python main.py --print-config
- 启动：uv run python main.py，或双击 Launch Tablesnap Tool.cmd
- 重新锁（镜像可自由更换，按需指定）：uv lock --default-index <PyPI 镜像源>

## 验证快照（2026-08-24 实测）
- pytest：10 passed / 0 failed（单测；test_vlm 6 + test_xlsx 4）
- 端到端：未验证（需本地 Ollama + 模型）

## 待办
- [ ] Ollama 可用时跑端到端测试并回填验证快照

## 活跃坑
- uv run pytest 在本机报 uv trampoline 错误；用 uv run python -m pytest（见 [tests/README.md](tests/README.md)）
- tests/test_output/ 运行前自动清理旧 .xlsx/.json；目录为生成物勿手改（见 [tests/README.md](tests/README.md)）

## 文档地图
- 架构 → [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) · 哲学 → [docs/PHILOSOPHY.md](docs/PHILOSOPHY.md) · 部署 → [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)
- 模块手册 → [core/README.md](core/README.md) · [capture/README.md](capture/README.md) · [export/README.md](export/README.md) · [vlm/README.md](vlm/README.md) · [tests/README.md](tests/README.md)