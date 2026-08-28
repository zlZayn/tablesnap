# vlm/ — VLM 识别

- 职责：Ollama 请求封装（stdlib urllib）+ 提示词集中管理
- client.py：`OllamaClient.analyze(image_bytes)`，POST /api/generate（base64 图片 + 双提示词）；被 core/pipeline.py、tests/test_vlm.py 依赖
- prompts.py：`SYSTEM_PROMPT` / `USER_PROMPT`；被 client.py 依赖；改提示词需人工 VLM 验证，影响所有识别质量
- 改后必跑：tests/test_vlm.py（6 用例，mock 网络，无需 Ollama）
- 返回契约：正常 PSV / `NO_TABLE` / `ERROR: ...`
- 变更影响路由：改这里 → 契约变化写 [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md) Stage 2；提示词改动参考 [docs/PHILOSOPHY.md](../docs/PHILOSOPHY.md)
- 回根：规则继承见 [../AGENTS.md](../AGENTS.md)
- 使用约束与工作偏好 → 见 [AGENTS.md](AGENTS.md)