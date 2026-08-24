# core/ — 规则层

继承根规则，见 [../AGENTS.md](../AGENTS.md)。

core/ 特有约束：
- 新可调常量必须登记进 `_OVERRIDABLE` 白名单，否则 config.json / 环境变量无法覆盖
- 用户可见输出不得绕过 output.py 直接 import rich
- 契约变更（默认值、键名、输出格式）需同步根 [README.md](../README.md) 与 [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md)
- 不写“有什么文件/怎么改”，那是 [README.md](README.md) 的职责