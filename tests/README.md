# tests/ — 测试与调试工具

- 职责：单元测试、端到端脚本、调试工具、样本/输出目录
- test_vlm.py：`OllamaClient.analyze()` 6 个 mock 用例（无需 Ollama）
- test_xlsx.py：`psv_to_xlsx()` 4 用例（基础 / fence / 空值 / 时间戳）
- test_end_to_end.py：5 张样本图全流程（需 Ollama + 模型）；`--show` 离线回放 _report.json；输出到 test_output/
- read_xlsx.py：调试工具，`uv run python tests/read_xlsx.py path/to/file.xlsx`
- test_table_pics/：5 张样本表图；test_output/：输出与 _report.json（gitignored）
- 常用命令：`uv run python -m pytest -q`（单测 10 用例）；`uv run python tests/test_end_to_end.py [--show]`（E2E）
- 坑：`uv run pytest` 在本机报 uv trampoline 错误，必须用 `uv run python -m pytest`
- 变更影响路由：改 core/export/vlm → 先跑对应单测；改提示词或端到端 → 跑 E2E
- 回根：规则继承见 [../AGENTS.md](../AGENTS.md)
- 使用约束与工作偏好 → 见 [AGENTS.md](AGENTS.md)