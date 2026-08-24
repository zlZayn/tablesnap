# export/ — 规则层

继承根规则，见 [../AGENTS.md](../AGENTS.md)。

export/ 特有约束：
- 解析逻辑保持通用：不针对特定图片加条件分支；输出缺陷先改提示词，不加正则后处理（见 [docs/PHILOSOPHY.md](../docs/PHILOSOPHY.md)）
- 导出参数（OUTPUT_DIR）来自 core/config.py，不在本目录硬编码路径
- 不写“有什么文件/怎么改”，那是 [README.md](README.md) 的职责