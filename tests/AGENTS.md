# tests/ — 规则层

继承根规则，见 [../AGENTS.md](../AGENTS.md)。

tests/ 特有约束：
- 单测不许依赖 Ollama / 网络 / 摄像头，必须可离线跑
- test_output/ 是生成物，不手工编辑；运行前自动清理
- 新增模块时同步补对应单测，并在 [README.md](README.md) 文件索引登记
- 命令用 `uv run python -m pytest`，不用 `uv run pytest`（本机 uv trampoline 问题）