# core/ — 配置与编排

- 职责：配置加载与覆盖、热键轮询、统一输出、流程编排
- config.py：全部可调常量 + `_OVERRIDABLE` 白名单 + 覆盖加载（config.json / TABLESNAP_* 环境变量）；被全项目依赖；改后必跑 `uv run python main.py --print-config` 与单测
- output.py：`console` 与全部 print_* / spinner；被 pipeline.py、main.py 依赖；改动影响所有终端外观，无单测覆盖，改后手动验证
- hotkey.py：`wait_for_hotkey()` 轮询（默认 50 ms）；被 pipeline.py 依赖；改后手动验证热键触发与防抖
- pipeline.py：`main_loop` / `process_screenshot` / `process_image_file` / `_ensure_ollama`；被 main.py 依赖；单测不覆盖，改后手动跑
- 变更影响路由：改这里 → 同步根 [AGENTS.md](../AGENTS.md) 待办/坑；契约变化写 [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md)
- 使用约束与工作偏好 → 见 [AGENTS.md](AGENTS.md)