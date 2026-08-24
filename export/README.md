# export/ — XLSX 导出

- 职责：PSV 文本 → XLSX（fence 提取、csv.reader 解析、CJK 感知列宽自适应）
- xlsx.py：`psv_to_xlsx()`（PSV → 文件）、`export_to_xlsx()`（网格 → 文件）、`display_width()`（全角计数）；被 core/pipeline.py、tests/test_xlsx.py、tests/test_end_to_end.py 依赖
- 改后必跑：tests/test_xlsx.py（4 用例，覆盖 fence / 空值 / 时间戳）
- 契约：空文本抛 `ValueError`；输出文件名 `{timestamp}.xlsx`，默认目录 results/
- 变更影响路由：改这里 → 输出契约变化写 [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md) Stage 3；同步根 [README.md](../README.md)
- 使用约束与工作偏好 → 见 [AGENTS.md](AGENTS.md)