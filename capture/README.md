# capture/ — 截图与选区

- 职责：全屏截图（mss）+ tkinter 暗化选区 + 保存裁剪 PNG 到 results/captures/
- screen.py：`capture_screen()`（mss 全屏）、`save_temp()`（PNG 落盘）；被 selector.py 依赖
- selector.py：`RegionSelector` 覆盖层 + `capture_region()` 入口；被 [core/pipeline.py](../core/README.md) 依赖；改后手动验证拖拽 / Esc 取消 / 最小尺寸（MIN_SIZE）
- 截图输出目录由 core/config.py 的 `CAPTURES_DIR` 决定，`OUTPUT_DIR` 被覆盖时自动跟随
- 变更影响路由：改这里 → 同步根 [AGENTS.md](../AGENTS.md) 坑；行为契约变化写 [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md) Stage 1
- 使用约束与工作偏好 → 见 [AGENTS.md](AGENTS.md)