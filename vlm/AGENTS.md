# vlm/ — 规则层

继承根规则，见 [../AGENTS.md](../AGENTS.md)。

vlm/ 特有约束：
- 协议层保持 stdlib-only，不引入第三方 HTTP 依赖
- 提示词统一放 prompts.py；输出格式缺陷先改提示词，不写正则后处理（见 [docs/PHILOSOPHY.md](../docs/PHILOSOPHY.md)）
- 返回契约（`ERROR:` 前缀 / `NO_TABLE` / PSV）由 core/pipeline.py 消费，改动需同步 [core/README.md](../core/README.md)
- 不写“有什么文件/怎么改”，那是 [README.md](README.md) 的职责